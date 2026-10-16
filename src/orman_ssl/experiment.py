"""Masked temporal pretraining, fair supervised baseline and RF baseline.

No labels enter pretraining; normalization and pretraining use training groups only.
Synthetic data are an integration check, never evidence of real-world accuracy.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import time
import joblib

os.environ.setdefault('MPLCONFIGDIR', str(Path('.cache/matplotlib').resolve()))
import numpy as np
import torch
from torch import nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import GroupShuffleSplit


def synthetic(path, seed=2026):
    """Toy multivariate series with three stylized patterns and missing optics."""
    rng = np.random.default_rng(seed)
    n, t, c = 720, 24, 6
    days = np.sort(rng.uniform(0, 730, (n, t)), axis=1).astype('float32')
    groups = np.repeat(np.arange(60), n // 60)
    y = rng.integers(0, 3, n)
    x = np.empty((n, t, c), dtype='float32')
    offsets = rng.normal(0, .07, (60, c))
    for i in range(n):
        seasonal = np.sin(2 * np.pi * days[i] / 365.25 + rng.uniform(-.4, .4))
        event = rng.uniform(230, 480)
        change = np.maximum(days[i] - event, 0)
        signal = np.zeros(t) if y[i] == 0 else ((change > 0) * np.exp(-change / 340) if y[i] == 1 else np.minimum(change / 240, 1))
        x[i] = (np.array([.65, .55, .28, .2, -.4, -.8])[None, :]
                + seasonal[:, None] * np.array([.13, .1, .04, .03, .09, .07])
                + signal[:, None] * np.array([-.3, -.35, .17, .12, -.15, -.18])
                + offsets[groups[i]] + rng.normal(0, .08, (t, c)))
    observed = rng.random((n, t, c)) > .08
    cloudy = rng.random((n, t)) < .30
    observed[:, :, :4] &= ~cloudy[:, :, None]
    x[~observed] = np.nan
    meta = dict(kind='synthetic', description='Stylized patterns; NOT satellite measurements',
                classes=['stable_pattern', 'abrupt_recovering_pattern', 'gradual_pattern'],
                channels=['optical_proxy_1', 'optical_proxy_2', 'optical_proxy_3', 'optical_proxy_4', 'radar_proxy_1', 'radar_proxy_2'], seed=seed)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, x=x, observed=observed, days=days, y=y,
                        groups=groups, ids=np.array([f'toy-{i:04}' for i in range(n)]), metadata=json.dumps(meta))


def validate(d):
    required = {'x', 'observed', 'days', 'y', 'groups', 'ids', 'metadata'}
    if not required.issubset(d):
        raise ValueError(f'Missing fields: {required - set(d)}')
    x, m, days, y = d['x'], d['observed'], d['days'], d['y']
    if x.ndim != 3 or m.shape != x.shape or m.dtype != bool:
        raise ValueError('x/observed must be matching N,T,C arrays; observed must be bool')
    n = x.shape[0]
    if days.shape != x.shape[:2] or not np.isfinite(days).all() or (np.diff(days, axis=1) < 0).any():
        raise ValueError('days must be finite, ordered N,T acquisition offsets')
    if not np.isfinite(x[m]).all() or not m.any(axis=(1, 2)).all():
        raise ValueError('Observed entries must be finite; entirely missing samples are invalid')
    if any(d[k].shape != (n,) for k in ['y', 'groups', 'ids']):
        raise ValueError('y/groups/ids must have N entries')
    if len(np.unique(d['ids'])) != n or len(np.unique(d['groups'])) < 10:
        raise ValueError('Unique IDs and at least 10 independent groups required')
    if not np.issubdtype(y.dtype, np.integer) or not np.array_equal(np.unique(y), np.arange(len(np.unique(y)))):
        raise ValueError('Labels must be contiguous integers starting at zero')
    meta = json.loads(str(d['metadata']))
    if meta.get('kind') not in ['synthetic', 'real'] or len(meta.get('classes', [])) != len(np.unique(y)):
        raise ValueError('metadata.kind and class names are required')
    if len(meta.get('channels', [])) != x.shape[2]:
        raise ValueError('metadata.channels must describe every input channel')
    if meta['kind'] == 'real' and not all(meta.get(k) for k in ['source', 'label_provenance', 'group_definition', 'temporal_alignment']):
        raise ValueError('Real data require source, label_provenance, group_definition, temporal_alignment')
    return meta


def split_groups(groups, y):
    # Fixed held-out geography across seeds/budgets; seeds only vary training.
    idx = np.arange(len(groups))
    tr, rest = next(GroupShuffleSplit(n_splits=1, test_size=.4, random_state=1729).split(idx, y, groups))
    va, te = next(GroupShuffleSplit(n_splits=1, test_size=.5, random_state=1730).split(rest, y[rest], groups[rest]))
    parts = tr, rest[va], rest[te]
    for part in parts:
        if set(y[part]) != set(y):
            raise ValueError('Fixed group split misses a class. Redesign the sampling; do not search test scores.')
    return parts


def normalize(x, observed, train):
    z = np.where(observed[train], x[train], np.nan)
    if not np.isfinite(z).any(axis=(0, 1)).all():
        raise ValueError('Every channel needs observed training values')
    mean = np.nanmean(z, axis=(0, 1))
    std = np.maximum(np.nanstd(z, axis=(0, 1)), 1e-5)
    return np.where(observed, (x - mean) / std, 0).astype('float32'), mean, std


def subset(y, train, fraction, seed):
    rng = np.random.default_rng(seed)
    # Per-class nested ordering: label budgets are comparable within each seed.
    return np.concatenate([rng.permutation(train[y[train] == k])[:max(1, int(np.ceil((y[train] == k).sum() * fraction)))] for k in np.unique(y)])


class TemporalModel(nn.Module):
    def __init__(self, channels, classes, width=32):
        super().__init__()
        self.embed = nn.Linear(channels * 2 + 3, width)
        layer = nn.TransformerEncoderLayer(width, 4, width * 2, dropout=.1, batch_first=True)
        self.encoder = nn.TransformerEncoder(layer, 1, enable_nested_tensor=False)
        self.reconstruct = nn.Linear(width, channels)
        self.classifier = nn.Linear(width, classes)

    def forward(self, x, observed, days):
        time_features = torch.stack([days / 730., torch.sin(days * (2 * np.pi / 365.25)), torch.cos(days * (2 * np.pi / 365.25))], -1)
        h = self.encoder(self.embed(torch.cat([x * observed, observed.float(), time_features], -1)))
        # Missing tokens retain time information; pool only observed timestamps.
        valid = observed.any(-1).float().unsqueeze(-1)
        pooled = (h * valid).sum(1) / valid.sum(1).clamp_min(1)
        return self.classifier(pooled), self.reconstruct(h)


def mask_observations(observed, generator=None):
    hidden = (torch.rand(observed.shape, generator=generator) < .3) & observed
    if not hidden.any():
        hidden.reshape(-1)[torch.where(observed.reshape(-1))[0][0]] = True
    return hidden


def pretrain(model, x, m, days, train, epochs):
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    losses = []
    for _ in range(epochs):
        model.train()
        total = []
        for ix in torch.tensor(train)[torch.randperm(len(train))].split(64):
            hidden = mask_observations(m[ix])
            _, pred = model(x[ix].masked_fill(hidden, 0), m[ix] & ~hidden, days[ix])
            loss = ((pred[hidden] - x[ix][hidden]) ** 2).mean()
            opt.zero_grad(); loss.backward(); opt.step()
            total.append(loss.item())
        losses.append(float(np.mean(total)))
    return losses


def finetune(model, x, m, days, y, labeled, val, epochs):
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    best_score, best_state, best_epoch = -1., None, 0
    for epoch in range(epochs):
        model.train()
        for ix in torch.tensor(labeled)[torch.randperm(len(labeled))].split(64):
            logits, _ = model(x[ix], m[ix], days[ix])
            loss = nn.functional.cross_entropy(logits, y[ix])
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            pred = model(x[val], m[val], days[val])[0].argmax(1).numpy()
        score = f1_score(y[val].numpy(), pred, average='macro', zero_division=0)
        if score > best_score:
            best_score, best_state, best_epoch = score, copy.deepcopy(model.state_dict()), epoch + 1
    model.load_state_dict(best_state)
    return best_epoch, best_score


def rf_features(x, m):
    # No imputation fit on held-out data; normalized missing entries remain zero.
    count = m.sum(1).clip(1)
    mean = (x * m).sum(1) / count
    std = np.sqrt(((x - mean[:, None]) ** 2 * m).sum(1) / count)
    low = np.where(m, x, np.inf).min(1)
    high = np.where(m, x, -np.inf).max(1)
    low[~np.isfinite(low)] = 0; high[~np.isfinite(high)] = 0
    # Time-order information through first-half / second-half means.
    h = x.shape[1] // 2
    delta = (x[:, h:] * m[:, h:]).sum(1) / m[:, h:].sum(1).clip(1) - (x[:, :h] * m[:, :h]).sum(1) / m[:, :h].sum(1).clip(1)
    return np.concatenate([mean, std, low, high, delta, m.mean(1)], axis=1)


def run(path, out, seeds, fractions, pre_epochs, epochs):
    start = time.time()
    torch.set_num_threads(2)
    d = dict(np.load(path, allow_pickle=False))
    meta = validate(d)
    train, val, test = split_groups(d['groups'], d['y'])
    z, mean, std = normalize(d['x'], d['observed'], train)
    x, m, days, y = map(torch.as_tensor, (z, d['observed'], d['days'].astype('float32'), d['y'].astype('int64')))
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    (out / 'checkpoints').mkdir(exist_ok=True)
    split = {name: {'ids': d['ids'][ix].tolist(), 'groups': np.unique(d['groups'][ix]).tolist(), 'n': len(ix)} for name, ix in zip(['train', 'validation', 'test'], [train, val, test])}
    (out / 'split.json').write_text(json.dumps(split, indent=2))
    rows, curves = [], {}
    features = rf_features(z, d['observed'])
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        base = TemporalModel(x.shape[-1], len(meta['classes']))
        initial = copy.deepcopy(base.state_dict())
        curves[str(seed)] = pretrain(base, x, m, days, train, pre_epochs)
        pretrained = copy.deepcopy(base.state_dict())
        for fraction in fractions:
            labeled = subset(d['y'], train, fraction, seed)
            for method in ['RandomForest', 'Transformer', 'SSL_Transformer']:
                torch.manual_seed(seed)
                selected_epoch = None; val_score = None
                if method == 'RandomForest':
                    model = RandomForestClassifier(n_estimators=200, min_samples_leaf=2, class_weight='balanced', random_state=seed, n_jobs=2)
                    model.fit(features[labeled], d['y'][labeled]); pred = model.predict(features[test])
                    val_score = f1_score(d['y'][val], model.predict(features[val]), average='macro')
                    joblib.dump({'model':model,'mean':mean,'std':std,'metadata':meta},out/'checkpoints'/f'{method}_{seed}_{fraction}.joblib')
                else:
                    model = TemporalModel(x.shape[-1], len(meta['classes']))
                    model.load_state_dict(pretrained if method.startswith('SSL') else initial)
                    selected_epoch, val_score = finetune(model, x, m, days, y, labeled, val, epochs)
                    model.eval()
                    with torch.no_grad(): pred = model(x[test], m[test], days[test])[0].argmax(1).numpy()
                    torch.save({'model': model.state_dict(), 'mean': mean.tolist(), 'std': std.tolist(), 'metadata': meta,
                                'channels': x.shape[-1], 'classes': len(meta['classes']), 'timesteps':x.shape[1]}, out / 'checkpoints' / f'{method}_{seed}_{fraction}.pt')
                row = dict(method=method, seed=seed, label_fraction=fraction, n_labeled=len(labeled),
                           n_validation=len(val), n_test=len(test), macro_f1=float(f1_score(d['y'][test], pred, average='macro', zero_division=0)),
                           accuracy=float(accuracy_score(d['y'][test], pred)), validation_macro_f1=float(val_score), selected_epoch=selected_epoch,
                           confusion_matrix=confusion_matrix(d['y'][test], pred, labels=np.arange(len(meta['classes']))).tolist(),
                           per_class=classification_report(d['y'][test], pred, target_names=meta['classes'], output_dict=True, zero_division=0),
                           labeled_ids=d['ids'][labeled].tolist(), test_ids=d['ids'][test].tolist(), predictions=pred.tolist())
                rows.append(row)
                print(f'{meta["kind"]} seed={seed} budget={fraction} {method}: F1={row["macro_f1"]:.3f}', flush=True)
    summary = []
    for fraction in fractions:
        for method in ['RandomForest', 'Transformer', 'SSL_Transformer']:
            values = [r['macro_f1'] for r in rows if r['method'] == method and r['label_fraction'] == fraction]
            summary.append(dict(method=method, label_fraction=fraction, macro_f1_mean=float(np.mean(values)),
                                macro_f1_std=float(np.std(values, ddof=1)) if len(values) > 1 else 0., seeds=len(values)))
    result = dict(metadata=meta, dataset_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                  config=dict(seeds=seeds, fractions=fractions, pretrain_epochs=pre_epochs, finetune_epochs=epochs, device='cpu', width=32, layers=1,
                              split_seed=[1729,1730], note='Validation labels are additional to the stated TRAINING label budget; std is seed variability, not a confidence interval.'),
                  environment=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__),
                  elapsed_seconds=time.time()-start, normalization=dict(mean=mean.tolist(), std=std.tolist()),
                  summary=summary, runs=rows, pretrain_loss=curves)
    (out / 'results.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    for method in ['RandomForest', 'Transformer', 'SSL_Transformer']:
        rs = [r for r in summary if r['method'] == method]
        ax.errorbar([r['label_fraction'] * 100 for r in rs], [r['macro_f1_mean'] for r in rs], yerr=[r['macro_f1_std'] for r in rs], marker='o', capsize=4, label=method)
    ax.set(xlabel='Labeled training samples (%) — validation labels additional', ylabel='Held-out macro F1', ylim=(0,1.03), title=f'{meta["kind"].upper()} • pipeline check, not field validation' if meta['kind']=='synthetic' else 'Real-data experiment • inspect label provenance')
    ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(out/'label_efficiency.png',dpi=170); plt.close(fig)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data', default='data/processed/synthetic.npz')
    p.add_argument('--out', default='reports/experiment')
    p.add_argument('--generate-synthetic', action='store_true')
    p.add_argument('--seeds', type=int, nargs='+', default=[7, 17, 27])
    p.add_argument('--fractions', type=float, nargs='+', default=[.05,.1,.2,1.])
    p.add_argument('--pretrain-epochs', type=int, default=30)
    p.add_argument('--epochs', type=int, default=25)
    a = p.parse_args()
    if not all(0 < f <= 1 for f in a.fractions) or min(a.epochs,a.pretrain_epochs) < 1:
        p.error('Fractions must be in (0,1]; epochs must be positive')
    if a.generate_synthetic: synthetic(a.data)
    run(a.data, a.out, a.seeds, a.fractions, a.pretrain_epochs, a.epochs)


if __name__ == '__main__': main()
