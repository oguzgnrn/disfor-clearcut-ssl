"""Exploratory frozen Presto probes on the unchanged paper_v4 paired splits.

No encoder fine-tuning, test-set model selection, or claim of independent
external validation. See protocol.json and the source/weight provenance.
"""
import hashlib
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'third_party/presto'))
from orman_ssl.inputs import BANDS, validate_input
from orman_ssl.experiment import subset
from train_paper import score

OUT = ROOT / 'experiments/presto_v1_exploratory'
METHODS = ['presto_pretrained_geo', 'presto_pretrained_constant', 'presto_random_constant']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def adapt(data):
    """DN / 10000, derived NDVI; preserve missingness, no gap interpolation.

    Upstream masks a whole band-group token if any constituent is missing.
    Other modalities are wholly absent, never synthesized as observations.
    """
    validate_input(data)
    raw, observed = data['x'], data['observed']
    x = np.zeros((*raw.shape[:2], 17), dtype='float32')
    mask = np.ones_like(x, dtype=bool)
    x[:, :, 2:12] = np.where(observed, raw / 10000., 0)
    mask[:, :, 2:12] = ~observed
    nir, red = BANDS.index('B08'), BANDS.index('B04')
    valid = observed[:, :, nir] & observed[:, :, red]
    denominator = raw[:, :, nir] + raw[:, :, red]
    ratio = np.zeros(raw.shape[:2], dtype='float32')
    np.divide(raw[:, :, nir] - raw[:, :, red], denominator,
              out=ratio, where=valid & (denominator > 0))
    x[:, :, 16] = ratio
    mask[:, :, 16] = ~valid
    return x, mask


def encode(data, latlons, pretrained=True, geographic=True):
    from single_file_presto import Presto, BANDS_GROUPS_IDX
    torch.manual_seed(20261001)
    model = Presto.construct().cpu()
    if pretrained:
        model.load_state_dict(torch.load(ROOT / 'third_party/presto/default_model.pt',
                                         map_location='cpu', weights_only=True), strict=True)
    model.eval().requires_grad_(False)
    x, mask = adapt(data)
    coordinates = latlons if geographic else np.zeros_like(latlons)
    # Upstream requires equal visible token counts, not equal mask patterns.
    # Bucketing therefore preserves every observation without padding/imputation.
    counts = np.zeros(len(x), dtype=int)
    for group, indices in BANDS_GROUPS_IDX.items():
        gm = mask[:, :1 if group == 'SRTM' else x.shape[1], indices]
        counts += (~gm.any(axis=-1)).sum(axis=1)
    result = np.empty((len(x), 128), dtype='float32')
    started = time.monotonic()
    with torch.inference_mode():
        for count in np.unique(counts):
            members = np.flatnonzero(counts == count)
            for start in range(0, len(members), 32):
                ix = members[start:start + 32]
                result[ix] = model.encoder(
                    torch.from_numpy(x[ix]), torch.full((len(ix), 24), 9, dtype=torch.long),
                    torch.from_numpy(coordinates[ix]), torch.from_numpy(mask[ix]).float(),
                    month=0, eval_task=True).numpy()
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite frozen embeddings')
    return result, {'seconds': time.monotonic() - started,
                    'visible_token_min': int(counts.min()), 'visible_token_max': int(counts.max()),
                    'encoder_parameters': sum(p.numel() for p in model.encoder.parameters()),
                    'frozen': True}


def protocol():
    return dict(version='presto_v1_exploratory', role='post-hoc exploratory extension; not original paper_v4 protocol',
        source_revision=json.loads((ROOT / 'third_party/presto/PROVENANCE.json').read_text())['commit'],
        folds='exact paper_v4 folds', label_budgets=[.2, 1.], label_seeds=[7, 17, 27], methods=METHODS,
        jobs=90, encoder='frozen upstream default Presto, 128 features, 24 months, January start',
        random_encoder_seed=20261001, missing_modalities=['S1', 'ERA5', 'SRTM', 'Dynamic World'],
        preprocessing='Source DN / 10000 per upstream normalization, NDVI from B08/B04; masks retained; no clipping or offsets; no interpolation',
        coordinate_control='constant (0,0) coordinate token, not deletion of the geographic embedding',
        linear_probe={'standardization_fit': 'labeled training subset only', 'C': 1., 'class_weight': 'balanced',
                      'solver': 'lbfgs', 'max_iter': 2000, 'tol': 1e-6, 'threshold': .5},
        selection='No hyperparameter search, no held-out test adaptation, no early stopping, no production replacement',
        limitations=['Same adaptively examined DISFOR cohort, not external validation',
                     'Pretraining data may overlap geographically/temporally; not independently audited',
                     'Source DN harmonization/offset compatibility is not independently established',
                     'Frozen linear probing only; does not evaluate fully fine-tuned Presto',
                     'Pretrained model has external data/compute; not a compute-matched SSL control',
                     'Random encoder uses one initialization; label seeds do not capture initialization uncertainty'])


def main():
    torch.set_num_threads(2)
    OUT.mkdir(parents=True, exist_ok=True)
    config = protocol()
    ppath = OUT / 'protocol.json'
    if ppath.exists() and json.loads(ppath.read_text()) != config:
        raise ValueError('Protocol changed; use a new experiment version')
    write(ppath, config)
    provenance = json.loads((ROOT / 'third_party/presto/PROVENANCE.json').read_text())
    for item in provenance['files']:
        if digest(ROOT / item['local_path']) != item['sha256']:
            raise ValueError('Upstream file changed: ' + item['local_path'])
    paths = ['scripts/train_presto_probe.py', 'src/orman_ssl/experiment.py', 'src/orman_ssl/inputs.py',
             'scripts/train_paper.py', 'data/processed/real_series.npz', 'data/disfor/sample_manifest.json',
             'experiments/paper_v4/folds.json', 'requirements-lock.txt', 'requirements-presto.txt',
             'third_party/presto/PROVENANCE.json', str(ppath.relative_to(ROOT))]
    signature = {name: digest(ROOT / name) for name in paths}
    lock = OUT / 'signature.json'
    if lock.exists() and json.loads(lock.read_text())['files'] != signature:
        raise ValueError('Code/data changed; cached fits cannot be mixed')
    if not lock.exists():
        write(lock, {'frozen_at_utc': datetime.now(timezone.utc).isoformat(), 'files': signature})
    data = dict(np.load(ROOT / 'data/processed/real_series.npz', allow_pickle=False))
    source = {r['id']: r for r in json.loads((ROOT / 'data/disfor/sample_manifest.json').read_text())}
    latlons = np.array([[source[i]['lat'], source[i]['lon']] for i in data['ids']], dtype='float32')
    folds = json.loads((ROOT / 'experiments/paper_v4/folds.json').read_text())
    embeddings = {}; encoder_logs = {}
    for method in METHODS:
        dest = OUT / (method + '_embeddings.npz')
        if dest.exists():
            cached = dict(np.load(dest, allow_pickle=False))
            if not np.array_equal(cached['ids'], data['ids']):
                raise ValueError('Embedding ID mismatch')
            embeddings[method] = cached['features']
            encoder_logs[method] = json.loads(str(cached['log']))
        else:
            embeddings[method], encoder_logs[method] = encode(data, latlons,
                pretrained=method != 'presto_random_constant', geographic=method == 'presto_pretrained_geo')
            np.savez_compressed(dest, ids=data['ids'], features=embeddings[method], log=json.dumps(encoder_logs[method]))
        print(method, 'encoded', encoder_logs[method], flush=True)
    summaries = []; pooled = {'ids': data['ids'], 'y': data['y'], 'groups': data['groups']}; rows = []
    for budget in [.2, 1.]:
        for method in METHODS:
            per_seed = []; probabilities = []
            for seed in [7, 17, 27]:
                oof = np.full(len(data['ids']), np.nan)
                for part in folds:
                    tr = np.array(part['train_indices']); te = np.array(part['test_indices'])
                    labeled = subset(data['y'], tr, budget, seed)
                    if set(data['groups'][tr]) & set(data['groups'][te]):
                        raise ValueError('Group leakage')
                    started = time.monotonic()
                    scaler = StandardScaler().fit(embeddings[method][labeled])
                    classifier = LogisticRegression(C=1., class_weight='balanced', max_iter=2000,
                                                    tol=1e-6, random_state=seed, solver='lbfgs')
                    with warnings.catch_warnings():
                        warnings.simplefilter('error', ConvergenceWarning)
                        classifier.fit(scaler.transform(embeddings[method][labeled]), data['y'][labeled])
                    p = classifier.predict_proba(scaler.transform(embeddings[method][te]))[:, 1]
                    if np.isfinite(oof[te]).any():
                        raise ValueError('Duplicate test assignment')
                    oof[te] = p
                    row = dict(method=method, budget=budget, seed=seed, fold=part['fold'],
                        train_ids=data['ids'][tr].tolist(), labeled_ids=data['ids'][labeled].tolist(),
                        test_ids=data['ids'][te].tolist(), y=data['y'][te].tolist(),
                        probabilities=p.tolist(), metrics=score(data['y'][te], p), seconds=time.monotonic()-started,
                        iterations=classifier.n_iter_.tolist(), coefficients=classifier.coef_.tolist(),
                        intercept=classifier.intercept_.tolist(), scaler_mean=scaler.mean_.tolist(), scaler_scale=scaler.scale_.tolist())
                    write(OUT / 'runs' / f'{method}_f{part["fold"]}_s{seed}_b{budget}.json', row)
                    rows.append(row)
                if not np.isfinite(oof).all():
                    raise ValueError('Incomplete OOF coverage')
                probabilities.append(oof); per_seed.append({'seed': seed, **score(data['y'], oof)})
            pooled[f'{method}_{budget}'] = np.stack(probabilities)
            summary = dict(method=method, budget=budget, seed_results=per_seed,
                macro_f1_mean=float(np.mean([r['macro_f1'] for r in per_seed])),
                macro_f1_std=float(np.std([r['macro_f1'] for r in per_seed], ddof=1)),
                average_precision_mean=float(np.mean([r['pr_auc'] for r in per_seed])),
                brier_mean=float(np.mean([r['brier'] for r in per_seed])))
            summaries.append(summary); print(method, budget, summary['macro_f1_mean'], flush=True)
    if len(rows) != 90:
        raise ValueError('Unexpected fit count')
    np.savez_compressed(OUT / 'oof_predictions.npz', **pooled)
    write(OUT / 'analysis.json', {'status': 'complete', 'fits': len(rows), 'summary': summaries,
        'encoder_logs': encoder_logs, 'limitations': config['limitations'],
        'source_dn_percentiles': np.quantile(data['x'][data['observed']], [0, .01, .5, .99, 1]).tolist()})
    artifacts = sorted([p for p in OUT.rglob('*') if p.is_file() and p.name != 'completion.json'])
    write(OUT / 'completion.json', {'status': 'complete', 'fits': 90, 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
        'artifacts': {str(p.relative_to(ROOT)): digest(p) for p in artifacts}})


if __name__ == '__main__':
    main()
