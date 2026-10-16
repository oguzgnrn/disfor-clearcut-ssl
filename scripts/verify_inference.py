"""Verify frozen raw-data inference without evaluating or tuning a new model."""
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
with np.load(ROOT/'output/prediction/input.npz',allow_pickle=False) as actual, np.load(ROOT/'data/processed/test_inference.npz',allow_pickle=False) as expected:
    for key in ['x','observed','days','ids']:
        np.testing.assert_array_equal(actual[key],expected[key])
a=json.loads((ROOT/'output/prediction/predictions.json').read_text())
b=json.loads((ROOT/'reports/real_experiment/selected_test_predictions.json').read_text())
assert a['ids']==b['ids'] and a['predictions']==b['predictions']
np.testing.assert_allclose(a['probabilities'],b['probabilities'],atol=1e-6)
features=json.loads((ROOT/'output/prediction/predictions.geojson').read_text())['features']
windows=json.loads((ROOT/'data/examples/inference_windows.json').read_text())
assert len(features)==len(windows)==486
for f,w in zip(features,windows):
    assert f['properties']['id']==w['id']
    assert f['geometry']['coordinates']==[w['lon'],w['lat']]
result=dict(status='passed',n=486,checks=['Raw label-free observations reproduce x, mask, days and IDs exactly',
    'Predictions and scores match frozen model evaluation', 'GeoJSON IDs and WGS84 points match input windows'])
(ROOT/'output/prediction/verification.json').write_text(json.dumps(result,indent=2))
print('Raw-input inference, predictions and GeoJSON: OK (486 samples)')
