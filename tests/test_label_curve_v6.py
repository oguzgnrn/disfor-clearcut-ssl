import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from label_curve_v6 import BUDGETS, OUT, V4, SEEDS, locked_write, macro, read, run_name, scores, step_matched_epochs
from orman_ssl.experiment import subset


class LabelCurveContracts(unittest.TestCase):
    def test_step_matched_epochs_match_v4_formula(self):
        # paper_v4: n_train ~1774, 20 percent labels ~356 -> 320 epochs.
        self.assertEqual(step_matched_epochs(1774, 356), 320)
        self.assertEqual(step_matched_epochs(1774, 90), 880)

    def test_label_subsets_are_nested_across_budgets(self):
        y = np.array([0] * 160 + [1] * 40)
        train = np.arange(200)
        small = set(subset(y, train, .05, 7)); mid = set(subset(y, train, .2, 7)); big = set(subset(y, train, .5, 7))
        self.assertTrue(small <= mid <= big)
        self.assertEqual(len(small), 8 + 2)

    def test_locked_declaration_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'protocol.json'
            locked_write(path, {'budgets': [.05]})
            with self.assertRaisesRegex(ValueError, 'Frozen v6'):
                locked_write(path, {'budgets': [.1]})

    def test_weighted_macro_matches_unweighted_score(self):
        y = np.array([0, 0, 1, 1, 0, 1]); p = np.array([.1, .9, .8, .2, .3, .6])
        self.assertAlmostEqual(macro(y, p, np.ones(6)), scores(y, p)['macro_f1'], places=12)

    def test_invalid_probabilities_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Invalid probabilities'):
            scores([0, 1], [.1, 1.2])

    def test_declared_jobs_cover_design_if_prepared(self):
        if not (OUT / 'jobs.json').exists():
            self.skipTest('v6 not prepared')
        jobs = read(OUT / 'jobs.json')
        self.assertEqual(len(jobs), 5 * len(SEEDS) * len(BUDGETS) * 5)
        self.assertEqual(len({run_name(j) for j in jobs}), len(jobs))
        allocation = read(OUT / 'label_allocation.json')
        folds = read(V4 / 'folds.json')
        for a in allocation:
            self.assertTrue(set(a['labeled_ids']) <= set(folds[a['fold']]['train_ids']))

    def test_completed_analysis_is_internally_consistent(self):
        path = OUT / 'analysis.json'
        if not path.exists():
            self.skipTest('v6 analysis not complete')
        a = read(path)
        self.assertEqual(a['status'], 'complete_verified')
        for s in a['summary']:
            self.assertAlmostEqual(s['macro_f1_mean'], float(np.mean([r['macro_f1'] for r in s['seed_results']])), places=12)
        budgets = sorted({r['budget'] for r in a['combined_curve']})
        self.assertEqual(budgets, [.05, .1, .2, .5, 1.])


if __name__ == '__main__':
    unittest.main()
