import json,sys,unittest
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from orman_ssl.predict import predict

class RealPipeline(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=dict(np.load(ROOT/'data/processed/real_series.npz',allow_pickle=False))
  cls.prep=json.loads((ROOT/'reports/disfor_preparation.json').read_text())
  cls.result=json.loads((ROOT/'reports/real_experiment/results.json').read_text())
  cls.manifest=json.loads((ROOT/'data/disfor/sample_manifest.json').read_text())
  cls.card=json.loads((ROOT/'models/model_card.json').read_text())
 def test_unique_points(self):
  self.assertEqual(len({r['sample_id'] for r in self.manifest}),len(self.manifest))
 def test_spatial_buffer(self):
  self.assertTrue(all(v>5 for v in self.prep['minimum_cross_split_distance_km'].values()))
 def test_source_event_not_split(self):
  clusters={}
  for r in self.manifest:
   if r['dataset'] in [1,3] and r['source_cluster'] is not None:
    clusters.setdefault((r['dataset'],r['source_cluster']),set()).add(r['split'])
  self.assertTrue(all(len(v)==1 for v in clusters.values()))
 def test_real_primary_support(self):
  self.assertEqual(self.prep['class_counts'],[1937,276])
  self.assertGreaterEqual(min(self.prep['split']['test']['class_counts']),30)
 def test_no_label_features(self):
  self.assertEqual(json.loads(str(self.data['metadata']))['channels'],['B02','B03','B04','B05','B06','B07','B08','B8A','B11','B12'])
  self.assertEqual(self.data['x'].shape[1:],(24,10))
 def test_nested_real_budgets_and_no_test_overlap(self):
  for seed in [7,17,27]:
   rows=[r for r in self.result['runs'] if r['seed']==seed and r['method']=='Transformer']
   for a,b in zip(rows,rows[1:]):self.assertTrue(set(a['labeled_ids'])<=set(b['labeled_ids']))
   for r in rows:self.assertFalse(set(r['labeled_ids'])&set(r['test_ids']))
 def test_selection_uses_validation(self):
  scores=self.card['validation_scores']
  self.assertEqual(self.card['method'],max(scores,key=scores.get));self.assertEqual(self.card['seed'],7)
 def test_inference_matches_recorded_test(self):
  saved=json.loads((ROOT/'reports/real_experiment/selected_test_predictions.json').read_text());lookup={v:i for i,v in enumerate(self.data['ids'])}
  ix=np.array([lookup[s] for s in saved['ids'][:12]])
  d={k:v[ix] if isinstance(v,np.ndarray) and v.ndim and len(v)==len(self.data['x']) else v for k,v in self.data.items()}
  d.pop('y');d.pop('groups')
  q=predict(ROOT/self.card['checkpoint'],d)
  np.testing.assert_allclose(q['probabilities'],saved['probabilities'][:12],rtol=1e-5,atol=1e-6)
 def test_wrong_band_order_rejected(self):
  d=self.data.copy();meta=json.loads(str(d['metadata']));meta['channels']=meta['channels'][::-1];d['metadata']=json.dumps(meta)
  with self.assertRaises(ValueError):predict(ROOT/self.card['checkpoint'],d)

if __name__=='__main__':unittest.main()
