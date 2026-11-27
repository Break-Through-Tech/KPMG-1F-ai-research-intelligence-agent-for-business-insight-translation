"""Collect and adjudicate two blinded AI assessments, then compute frozen gates."""

import argparse
import csv
import io
import json
from pathlib import Path
from statistics import mean
import zipfile

from runner import DESTINATION, ROOT, read, sha, write

DIMS = ('fidelity', 'business_relevance', 'action_specificity', 'proportionality', 'limitations')
DEFECTS = ('generic_advice', 'workflow_parroting', 'semantic_repetition', 'pilot_overreliance')
OBSERVATIONS = ('application_condition', 'decision_action', 'research_scope', 'evidence_gap')
FIELDS = (*DIMS, *DEFECTS, 'critical_unsupported_claim', 'appropriate_abstention', *OBSERVATIONS)
MISSING = {'skipped_no_accepted_evidence', 'execution_failed', 'not_run_after_provider_failure'}
ABSTAINS = {'insufficient_evidence', 'skipped_no_accepted_evidence'}
ADJUDICATION = ('blind_case', 'output_label', 'field', 'first', 'second', 'final', 'evidence_citation', 'rationale')


def load_blind(directory):
    rows = {}
    with zipfile.ZipFile(directory / 'anonymous-review.zip') as archive:
        for name in archive.namelist():
            if name.endswith(('-A.json', '-B.json', '-C.json')):
                row = json.loads(archive.read(name))
                rows[(row['blind_case'], row['output_label'])] = row['status']
    assert len(rows) == 41
    return rows


def read_csv(path):
    return list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))))


def parse(field, value, status):
    if field in DIMS:
        if status in MISSING:
            assert value == 'NA', field
            return None
        value = int(value)
        assert 1 <= value <= 5, field
    elif field in DEFECTS:
        value = int(value)
        assert 0 <= value <= 2, field
        assert status not in MISSING or value == 0, field
    elif field == 'critical_unsupported_claim':
        assert value in {'yes', 'no'}
        assert status not in MISSING or value == 'no'
    elif field == 'appropriate_abstention':
        assert value in ({'yes', 'no'} if status in ABSTAINS else {'not_applicable'})
    else:
        assert field in OBSERVATIONS
        assert value in {'yes', 'no', 'not_applicable'}
        assert status not in MISSING or value == 'not_applicable'
    return value


def assessment(path, outcomes):
    rows = {}
    identities = set()
    for source in read_csv(path):
        item = (source['blind_case'], source['output_label'])
        assert item not in rows and item in outcomes
        identities.add(source['reviewer_id'].strip())
        row = {field: parse(field, source[field].strip(), outcomes[item]) for field in FIELDS}
        if (row['critical_unsupported_claim'] == 'yes' or row['appropriate_abstention'] == 'no'
                or any(row[field] == 2 for field in DEFECTS)):
            assert source['evidence_citation'].strip() and source['notes'].strip(), item
        rows[item] = row
    assert set(rows) == set(outcomes)
    assert len(identities) == 1 and next(iter(identities)).startswith('AI_')
    return next(iter(identities)), rows


def disputes(first, second):
    for item, row in first.items():
        for field, a in row.items():
            b = second[item][field]
            different = a is not None and abs(a - b) > 1 if field in DIMS else a != b
            if different:
                yield (*item, field, a, b)


def collect(directory, first_path, second_path):
    outcomes = load_blind(directory)
    first_id, first = assessment(first_path, outcomes)
    second_id, second = assessment(second_path, outcomes)
    assert first_id != second_id
    review = directory / 'ai-review'
    review.mkdir(exist_ok=False)
    for name, path in [('first.csv', first_path), ('second.csv', second_path)]:
        (review / name).write_bytes(path.read_bytes())
    pending = list(disputes(first, second))
    with (review / 'adjudication.csv').open('x', encoding='utf-8', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(ADJUDICATION)
        for pair in pending:
            writer.writerow((*pair, '', '', ''))
    write(review / 'collection-seal.json',
          {'assessments': {name: sha(review / name) for name in ('first.csv', 'second.csv')},
           'archive_sha256': sha(directory / 'anonymous-review.zip'),
           'identity_key_sha256': sha(directory / 'private/blind-key.json'),
           'disputes': len(pending), 'identity_key_parsed': False})
    return len(pending)


def blind_consensus(outcomes, first, second, adjudication):
    expected = {(case, label, field): (a, b) for case, label, field, a, b in disputes(first, second)}
    resolved = {}
    for row in adjudication:
        case, label, field = key = (row['blind_case'], row['output_label'], row['field'])
        assert key in expected and key not in resolved
        assert tuple(str(value) for value in expected[key]) == (row['first'], row['second'])
        assert row['rationale'].strip() and row['evidence_citation'].strip(), key
        resolved[key] = parse(field, row['final'].strip(), outcomes[case, label])
    assert set(resolved) == set(expected), 'Resolve every dispute before unblinding.'
    consensus = []
    for item, status in outcomes.items():
        row = {}
        for field, a in first[item].items():
            key = (*item, field)
            if key in resolved:
                row[field] = resolved[key]
            elif field in DIMS and a is not None:
                row[field] = mean((a, second[item][field]))
            else:
                row[field] = a
        row.update(blind_case=item[0], output_label=item[1], status=status)
        row['usefulness'] = None if status in MISSING else mean(row[field] for field in DIMS[1:4])
        consensus.append(row)
    return consensus


def average(values):
    values = [value for value in values if value is not None]
    return mean(values) if values else None


def summarize(rows):
    eligible = [row for row in rows if row['case'] != 'U7']
    abstentions = [row for row in rows if row['status'] in ABSTAINS]
    return {
        'eligible': len(eligible),
        'available': sum(row['status'] == 'ok' for row in eligible),
        'usefulness': average(row['usefulness'] for row in eligible),
        **{field: average(row[field] for row in eligible) for field in DIMS},
        'critical_claim_cases': sum(row['critical_unsupported_claim'] == 'yes' for row in rows),
        'defects_by_severity': {
            field: {str(level): sum(row[field] == level for row in eligible) for level in (0, 1, 2)}
            for field in DEFECTS},
        'appropriate_abstentions': sum(row['appropriate_abstention'] == 'yes' for row in abstentions),
        'postgeneration_abstentions': sum(row['status'] == 'insufficient_evidence' for row in eligible),
        'appropriate_postgeneration': sum(row['status'] == 'insufficient_evidence'
                                          and row['appropriate_abstention'] == 'yes' for row in eligible),
        'abstentions_including_control': len(abstentions),
        'failures': [row['case'] for row in eligible if row['status'] == 'execution_failed'],
        'not_run': [row['case'] for row in eligible if row['status'] == 'not_run_after_provider_failure'],
        'observations': {field: {value: sum(row[field] == value for row in eligible)
                                 for value in ('yes', 'no', 'not_applicable')} for field in OBSERVATIONS},
    }


def reports(rows, empty_attempts):
    groups = {}
    for split in ('known', 'reference_aligned', 'generation_heldout', 'fresh'):
        for arm in (('v1.2',) if split == 'fresh' else ('baseline', 'v1.1', 'v1.2')):
            group = [row for row in rows if row['arm'] == arm and
                     (row['split'] != 'fresh' if split == 'known' else row['split'] == split)]
            groups[f'{split}/{arm}'] = summarize(group)
    comparisons = {}
    for arm in ('baseline', 'v1.1'):
        pairs = []
        for case in sorted({row['case'] for row in rows if row['arm'] == arm} - {'U7'}):
            old, = (row for row in rows if row['case'] == case and row['arm'] == arm)
            new, = (row for row in rows if row['case'] == case and row['arm'] == 'v1.2')
            common = old['status'] == new['status'] == 'ok'
            pairs.append({'case': case, 'split': new['split'], 'old_status': old['status'],
                          'new_status': new['status'], 'old_usefulness': old['usefulness'],
                          'new_usefulness': new['usefulness'],
                          'paired_gain': new['usefulness'] - old['usefulness'] if common else None})
        comparisons[arm] = {split: {'common_available_pairs': sum(p['paired_gain'] is not None for p in selected),
                                   'paired_mean_gain': average(p['paired_gain'] for p in selected),
                                   'excluded_cases': [p['case'] for p in selected if p['paired_gain'] is None],
                                   'per_case': selected}
                            for split, selected in [
                                ('known', pairs), ('reference_aligned', [p for p in pairs if p['split'] == 'reference_aligned']),
                                ('generation_heldout', [p for p in pairs if p['split'] == 'generation_heldout'])]}
    limits = read(ROOT / 'criteria.json')
    known, fresh = (groups[f'{split}/v1.2'] for split in ('known', 'fresh'))
    common_gain = comparisons['baseline']['known']['paired_mean_gain']
    dims = ('usefulness', 'fidelity', 'limitations')
    control = [row for row in rows if row['case'] == 'U7']
    assert len(control) == 3
    known_threshold = limits['known']['minimum_usefulness_fidelity_and_limitations_per_split']
    fresh_threshold = limits['fresh']['minimum_usefulness_fidelity_and_limitations']
    gates = {
        'known': {
            'critical_claims': known['critical_claim_cases'] == 0,
            'availability': known['available'] >= limits['known']['availability_minimum'],
            'split_means': all((groups[f'{split}/v1.2'][field] or 0) >= known_threshold
                               for split in ('reference_aligned', 'generation_heldout') for field in dims),
            'material_defects': all(counts['2'] <= limits['known']['maximum_material_cases_per_defect']
                                    for counts in known['defects_by_severity'].values()),
            'paired_vs_baseline': common_gain is not None
                                 and common_gain >= limits['known']['minimum_paired_usefulness_gain_vs_baseline'],
            'zero_call_empty_control': empty_attempts == 0 and all(
                r['status'] == 'skipped_no_accepted_evidence' and r['appropriate_abstention'] == 'yes'
                for r in control),
        },
        'fresh': {
            'critical_claims': fresh['critical_claim_cases'] == 0,
            'availability': fresh['available'] >= limits['fresh']['availability_minimum'],
            'means': all((fresh[field] or 0) >= fresh_threshold for field in dims),
            'material_defects': all(counts['2'] <= limits['fresh']['maximum_material_cases_per_defect']
                                    for counts in fresh['defects_by_severity'].values()),
        },
    }
    return {'assessment': 'AI-assisted engineering evaluation', 'human_acceptance': 'unverified',
            'groups': groups, 'known_comparisons': comparisons, 'fresh_pairing': 'not_applicable',
            'quality_gates': gates, 'all_applicable_quality_gates_met': all(
                passed for group in gates.values() for passed in group.values()), 'case_scores': rows}


def finalize(directory):
    review = directory / 'ai-review'
    seal = read(review / 'collection-seal.json')
    assert sha(directory / 'anonymous-review.zip') == seal['archive_sha256']
    assert sha(directory / 'private/blind-key.json') == seal['identity_key_sha256']
    for name, expected in seal['assessments'].items():
        assert sha(review / name) == expected
    outcomes = load_blind(directory)
    _, first = assessment(review / 'first.csv', outcomes)
    _, second = assessment(review / 'second.csv', outcomes)
    adjudication = review / 'adjudication.csv'
    rows = blind_consensus(outcomes, first, second, read_csv(adjudication))
    write(review / 'blind-consensus.json',
          {'adjudication_sha256': sha(adjudication), 'rows': rows, 'identities_opened': False})
    # Only parse the arm identities after the blind judgments are sealed.
    key = read(directory / 'private/blind-key.json')
    original = {row['id']: row['split'] for row in read(ROOT.parent / 'v1/frozen/cases.json')}
    for row in rows:
        link = key[row['blind_case']]
        row.update(case=link['case'], arm=link['labels'][row['output_label']],
                   split=original.get(link['case'], 'fresh'))
    receipt = read(directory / 'private/execution-receipt.json')
    report = reports(rows, receipt['empty_control_attempts'])
    write(review / 'metrics-unblinded.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['collect', 'finalize'])
    parser.add_argument('--run', type=Path, default=DESTINATION)
    parser.add_argument('--first', type=Path)
    parser.add_argument('--second', type=Path)
    args = parser.parse_args()
    if args.phase == 'collect':
        if args.first is None or args.second is None:
            parser.error('Supply both completed AI score sheets.')
        print(f'{collect(args.run, args.first, args.second)} blinded disagreements to adjudicate.')
    else:
        finalize(args.run)
