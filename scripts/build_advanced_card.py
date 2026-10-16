"""Persist machine-readable model metadata from completed advanced experiments."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/advanced_v3';MODEL=ROOT/'models/advanced_v3'
a=json.loads((OUT/'evaluation.json').read_text());b=json.loads((MODEL/'bundle.json').read_text())
selection=json.loads((OUT/'selection.json').read_text());acceptance=json.loads((OUT/'acceptance.json').read_text())
card=dict(name='Orman-SSL advanced_v3',status='trained and verified local research model',
    task='Retrospective clear-cut versus undisturbed forest; two full calendar years; 10 Sentinel-2 DN bands',
    architecture=[dict(config=item['config'],members=5,epochs=item['final_epochs']) for item in selection['selected']],
    selection='Four spatial-group folds inside training only; fixed top-two rule',
    training_points=1266,calibration_points=461,benchmark_points=486,benchmark_positive_points=38,
    benchmark_spatial_groups=a['spatial_groups'],benchmark_positive_groups=a['positive_spatial_groups'],
    threshold=b['threshold'],calibration=b['calibration'],
    metrics=a['ensemble'],paired_comparison=a['bootstrap'],
    evaluation_status=a['test_status'],acceptance=acceptance,
    calibration_limits='Fitted on the 461 development points; not guaranteed under geographic or temporal shift',
    disagreement_limits='Member standard deviation is model disagreement, not a calibrated confidence interval',
    quality='At least six observed months in each year; unsuitable samples flagged in output',
    data_source=b['metadata']['source'],data_license=b['metadata']['license'],
    not_validated=['Turkey external field performance','Sentinel-1 fusion','early warning','all forest disturbance types','nationwide mapping'],
    entrypoints=['MODELI_CALISTIR.command','scripts/run_advanced.py','python -m orman_ssl.predict_advanced'],
    provenance=dict(bundle_sha256=a['bundle_sha256'],protocol_sha256=b['protocol_sha256']))
(MODEL/'model_card.json').write_text(json.dumps(card,indent=2))
print('Saved model card from frozen evaluation')
