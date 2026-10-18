"""Zero-shot Türkiye evaluation: models trained on DISFOR (Europe) are applied, without any retraining, to
Turkish forest locations whose reference labels come from an independent source (Hansen Global Forest Change
tree cover loss year). Nothing in this script touches paper_v4/v5/v6 or the product bundle.

Stages (run in order; every stage is resumable and writes under experiments/turkiye_zero_shot/):
  prepare   sample candidate points from Hansen GFC inside Turkish forest regions, enforce 5 km separation,
            freeze the candidate list BEFORE any satellite data or model output is seen
  fetch     pull Sentinel-2 L2A observations for each point from the Earth Search STAC/COG archive and build
            the 24 x 10 monthly input exactly as in the data contract (SCL 4/5, monthly median, missing months masked)
  predict   run the frozen advanced_v3 ensemble (and optional full-cohort paper_v4 recipes) on the Turkish inputs
  report    metrics with 5 km component bootstrap, confusion matrices, a figure and a Markdown table

Needs network access to storage.googleapis.com (Hansen GFC tiles), earth-search.aws.element84.com (STAC) and
sentinel-cogs.s3.us-west-2.amazonaws.com (COGs). Run on a normal internet connection with the project .venv.

Reference-label caveat: Hansen "loss" is any stand-replacing tree cover loss (harvest, fire, storm, disease).
Candidates are restricted to compact loss patches to favour clear cuts, but the labels remain noisier than
DISFOR interpretations. The evaluation is therefore a transfer probe, and is reported as such.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
OUT = ROOT / 'experiments/turkiye_zero_shot'
BANDS = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12']
# Earth Search v1 asset keys for the ten bands and the scene classification layer
ASSETS = {'B02': 'blue', 'B03': 'green', 'B04': 'red', 'B05': 'rededge1', 'B06': 'rededge2', 'B07': 'rededge3',
          'B08': 'nir', 'B8A': 'nir08', 'B11': 'swir16', 'B12': 'swir22'}
SCL_ASSET = 'scl'
STAC = 'https://earth-search.aws.element84.com/v1/search'
GFC = 'https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/Hansen_GFC-2023-v1.11_{layer}_{tile}.tif'
# Turkish forest regions (lon_min, lat_min, lon_max, lat_max). Boxes, not administrative polygons.
REGIONS = {
    'bati_karadeniz': (31.0, 40.6, 34.5, 41.9),
    'dogu_karadeniz': (37.0, 40.4, 41.5, 41.5),
    'marmara_guney': (27.0, 39.3, 29.8, 40.4),
    'ege_mugla': (27.8, 36.6, 29.3, 37.6),
    'akdeniz_antalya_mersin': (30.0, 36.3, 34.0, 37.3),
}
LOSS_YEARS = [19, 20, 21, 22]          # Hansen lossyear codes -> target years 2019..2022
SEED = 20261018
EARTH_KM = 6371.0088


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp'); tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False)); tmp.replace(path)


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gfc_tile(lon, lat):
    """Hansen tiles are 10 x 10 degrees named by their top-left corner, e.g. 50N_030E covers lat 40..50, lon 30..40."""
    top = int(math.ceil(lat / 10.0) * 10); left = int(math.floor(lon / 10.0) * 10)
    return f"{abs(top):02d}{'N' if top >= 0 else 'S'}_{abs(left):03d}{'E' if left >= 0 else 'W'}"


# ---------------------------------------------------------------- pure helpers (unit tested)
def loss_patch_mask(lossyear, year_code, treecover, min_cover=50, window=5, min_agree=20):
    """True where the pixel is loss in year_code, had enough tree cover in 2000, and sits in a compact
    same-year loss patch (at least min_agree of the window x window neighbours share the year)."""
    same = (lossyear == year_code)
    k = window // 2
    padded = np.pad(same.astype(np.int32), k)
    count = np.zeros_like(lossyear, dtype=np.int32)
    for dy in range(window):
        for dx in range(window):
            count += padded[dy:dy + lossyear.shape[0], dx:dx + lossyear.shape[1]]
    return same & (treecover >= min_cover) & (count >= min_agree)


def stable_mask(lossyear, treecover, datamask, min_cover=50, window=7):
    """True where tree cover is high and no loss is recorded in the window x window neighbourhood (2001 to 2023)."""
    k = window // 2
    anyloss = np.pad((lossyear > 0).astype(np.int32), k)
    count = np.zeros_like(lossyear, dtype=np.int32)
    for dy in range(window):
        for dx in range(window):
            count += anyloss[dy:dy + lossyear.shape[0], dx:dx + lossyear.shape[1]]
    return (count == 0) & (treecover >= min_cover) & (datamask == 1)


def greedy_separate(points, min_km, rng, fixed=(), limit=None):
    """Keep a random subset of points so that every kept pair (and every kept point versus the fixed points)
    is at least min_km apart (haversine). Stops after `limit` kept points."""
    from sklearn.neighbors import BallTree
    order = rng.permutation(len(points)); kept = []
    coords = np.deg2rad(np.array([[p['lat'], p['lon']] for p in points]))
    anchor = [np.deg2rad([p['lat'], p['lon']]) for p in fixed]
    tree = BallTree(np.array(anchor), metric='haversine') if anchor else None
    for i in order:
        if tree is not None:
            d = tree.query(coords[i:i + 1], k=1)[0][0][0] * EARTH_KM
            if d < min_km:
                continue
        kept.append(int(i)); anchor.append(coords[i]); tree = BallTree(np.array(anchor), metric='haversine')
        if limit and len(kept) >= limit:
            break
    return [points[i] for i in kept]


def harmonize_dn(values, processing_baseline):
    """Sentinel-2 L2A scenes processed with baseline >= 04.00 carry a +1000 BOA offset; DISFOR values do not.
    The offset is removed so that Turkish inputs are on the same digital-number scale as the training data."""
    try:
        major = float(str(processing_baseline).split('.')[0])
    except (ValueError, AttributeError):
        major = 0.0
    v = np.asarray(values, dtype=np.float64)
    return np.clip(v - 1000.0, 0, None) if major >= 4 else v


def monthly_inputs(observations, target_year):
    """observations: list of dicts with keys date (YYYY-MM-DD), scl, bands (list of 10 DN). Returns x[24,10], observed[24,10].
    Rule identical to the data contract: keep SCL 4/5 only, take the per-band median within each calendar month,
    leave months without clear observations masked. Both years need at least six observed months."""
    x = np.zeros((24, 10), dtype=np.float32); observed = np.zeros((24, 10), dtype=bool)
    buckets = {}
    for o in observations:
        if int(o['scl']) not in (4, 5):
            continue
        d = datetime.strptime(o['date'][:10], '%Y-%m-%d').date()
        slot = (d.year - (target_year - 1)) * 12 + d.month - 1
        if 0 <= slot < 24:
            buckets.setdefault(slot, []).append(o['bands'])
    for slot, rows in buckets.items():
        arr = np.asarray(rows, dtype=np.float64)
        if np.isfinite(arr).all() and len(arr):
            x[slot] = np.median(arr, axis=0); observed[slot] = True
    months = observed.any(-1)
    eligible = months[:12].sum() >= 6 and months[12:].sum() >= 6
    return x, observed, bool(eligible)


# ---------------------------------------------------------------- stage: prepare
def prepare(n_loss=120, n_stable=120, min_km=5.0):
    import rasterio
    from rasterio.windows import from_bounds
    rng = np.random.default_rng(SEED)
    candidates = []
    for region, (x0, y0, x1, y1) in REGIONS.items():
        tiles = {gfc_tile(lon, lat) for lon in (x0, x1) for lat in (y0, y1)}
        for tile in tiles:
            layers = {}
            for layer in ['lossyear', 'treecover2000', 'datamask']:
                url = GFC.format(layer=layer, tile=tile)
                with rasterio.open(url) as src:
                    b = src.bounds
                    bx0, by0, bx1, by1 = max(x0, b.left), max(y0, b.bottom), min(x1, b.right), min(y1, b.top)
                    if bx0 >= bx1 or by0 >= by1:
                        layers = None; break
                    win = from_bounds(bx0, by0, bx1, by1, src.transform)
                    layers[layer] = src.read(1, window=win)
                    layers['transform'] = src.window_transform(win)
            if not layers:
                continue
            ly, tc, dm, tr = layers['lossyear'], layers['treecover2000'], layers['datamask'], layers['transform']
            print(region, tile, ly.shape, flush=True)
            for code in LOSS_YEARS:
                rows, cols = np.nonzero(loss_patch_mask(ly, code, tc))
                take = rng.choice(len(rows), size=min(len(rows), 30000), replace=False) if len(rows) else []
                for i in take:
                    lon, lat = tr * (cols[i] + 0.5, rows[i] + 0.5)
                    candidates.append(dict(region=region, tile=tile, lon=float(lon), lat=float(lat), label=1, target_year=2000 + code, source='GFC-2023-v1.11 lossyear'))
            rows, cols = np.nonzero(stable_mask(ly, tc, dm))
            take = rng.choice(len(rows), size=min(len(rows), 8000), replace=False) if len(rows) else []
            for i in take:
                lon, lat = tr * (cols[i] + 0.5, rows[i] + 0.5)
                candidates.append(dict(region=region, tile=tile, lon=float(lon), lat=float(lat), label=0, target_year=int(rng.choice([2019, 2020, 2021, 2022])), source='GFC-2023-v1.11 no loss 2001-2023'))
    loss = [c for c in candidates if c['label'] == 1]; stable = [c for c in candidates if c['label'] == 0]
    chosen_loss = greedy_separate(loss, min_km, rng, limit=n_loss)
    chosen_stable = greedy_separate(stable, min_km, rng, fixed=chosen_loss, limit=n_stable)
    final = chosen_loss + chosen_stable
    for i, c in enumerate(final):
        c['id'] = f"tr-{c['region'][:4]}-{i:04d}-{c['target_year']}"
    # Distance to every DISFOR location used in development (must exceed min_km; Türkiye is far from the cohort anyway).
    manifest = read(ROOT / 'data/disfor/sample_manifest.json')
    from sklearn.neighbors import BallTree
    tree = BallTree(np.deg2rad([[m['lat'], m['lon']] for m in manifest]), metric='haversine')
    nearest = tree.query(np.deg2rad([[c['lat'], c['lon']] for c in final]), k=1)[0][:, 0] * EARTH_KM
    protocol = dict(version='turkiye_zero_shot_v1', frozen_at_utc=datetime.now(timezone.utc).isoformat(), seed=SEED,
                    regions=REGIONS, loss_year_codes=LOSS_YEARS, reference='Hansen GFC-2023-v1.11 (lossyear, treecover2000, datamask)',
                    positive_rule='lossyear in target year, treecover2000 >= 50, >= 20 of 25 pixels in 5x5 window share the loss year',
                    negative_rule='treecover2000 >= 50, no loss 2001-2023 in 7x7 window, datamask == 1, random target year 2019-2022',
                    separation_km=min_km, n_candidates=len(final), n_loss=len(chosen_loss), n_stable=len(chosen_stable),
                    min_distance_to_disfor_km=float(nearest.min()),
                    models='advanced_v3 bundle, frozen threshold; optional full-cohort paper_v4 recipes', retraining='none',
                    caveats=['Hansen loss includes fire, storm and disease; compact-patch rule favours but does not guarantee clear cuts',
                             'Negative class uses absence of recorded loss, which can miss unrecorded disturbance',
                             'Processing-baseline BOA offset removed for scenes >= 04.00 to match DISFOR DN scale',
                             'Only SCL 4/5 clear filter is available here; DISFOR additionally used a source clear flag'])
    write(OUT / 'protocol.json', protocol); write(OUT / 'candidates.json', final)
    write(OUT / 'signature.json', dict(protocol=digest(OUT / 'protocol.json'), candidates=digest(OUT / 'candidates.json'),
                                       bundle=digest(ROOT / 'models/advanced_v3/bundle.json')))
    print(json.dumps({k: protocol[k] for k in ['n_candidates', 'n_loss', 'n_stable', 'min_distance_to_disfor_km']}, indent=2))


# ---------------------------------------------------------------- stage: fetch
def stac_items(lon, lat, start, end, max_per_month=2):
    import requests
    body = dict(collections=['sentinel-2-l2a'], intersects=dict(type='Point', coordinates=[lon, lat]),
                datetime=f'{start}T00:00:00Z/{end}T23:59:59Z', limit=500, fields=dict(include=['id', 'properties', 'assets']))
    items = []
    url = STAC
    while url:
        for attempt in range(6):          # Earth Search occasionally answers 502; back off and retry
            r = requests.post(url, json=body, timeout=60)
            if r.status_code < 500:
                break
            time.sleep(5 * (attempt + 1))
        r.raise_for_status(); page = r.json()
        items += page.get('features', [])
        nxt = [l for l in page.get('links', []) if l.get('rel') == 'next']
        url = nxt[0]['href'] if nxt else None; body = nxt[0].get('body', body) if nxt else body
    # keep the clearest scenes per month to bound the number of range requests
    by_month = {}
    for it in items:
        d = it['properties']['datetime'][:7]; by_month.setdefault(d, []).append(it)
    out = []
    for d, its in by_month.items():
        its.sort(key=lambda i: i['properties'].get('eo:cloud_cover', 100))
        out += its[:max_per_month]
    return out


def read_pixel(url, lon, lat):
    import rasterio
    from rasterio.warp import transform
    with rasterio.Env(AWS_NO_SIGN_REQUEST='YES', GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif,.TIF', GDAL_HTTP_MAX_RETRY='3', GDAL_HTTP_RETRY_DELAY='2', CPL_VSIL_CURL_USE_HEAD='NO'):
        with rasterio.open(url) as src:
            x, y = transform('EPSG:4326', src.crs, [lon], [lat])
            row, col = src.index(x[0], y[0])
            if not (0 <= row < src.height and 0 <= col < src.width):
                return None
            return float(src.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])


def fetch_one(c):
    dest = OUT / 'observations' / (c['id'] + '.json')
    if dest.exists():
        return c['id'], 'cached'
    y = c['target_year']
    items = stac_items(c['lon'], c['lat'], f'{y-1}-01-01', f'{y}-12-31')
    obs = []
    for it in items:
        try:
            scl = read_pixel(it['assets'][SCL_ASSET]['href'], c['lon'], c['lat'])
        except Exception:
            continue                      # unreadable scene: skip it rather than failing the whole point
        if scl is None:
            continue
        rec = dict(date=it['properties']['datetime'][:10], item=it['id'], scl=int(scl), baseline=it['properties'].get('s2:processing_baseline', ''), bands=None)
        if int(scl) in (4, 5):
            try:
                vals = [read_pixel(it['assets'][ASSETS[b]]['href'], c['lon'], c['lat']) for b in BANDS]
            except Exception:
                continue
            if any(v is None for v in vals):
                continue
            rec['bands'] = harmonize_dn(vals, rec['baseline']).tolist()
        obs.append(rec)
    write(dest, dict(candidate=c, observations=obs, fetched_at_utc=datetime.now(timezone.utc).isoformat()))
    return c['id'], f'{len(obs)} scenes'


def fetch(workers=8):
    cands = read(OUT / 'candidates.json')
    (OUT / 'observations').mkdir(parents=True, exist_ok=True)
    start = time.time()
    pending = [c for c in cands if not (OUT / 'observations' / (c['id'] + '.json')).exists()]
    print(f'{len(cands) - len(pending)} already fetched, {len(pending)} to go; each point needs roughly 50 scenes x 11 small reads', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_one, c): c for c in pending}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                cid, msg = fut.result()
            except Exception as exc:
                cid, msg = futures[fut]['id'], f'FAILED: {exc}'
            print(f'{i}/{len(pending)} {cid} {msg} ({time.time()-start:.0f}s)', flush=True)


def build_npz():
    from orman_ssl.inputs import BANDS as CB, UNITS, monthly_days, validate_input
    cands = read(OUT / 'candidates.json'); xs, ms, ds, ids, labels, dropped = [], [], [], [], [], []
    for c in cands:
        f = OUT / 'observations' / (c['id'] + '.json')
        if not f.exists():
            dropped.append((c['id'], 'not fetched')); continue
        obs = [o for o in read(f)['observations'] if o['bands'] is not None]
        x, m, ok = monthly_inputs(obs, c['target_year'])
        if not ok:
            dropped.append((c['id'], 'fewer than 6 clear months in a year')); continue
        xs.append(x); ms.append(m); ds.append(monthly_days(c['target_year'])); ids.append(c['id']); labels.append(c['label'])
    meta = dict(kind='real', name='Türkiye zero-shot probe (Hansen GFC reference)', classes=['undisturbed_forest', 'clear_cut'], channels=CB,
                source='Earth Search sentinel-2-l2a COGs; BOA offset removed for baseline >= 04.00', units=UNITS,
                monthly_quality='Median of SCL 4/5 observations per calendar month; at least 6 valid months per year',
                label_provenance='Hansen GFC-2023-v1.11 lossyear / no-loss; independent of DISFOR; not field verified')
    data = dict(x=np.stack(xs).astype('float32'), observed=np.stack(ms), days=np.stack(ds).astype('float32'), ids=np.array(ids), metadata=json.dumps(meta))
    validate_input(data)
    np.savez_compressed(OUT / 'input.npz', **data)
    write(OUT / 'labels.json', dict(ids=ids, labels=labels, dropped=dropped))
    print('inputs', len(ids), 'dropped', len(dropped))


# ---------------------------------------------------------------- stage: predict / report
def predict(full_cohort_recipes=False):
    import orman_ssl.advanced as adv
    data = dict(np.load(OUT / 'input.npz', allow_pickle=False))
    res = adv.ensemble_predict(ROOT / 'models/advanced_v3/bundle.json', data)
    out = dict(advanced_v3=dict(ids=res['ids'], probabilities=[p[1] for p in res['probabilities']], predictions=res['predictions'], threshold=res['threshold']))
    if full_cohort_recipes:
        d = dict(np.load(ROOT / 'data/processed/real_series.npz', allow_pickle=False)); train = np.arange(len(d['y']))
        cfg = {c['name']: c for c in adv.CONFIGS}
        for name in ['rf_leaf4', 'cnn64', 'transformer48', 'ssl_transformer48']:
            probs = []
            for seed in [7, 17, 27]:
                state, _ = adv.fit(cfg[name], d, train, seed=seed, epochs=40, pre_epochs=60, labeled=train, early_stop=False)
                probs.append(adv.state_probability(state, data))
            out[f'full_cohort_{name}'] = dict(ids=list(map(str, data['ids'])), probabilities=np.mean(probs, 0).tolist(), per_seed=[p.tolist() for p in probs], threshold=0.5)
            print('trained', name, flush=True)
    write(OUT / 'predictions.json', out)


def report():
    from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, roc_auc_score
    from sklearn.neighbors import BallTree
    preds = read(OUT / 'predictions.json'); lab = read(OUT / 'labels.json'); cands = {c['id']: c for c in read(OUT / 'candidates.json')}
    y = np.array(lab['labels']); ids = lab['ids']
    coords = np.deg2rad([[cands[i]['lat'], cands[i]['lon']] for i in ids])
    # 5 km components for the bootstrap unit
    tree = BallTree(coords, metric='haversine'); parent = list(range(len(ids)))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, nb in enumerate(tree.query_radius(coords, r=5 / EARTH_KM)):
        for j in nb: parent[find(int(j))] = find(i)
    groups = np.array([find(i) for i in range(len(ids))]); uniq, gi = np.unique(groups, return_inverse=True)
    rng = np.random.default_rng(SEED); rows = []
    for name, r in preds.items():
        p = np.array(r['probabilities']); thr = r['threshold']; q = p >= thr
        cm = confusion_matrix(y, q, labels=[0, 1])
        boots = []
        for _ in range(2000):
            w = np.bincount(rng.integers(0, len(uniq), len(uniq)), minlength=len(uniq))[gi]
            if w[y == 0].sum() and w[y == 1].sum():
                boots.append(f1_score(np.repeat(y, w), np.repeat(q, w), average='macro'))
        rows.append(dict(model=name, n=len(y), positives=int(y.sum()), components=len(uniq), macro_f1=float(f1_score(y, q, average='macro')),
                         macro_f1_ci=np.quantile(boots, [.025, .975]).tolist(), average_precision=float(average_precision_score(y, p)),
                         roc_auc=float(roc_auc_score(y, p)), recall_loss=float(cm[1, 1] / cm[1].sum()), false_alarm_rate=float(cm[0, 1] / cm[0].sum()),
                         confusion=cm.tolist(), threshold=thr))
    result = dict(status='complete', version='turkiye_zero_shot_v1', rows=rows, dropped=lab['dropped'],
                  note='Zero-shot transfer from DISFOR (Europe) to Türkiye with Hansen GFC reference labels; no Turkish data used in training, calibration or threshold selection.')
    write(OUT / 'analysis.json', result)
    lines = ['| Model | n (loss) | Macro F1 [95% CI] | AP | ROC AUC | Loss recall | False alarm rate |', '|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['model']} | {r['n']} ({r['positives']}) | {r['macro_f1']:.3f} [{r['macro_f1_ci'][0]:.3f}, {r['macro_f1_ci'][1]:.3f}] | {r['average_precision']:.3f} | {r['roc_auc']:.3f} | {r['recall_loss']:.3f} | {r['false_alarm_rate']:.3f} |")
    (OUT / 'RESULTS.md').write_text('# Türkiye zero-shot probe\n\n' + '\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('stage', choices=['prepare', 'fetch', 'build', 'predict', 'report', 'all'])
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--full-cohort-recipes', action='store_true', help='also train RF/CNN/Transformer/SSL on all 2213 DISFOR points and apply them')
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.stage in ('prepare', 'all'): prepare()
    if a.stage in ('fetch', 'all'): fetch(a.workers)
    if a.stage in ('build', 'all'): build_npz()
    if a.stage in ('predict', 'all'): predict(a.full_cohort_recipes)
    if a.stage in ('report', 'all'): report()


if __name__ == '__main__':
    main()
