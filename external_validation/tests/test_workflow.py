"""Synthetic fixtures only: these tests are not real external validation data."""
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import workflow as w


class ExternalWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='orman-external-fixtures-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.reference = self.put('reference.json', [dict(id='used-0', sample_id=0,
            lon=0., lat=0., dataset=1, source_cluster='7.0', label=1)])
        self.model_dir = self.root/'model'; self.model_dir.mkdir()
        payload = b'synthetic test artifact; not a trained model'
        (self.model_dir/'fixture.pt').write_bytes(payload)
        self.bundle = self.put('model/bundle.json', dict(version='advanced_v3', threshold=.5,
            members=[dict(path='fixture.pt', sha256=hashlib.sha256(payload).hexdigest())]))
        self.rows = [self.candidate(i) for i in range(4)]
        self.candidates = self.put('candidates.json', self.rows)
        self.protocol = w.read_json(w.HERE/'templates/protocol.json')
        for key in ['study_id', 'coordinator', 'research_question', 'region_and_period',
                    'sampling_plan', 'evidence_source', 'support_rationale', 'exclusion_rules',
                    'unknown_event_policy', 'prior_use_review', 'human_review_plan']:
            self.protocol[key] = 'Synthetic fixture only: ' + key
        self.protocol.update(reviewers=['reader-a', 'reader-b'], adjudicator='reader-c',
            minimum_class_samples={'0':2,'1':2}, minimum_class_groups={'0':2,'1':2},
            model_scores_not_inspected=True, review_evidence_has_no_model_scores=True)
        self.protocol_path = self.put('protocol.json', self.protocol)
        self.run = self.root/'frozen'

    def put(self, name, value):
        path=self.root/name; path.parent.mkdir(exist_ok=True, parents=True)
        path.write_bytes(w.json_bytes(value)); return path

    def candidate(self, i, **changes):
        row=dict(id=f'candidate-{i}', source_namespace='SYNTHETIC-TEST-FIXTURE',
                 sample_id=str(i), target_year=2020, lon=10.+i, lat=0.,
                 event_namespace='fixture-events', event_id=str(i), partition='test',
                 evidence_ref='Synthetic fixture; no real observations')
        row.update(changes); return row

    def audit(self, rows=None):
        return w.audit(rows or self.rows, w.reference_rows(w.read_json(self.reference)))

    def freeze(self):
        self.put('candidates.json',self.rows); self.put('protocol.json',self.protocol)
        return w.freeze(self.protocol_path,self.candidates,self.reference,self.bundle,self.run)

    def submission(self, packet, name, changes=None):
        with Path(packet).open(newline='') as stream: rows=list(csv.DictReader(stream))
        mapping=w.read_json(self.run/'private_review_mapping.json')
        classes={mapping[f'candidate-{i}']:'0' if i<2 else '1' for i in range(4)}
        for row in rows:
            row.update(label=classes[row['review_id']], confidence='high', rationale='Fixture rationale',
                       reviewed_at=(datetime.now(timezone.utc)+timedelta(seconds=1)).isoformat())
            if changes: changes(row)
        path=self.root/name; path.write_bytes(w.csv_bytes(rows)); return path

    def reviews(self, change_b=None):
        a=self.submission(self.run/'packets/reviewer_a.csv','a.csv')
        b=self.submission(self.run/'packets/reviewer_b.csv','b.csv',change_b)
        return a,b

    def test_prior_id_excluded_even_far_away(self):
        self.rows[0]['id']='used-0'
        self.assertIn('previously_used_id',self.audit()['records'][0]['rejection_reasons'])

    def test_prior_disfor_point_alias_excluded(self):
        self.rows[0].update(source_namespace='disfor',sample_id='0.0')
        self.assertIn('previously_used_source_point',self.audit()['records'][0]['rejection_reasons'])

    def test_five_km_buffer_excludes_close_point(self):
        self.rows[0]['lon']=.02
        self.assertIn('within_prior_use_buffer',self.audit()['records'][0]['rejection_reasons'])
        self.assertLess(self.audit()['records'][0]['nearest_prior_km'],5)

    def test_shared_source_event_excluded_when_geographically_far(self):
        self.rows[0].update(event_namespace='DISFOR:dataset:1',event_id='7')
        self.assertIn('shared_prior_event',self.audit()['records'][0]['rejection_reasons'])

    def test_campaign_two_stratum_not_treated_as_event(self):
        r=w.read_json(self.reference);r[0]['dataset']=2;self.put('reference.json',r)
        self.rows[0].update(event_namespace='DISFOR:dataset:2',event_id='7')
        self.assertEqual(self.audit()['status'],'separation_checks_passed')

    def test_transitive_spatial_component_cannot_cross_partitions(self):
        rows=[self.candidate(0,lon=10.,partition='development'),self.candidate(1,lon=10.03),
              self.candidate(2,lon=10.06)]
        self.assertGreater(w.distance(rows[0],rows[2]),5)
        result=self.audit(rows)
        self.assertEqual(result['groups'],1)
        self.assertEqual(result['status'],'blocked')
        self.assertEqual(len(result['components_crossing_partitions']),1)

    def test_shared_new_event_cannot_cross_partitions(self):
        self.rows[0]['partition']='development';self.rows[1]['event_id']=self.rows[0]['event_id']
        self.assertEqual(self.audit()['status'],'blocked')

    def test_score_or_reference_label_columns_rejected(self):
        for key in ['label','probability','model_score']:
            row=self.candidate(0);row[key]=1
            with self.assertRaisesRegex(ValueError,'forbidden'):self.audit([row])

    def test_invalid_coordinates_duplicates_and_small_buffer_rejected(self):
        with self.assertRaises(ValueError):self.audit([self.candidate(0,lat=float('nan'))])
        with self.assertRaises(ValueError):self.audit([self.candidate(0),self.candidate(0)])
        with self.assertRaises(ValueError):w.audit(self.rows,w.reference_rows(w.read_json(self.reference)),4.9)

    def test_blank_protocol_cannot_freeze(self):
        self.protocol=w.read_json(w.HERE/'templates/protocol.json')
        with self.assertRaises(ValueError):self.freeze()
        self.assertFalse(self.run.exists())

    def test_attestations_and_distinct_reviewers_required(self):
        self.protocol['model_scores_not_inspected']=False
        with self.assertRaisesRegex(ValueError,'attest'):self.freeze()
        self.protocol['model_scores_not_inspected']=True
        self.protocol['adjudicator']='READER-A'
        with self.assertRaisesRegex(ValueError,'distinct'):self.freeze()

    def test_model_integrity_is_bound_before_freeze(self):
        (self.model_dir/'fixture.pt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.freeze()

    def test_same_source_cannot_claim_external_validation(self):
        self.rows[0]['source_namespace']='DISFOR';self.rows[0]['sample_id']='999999'
        with self.assertRaisesRegex(ValueError,'same-source'):self.freeze()

    def test_packets_hide_source_ids_events_scores_and_labels(self):
        self.freeze()
        for name in ['reviewer_a.csv','reviewer_b.csv']:
            with (self.run/'packets'/name).open(newline='') as stream:
                reader=csv.DictReader(stream);rows=list(reader)
                self.assertEqual(reader.fieldnames,w.REVIEW_FIELDS)
            self.assertEqual(len(rows),4)
            self.assertTrue(all(r['label']=='' and r['confidence']=='' for r in rows))
            self.assertNotIn('candidate-',(self.run/'packets'/name).read_text())
            self.assertNotIn('event_namespace',reader.fieldnames)
            self.assertNotIn('probability',reader.fieldnames)

    def test_freeze_cannot_overwrite_and_detects_modified_protocol(self):
        self.freeze()
        with self.assertRaises(FileExistsError):self.freeze()
        changed=w.read_json(self.run/'protocol.json');changed['threshold']=.8
        (self.run/'protocol.json').write_bytes(w.json_bytes(changed))
        with self.assertRaisesRegex(ValueError,'modified'):w.load_run(self.run)

    def test_agreeing_reviews_yield_label_support_without_scores(self):
        self.freeze();a,b=self.reviews()
        report=w.finalize(self.run,a,b,None,self.root/'final')
        self.assertEqual(report['status'],'annotation_support_ready')
        self.assertEqual(report['class_counts'],{'0':2,'1':2})
        self.assertEqual(report['class_group_counts'],{'0':2,'1':2})
        self.assertFalse(report['metric_scores_computed'])
        self.assertNotIn('macro_f1',report)

    def test_conflict_requires_third_reader_and_can_be_resolved(self):
        self.freeze();mapping=w.read_json(self.run/'private_review_mapping.json');ident=mapping['candidate-0']
        a,b=self.reviews(lambda row:row.update(label='1') if row['review_id']==ident else None)
        result=w.reconcile(self.run,a,b,self.root/'reconciliation')
        self.assertEqual(result['conflicts'],1)
        with self.assertRaisesRegex(ValueError,'adjudication'):w.finalize(self.run,a,b,None,self.root/'bad')
        resolution=self.submission(self.root/'reconciliation/adjudication_template.csv','resolution.csv')
        report=w.finalize(self.run,a,b,resolution,self.root/'final')
        self.assertEqual(report['adjudicated'],1)
        self.assertEqual(report['status'],'annotation_support_ready')

    def test_uncertain_or_low_confidence_never_silently_becomes_negative(self):
        self.freeze();a,b=self.reviews(lambda row:row.update(label='uncertain',confidence='low'))
        result=w.reconcile(self.run,a,b,self.root/'reconciliation')
        self.assertEqual(result['conflicts'],4)
        with self.assertRaisesRegex(ValueError,'adjudication'):w.finalize(self.run,a,b,None,self.root/'final')

    def test_explicit_exclusion_can_fail_support_gate(self):
        self.freeze();mapping=w.read_json(self.run/'private_review_mapping.json');ident=mapping['candidate-2']
        edit=lambda row:row.update(label='exclude') if row['review_id']==ident else None
        a=self.submission(self.run/'packets/reviewer_a.csv','a.csv',edit)
        b=self.submission(self.run/'packets/reviewer_b.csv','b.csv',edit)
        report=w.finalize(self.run,a,b,None,self.root/'final')
        self.assertEqual(report['status'],'insufficient_support')
        self.assertEqual(report['excluded_test_samples'],1)
        self.assertIn('class_1_sample_support',report['support_failures'])

    def test_many_points_do_not_replace_independent_positive_groups(self):
        self.rows[3]['lon']=self.rows[2]['lon']+.02
        self.freeze();a,b=self.reviews();report=w.finalize(self.run,a,b,None,self.root/'final')
        self.assertEqual(report['class_counts']['1'],2)
        self.assertEqual(report['class_group_counts']['1'],1)
        self.assertIn('class_1_group_support',report['support_failures'])

    def test_positive_without_event_identity_cannot_claim_ready(self):
        self.rows[2].update(event_id='',event_namespace='')
        self.freeze();a,b=self.reviews();report=w.finalize(self.run,a,b,None,self.root/'final')
        self.assertEqual(report['status'],'insufficient_support')
        self.assertIn('positive_event_identity_unresolved',report['support_failures'])
        self.assertEqual(report['positive_candidates_without_event_ids'],['candidate-2'])

    def test_wrong_reviewer_or_changed_evidence_is_rejected(self):
        self.freeze()
        for key,value in [('reviewer_id','someone-else'),('lon','33'),('evidence_ref','changed'),('reviewed_at','2000-01-01T00:00:00+00:00')]:
            a,b=self.reviews(lambda row:row.update({key:value}))
            with self.assertRaises(ValueError):w.reconciliation(self.run,a,b)

    def test_extra_review_score_columns_rejected(self):
        self.freeze();a,b=self.reviews()
        b.write_text(b.read_text().replace('reviewed_at\n','reviewed_at,score\n'))
        with self.assertRaisesRegex(ValueError,'columns changed'):w.reconciliation(self.run,a,b)

    def test_init_cli_makes_empty_templates_not_fake_data(self):
        result=subprocess.run([sys.executable,str(w.HERE/'workflow.py'),'init','--out',str(self.root/'draft')],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(w.read_json(self.root/'draft/candidates.json'),[])
        self.assertFalse(w.read_json(self.root/'draft/protocol.json')['model_scores_not_inspected'])
        self.assertEqual(json.loads(result.stdout)['candidates'],0)


if __name__=='__main__':unittest.main()
