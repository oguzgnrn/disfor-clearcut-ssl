import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from turkiye_zero_shot import gfc_tile, greedy_separate, harmonize_dn, loss_patch_mask, monthly_inputs, stable_mask


class TurkiyeProbeContracts(unittest.TestCase):
    def test_gfc_tile_naming(self):
        self.assertEqual(gfc_tile(32.5, 41.0), '50N_030E')
        self.assertEqual(gfc_tile(28.0, 39.5), '40N_020E')
        self.assertEqual(gfc_tile(30.0, 36.5), '40N_030E')

    def test_loss_patch_requires_compact_same_year_patch(self):
        ly = np.zeros((9, 9), dtype=np.uint8); tc = np.full((9, 9), 80, dtype=np.uint8)
        ly[2:7, 2:7] = 20                      # 5x5 compact patch of 2020 loss
        ly[0, 0] = 20                          # isolated loss pixel
        m = loss_patch_mask(ly, 20, tc)
        self.assertTrue(m[4, 4]); self.assertFalse(m[0, 0]); self.assertFalse(m[4, 4] and m[8, 8])
        tc[4, 4] = 10
        self.assertFalse(loss_patch_mask(ly, 20, tc)[4, 4])

    def test_stable_requires_no_loss_in_neighbourhood(self):
        ly = np.zeros((15, 15), dtype=np.uint8); tc = np.full((15, 15), 80, dtype=np.uint8); dm = np.ones((15, 15), dtype=np.uint8)
        ly[7, 7] = 5
        m = stable_mask(ly, tc, dm)
        self.assertFalse(m[7, 7]); self.assertFalse(m[5, 5]); self.assertTrue(m[0, 0])
        dm[0, 0] = 2
        self.assertFalse(stable_mask(ly, tc, dm)[0, 0])

    def test_greedy_separation_enforces_distance(self):
        rng = np.random.default_rng(0)
        pts = [dict(lat=41.0, lon=32.0 + i * 0.01) for i in range(20)]     # ~0.85 km spacing
        kept = greedy_separate(pts, 5.0, rng)
        self.assertLessEqual(len(kept), 4)
        lons = sorted(p['lon'] for p in kept)
        self.assertTrue(all((b - a) * 84 >= 5 for a, b in zip(lons, lons[1:])))

    def test_offset_removed_only_for_new_baselines(self):
        np.testing.assert_array_equal(harmonize_dn([1300, 2500], '05.09'), [300, 1500])
        np.testing.assert_array_equal(harmonize_dn([300, 2500], '03.01'), [300, 2500])
        np.testing.assert_array_equal(harmonize_dn([500], '04.00'), [0])

    def test_monthly_median_and_mask_follow_contract(self):
        obs = [dict(date='2019-03-05', scl=4, bands=[100] * 10), dict(date='2019-03-25', scl=5, bands=[300] * 10),
               dict(date='2019-03-15', scl=9, bands=[9999] * 10), dict(date='2020-07-10', scl=4, bands=[50] * 10)]
        x, m, ok = monthly_inputs(obs, 2020)
        self.assertTrue(m[2].all()); self.assertAlmostEqual(float(x[2, 0]), 200.0)   # cloudy (SCL 9) scene ignored
        self.assertTrue(m[18].all()); self.assertFalse(m[0].any()); self.assertFalse(ok)  # fewer than 6 months per year


if __name__ == '__main__':
    unittest.main()
