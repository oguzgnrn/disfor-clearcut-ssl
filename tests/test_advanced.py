import json
import sys
import unittest
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from orman_ssl.advanced import TemporalNet,CONFIGS,block_mask,augment,context

class AdvancedContracts(unittest.TestCase):
    def test_block_mask_targets_only_observed_cells(self):
        torch.manual_seed(7)
        m=torch.rand(16,24,10)>.4;hidden=block_mask(m)
        self.assertFalse((hidden&~m).any());self.assertTrue((m&~hidden).any((1,2)).all())
        self.assertTrue(hidden.any((1,2)).all())
    def test_missing_month_augmentation_keeps_at_least_one_observation(self):
        m=torch.zeros(100,24,10,dtype=torch.bool);m[:,3,0]=True
        q=augment(m);self.assertTrue(q.any((1,2)).all());self.assertFalse((q&~m).any())
    def test_network_ignores_masked_payload(self):
        torch.set_num_threads(2);torch.manual_seed(7)
        x=torch.randn(3,24,10);m=torch.rand(3,24,10)>.3;m[:,5:9]=False
        t=torch.arange(24).float()[None].repeat(3,1)*30
        for config in [CONFIGS[2],CONFIGS[4]]:
            model=TemporalNet(config).eval()
            with torch.no_grad():
                a=model(x,m,t)[0];b=model(x.masked_fill(~m,float('nan')),m,t)[0]
            torch.testing.assert_close(a,b);self.assertTrue(torch.isfinite(a).all())
    def test_fold_ids_exclude_outer_development_and_test(self):
        path=ROOT/'experiments/advanced_v3/folds.json'
        if not path.exists():self.skipTest('Run training to generate fold manifest')
        d,parts=context();lookup={s:i for i,s in enumerate(d['ids'])}
        allowed=set(d['ids'][parts['train']]);seen=[]
        for fold in json.loads(path.read_text()):
            a,b=set(fold['train_ids']),set(fold['validation_ids'])
            self.assertFalse(a&b);self.assertEqual(a|b,allowed);seen.extend(b)
            ga={int(d['groups'][lookup[s]]) for s in a};gb={int(d['groups'][lookup[s]]) for s in b}
            self.assertFalse(ga&gb)
        self.assertEqual(set(seen),allowed);self.assertEqual(len(seen),len(allowed))

if __name__=='__main__':unittest.main()
