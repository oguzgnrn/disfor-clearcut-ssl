"""Check actual input semantics, including partially missing band groups."""
import sys
import unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from train_presto_probe import adapt


class PrestoAdapterTests(unittest.TestCase):
    def setUp(self):
        with np.load(ROOT / 'data/processed/real_series.npz', allow_pickle=False) as source:
            self.data = {k: (source[k][:2].copy() if source[k].ndim else source[k].copy())
                         for k in ['x', 'observed', 'days', 'ids', 'metadata']}

    def test_dn_scale_band_order_ndvi_and_absent_modalities(self):
        self.data['x'][:] = 2000
        self.data['x'][:, :, 6] = 6000
        self.data['observed'][:] = True
        x, mask = adapt(self.data)
        np.testing.assert_allclose(x[:, :, 2], .2)
        np.testing.assert_allclose(x[:, :, 8], .6)
        np.testing.assert_allclose(x[:, :, 16], .5)
        self.assertTrue(mask[:, :, [0, 1, 12, 13, 14, 15]].all())
        self.assertFalse(mask[:, :, 2:12].any())

    def test_missing_values_never_become_observed(self):
        self.data['observed'][0, 0, 2] = False
        self.data['x'][0, 0, 2] = np.nan
        x, mask = adapt(self.data)
        self.assertTrue(mask[0, 0, 4])
        self.assertTrue(mask[0, 0, 16])
        self.assertEqual(x[0, 0, 4], 0)
        self.assertTrue(np.isfinite(x).all())

    def test_zero_denominator_follows_upstream(self):
        self.data['x'][0, 0, [2, 6]] = 0
        self.data['observed'][0, 0, [2, 6]] = True
        x, mask = adapt(self.data)
        self.assertEqual(x[0, 0, 16], 0)
        self.assertFalse(mask[0, 0, 16])


if __name__ == '__main__':
    unittest.main()
