import json
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from orman_ssl.inputs import BANDS,monthly_days,prepare_observations,validate_input
from orman_ssl.predict import predict

class InputContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with np.load(ROOT/'data/processed/test_inference.npz',allow_pickle=False) as src:
            cls.reference={k:src[k].copy() for k in src.files}
    def fresh(self):
        return {k:v[:2].copy() if v.ndim else v.copy() for k,v in self.reference.items()}
    def test_empty_batch_rejected(self):
        d=self.fresh()
        for k in ['x','observed','days','ids']: d[k]=d[k][:0]
        with self.assertRaisesRegex(ValueError,'nonempty'): validate_input(d)
    def test_channel_count_rejected_before_broadcast(self):
        d=self.fresh();d['x']=d['x'][:,:,:1];d['observed']=d['observed'][:,:,:1]
        with self.assertRaises(ValueError): predict(ROOT/'models/model.pt',d)
    def test_reflectance_units_rejected(self):
        d=self.fresh();meta=json.loads(str(d['metadata']));meta['units']='reflectance';d['metadata']=json.dumps(meta)
        with self.assertRaisesRegex(ValueError,'DN units'):validate_input(d)
    def test_timestamps_cannot_be_unix_or_month_indices(self):
        for bad in [np.arange(24),np.arange(24)+1700000000]:
            d=self.fresh();d['days']=np.tile(bad,(2,1))
            with self.assertRaisesRegex(ValueError,'calendar'):validate_input(d)
    def test_leap_calendar_templates_accepted(self):
        for year in [2018,2020,2021,2024,2025]:
            d=self.fresh();d['days']=np.tile(monthly_days(year),(2,1));validate_input(d)
    def test_incorrect_id_dimensions_rejected(self):
        d=self.fresh();d['ids']=d['ids'][:,None]
        with self.assertRaisesRegex(ValueError,'vector'):validate_input(d)
    def test_missing_month_payload_does_not_affect_inference(self):
        d=self.fresh();a=predict(ROOT/'models/model.pt',d)
        d['x'][~d['observed']]=123456
        b=predict(ROOT/'models/model.pt',d)
        np.testing.assert_array_equal(a['probabilities'],b['probabilities'])
    def observations(self):
        rows=[]
        for t in ['2019-01-01','2019-01-20','2019-01-25','2020-02-10']:
            rows.append(dict(sample_id=1,timestamps=t,clear=True,SCL=4,**{b:10. for b in BANDS}))
        rows[1].update({b:30. for b in BANDS})
        rows[2].update({b:9999. for b in BANDS});rows[2]['SCL']=9
        return pd.DataFrame(rows)
    def test_monthly_median_cloud_mask_and_missingness(self):
        d,details=prepare_observations(self.observations(),[dict(id='one',sample_id=1,target_year=2020)],'unit test')
        np.testing.assert_array_equal(d['x'][0,0],np.full(10,20.))
        self.assertTrue(np.isnan(d['x'][0,1]).all())
        self.assertFalse(d['observed'][0,1].any())
        self.assertFalse(details[0]['quality_eligible'])
    def test_labels_cannot_change_prepared_features(self):
        obs=self.observations();obs['label']=0
        a,_=prepare_observations(obs,[dict(id='one',sample_id=1,target_year=2020)],'test')
        obs['label']=999
        b,_=prepare_observations(obs,[dict(id='one',sample_id=1,target_year=2020)],'test')
        self.assertNotIn('y',a);np.testing.assert_array_equal(a['x'],b['x'])
    def test_string_false_not_interpreted_as_true(self):
        obs=self.observations();obs['clear']='False'
        with self.assertRaisesRegex(ValueError,'booleans'):
            prepare_observations(obs,[dict(id='one',sample_id=1,target_year=2020)],'test')
    def test_no_usable_observation_fails_before_prediction(self):
        obs=self.observations();obs['clear']=False
        with self.assertRaisesRegex(ValueError,'No usable'):
            prepare_observations(obs,[dict(id='one',sample_id=1,target_year=2020)],'test')

if __name__=='__main__':unittest.main()
