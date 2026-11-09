"""Figure with example DISFOR windows: spectral index trajectories, reference label and held-out model probabilities.

Examples are chosen deterministically from the frozen pooled out-of-fold predictions at 20% labels:
one confidently correct clear cut, one missed clear cut, one confidently correct stable forest and one
stable window with a false alarm. Probabilities are the mean over the three training seeds.
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper/figures'
d = np.load(ROOT / 'data/processed/real_series.npz', allow_pickle=True)
z = np.load(ROOT / 'experiments/paper_v4/oof_predictions.npz', allow_pickle=True)
assert (d['ids'] == z['ids']).all() and (d['y'] == z['y']).all()
x, obs, y = d['x'].astype(float), d['observed'].astype(bool), d['y']
meta = json.loads(str(d['metadata'])) if d['metadata'].shape == () else {}
manifest = {r['id']: r for r in json.loads((ROOT / 'data/disfor/sample_manifest.json').read_text())}
p_ssl = z['ssl_transformer48_0.2'].mean(0); p_cnn = z['cnn64_0.2'].mean(0); p_rf = z['rf_leaf4_0.2'].mean(0); p_step = z['step_matched_0.2'].mean(0)
B = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B11', 'B12']
nir, red, swir = B.index('B08'), B.index('B04'), B.index('B12')
full = obs.all(-1).sum(1)   # months with any observation
ok = full >= 18              # well observed windows make clearer illustrations
def pick(mask, key):
    idx = np.where(mask & ok)[0]; return idx[np.argsort(key[idx])[0]]
cases = [
    ('Clear cut, detected', pick(y == 1, -p_ssl)),
    ('Clear cut, missed', pick(y == 1, p_ssl)),
    ('Stable forest, correct', pick(y == 0, p_ssl)),
    ('Stable forest, false alarm', pick(y == 0, -p_ssl)),
]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'pdf.fonttype': 42, 'savefig.dpi': 240})
fig, axes = plt.subplots(2, 2, figsize=(10, 5.6), sharex=True, sharey=True)
months = np.arange(1, 25)
for ax, (title, i) in zip(axes.ravel(), cases):
    m = obs[i].all(-1)
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (x[i, :, nir] - x[i, :, red]) / (x[i, :, nir] + x[i, :, red])
        nbr = (x[i, :, nir] - x[i, :, swir]) / (x[i, :, nir] + x[i, :, swir])
    for arr, lab, c in [(ndvi, 'NDVI', '#267d87'), (nbr, 'NBR', '#e1a23b')]:
        ax.plot(months[m], arr[m], '-', color=c, lw=1.8, label=lab); ax.plot(months[m], arr[m], 'o', color=c, ms=4)
    for mm in months[~m]:
        ax.axvspan(mm - .5, mm + .5, color='#dddddd', alpha=.6, lw=0)
    ax.axvline(12.5, color='gray', ls='--', lw=1)
    r = manifest.get(str(d['ids'][i]), {})
    ax.set_title(f"{title}   (label: {'clear cut' if y[i] else 'stable forest'}; target year {r.get('year', '')})", fontsize=9, loc='left')
    txt = f"held-out p(clear cut) at 20% labels\nSSL {p_ssl[i]:.2f}   CNN {p_cnn[i]:.2f}   RF {p_rf[i]:.2f}   step-matched {p_step[i]:.2f}"
    ax.text(0.02, 0.05, txt, transform=ax.transAxes, fontsize=8, va='bottom', bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#cccccc'))
    ax.grid(axis='y', alpha=.18); ax.set_ylim(-0.25, 1.0)
for ax in axes[1]: ax.set_xlabel('Month of the 24 month window (dashed line: start of the target year)')
for ax in axes[:, 0]: ax.set_ylabel('Spectral index')
axes[0, 0].legend(loc='upper right', frameon=False, ncol=2)
fig.tight_layout()
fig.savefig(OUT / '06_examples.png', bbox_inches='tight'); fig.savefig(OUT / '06_examples.pdf', bbox_inches='tight')
print('examples', [(t, str(d['ids'][i]), int(y[i]), round(float(p_ssl[i]), 3)) for t, i in cases])
