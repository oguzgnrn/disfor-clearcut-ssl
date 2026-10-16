"""Acceptance checks for model selection, leakage boundaries and deployed inference."""
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from orman_ssl.advanced import context,ensemble_predict,write_json,digest
OUT=ROOT/'experiments/advanced_v3';MODEL=ROOT/'models/advanced_v3'


def main():
    d,parts=context();bundle=json.loads((MODEL/'bundle.json').read_text());selection=json.loads((OUT/'selection.json').read_text())
    if len(list((OUT/'cv').glob('*.json')))!=24:raise ValueError('Expected 24 completed CV fits')
    if len(json.loads((OUT/'low_label_training.json').read_text()))!=18:raise ValueError('Expected 18 low-label fits')
    expected={r['config']['name'] for r in selection['ranking'][:2]}
    if len(bundle['members'])!=10:raise ValueError('Expected ten members')
    if {m['config']['name'] for m in bundle['members']}!=expected:raise ValueError('Selection mismatch')
    for config in expected:
        if {m['seed'] for m in bundle['members'] if m['config']['name']==config}!={7,17,27,37,47}:raise ValueError('Missing final seeds')
    train=set(d['ids'][parts['train']]);val=set(d['ids'][parts['validation']]);test=set(d['ids'][parts['test']])
    if set(bundle['training_ids'])!=train or set(bundle['calibration_ids'])!=val:raise ValueError('Training/calibration leakage')
    if (train|val)&test:raise ValueError('Test IDs used for training')
    for row in json.loads((OUT/'low_label_training.json').read_text()):
        if not set(row['labeled_ids'])<=train:raise ValueError('Low-label split leakage')
    with np.load(ROOT/'data/processed/test_inference.npz',allow_pickle=False) as source:
        raw={k:source[k] for k in source.files}
    q=ensemble_predict(MODEL/'bundle.json',raw);saved=json.loads((OUT/'test_predictions.json').read_text())
    if q['ids']!=saved['ids'] or q['predictions']!=saved['predictions']:raise ValueError('Deployed predictions mismatch')
    np.testing.assert_allclose(q['probabilities'],saved['probabilities'],atol=1e-7)
    if not np.isfinite(q['probabilities']).all():raise ValueError('Nonfinite probabilities')
    np.testing.assert_allclose(np.sum(q['probabilities'],axis=1),1,atol=1e-7)
    actual=json.loads((ROOT/'output/advanced_prediction/predictions.json').read_text())
    if actual['ids']!=q['ids'] or actual['predictions']!=q['predictions']:raise ValueError('Raw observation path differs')
    np.testing.assert_allclose(actual['probabilities'],q['probabilities'],atol=1e-7)
    evaluation=json.loads((OUT/'evaluation.json').read_text())
    if evaluation['bundle_sha256']!=digest(MODEL/'bundle.json'):raise ValueError('Evaluation is from a different bundle')
    result=dict(status='passed',members=10,cv_fits=24,low_label_fits=18,heldout_inference_samples=len(q['ids']),
                checks=['CV-only selection','five fixed seeds per selected config','no test in training/calibration',
                        'low-label subsets restricted to training','member file hashes','NPZ inference equals evaluation',
                        'raw observation inference equals NPZ inference','probability normalization','frozen evaluation bundle'])
    write_json(OUT/'acceptance.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
