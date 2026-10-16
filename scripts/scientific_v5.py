"""Separate, bounded exploratory radius-sensitivity experiment; never writes paper_v4."""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neighbors import BallTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import orman_ssl.advanced as adv
from orman_ssl.experiment import subset

OUT = ROOT / 'experiments/paper_v5_exploratory'
RADII = [5, 10, 20]
METHODS = ['rf_leaf4', 'cnn64', 'transformer48', 'ssl_transformer48', 'step_matched']
SEED = 7
SPLIT_SEED = 4192026
EARTH_KM = 6371.0088


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    adv.write_json(path, value)


def component_groups(metadata, radius_km):
    """Match v4's transitive distance+event grouping, retaining sampling strata separately."""
    if radius_km <= 0:
        raise ValueError('Radius must be positive')
    n = len(metadata)
    if not n:
        raise ValueError('No locations')
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[b] = a

    coords = np.deg2rad([[r['lat'], r['lon']] for r in metadata])
    tree = BallTree(coords, metric='haversine')
    for i, neighbors in enumerate(tree.query_radius(coords, r=radius_km / EARTH_KM)):
        for j in neighbors:
            union(i, int(j))
    events = {}
    for i, row in enumerate(metadata):
        if row['source_cluster'] is not None and row['dataset'] in [1, 3]:
            key = (row['dataset'], row['source_cluster'])
            if key in events:
                union(i, events[key])
            else:
                events[key] = i
    roots = [find(i) for i in range(n)]
    mapping = {k: i for i, k in enumerate(sorted(set(roots)))}
    return np.array([mapping[k] for k in roots], dtype=np.int64)


def has_country_metadata(columns):
    aliases = {'country', 'country_code', 'country_name', 'iso_a2', 'iso_a3', 'iso2', 'iso3'}
    return [c for c in columns if str(c).lower() in aliases]


def context():
    d = dict(np.load(ROOT / 'data/processed/real_series.npz', allow_pickle=False))
    lookup = {r['id']: r for r in read(ROOT / 'data/disfor/sample_manifest.json')}
    metadata = [lookup[str(i)] for i in d['ids']]
    if any(r['label'] != int(y) for r, y in zip(metadata, d['y'])):
        raise ValueError('Manifest labels do not match frozen cohort')
    return d, metadata


def locked_write(path, value):
    """Never silently replace an existing declared protocol or partition."""
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise ValueError(f'Frozen v5 declaration changed: {path.name}; use a new version')
    else:
        write(path, value)


def prepare():
    d, metadata = context()
    source_columns = pd.read_parquet(ROOT / 'data/disfor/samples.parquet').columns.tolist()
    country_columns = has_country_metadata(source_columns)
    if country_columns:
        raise ValueError('Country metadata is newly available; inspect provenance before extending this protocol')
    country = dict(status='not_evaluated_missing_country_metadata', source_columns=source_columns,
                   country_columns=country_columns, retained_manifest_columns=list(metadata[0]),
                   countries=None, per_country_class_support=None, per_country_event_support=None,
                   reason='Neither the pinned raw sample table nor retained manifest supplies per-location country labels.',
                   policy='No country is guessed from coordinates, source text, S2 tile or campaign. Leave-country-out is not run.',
                   future_requirement='A provenance-checked country field or separately documented boundary join would be a new derived attribute, not an original DISFOR label.')
    coords = np.deg2rad([[r['lat'], r['lon']] for r in metadata])
    radius_records = []
    groups_file = {}
    for radius in RADII:
        groups = component_groups(metadata, radius)
        if radius == 5 and not np.array_equal(groups, d['groups']):
            raise ValueError('Five-kilometre groups differ from frozen v4')
        groups_file[f'radius_{radius}'] = groups.tolist()
        sizes = np.unique(groups, return_counts=True)[1]
        folds = []
        cv = StratifiedGroupKFold(5, shuffle=True, random_state=SPLIT_SEED)
        for fold, (train, test) in enumerate(cv.split(d['x'], d['y'], groups)):
            counts = np.bincount(d['y'][test], minlength=2)
            if not counts.all() or len(np.unique(d['y'][train])) != 2:
                raise ValueError('Both classes required in every fixed fold; no score-based split search')
            if set(groups[train]) & set(groups[test]):
                raise ValueError('Spatial component overlap')
            nearest = float(BallTree(coords[train], metric='haversine').query(coords[test], k=1)[0].min() * EARTH_KM)
            if nearest <= radius - 1e-6:
                raise ValueError('Cross-fold radius violation')
            labeled = subset(d['y'], train, .2, SEED)
            steps = math.ceil((60 * math.ceil(len(train) / 64) + 40 * math.ceil(len(labeled) / 64)) / math.ceil(len(labeled) / 64))
            folds.append(dict(fold=fold, train_indices=train.tolist(), test_indices=test.tolist(),
                              train_ids=d['ids'][train].tolist(), test_ids=d['ids'][test].tolist(),
                              labeled_indices=labeled.tolist(), labeled_ids=d['ids'][labeled].tolist(),
                              test_class_counts=counts.tolist(), training_class_counts=np.bincount(d['y'][train], minlength=2).tolist(),
                              labeled_class_counts=np.bincount(d['y'][labeled], minlength=2).tolist(),
                              test_groups=int(len(np.unique(groups[test]))),
                              test_positive_groups=int(len(np.unique(groups[test][d['y'][test] == 1]))),
                              nearest_train_test_km=nearest, step_matched_epochs=steps))
        if radius == 5:
            old = read(ROOT / 'experiments/paper_v4/folds.json')
            if any(a['test_ids'] != b['test_ids'] for a, b in zip(folds, old)):
                raise ValueError('Five-kilometre folds differ from frozen v4')
        locked_write(OUT / f'folds_r{radius}.json', folds)
        radius_records.append(dict(radius_km=radius, groups=int(len(sizes)),
                                   positive_groups=int(len(np.unique(groups[d['y'] == 1]))),
                                   largest_component=int(sizes.max()), median_component=float(np.median(sizes)),
                                   folds=[{k: v for k, v in f.items() if k not in ['train_indices', 'test_indices', 'train_ids', 'test_ids', 'labeled_indices', 'labeled_ids']} for f in folds]))
    locked_write(OUT / 'groups.json', groups_file)
    support = dict(status='supported_for_descriptive_radius_sensitivity', locations=len(d['y']),
                   class_counts=np.bincount(d['y'], minlength=2).tolist(), radii=radius_records, country=country,
                   limitation='At 10 and 20 km some test folds have only two positive components; point counts must not be treated as independent event support.')
    locked_write(OUT / 'support_audit.json', support)
    protocol = dict(version='paper_v5_exploratory', purpose='Descriptive spatial-radius sensitivity extension, separate from frozen paper_v4',
                    declaration_timing='Protocol and signatures created by prepare before v5 fitting. Actual UTC event in preparation_event.json; no external preregistration claim.',
                    cohort='Unchanged 2213 DISFOR locations; 1937 forest and 276 clear-cut.',
                    radii_km=RADII, grouping='Transitive distance graph plus campaign 1/3 source-event identifiers; campaign 2 sampling strata are not events.',
                    folds=5, split_seed=SPLIT_SEED, seeds=[SEED], label_budgets=[.2], methods=METHODS,
                    fits=75, label_allocation='Same class-stratified ceiling-count label IDs for every method within radius/fold/seed.',
                    training='Reuse frozen advanced.py recipes. 40 supervised epochs; SSL adds 60 reconstruction epochs. Step-matched supervised epochs computed from optimizer updates. No early stopping or test-based selection; threshold 0.5.',
                    estimand='One-seed pooled OOF metrics by radius and method; changes combine radius grouping and induced fold/training changes, not a causal radius effect.',
                    uncertainty='Descriptive results only; no seed SD, p-values or confirmatory confidence intervals. One seed and sparse independent positive components limit inference.',
                    pilot=dict(radius_km=10, fold=0, methods=METHODS, purpose='Measure full-recipe CPU cost; pilot jobs are retained in the declared 75 fits.'),
                    country_evaluation='Not run: source country labels absent; no invented country assignments.',
                    checkpoints='Every new fitted model retained with SHA-256; old v4 weights and data untouched.',
                    limits=['Same-source retrospective cohort, not external data.', 'Architectures and original recipes were developed on this dataset.', 'Only seed 7 and 20 percent labels in this bounded extension.', 'No radius, fold or model recipe selected by scores.'])
    locked_write(OUT / 'protocol.json', protocol)
    jobs = [dict(radius_km=r, fold=f, seed=SEED, budget=.2, method=m) for r in RADII for f in range(5) for m in METHODS]
    locked_write(OUT / 'jobs.json', jobs)
    sources = ['scripts/scientific_v5.py', 'src/orman_ssl/advanced.py', 'src/orman_ssl/experiment.py',
               'src/orman_ssl/inputs.py', 'data/processed/real_series.npz', 'data/disfor/sample_manifest.json',
               'data/disfor/samples.parquet', 'experiments/paper_v4/signature.json', 'requirements-lock.txt']
    sources += [str(p.relative_to(ROOT)) for p in [OUT / 'protocol.json', OUT / 'groups.json', OUT / 'support_audit.json', OUT / 'jobs.json']]
    sources += [str((OUT / f'folds_r{r}.json').relative_to(ROOT)) for r in RADII]
    locked_write(OUT / 'signature.json', {name: digest(ROOT / name) for name in sources})
    if not (OUT / 'preparation_event.json').exists():
        write(OUT / 'preparation_event.json', dict(prepared_at_utc=datetime.now(timezone.utc).isoformat(),
                                                 run_files_present=len(list((OUT / 'runs').glob('*.json')))))
    return support


def verify_signature():
    for name, expected in read(OUT / 'signature.json').items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Frozen v5 input changed: {name}')
    for name, expected in read(ROOT / 'experiments/paper_v4/signature.json').items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Frozen v4 input changed: {name}')


def run_name(job):
    return f"r{job['radius_km']}_f{job['fold']}_s{job['seed']}_{job['method']}"


def scores(y, p):
    y = np.asarray(y)
    p = np.asarray(p, dtype=np.float64)
    if len(np.unique(y)) != 2:
        raise ValueError('Two classes required for binary comparison')
    if p.shape != y.shape or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('Invalid probabilities')
    q = p >= .5
    cm = confusion_matrix(y, q, labels=[0, 1])
    return dict(macro_f1=float(f1_score(y, q, average='macro')), average_precision=float(average_precision_score(y, p)),
                roc_auc=float(roc_auc_score(y, p)), brier=float(brier_score_loss(y, p)),
                clear_cut_recall=float(cm[1, 1] / cm[1].sum()), confusion_matrix=cm.tolist())


def worker(job):
    verify_signature()
    name = run_name(job)
    dest = OUT / 'runs' / (name + '.json')
    if dest.exists():
        row = read(dest)
        if row['signature_sha256'] != digest(OUT / 'signature.json') or digest(ROOT / row['checkpoint']) != row['checkpoint_sha256']:
            raise ValueError('Cached run/checkpoint integrity failure')
        return dict(name=name, cached=True, seconds=row['seconds'])
    start = time.monotonic()
    d, _ = context()
    d['groups'] = np.array(read(OUT / 'groups.json')[f"radius_{job['radius_km']}"])
    part = read(OUT / f"folds_r{job['radius_km']}.json")[job['fold']]
    train, test, labeled = [np.array(part[k], dtype=int) for k in ['train_indices', 'test_indices', 'labeled_indices']]
    chosen = 'transformer48' if job['method'] == 'step_matched' else job['method']
    config = {c['name']: c for c in adv.CONFIGS}[chosen]
    epochs = part['step_matched_epochs'] if job['method'] == 'step_matched' else 40
    state, log = adv.fit(config, d, train, seed=job['seed'], epochs=epochs, pre_epochs=60, labeled=labeled, early_stop=False)
    p = adv.state_probability(state, adv.view(d, test))
    suffix = '.joblib' if config['kind'] == 'rf' else '.pt'
    checkpoint = OUT / 'checkpoints' / (name + suffix)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    temporary = checkpoint.with_suffix(suffix + '.tmp')
    adv.save_state(temporary, state)
    temporary.replace(checkpoint)
    row = dict(**job, name=name, train_ids=d['ids'][train].tolist(), test_ids=d['ids'][test].tolist(),
               labeled_ids=d['ids'][labeled].tolist(), n_train=len(train), n_labeled=len(labeled),
               supervised_epochs=0 if config['kind'] == 'rf' else epochs,
               pretraining_epochs=60 if config.get('ssl') else 0,
               y=d['y'][test].tolist(), groups=d['groups'][test].tolist(), probabilities=p.tolist(), metrics=scores(d['y'][test], p),
               checkpoint=str(checkpoint.relative_to(ROOT)), checkpoint_sha256=digest(checkpoint),
               signature_sha256=digest(OUT / 'signature.json'), seconds=time.monotonic() - start, log=log)
    write(dest, row)
    return dict(name=name, cached=False, seconds=row['seconds'], macro_f1=row['metrics']['macro_f1'])


def train(pilot=False, workers=2, max_jobs=75):
    verify_signature()
    if not 1 <= workers <= 3 or not 1 <= max_jobs <= 75:
        raise ValueError('Bounded execution requires 1-3 workers and 1-75 jobs')
    jobs = read(OUT / 'jobs.json')
    if pilot:
        jobs = [j for j in jobs if j['radius_km'] == 10 and j['fold'] == 0]
    pending = [j for j in jobs if not (OUT / 'runs' / (run_name(j) + '.json')).exists()]
    selected = pending[:max_jobs]
    start = time.monotonic()
    results = []
    if workers == 1:
        for j in selected:
            value = worker(j); results.append(value); print(json.dumps(value), flush=True)
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(worker, j) for j in selected]
            for future in concurrent.futures.as_completed(futures):
                value = future.result(); results.append(value); print(json.dumps(value), flush=True)
    elapsed = time.monotonic() - start
    record = dict(scope='pilot' if pilot else 'bounded_declared_run', new_fits=len(selected), workers=workers,
                  elapsed_wall_seconds=elapsed, completed_records=len(list((OUT / 'runs').glob('*.json'))),
                  result=results, note='Pilot cost is a local concurrency-specific estimate, not a hardware-independent benchmark.')
    write(OUT / ('pilot_cost.json' if pilot else 'execution.json'), record)
    verify_signature()
    return record


def analyze():
    verify_signature()
    jobs = read(OUT / 'jobs.json')
    paths = sorted((OUT / 'runs').glob('*.json'))
    if len(paths) != 75:
        raise ValueError('All 75 declared runs must finish before pooled analysis')
    records = {r['name']: r for r in map(read, paths)}
    if set(records) != {run_name(j) for j in jobs}:
        raise ValueError('Unexpected or missing runs')
    d, _ = context()
    lookup = {v: i for i, v in enumerate(d['ids'])}
    summaries = []
    arrays = dict(ids=d['ids'], y=d['y'])
    v4 = np.load(ROOT / 'experiments/paper_v4/oof_predictions.npz', allow_pickle=False)
    baseline_errors = []
    for radius in RADII:
        groups = np.array(read(OUT / 'groups.json')[f'radius_{radius}'])
        arrays[f'groups_r{radius}'] = groups
        for method in METHODS:
            pooled = np.full(len(d['y']), np.nan)
            seconds = 0.0
            for fold in range(5):
                job = dict(radius_km=radius, fold=fold, seed=SEED, budget=.2, method=method)
                row = records[run_name(job)]
                part = read(OUT / f'folds_r{radius}.json')[fold]
                if row['train_ids'] != part['train_ids'] or row['test_ids'] != part['test_ids'] or row['labeled_ids'] != part['labeled_ids']:
                    raise ValueError('Run identities differ from fixed folds')
                ix = np.array([lookup[v] for v in row['test_ids']])
                if not np.isnan(pooled[ix]).all() or not np.array_equal(d['y'][ix], row['y']) or not np.array_equal(groups[ix], row['groups']):
                    raise ValueError('Invalid OOF/label/group alignment')
                if digest(ROOT / row['checkpoint']) != row['checkpoint_sha256'] or row['signature_sha256'] != digest(OUT / 'signature.json'):
                    raise ValueError('Checkpoint or signature mismatch')
                actual = scores(row['y'], row['probabilities'])
                for key in actual:
                    if key == 'confusion_matrix':
                        if actual[key] != row['metrics'][key]: raise ValueError('Confusion matrix mismatch')
                    elif abs(actual[key] - row['metrics'][key]) > 1e-7:
                        raise ValueError('Stored metric mismatch')
                if row['method'] != 'rf_leaf4':
                    if len(row['log']['history']) != row['supervised_epochs'] or any(v['validation_macro_f1'] is not None for v in row['log']['history']):
                        raise ValueError('Training history mismatch or validation selection')
                    if len(row['log']['pretrain_loss']) != row['pretraining_epochs']:
                        raise ValueError('Pretraining history mismatch')
                pooled[ix] = row['probabilities']; seconds += row['seconds']
            if not np.isfinite(pooled).all():
                raise ValueError('Incomplete OOF coverage')
            arrays[f'r{radius}_{method}'] = pooled
            summaries.append(dict(radius_km=radius, seed=SEED, budget=.2, method=method, n=len(pooled),
                                  groups=len(np.unique(groups)), fit_seconds_sum=seconds, **scores(d['y'], pooled)))
            if radius == 5:
                difference = float(np.max(np.abs(pooled - v4[f'{method}_0.2'][0])))
                baseline_errors.append(dict(method=method, maximum_probability_difference=difference,
                                            interpretation='Reproduction check of seed 7, not independent confirmation.'))
    result = dict(status='complete_verified', version='paper_v5_exploratory', fits=75, seeds=[SEED],
                  locations=len(d['y']), prediction_values=15 * len(d['y']), summary=summaries,
                  radius_5_v4_reproduction=baseline_errors,
                  country=read(OUT / 'support_audit.json')['country'],
                  limitations=read(OUT / 'protocol.json')['limits'] + [read(OUT / 'protocol.json')['uncertainty'], read(OUT / 'protocol.json')['estimand']])
    write(OUT / 'analysis.json', result)
    np.savez_compressed(OUT / 'oof_predictions.npz', **arrays)
    fields = ['radius_km', 'seed', 'budget', 'method', 'n', 'groups', 'macro_f1', 'average_precision', 'roc_auc', 'brier', 'clear_cut_recall']
    with (OUT / 'results.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows({k: r[k] for k in fields} for r in summaries)
    write(OUT / 'verification.json', dict(status='passed', fits=75, checkpoints=75, pooled_vectors=15,
                                          prediction_values=15 * len(d['y']), checks=['v4 and v5 signatures', 'exact declared run IDs', 'paired fixed label subsets', 'OOF once per location', 'label/group alignment', 'metrics recomputed', 'saved checkpoint hashes', 'fixed epoch histories and no validation selection']))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'pilot', 'train', 'analyze'])
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--max-jobs', type=int, default=75)
    args = parser.parse_args()
    if args.stage == 'prepare':
        result = prepare()
        print(json.dumps({k: v for k, v in result.items() if k != 'radii'}, indent=2))
    elif args.stage in ['pilot', 'train']:
        print(json.dumps(train(args.stage == 'pilot', args.workers, args.max_jobs), indent=2))
    else:
        result = analyze()
        print(json.dumps(dict(status=result['status'], fits=result['fits'], summary=result['summary']), indent=2))


if __name__ == '__main__':
    main()
