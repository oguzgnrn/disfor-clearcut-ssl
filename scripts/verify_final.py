"""Verify the real-data delivery without training or choosing new models."""
import hashlib
import json
from pathlib import Path
import numpy as np
from pypdf import PdfReader
from sklearn.metrics import confusion_matrix, f1_score
ROOT = Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT/path).read_text())
checks = []
for row in read('data/disfor/downloads.json')['files']:
    assert hashlib.sha256((ROOT/'data/disfor'/row['name']).read_bytes()).hexdigest() == row['sha256']
checks.append('All pinned DISFOR download hashes match')
p = read('reports/inference_cli.json')
q = read('reports/real_experiment/selected_test_predictions.json')
assert p['ids'] == q['ids'] and len(p['ids']) == 486
np.testing.assert_allclose(p['probabilities'], q['probabilities'], atol=1e-6)
assert p['predictions'] == q['predictions']
assert all(p['quality_eligible'])
checks.append('Unlabeled CLI inference reproduces all 486 saved predictions and passes quality checks')
d = np.load(ROOT/'data/processed/real_series.npz',allow_pickle=False)
labels = dict(zip(d['ids'].tolist(),d['y'].tolist()))
y = [labels[i] for i in p['ids']]
a = read('reports/real_analysis.json')
assert confusion_matrix(y,p['predictions']).tolist() == a['selected_confusion_matrix']
assert abs(f1_score(y,p['predictions'],average='macro')-a['selected_test_macro_f1']) < 1e-12
features = read('reports/real_experiment/test_predictions.geojson')['features']
assert len(features) == 486
checks.append('Selected-model metrics and GeoJSON support agree with actual test labels')
pdf = PdfReader(ROOT/'output/pdf/Orman_SSL_Toplanti_Dosyasi.pdf')
assert len(pdf.pages)==7
assert all(len(page.extract_text())>200 for page in pdf.pages)
checks.append('Seven-page PDF contains text on every page')
assert len(read('reports/real_experiment/results.json')['runs'])==36
checks.append('All 36 primary real-data runs are present')
result = dict(status='passed', checks=checks, automated_test_log='reports/tests_v2.log', manual_review_record='docs/TESLIM_KONTROLU.md')
(ROOT/'reports/final_verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
