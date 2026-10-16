"""Local preregistration and blinded annotation workflow; never runs a model.

This tool checks local file integrity and declared separation rules. It cannot
certify that people have never seen outcomes or establish external data validity.
"""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
CANDIDATE_FIELDS = {'id', 'source_namespace', 'sample_id', 'target_year', 'lon', 'lat',
                    'event_namespace', 'event_id', 'partition', 'evidence_ref'}
REVIEW_FIELDS = ['review_id', 'target_year', 'lon', 'lat', 'evidence_ref',
                 'reviewer_id', 'label', 'confidence', 'rationale', 'reviewed_at']
LABELS = {'0', '1', 'uncertain', 'exclude'}
CONFIDENCE = {'high', 'medium', 'low'}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + ' must be a nonempty string')
    return value.strip()


def identifier(value):
    value = str(value).strip()
    try:
        number = Decimal(value)
        if number.is_finite() and number == number.to_integral_value():
            return str(int(number))
    except InvalidOperation:
        pass
    return value


def candidates_checked(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('Candidates must be a nonempty list of real candidate records')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != CANDIDATE_FIELDS:
            raise ValueError('Candidate columns must match the template exactly; labels/scores are forbidden')
        for key in ['id', 'source_namespace', 'sample_id', 'partition', 'evidence_ref']:
            text(row[key], key)
        if row['id'] in seen:
            raise ValueError('Duplicate candidate id: ' + row['id'])
        seen.add(row['id'])
        if row['partition'] not in {'development', 'test'}:
            raise ValueError('partition must be development or test')
        if type(row['target_year']) is not int or not 1901 <= row['target_year'] <= 9998:
            raise ValueError('target_year must be an integer calendar year')
        for key, limit in [('lon', 180), ('lat', 90)]:
            if type(row[key]) not in [int, float] or not math.isfinite(row[key]) or abs(row[key]) > limit:
                raise ValueError('Invalid finite WGS84 coordinate: ' + key)
        if not isinstance(row['event_id'], str) or not isinstance(row['event_namespace'], str):
            raise ValueError('Event fields must be strings; use two empty strings when unknown')
        if bool(row['event_id'].strip()) != bool(row['event_namespace'].strip()):
            raise ValueError('event_namespace and event_id must be supplied together')
        for key in ['id', 'source_namespace', 'sample_id', 'event_namespace', 'event_id', 'evidence_ref']:
            if row[key] != row[key].strip():
                raise ValueError('Leading/trailing whitespace is not allowed: ' + key)
    if not any(row['partition'] == 'test' for row in rows):
        raise ValueError('At least one test candidate is required')
    return rows


def point_key(row):
    namespace = row['source_namespace'].casefold()
    sample = identifier(row['sample_id']) if namespace == 'disfor' else row['sample_id']
    return namespace, sample


def event_key(row):
    return ((row['event_namespace'].casefold(), identifier(row['event_id']))
            if row['event_id'] else None)


def distance(a, b):
    la, lb = math.radians(a['lat']), math.radians(b['lat'])
    dlat = lb - la
    dlon = math.radians(b['lon'] - a['lon'])
    q = math.sin(dlat / 2) ** 2 + math.cos(la) * math.cos(lb) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(min(1, max(0, q))))


def reference_rows(manifest):
    if not isinstance(manifest, list) or not manifest:
        raise ValueError('Prior-use manifest must be a nonempty list')
    rows = []
    for row in manifest:
        for field in ['id', 'sample_id', 'lon', 'lat', 'dataset', 'source_cluster']:
            if field not in row:
                raise ValueError('Incomplete prior-use manifest: ' + field)
        for field, limit in [('lon', 180), ('lat', 90)]:
            if type(row[field]) not in [int, float] or not math.isfinite(row[field]) or abs(row[field]) > limit:
                raise ValueError('Invalid prior-use coordinate')
        has_event = row['dataset'] in [1, 3] and row['source_cluster'] is not None
        rows.append(dict(id=str(row['id']), sample_id=str(row['sample_id']),
                         source_namespace='DISFOR', lon=row['lon'], lat=row['lat'],
                         event_namespace=f"DISFOR:dataset:{row['dataset']}" if has_event else '',
                         event_id=str(row['source_cluster']) if has_event else ''))
    return rows


def audit(rows, prior, minimum_km=5.0):
    candidates_checked(rows)
    if type(minimum_km) not in [int, float] or not math.isfinite(minimum_km) or minimum_km < 5:
        raise ValueError('minimum_distance_km must be at least 5')
    if not prior:
        raise ValueError('Prior-use reference cannot be empty')
    prior_ids = {r['id'] for r in prior}
    prior_points = {point_key(r) for r in prior}
    prior_events = {event_key(r) for r in prior if event_key(r)}
    records, parent = [], list(range(len(rows)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, row in enumerate(rows):
        nearest = min(distance(row, old) for old in prior)
        reasons = []
        if row['id'] in prior_ids: reasons.append('previously_used_id')
        if point_key(row) in prior_points: reasons.append('previously_used_source_point')
        if nearest <= minimum_km: reasons.append('within_prior_use_buffer')
        if event_key(row) and event_key(row) in prior_events: reasons.append('shared_prior_event')
        records.append(dict(id=row['id'], nearest_prior_km=nearest, rejection_reasons=reasons))
        for j in range(i):
            other = rows[j]
            if (point_key(row) == point_key(other)
                or (event_key(row) and event_key(row) == event_key(other))
                or distance(row, other) <= minimum_km):
                parent[find(i)] = find(j)
    components = {}
    for i, row in enumerate(rows): components.setdefault(find(i), []).append(row['id'])
    group_by_id = {}
    mixed = []
    lookup = {r['id']: r for r in rows}
    for members in sorted(components.values(), key=lambda value: min(value)):
        group = 'group-' + digest(json_bytes(sorted(members)))[:16]
        for ident in members: group_by_id[ident] = group
        if len({lookup[ident]['partition'] for ident in members}) > 1:
            mixed.append(dict(group_id=group, candidate_ids=members))
    blocked = any(r['rejection_reasons'] for r in records) or bool(mixed)
    return dict(status='blocked' if blocked else 'separation_checks_passed',
                candidates=len(rows), prior_locations=len(prior), minimum_distance_km=minimum_km,
                records=records, group_by_id=group_by_id, groups=len(components),
                components_crossing_partitions=mixed,
                missing_event_ids=sum(not row['event_id'] for row in rows),
                same_source_candidates=sum(row['source_namespace'].casefold() == 'disfor' for row in rows),
                limitation='Technical separation only. Unknown/renamed events, source aliases and unrecorded prior use require human review; this is not proof of external validity.')


def validate_protocol(protocol, rows, bundle):
    template = read_json(HERE / 'templates/protocol.json')
    if not isinstance(protocol, dict) or set(protocol) != set(template):
        raise ValueError('Protocol fields must match templates/protocol.json')
    for key in ['study_id', 'coordinator', 'research_question', 'region_and_period',
                'sampling_plan', 'evidence_source', 'support_rationale', 'exclusion_rules',
                'unknown_event_policy', 'prior_use_review', 'human_review_plan']:
        text(protocol[key], key)
    if protocol['claim'] not in {'external_validation_candidate', 'same_source_probe'}:
        raise ValueError('Unknown evaluation claim')
    if protocol['claim'] == 'external_validation_candidate' and any(r['source_namespace'].casefold() == 'disfor' for r in rows):
        raise ValueError('DISFOR candidates are a same-source probe, not external validation')
    if protocol['primary_metric'] != 'macro_f1' or protocol['label_confidence_required'] != 'high':
        raise ValueError('This workflow fixes macro_f1 and high-confidence accepted labels')
    for key in ['model_scores_not_inspected', 'review_evidence_has_no_model_scores']:
        if protocol[key] is not True:
            raise ValueError('Coordinator must explicitly attest: ' + key)
    reviewers = protocol['reviewers']
    if not isinstance(reviewers, list) or len(reviewers) != 2:
        raise ValueError('Exactly two independent reviewers are required')
    identities = [text(v, 'reviewer') for v in reviewers] + [text(protocol['adjudicator'], 'adjudicator')]
    if len(set(v.casefold() for v in identities)) != 3:
        raise ValueError('Two reviewers and adjudicator must have distinct identities')
    definitions = protocol['label_definitions']
    if not isinstance(definitions, dict) or set(definitions) != LABELS:
        raise ValueError('Provide definitions for 0, 1, uncertain and exclude')
    for key, definition in definitions.items(): text(definition, 'label definition ' + key)
    for key in ['minimum_class_samples', 'minimum_class_groups']:
        limits = protocol[key]
        if not isinstance(limits, dict) or set(limits) != {'0', '1'}:
            raise ValueError('Both class support limits must be declared: ' + key)
        if any(type(v) is not int or v < 2 for v in limits.values()):
            raise ValueError('Support limits must be integers >= 2 with a human precision rationale')
    if (protocol['model_version'] != bundle.get('version')
        or type(protocol['threshold']) not in [float, int]
        or protocol['threshold'] != bundle.get('threshold')):
        raise ValueError('Model version/threshold must match the current frozen bundle')


def csv_bytes(rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=REVIEW_FIELDS, lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return output.getvalue().encode('utf-8')


def review_rows(rows, mapping, reviewer):
    return [dict(review_id=mapping[r['id']], target_year=str(r['target_year']),
                 lon=str(r['lon']), lat=str(r['lat']), evidence_ref=r['evidence_ref'],
                 reviewer_id=reviewer, label='', confidence='', rationale='', reviewed_at='')
            for r in sorted(rows, key=lambda r: mapping[r['id']])]


def write_directory(out, payloads):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    for name, payload in payloads.items():
        path = out / name; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream: stream.write(payload)


def freeze(protocol_path, candidate_path, reference_path, bundle_path, out):
    rows = candidates_checked(read_json(candidate_path))
    protocol, bundle = read_json(protocol_path), read_json(bundle_path)
    validate_protocol(protocol, rows, bundle)
    prior = reference_rows(read_json(reference_path))
    audit_result = audit(rows, prior, protocol['minimum_distance_km'])
    if audit_result['status'] != 'separation_checks_passed':
        raise ValueError('Separation audit blocked freezing; run audit to inspect exclusions and mixed groups')
    bundle_path = Path(bundle_path)
    member_hashes = {}
    if not bundle.get('members'): raise ValueError('Model bundle has no members')
    for member in bundle['members']:
        path = (bundle_path.parent / member['path']).resolve()
        if not path.is_relative_to(bundle_path.parent.resolve()):
            raise ValueError('Model member outside bundle directory')
        actual = digest(path.read_bytes())
        if actual != member['sha256']: raise ValueError('Model member hash mismatch')
        member_hashes[member['path']] = actual
    mapping = {r['id']: 'review-' + uuid.uuid4().hex[:20] for r in rows}
    payloads = {
        'protocol.json': json_bytes(protocol), 'candidates.json': json_bytes(rows),
        'prior_locations.json': json_bytes(prior), 'separation_audit.json': json_bytes(audit_result),
        'private_review_mapping.json': json_bytes(mapping),
        'model_fingerprint.json': json_bytes(dict(bundle_sha256=digest(bundle_path.read_bytes()), members=member_hashes,
            prior_manifest_sha256=digest(Path(reference_path).read_bytes()), threshold=bundle['threshold'])),
        'packets/reviewer_a.csv': csv_bytes(review_rows(rows, mapping, protocol['reviewers'][0])),
        'packets/reviewer_b.csv': csv_bytes(review_rows(rows, mapping, protocol['reviewers'][1])),
        'packets/OKU_BENI.md': (HERE / 'templates/REVIEWER_README_TR.md').read_bytes(),
    }
    lock = dict(status='locally_frozen_before_annotation', created_at=datetime.now(timezone.utc).isoformat(),
                study_id=protocol['study_id'], files={name: digest(payload) for name, payload in payloads.items()},
                limits='Local checksum record, not an externally timestamped registration. Attestations require human accountability; no model was run.')
    payloads['freeze.json'] = json_bytes(lock)
    write_directory(out, payloads)
    return dict(status=lock['status'], candidates=len(rows), groups=audit_result['groups'], out=str(out))


def load_run(run):
    run = Path(run); lock = read_json(run / 'freeze.json')
    required = {'protocol.json', 'candidates.json', 'prior_locations.json', 'separation_audit.json',
                'private_review_mapping.json', 'model_fingerprint.json', 'packets/reviewer_a.csv', 'packets/reviewer_b.csv',
                'packets/OKU_BENI.md'}
    if set(lock.get('files', {})) != required:
        raise ValueError('Frozen file manifest schema differs')
    for name, expected in lock['files'].items():
        if digest((run / name).read_bytes()) != expected:
            raise ValueError('Frozen artifact modified: ' + name)
    return {name[:-5]: read_json(run / name) for name in required if name.endswith('.json')} | {'freeze': lock}


def read_review(path, expected_rows, reviewer, frozen_at):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != REVIEW_FIELDS:
            raise ValueError('Review columns changed; added labels/scores or deleted fields are forbidden')
        rows = list(reader)
    expected = {row['review_id']: row for row in expected_rows}
    found = {}
    for row in rows:
        ident = row['review_id']
        if None in row or any(value is None for value in row.values()):
            raise ValueError('Malformed CSV row')
        if ident not in expected or ident in found:
            raise ValueError('Unknown or duplicate review id')
        for key in ['target_year', 'lon', 'lat', 'evidence_ref']:
            if row[key] != expected[ident][key]: raise ValueError('Review evidence or coordinates changed: ' + ident)
        if row['reviewer_id'] != reviewer: raise ValueError('Reviewer identity mismatch')
        if row['label'] not in LABELS or row['confidence'] not in CONFIDENCE:
            raise ValueError('Complete label and confidence are required')
        text(row['rationale'], 'rationale')
        try:
            timestamp = datetime.fromisoformat(row['reviewed_at'].replace('Z', '+00:00'))
            if timestamp.tzinfo is None or timestamp < datetime.fromisoformat(frozen_at): raise ValueError()
        except (ValueError, TypeError):
            raise ValueError('reviewed_at needs an ISO timestamp with timezone after the local freeze')
        found[ident] = row
    if set(found) != set(expected): raise ValueError('Review coverage does not match frozen candidates')
    return found


def reconciliation(run, first, second):
    data = load_run(run); rows = data['candidates']; protocol = data['protocol']; mapping = data['private_review_mapping']
    common = review_rows(rows, mapping, '')
    a = read_review(first, common, protocol['reviewers'][0], data['freeze']['created_at'])
    b = read_review(second, common, protocol['reviewers'][1], data['freeze']['created_at'])
    accepted, conflicts = {}, []
    for ident in a:
        left, right = a[ident], b[ident]
        agreed = left['label'] == right['label'] and left['label'] != 'uncertain'
        high = left['confidence'] == right['confidence'] == 'high'
        if agreed and high:
            accepted[ident] = dict(label=left['label'], decision='two_reviewers_agree')
        else:
            conflicts.append(dict(review_id=ident, reviewer_a=left, reviewer_b=right))
    return data, common, accepted, conflicts


def reconcile(run, first, second, out):
    data, common, accepted, conflicts = reconciliation(run, first, second)
    wanted = {r['review_id'] for r in conflicts}
    template = [dict(row, reviewer_id=data['protocol']['adjudicator']) for row in common if row['review_id'] in wanted]
    result = dict(status='needs_adjudication' if conflicts else 'review_complete',
                  agreed=len(accepted), conflicts=len(conflicts),
                  review_a_sha256=digest(Path(first).read_bytes()), review_b_sha256=digest(Path(second).read_bytes()),
                  note='Adjudication remains blind to model scores. Do not edit original reviewer submissions.')
    write_directory(out, {'reconciliation.json': json_bytes(result),
                          'disagreements.json': json_bytes(conflicts),
                          'adjudication_template.csv': csv_bytes(template)})
    return result


def finalize(run, first, second, adjudication, out):
    data, common, accepted, conflicts = reconciliation(run, first, second)
    if conflicts:
        if adjudication is None: raise ValueError('Unresolved reviews require adjudication')
        wanted = {r['review_id'] for r in conflicts}
        resolutions = read_review(adjudication, [r for r in common if r['review_id'] in wanted],
                                  data['protocol']['adjudicator'], data['freeze']['created_at'])
        for ident, row in resolutions.items():
            if row['label'] == 'uncertain' or row['confidence'] != 'high':
                raise ValueError('Adjudication must resolve to a high-confidence class or explicit exclusion')
            accepted[ident] = dict(label=row['label'], decision='adjudicated')
    elif adjudication is not None:
        raise ValueError('No conflicts exist; do not add outcome-driven adjudication')
    mapping, grouping = data['private_review_mapping'], data['separation_audit']['group_by_id']
    labels = []
    for row in data['candidates']:
        decision = accepted[mapping[row['id']]]
        labels.append(dict(id=row['id'], review_id=mapping[row['id']], partition=row['partition'],
                           group_id=grouping[row['id']], label=decision['label'], decision=decision['decision']))
    test = [row for row in labels if row['partition'] == 'test' and row['label'] in {'0', '1'}]
    counts = {label: sum(row['label'] == label for row in test) for label in ['0', '1']}
    groups = {label: len({row['group_id'] for row in test if row['label'] == label}) for label in ['0', '1']}
    failures = []
    for label in ['0', '1']:
        if counts[label] < data['protocol']['minimum_class_samples'][label]: failures.append('class_' + label + '_sample_support')
        if groups[label] < data['protocol']['minimum_class_groups'][label]: failures.append('class_' + label + '_group_support')
    candidates_by_id = {row['id']: row for row in data['candidates']}
    missing_positive_events = [row['id'] for row in test
                               if row['label'] == '1' and not candidates_by_id[row['id']]['event_id']]
    if missing_positive_events: failures.append('positive_event_identity_unresolved')
    result = dict(status='insufficient_support' if failures else 'annotation_support_ready',
                  metric_scores_computed=False, input_arrays_validated=False,
                  class_counts=counts, class_group_counts=groups,
                  positive_candidates_without_event_ids=missing_positive_events,
                  excluded_test_samples=sum(r['partition'] == 'test' and r['label'] == 'exclude' for r in labels),
                  adjudicated=len(conflicts), support_failures=failures,
                  protocol_sha256=data['freeze']['files']['protocol.json'],
                  freeze_sha256=digest((Path(run) / 'freeze.json').read_bytes()),
                  model_bundle_sha256=data['model_fingerprint']['bundle_sha256'],
                  review_a_sha256=digest(Path(first).read_bytes()), review_b_sha256=digest(Path(second).read_bytes()),
                  adjudication_sha256=digest(Path(adjudication).read_bytes()) if adjudication else None,
                  claim=data['protocol']['claim'],
                  limitation='Meeting declared support thresholds is not a power calculation or proof of independent external validity. No predictions or performance metrics were computed.')
    write_directory(out, {'labels.json': json_bytes(labels), 'readiness.json': json_bytes(result)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--out', type=Path, required=True)
    inspect = sub.add_parser('audit'); inspect.add_argument('--candidates', type=Path, required=True)
    inspect.add_argument('--reference', type=Path, default=ROOT/'data/disfor/sample_manifest.json')
    inspect.add_argument('--minimum-distance-km', type=float, default=5.)
    lock = sub.add_parser('freeze')
    for name in ['protocol', 'candidates', 'out']: lock.add_argument('--' + name, type=Path, required=True)
    lock.add_argument('--reference', type=Path, default=ROOT/'data/disfor/sample_manifest.json')
    lock.add_argument('--bundle', type=Path, default=ROOT/'models/advanced_v3/bundle.json')
    for command in ['reconcile', 'finalize']:
        cmd = sub.add_parser(command)
        for name in ['run', 'a', 'b', 'out']: cmd.add_argument('--' + name, type=Path, required=True)
        if command == 'finalize': cmd.add_argument('--adjudication', type=Path)
    verify = sub.add_parser('verify-freeze'); verify.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            write_directory(args.out, {p.name: p.read_bytes() for p in (HERE/'templates').glob('*.json')})
            result = dict(status='blank_templates_created', out=str(args.out), candidates=0, note='No real external data supplied or evaluated')
        elif args.command == 'audit': result = audit(read_json(args.candidates), reference_rows(read_json(args.reference)), args.minimum_distance_km)
        elif args.command == 'freeze': result = freeze(args.protocol, args.candidates, args.reference, args.bundle, args.out)
        elif args.command == 'verify-freeze':
            load_run(args.run); result = dict(status='frozen_checksums_match', note='Local integrity check only')
        elif args.command == 'reconcile': result = reconcile(args.run, args.a, args.b, args.out)
        else: result = finalize(args.run, args.a, args.b, args.adjudication, args.out)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        if result['status'] in {'blocked', 'insufficient_support'}: return 2
    except (ValueError, KeyError, OSError, TypeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
