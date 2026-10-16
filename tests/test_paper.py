import json,sys,unittest
from pathlib import Path
import numpy as np
from sklearn.metrics import f1_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from analyze_paper import macro
from audit_paper_errors import subgroup_metrics, fingerprint

class PaperContracts(unittest.TestCase):
    def test_weighted_macro_matches_replication(self):
        y=np.array([0,0,1,1,1]);p=np.array([.1,.7,.2,.6,.9]);w=np.array([3,1,2,0,4]);ix=np.repeat(np.arange(len(y)),w)
        self.assertAlmostEqual(macro(y,p,w),f1_score(y[ix],p[ix]>=.5,average='macro'))
    def test_paper_outer_folds_partition_every_point_once(self):
        folds=json.loads((ROOT/'experiments/paper_v4/folds.json').read_text());d=np.load(ROOT/'data/processed/real_series.npz')
        seen=[]
        for f in folds:
            a,b=set(f['train_ids']),set(f['test_ids']);self.assertFalse(a&b);self.assertEqual(a|b,set(d['ids']));seen.extend(b)
            ga=set(d['groups'][f['train_indices']]);gb=set(d['groups'][f['test_indices']]);self.assertFalse(ga&gb)
        self.assertEqual(len(seen),2213);self.assertEqual(len(set(seen)),2213)
    def test_unused_probe_excludes_prior_samples(self):
        p=json.loads((ROOT/'experiments/paper_v4/unused_probe_audit.json').read_text());used={r['sample_id'] for r in json.loads((ROOT/'data/disfor/sample_manifest.json').read_text())}
        self.assertTrue(all(w['sample_id'] not in used and w['distance_km']>5 for w in p['windows']))
    def test_declared_jobs_cover_all_fixed_controls(self):
        jobs=json.loads((ROOT/'experiments/paper_v4/jobs.json').read_text());self.assertEqual(len(jobs),180)
        self.assertEqual(len({(r['fold'],r['seed'],r['budget'],r['method']) for r in jobs}),180)

class PostHocAuditContracts(unittest.TestCase):
    def test_single_class_subgroup_does_not_report_binary_macro(self):
        result=subgroup_metrics(np.zeros(3,dtype=int),np.array([[.1,.2,.9]]*3))
        self.assertIsNone(result['macro_f1_mean']);self.assertIsNone(result['average_precision_mean'])
        self.assertFalse(result['both_classes']);self.assertEqual(result['confusion_matrices'][0],[[2,1],[0,0]])
    def test_three_seed_metrics_are_not_ensemble_metrics(self):
        y=np.array([0,0,1,1]);p=np.array([[.1,.2,.7,.8],[.1,.9,.2,.8],[.7,.8,.9,.6]])
        result=subgroup_metrics(y,p)
        expected=np.mean([f1_score(y,row>=.5,average='macro') for row in p])
        self.assertAlmostEqual(result['macro_f1_mean'],expected)
    def test_fingerprint_ignores_missing_payload_but_keeps_time(self):
        x=np.ones((24,10));m=np.ones_like(x,dtype=bool);m[0]=False;t=np.arange(24)
        altered=x.copy();altered[0]=np.nan
        self.assertEqual(fingerprint(x,m,t),fingerprint(altered,m,t))
        self.assertNotEqual(fingerprint(x,m,t),fingerprint(x,m,t+1))
    def test_error_review_preserves_original_labels(self):
        rows=json.loads((ROOT/'experiments/paper_v4/review_candidates.json').read_text())
        original={r['id']:r['label'] for r in json.loads((ROOT/'data/disfor/sample_manifest.json').read_text())}
        self.assertEqual(len(rows),81)
        for r in rows:
            self.assertEqual(r['label'],original[r['id']])
            self.assertEqual(r['review_status'],'not reviewed; original label unchanged')
            self.assertTrue(r['predictions']['cnn64']['wrong_seeds']>=2 or r['predictions']['ssl_transformer48']['wrong_seeds']>=2)

if __name__=='__main__':unittest.main()
