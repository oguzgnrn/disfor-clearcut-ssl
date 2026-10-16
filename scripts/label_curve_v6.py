"""Declared label-budget curve extension (paper_v6_label_curve); never writes paper_v4 or paper_v5.

Adds the 5 %, 10 % and 50 % label budgets that the original research plan listed but paper_v4 did not run.
Folds, seeds, label-allocation rule, recipes and threshold are identical to the frozen paper_v4 protocol, so the
new pooled out-of-fold scores can be placed on one curve with the existing 20 % and 100 % results.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, f1_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import orman_ssl.advanced as adv
from orman_ssl.experiment import subset

V4 = ROOT / 'experiments/paper_v4'
OUT = ROOT / 'experiments/paper_v6_label_curve'
BUDGETS = [.05, .1, .5]
V4_BUDGETS = [.2, 1.]
SEEDS = [7, 17, 27]
METHODS = ['rf_leaf4', 'cnn64', 'transformer48', 'ssl_transformer48', 'step_matched']
FOLDS = 5


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    adv.write_json(path, value)


def locked_write(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise ValueError(f'Frozen v6 declaration changed: {path.name}; use a new version')
    else:
        write(path, value)


def context():
    d = dict(np.load(ROOT / 'data/processed/real_series.npz', allow_pickle=False))
    return d


def step_matched_epochs(n_train, n_labeled):
    return math.ceil((60 * math.ceil(n_train / 64) + 40 * math.ceil(n_labeled / 64)) / math.ceil(n_labeled / 64))


def prepare():
    d = context()
    folds = read(V4 / 'folds.json')
    if len(folds) != FOLDS:
        raise ValueError('Expected five frozen v4 folds')
    allocation = []
    for part in folds:
        train = np.array(part['train_indices'])
        for seed in SEEDS:
            for budget in BUDGETS:
                labeled = subset(d['y'], train, budget, seed)
                # Nested check: smaller budgets are prefixes of the larger ones within a seed and class.
                v4_subset = set(subset(d['y'], train, .2, seed))
                nested = set(labeled) <= v4_subset if budget < .2 else v4_subset <= set(labeled)
                if not nested:
                    raise ValueError('Label subsets are not nested within seed')
                allocation.append(dict(fold=part['fold'], seed=seed, budget=budget, n_train=int(len(train)), n_labeled=int(len(labeled)),
                                       labeled_class_counts=np.bincount(d['y'][labeled], minlength=2).tolist(),
                                       labeled_ids=d['ids'][labeled].tolist(),
                                       step_matched_epochs=step_matched_epochs(len(train), len(labeled))))
    locked_write(OUT / 'label_allocation.json', allocation)
    protocol = dict(version='paper_v6_label_curve',
                    purpose='Label-budget curve extension of the frozen paper_v4 audit: 5, 10 and 50 percent budgets on the identical folds, seeds, recipes and threshold.',
                    declaration_timing='Protocol, allocation and signatures written by prepare before any v6 fitting; local UTC event in preparation_event.json; no external preregistration claim.',
                    cohort='Unchanged 2213 DISFOR locations; 1937 stable forest and 276 clear-cut; frozen v4 folds (5 km + source-event components).',
                    budgets=BUDGETS, reused_v4_budgets=V4_BUDGETS, seeds=SEEDS, methods=METHODS, folds=FOLDS, fits=FOLDS * len(SEEDS) * len(BUDGETS) * len(METHODS),
                    label_allocation='subset(y, train, budget, seed): per-class nested random order, ceiling count, minimum one per class; identical IDs for every method within fold/seed/budget; nested with the v4 20 percent subsets (5/10 percent are subsets of it; 50 percent contains it).',
                    training='Frozen advanced.py recipes. RF 500 trees; CNN/Transformer 40 supervised epochs; SSL 60 reconstruction epochs on all outer-training sequences plus 40 supervised epochs; step-matched Transformer epochs = ceil((60*ceil(n_train/64)+40*ceil(n_labeled/64))/ceil(n_labeled/64)). No early stopping, validation selection, calibration or threshold fitting; threshold 0.5.',
                    estimand='Per budget and method: three pooled out-of-fold macro-F1 values (one per seed) over all 2213 locations; mean and sample SD across seeds; paired spatial-component bootstrap intervals for SSL minus short Transformer and SSL minus step-matched Transformer.',
                    uncertainty='Conditional cluster bootstrap on the fixed cohort and fits; three seeds; no multiplicity adjustment; not external validation.',
                    limits=['Same-source retrospective cohort; recipes were developed on this dataset.',
                            'At 5 percent, labeled training sets hold roughly 11 clear-cut examples per fold, so single-seed results are noisy by construction.',
                            'Step matching equalises optimizer updates, not FLOPs, wall time, learning rate or labeled presentations.',
                            'Training hardware differs from paper_v4 (recorded in execution.json); cross-platform float differences at 1e-6 level are expected.'])
    locked_write(OUT / 'protocol.json', protocol)
    jobs = [dict(fold=f, seed=s, budget=b, method=m) for f in range(FOLDS) for s in SEEDS for b in BUDGETS for m in METHODS]
    locked_write(OUT / 'jobs.json', jobs)
    sources = ['scripts/label_curve_v6.py', 'src/orman_ssl/advanced.py', 'src/orman_ssl/experiment.py', 'src/orman_ssl/inputs.py',
               'data/processed/real_series.npz', 'experiments/paper_v4/folds.json', 'experiments/paper_v4/signature.json',
               'experiments/paper_v6_label_curve/protocol.json', 'experiments/paper_v6_label_curve/jobs.json',
               'experiments/paper_v6_label_curve/label_allocation.json']
    locked_write(OUT / 'signature.json', {name: digest(ROOT / name) for name in sources})
    if not (OUT / 'preparation_event.json').exists():
        write(OUT / 'preparation_event.json', dict(prepared_at_utc=datetime.now(timezone.utc).isoformat(),
                                                 run_files_present=len(list((OUT / 'runs').glob('*.json'))),
                                                 platform=platform.platform(), python=platform.python_version(), torch=torch.__version__))
    return protocol


def verify_signature():
    for name, expected in read(OUT / 'signature.json').items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Frozen v6 input changed: {name}')
    for name, expected in read(V4 / 'signature.json').items():
        if digest(ROOT / name) != expected:
            raise ValueError(f'Frozen v4 input changed: {name}')


def run_name(job):
    return f"{job['method']}_f{job['fold']}_s{job['seed']}_b{job['budget']}"


def scores(y, p):
    y = np.asarray(y)
    p = np.asarray(p, dtype=np.float64)
    if p.shape != y.shape or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('Invalid probabilities')
    q = p >= .5
    cm = confusion_matrix(y, q, labels=[0, 1])
    return dict(macro_f1=float(f1_score(y, q, average='macro', zero_division=0)), average_precision=float(average_precision_score(y, p)),
                roc_auc=float(roc_auc_score(y, p)), brier=float(brier_score_loss(y, p)),
                clear_cut_recall=float(cm[1, 1] / cm[1].sum()) if cm[1].sum() else 0.0, confusion_matrix=cm.tolist())


def worker(job):
    # One BLAS/torch thread per worker process: the frozen recipe calls torch.set_num_threads(2) internally,
    # which oversubscribes a two-core host when two workers run; pin it to the declared per-worker thread count.
    threads = int(os.environ.get('ORMAN_V6_THREADS', '1'))
    torch.set_num_threads = lambda n, _orig=torch.set_num_threads: _orig(threads)
    torch.set_num_threads(threads)
    verify_signature()
    name = run_name(job)
    dest = OUT / 'runs' / (name + '.json')
    if dest.exists():
        row = read(dest)
        if row['signature_sha256'] != digest(OUT / 'signature.json'):
            raise ValueError('Cached run integrity failure: ' + name)
        return dict(name=name, cached=True, seconds=row['seconds'], macro_f1=row['metrics']['macro_f1'])
    start = time.monotonic()
    d = context()
    part = read(V4 / 'folds.json')[job['fold']]
    train, test = np.array(part['train_indices']), np.array(part['test_indices'])
    alloc = [a for a in read(OUT / 'label_allocation.json') if a['fold'] == job['fold'] and a['seed'] == job['seed'] and a['budget'] == job['budget']][0]
    labeled = subset(d['y'], train, job['budget'], job['seed'])
    if d['ids'][labeled].tolist() != alloc['labeled_ids']:
        raise ValueError('Label allocation drifted from declaration')
    chosen = 'transformer48' if job['method'] == 'step_matched' else job['method']
    config = {c['name']: c for c in adv.CONFIGS}[chosen]
    epochs = alloc['step_matched_epochs'] if job['method'] == 'step_matched' else 40
    state, log = adv.fit(config, d, train, seed=job['seed'], epochs=epochs, pre_epochs=60, labeled=labeled, early_stop=False)
    p = adv.state_probability(state, adv.view(d, test))
    row = dict(**job, name=name, n_train=int(len(train)), n_labeled=int(len(labeled)),
               labeled_ids=d['ids'][labeled].tolist(), train_ids=d['ids'][train].tolist(), test_ids=d['ids'][test].tolist(),
               supervised_epochs=0 if config['kind'] == 'rf' else epochs, pretraining_epochs=60 if config.get('ssl') else 0,
               y=d['y'][test].tolist(), groups=d['groups'][test].tolist(), probabilities=p.tolist(), metrics=scores(d['y'][test], p),
               signature_sha256=digest(OUT / 'signature.json'), seconds=time.monotonic() - start, log=log)
    write(dest, row)
    return dict(name=name, cached=False, seconds=row['seconds'], macro_f1=row['metrics']['macro_f1'])


def train(workers=2, max_jobs=None):
    verify_signature()
    jobs = read(OUT / 'jobs.json')
    pending = [j for j in jobs if not (OUT / 'runs' / (run_name(j) + '.json')).exists()]
    selected = pending[: (max_jobs or len(pending))]
    # Longest jobs first so the pool tail is short.
    order = {'ssl_transformer48': 0, 'step_matched': 1, 'cnn64': 2, 'transformer48': 3, 'rf_leaf4': 4}
    selected.sort(key=lambda j: order[j['method']])
    start = time.monotonic()
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, j) for j in selected]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            value = future.result(); results.append(value); print(i, '/', len(selected), json.dumps(value), flush=True)
    record = dict(scope='declared_run', new_fits=len(selected), workers=workers, elapsed_wall_seconds=time.monotonic() - start,
                  completed_records=len(list((OUT / 'runs').glob('*.json'))),
                  platform=platform.platform(), python=platform.python_version(), torch=torch.__version__,
                  threads=torch.get_num_threads(), result=results)
    write(OUT / 'execution.json', record)
    verify_signature()
    return record


def macro(y, p, weights):
    q = p >= .5
    tp = np.sum(weights * (q & (y == 1))); tn = np.sum(weights * ((~q) & (y == 0)))
    fp = np.sum(weights * (q & (y == 0))); fn = np.sum(weights * ((~q) & (y == 1)))
    return .5 * ((2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0) + (2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0))


def analyze():
    verify_signature()
    jobs = read(OUT / 'jobs.json')
    paths = sorted((OUT / 'runs').glob('*.json'))
    if len(paths) != len(jobs):
        raise ValueError(f'All {len(jobs)} declared runs must finish before pooled analysis; found {len(paths)}')
    records = {r['name']: r for r in map(read, paths)}
    if set(records) != {run_name(j) for j in jobs}:
        raise ValueError('Unexpected or missing runs')
    d = context()
    y = d['y']; groups = d['groups']; n = len(y)
    lookup = {v: i for i, v in enumerate(d['ids'])}
    folds = read(V4 / 'folds.json')
    pooled = {}
    summary = []
    for budget in BUDGETS:
        for method in METHODS:
            probs = []; per_seed = []; seconds = 0.0; epochs = set()
            for seed in SEEDS:
                p = np.full(n, np.nan)
                for fold in range(FOLDS):
                    row = records[run_name(dict(fold=fold, seed=seed, budget=budget, method=method))]
                    part = folds[fold]
                    if row['train_ids'] != part['train_ids'] or row['test_ids'] != part['test_ids']:
                        raise ValueError('Run identities differ from frozen folds')
                    if not set(row['labeled_ids']) <= set(row['train_ids']):
                        raise ValueError('Labeled subset leaks outside training partition')
                    ix = np.array([lookup[v] for v in row['test_ids']])
                    if not np.isnan(p[ix]).all() or not np.array_equal(y[ix], row['y']):
                        raise ValueError('Invalid OOF/label alignment')
                    actual = scores(row['y'], row['probabilities'])
                    for key in actual:
                        if key == 'confusion_matrix':
                            if actual[key] != row['metrics'][key]: raise ValueError('Confusion matrix mismatch')
                        elif abs(actual[key] - row['metrics'][key]) > 1e-7:
                            raise ValueError('Stored metric mismatch')
                    if method != 'rf_leaf4':
                        if len(row['log']['history']) != row['supervised_epochs'] or any(v['validation_macro_f1'] is not None for v in row['log']['history']):
                            raise ValueError('Training history mismatch or validation selection')
                        if len(row['log']['pretrain_loss']) != row['pretraining_epochs']:
                            raise ValueError('Pretraining history mismatch')
                    p[ix] = row['probabilities']; seconds += row['seconds']; epochs.add(row['supervised_epochs'])
                if not np.isfinite(p).all():
                    raise ValueError('Incomplete OOF coverage')
                probs.append(p)
                per_seed.append(dict(seed=seed, **scores(y, p)))
            pooled[(budget, method)] = np.stack(probs)
            summary.append(dict(budget=budget, method=method, seed_results=per_seed,
                                macro_f1_mean=float(np.mean([r['macro_f1'] for r in per_seed])),
                                macro_f1_std=float(np.std([r['macro_f1'] for r in per_seed], ddof=1)),
                                average_precision_mean=float(np.mean([r['average_precision'] for r in per_seed])),
                                recall_mean=float(np.mean([r['clear_cut_recall'] for r in per_seed])),
                                brier_mean=float(np.mean([r['brier'] for r in per_seed])),
                                n_labeled=sorted({records[run_name(dict(fold=f, seed=s, budget=budget, method=method))]['n_labeled'] for f in range(FOLDS) for s in SEEDS}),
                                supervised_epochs=sorted(epochs), total_fit_seconds=seconds))
    # Paired spatial-component bootstrap, same construction as analyze_paper.py (seed 120926, 2000 draws).
    unique, gi = np.unique(groups, return_inverse=True)
    rng = np.random.default_rng(120926)
    comparators = ['transformer48', 'step_matched', 'cnn64', 'rf_leaf4']
    draws = {(b, c): [] for b in BUDGETS for c in comparators}
    skipped = 0
    for _ in range(2000):
        sampled = rng.integers(0, len(unique), size=len(unique)); weights = np.bincount(sampled, minlength=len(unique))[gi]
        if not weights[y == 0].sum() or not weights[y == 1].sum():
            skipped += 1; continue
        for b in BUDGETS:
            ssl = np.mean([macro(y, p, weights) for p in pooled[(b, 'ssl_transformer48')]])
            for c in comparators:
                other = np.mean([macro(y, p, weights) for p in pooled[(b, c)]])
                draws[(b, c)].append(float(ssl - other))
    ones = np.ones(n)
    comparisons = []
    for b in BUDGETS:
        for c in comparators:
            a, o = pooled[(b, 'ssl_transformer48')], pooled[(b, c)]
            comparisons.append(dict(budget=b, comparator=c, role='primary' if c == 'transformer48' else 'exploratory',
                                    mean_difference=float(np.mean([macro(y, p, ones) - macro(y, q, ones) for p, q in zip(a, o)])),
                                    paired_group_bootstrap_95_interval=np.quantile(draws[(b, c)], [.025, .975]).tolist(), draws=len(draws[(b, c)])))
    v4 = read(V4 / 'analysis.json')
    curve = []
    for s in v4['summary']:
        if s['method'] in METHODS:
            curve.append(dict(budget=s['budget'], method=s['method'], macro_f1_mean=s['macro_f1_mean'], macro_f1_std=s['macro_f1_std'],
                              average_precision_mean=s['pr_auc_mean'], source='paper_v4'))
    for s in summary:
        curve.append(dict(budget=s['budget'], method=s['method'], macro_f1_mean=s['macro_f1_mean'], macro_f1_std=s['macro_f1_std'],
                          average_precision_mean=s['average_precision_mean'], source='paper_v6'))
    curve.sort(key=lambda r: (r['method'], r['budget']))
    v4c = [c for c in v4['paired_comparisons'] if c['comparator'] in comparators]
    result = dict(status='complete_verified', version='paper_v6_label_curve', fits=len(jobs), seeds=SEEDS, locations=n,
                  summary=summary, paired_comparisons=comparisons,
                  bootstrap=dict(unit='spatial component', draws_requested=2000, one_class_draws_discarded=skipped, seed=120926,
                                 limitation='Conditional on fixed data, folds and trained fits; not external validation; no multiplicity adjustment.'),
                  combined_curve=curve, v4_paired_comparisons_at_20_percent=v4c,
                  limitations=read(OUT / 'protocol.json')['limits'])
    write(OUT / 'analysis.json', result)
    arrays = dict(ids=d['ids'], y=y, groups=groups)
    for (b, m), p in pooled.items():
        arrays[f'{m}_{b}'] = p
    np.savez_compressed(OUT / 'oof_predictions.npz', **arrays)
    fields = ['budget', 'method', 'macro_f1_mean', 'macro_f1_std', 'average_precision_mean', 'source']
    with (OUT / 'combined_curve.csv').open('w', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=fields); w.writeheader(); w.writerows({k: r[k] for k in fields} for r in curve)
    write(OUT / 'verification.json', dict(status='passed', fits=len(jobs), pooled_vectors=len(pooled) * len(SEEDS),
                                          checks=['v4 and v6 signatures', 'exact declared run IDs', 'declared label allocation', 'OOF once per location',
                                                  'label alignment', 'metrics recomputed', 'fixed epoch histories and no validation selection']))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'train', 'analyze'])
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--max-jobs', type=int, default=None)
    args = parser.parse_args()
    if args.stage == 'prepare':
        print(json.dumps(prepare(), indent=2))
    elif args.stage == 'train':
        record = train(args.workers, args.max_jobs)
        print(json.dumps({k: v for k, v in record.items() if k != 'result'}, indent=2))
    else:
        result = analyze()
        print(json.dumps(dict(status=result['status'], fits=result['fits'],
                              summary=[{k: s[k] for k in ['budget', 'method', 'macro_f1_mean', 'macro_f1_std']} for s in result['summary']],
                              paired_comparisons=result['paired_comparisons']), indent=2))


if __name__ == '__main__':
    main()
