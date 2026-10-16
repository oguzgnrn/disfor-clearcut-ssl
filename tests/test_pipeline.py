import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from orman_ssl.experiment import synthetic,validate,split_groups,normalize,subset,mask_observations,TemporalModel
from sentinel_demo import normalized_difference

class ScientificContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name)/'toy.npz';synthetic(p)
        self.d=dict(np.load(p,allow_pickle=False))
        self.parts=split_groups(self.d['groups'],self.d['y'])

    def tearDown(self): self.tmp.cleanup()

    def test_no_group_overlap(self):
        sets=[set(self.d['groups'][i]) for i in self.parts]
        self.assertFalse(sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2])
        self.assertEqual(sum(map(len,self.parts)),len(self.d['y']))

    def test_heldout_values_cannot_change_scaler(self):
        x,m=self.d['x'],self.d['observed'];tr,va,te=self.parts
        _,mean,std=normalize(x,m,tr)
        changed=x.copy();changed[np.r_[va,te]]=1e7
        _,mean2,std2=normalize(changed,m,tr)
        np.testing.assert_array_equal(mean,mean2);np.testing.assert_array_equal(std,std2)

    def test_nested_label_budgets_and_training_only(self):
        tr=self.parts[0]
        small=set(subset(self.d['y'],tr,.05,7));large=set(subset(self.d['y'],tr,.2,7))
        self.assertTrue(small<=large<=set(tr))
        self.assertEqual(len(np.unique(self.d['y'][list(small)])),3)

    def test_missing_values_never_become_ssl_targets(self):
        m=torch.tensor(self.d['observed'][:4]);hide=mask_observations(m)
        self.assertTrue(hide.any());self.assertFalse((hide&~m).any())

    def test_real_data_require_provenance(self):
        self.assertEqual(validate(self.d)['kind'],'synthetic')
        meta=json.loads(str(self.d['metadata']));meta['kind']='real';self.d['metadata']=json.dumps(meta)
        with self.assertRaises(ValueError): validate(self.d)

    def test_duplicate_id_rejected(self):
        self.d['ids'][1]=self.d['ids'][0]
        with self.assertRaises(ValueError): validate(self.d)

    def test_masked_payload_does_not_change_logits(self):
        z,_,_=normalize(self.d['x'],self.d['observed'],self.parts[0])
        x=torch.tensor(z[:3]);m=torch.tensor(self.d['observed'][:3]);days=torch.tensor(self.d['days'][:3])
        model=TemporalModel(6,3).eval()
        with torch.no_grad():
            a=model(x,m,days)[0];x[~m]=12345;b=model(x,m,days)[0]
        torch.testing.assert_close(a,b)

    def test_normalized_difference_zero_and_nodata(self):
        a=np.array([.6,0,np.nan],dtype='float32');b=np.array([.2,0,.1],dtype='float32')
        v=normalized_difference(a,b)
        self.assertAlmostEqual(float(v[0]),.5,places=5);self.assertTrue(np.isnan(v[1:]).all())

    def test_saved_result_integrity(self):
        path=Path(__file__).resolve().parents[1]/'reports/experiment/results.json'
        if not path.exists(): self.skipTest('Run experiment first')
        results=json.loads(path.read_text())
        for row in results['runs']:
            self.assertFalse(set(row['labeled_ids'])&set(row['test_ids']))
            self.assertEqual(sum(map(sum,row['confusion_matrix'])),row['n_test'])
            self.assertEqual(len(row['predictions']),row['n_test'])
            self.assertTrue(0<=row['macro_f1']<=1)

if __name__=='__main__': unittest.main()
