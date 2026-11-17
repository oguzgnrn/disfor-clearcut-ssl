"""True-colour Sentinel-2 chips before and after a clear cut at one DISFOR example location (Figure 2a).

The location is the detected clear-cut example of Figure 2 (plot_examples.py). Scenes are the least cloudy
Sentinel-2 L2A acquisitions from Earth Search (AWS COG) in the chosen months; a 1 km window around the
10 m pixel is read with /vsicurl and stretched per scene for display. Display only: no analysis uses these chips.
"""
import json, os, sys
from pathlib import Path
import numpy as np, requests, rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SID = sys.argv[1] if len(sys.argv) > 1 else 'disfor-1698-2019'
m = {r['id']: r for r in json.loads((ROOT / 'data/disfor/sample_manifest.json').read_text())}[SID]
lon, lat, year = m['lon'], m['lat'], m['year']
STAC = 'https://earth-search.aws.element84.com/v1/search'
HALF = 500  # metres

def best_scene(start, end):
    q = dict(collections=['sentinel-2-l2a'], intersects=dict(type='Point', coordinates=[lon, lat]), datetime=f'{start}T00:00:00Z/{end}T23:59:59Z', limit=50, query={'eo:cloud_cover': {'lt': 20}})
    feats = requests.post(STAC, json=q, timeout=60).json()['features']
    feats.sort(key=lambda f: f['properties']['eo:cloud_cover'])
    return feats

def read_rgb(feat):
    out = []
    for band in ['red', 'green', 'blue']:
        href = feat['assets'][band]['href']
        with rasterio.open(href) as d:
            x, y = transform('EPSG:4326', d.crs, [lon], [lat]); x, y = x[0], y[0]
            win = from_bounds(x - HALF, y - HALF, x + HALF, y + HALF, d.transform)
            out.append(d.read(1, window=win).astype(float))
    rgb = np.stack(out, -1)
    lo, hi = np.percentile(rgb, [2, 98]); return np.clip((rgb - lo) / (hi - lo), 0, 1)

def pick(start, end):
    for f in best_scene(start, end):
        try:
            img = read_rgb(f)
            if np.isfinite(img).all(): return f, img
        except Exception as e:
            print('skip', f['id'], e)
    raise SystemExit('no usable scene')

(fb, before), (fa, after) = pick(f'{year-1}-06-01', f'{year-1}-09-30'), pick(f'{year}-06-01', f'{year}-09-30')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'savefig.dpi': 240})
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.9))
for ax, img, f, lab in [(axes[0], before, fb, 'before'), (axes[1], after, fa, 'after')]:
    ax.imshow(img); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{lab}: {f['properties']['datetime'][:10]}", fontsize=9)
    c = img.shape[0] / 2; ax.plot(c, c, marker='s', ms=9, mfc='none', mec='#e1a23b', mew=1.6)
fig.suptitle(f'Sentinel-2 true colour, 1 km × 1 km, clear cut labelled in {year} (DISFOR, {lat:.3f}°N {abs(lon):.3f}°{"W" if lon < 0 else "E"})', fontsize=9)
fig.tight_layout()
fig.savefig(ROOT / 'paper/figures/07_chips.png', bbox_inches='tight'); fig.savefig(ROOT / 'paper/figures/07_chips.pdf', bbox_inches='tight')
json.dump(dict(location=SID, lon=lon, lat=lat, before=fb['id'], after=fa['id'], before_date=fb['properties']['datetime'], after_date=fa['properties']['datetime'], source='Earth Search STAC, sentinel-2-l2a, display only'), open(ROOT / 'paper/figures/07_chips.json', 'w'), indent=2)
print(fb['id'], fa['id'])
