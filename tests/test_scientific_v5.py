import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from scientific_v5 import component_groups, context, has_country_metadata, locked_write, scores


def location(lon, dataset=2, event=None):
    return dict(lon=lon, lat=0.0, dataset=dataset, source_cluster=event)


class SpatialSensitivityContracts(unittest.TestCase):
    def test_distance_components_are_transitive(self):
        # ~4.45 km consecutive spacing; endpoints ~8.9 km apart.
        groups = component_groups([location(0), location(.04), location(.08), location(1)], 5)
        self.assertEqual(len(set(groups[:3])), 1)
        self.assertNotEqual(groups[0], groups[3])

    def test_shared_events_join_far_points_but_sampling_strata_do_not(self):
        points = [location(0, 1, 'event'), location(1, 1, 'event'),
                  location(2, 2, 'stratum'), location(3, 2, 'stratum')]
        groups = component_groups(points, 5)
        self.assertEqual(groups[0], groups[1])
        self.assertNotEqual(groups[2], groups[3])

    def test_campaign_is_part_of_event_identity(self):
        groups = component_groups([location(0, 1, 'same-id'), location(1, 3, 'same-id')], 5)
        self.assertNotEqual(groups[0], groups[1])

    def test_five_km_reproduces_existing_cohort_groups(self):
        data, metadata = context()
        np.testing.assert_array_equal(component_groups(metadata, 5), data['groups'])

    def test_country_is_not_inferred_from_source_or_tile(self):
        self.assertEqual(has_country_metadata(['source', 'source_description', 's2_tile', 'geometry']), [])
        self.assertEqual(has_country_metadata(['source', 'country_code']), ['country_code'])

    def test_locked_declaration_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'protocol.json'
            locked_write(path, {'radius': 5})
            locked_write(path, {'radius': 5})
            with self.assertRaisesRegex(ValueError, 'Frozen v5'):
                locked_write(path, {'radius': 10})
            self.assertEqual(json.loads(path.read_text()), {'radius': 5})

    def test_single_class_and_invalid_probability_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Two classes'):
            scores([0, 0], [.1, .2])
        with self.assertRaisesRegex(ValueError, 'Invalid probabilities'):
            scores([0, 1], [.1, float('nan')])

    def test_confusion_matrix_counts_missed_positives(self):
        result = scores([0, 0, 1, 1], [.1, .2, .3, .5])
        self.assertEqual(result['confusion_matrix'], [[2, 0], [1, 1]])
        self.assertEqual(result['clear_cut_recall'], .5)
        self.assertAlmostEqual(result['macro_f1'], .5 * (4 / 5 + 2 / 3))


if __name__ == '__main__':
    unittest.main()
