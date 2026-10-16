"""Independently reconstruct frozen-probe predictions and paired assignments."""
import json
import sys
from pathlib import Path
import hashlib
import numpy as np
from scipy.special import expit
from sklearn.metrics import f1_score, average_precision_score, brier_score_loss

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from orman_ssl.experiment import subset

OUT = ROOT / 'experiments/presto_v1_exploratory'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for path, expected in read(OUT / 'completion.json')['artifacts'].items():
        if sha(ROOT / path) != expected:
            raise ValueError('Changed result ' + path)
    for path, expected in read(OUT / 'signature.json')['files'].items():
        if sha(ROOT / path) != expected:
            raise ValueError('Changed source ' + path)
    for row in read(ROOT / 'third_party/presto/PROVENANCE.json')['files']:
        if sha(ROOT / row['local_path']) != row['sha256']:
            raise ValueError('Changed upstream artifact')
    data = dict(np.load(ROOT / 'data/processed/real_series.npz', allow_pickle=False))
    folds = read(ROOT / 'experiments/paper_v4/folds.json')
    rows = [read(p) for p in sorted((OUT / 'runs').glob('*.json'))]
    expected_jobs = {(m, b, s, f) for m in read(OUT / 'protocol.json')['methods']
                     for b in [.2, 1.] for s in [7, 17, 27] for f in range(5)}
    if len(rows) != 90 or {(r['method'], r['budget'], r['seed'], r['fold']) for r in rows} != expected_jobs:
        raise ValueError('Incomplete fits')
    lookup = {str(key): n for n, key in enumerate(data['ids'])}
    recovered = {}; max_difference = 0
    for row in rows:
        fold = folds[row['fold']]; train = np.array(fold['train_indices']); test = np.array(fold['test_indices'])
        labeled = subset(data['y'], train, row['budget'], row['seed'])
        for field, indices in [('train_ids', train), ('test_ids', test), ('labeled_ids', labeled)]:
            if row[field] != data['ids'][indices].tolist():
                raise ValueError('Assignment mismatch: ' + field)
        np.testing.assert_array_equal(row['y'], data['y'][test])
        with np.load(OUT / (row['method'] + '_embeddings.npz'), allow_pickle=False) as cache:
            np.testing.assert_array_equal(cache['ids'], data['ids'])
            features = cache['features'].astype(float)
        np.testing.assert_allclose(features[labeled].mean(axis=0), row['scaler_mean'], rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(features[labeled].std(axis=0), row['scaler_scale'], rtol=1e-5, atol=1e-6)
        normalized = (features[test] - row['scaler_mean']) / row['scaler_scale']
        probability = expit(normalized @ np.array(row['coefficients'])[0] + row['intercept'][0])
        # Training path standardized float32 input. Reconstruction uses float64.
        difference = float(np.max(np.abs(probability - row['probabilities'])))
        if difference > 2e-6:
            raise ValueError('Stored classifier cannot reproduce predictions')
        max_difference = max(max_difference, difference)
        p = np.array(row['probabilities']); y = np.array(row['y'])
        for key, value in [('macro_f1', f1_score(y, p >= .5, average='macro')),
                           ('pr_auc', average_precision_score(y, p)), ('brier', brier_score_loss(y, p))]:
            if abs(value - row['metrics'][key]) > 1e-12:
                raise ValueError('Metric mismatch')
        key = (row['method'], row['budget'], row['seed'])
        if key not in recovered:
            recovered[key] = np.full(len(data['ids']), np.nan)
        if np.isfinite(recovered[key][test]).any():
            raise ValueError('Duplicate OOF test assignment')
        recovered[key][test] = p
    oof = dict(np.load(OUT / 'oof_predictions.npz', allow_pickle=False))
    for (method, budget, seed), p in recovered.items():
        if not np.isfinite(p).all():
            raise ValueError('Missing OOF assignment')
        np.testing.assert_array_equal(p, oof[f'{method}_{budget}'][[7, 17, 27].index(seed)])
    for row in read(OUT / 'analysis.json')['summary']:
        ps = oof[f'{row["method"]}_{row["budget"]}']; y = data['y']
        scores = [f1_score(y, p >= .5, average='macro') for p in ps]
        for key, value in [('macro_f1_mean', np.mean(scores)), ('macro_f1_std', np.std(scores, ddof=1)),
                           ('average_precision_mean', np.mean([average_precision_score(y, p) for p in ps]))]:
            if abs(value - row[key]) > 1e-12:
                raise ValueError('Summary mismatch')
    result = dict(status='passed', fits=90, unique_locations=len(data['ids']),
                  oof_values=sum(p.size for p in recovered.values()),
                  classifier_reconstruction_max_probability_difference=max_difference,
                  checks=['source and result hashes', 'exact paired folds and label IDs', 'training-only scaler',
                          'classifier coefficient reconstruction', 'all OOF coverage', 'metrics recalculated'],
                  scope='Frozen linear probes on historical cohort; not external validation')
    (ROOT / 'reports/presto_probe_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
