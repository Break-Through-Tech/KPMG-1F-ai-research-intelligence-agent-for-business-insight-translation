"""Offline preflight and approval-gated, one-shot business validation."""

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO))
from src.business_handoff import accepted_research
from src.business_insights import translate_result
from src.research_review import require_current_review

ORIGINAL = ROOT.parent / 'v1'
HISTORY = ROOT.parent / 'runs/initial-pair-20261126'
DESTINATION = ROOT.parent / 'runs/final-v1.2-live'
IMPLEMENTATION = '870ba4991a2ac9f5b58d6627e2da3141a3e6af2b'
OLD_MANIFEST = '0584099d08c21093cc078e66ce6fbaa0839b6535baab827f7624e777ef3886ce'
CALL_CAP = 16
DEFAULT_PDFS = Path('C:/Users/ngkho/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/data/pdfs')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(path.read_bytes())


def encode(data):
    return (json.dumps(data, indent=2, ensure_ascii=True) + '\n').encode()


def write(path, data):
    with path.open('xb') as file:
        file.write(encode(data))


def projected(packet):
    result = packet['result']
    require_current_review(result)
    summary, passages, _ = accepted_research(result['summary'], result['evidence'])
    summary['business_context'] = packet['context']
    assert digest(json.dumps([summary, passages], sort_keys=True).encode()) == packet['shared_input_sha256']
    return {'question': summary['query'], 'context': packet['context'],
            'accepted_research': summary, 'evidence': passages}


def packets():
    known = read(ORIGINAL / 'frozen/cases.json')
    fresh = read(ROOT / 'fresh/cases.json')
    return {case['id']: (case, read(base / (case['id'] + '.json')))
            for index, base in [(known, ORIGINAL / 'frozen/packets'), (fresh, ROOT / 'fresh')]
            for case in index}


def saved_comparators():
    comparisons = {}
    for alias, mapping in read(HISTORY / 'private/blind-key.json').items():
        case = mapping['case_id']
        comparisons[case] = {}
        for label, arm in mapping['labels'].items():
            audit = read(HISTORY / 'private' / f'{alias}-{label}.json')
            shown = read(HISTORY / 'blind' / f'{alias}-{label}.json')
            assert audit['arm'] == arm and audit['case'] == case
            assert shown['business_insight'] == audit['output'] and shown['status'] == audit['status']
            if case == 'U7':
                assert audit['attempts'] == 0 and shown['status'] == 'skipped_no_accepted_evidence'
            comparisons[case]['v1.1' if arm == 'candidate' else arm] = shown
    return comparisons


def preflight(pdf_root):
    assert sys.flags.optimize == 0, 'Preflight requires runtime assertions.'
    manifest_path = ROOT / 'manifest.json'
    manifest = read(manifest_path)
    assert manifest['implementation_commit'] == IMPLEMENTATION
    assert manifest['scheduled_calls'] == manifest['hard_cap'] == CALL_CAP
    assert sha(ORIGINAL / 'frozen/manifest.json') == OLD_MANIFEST
    for name, expected in read(ORIGINAL / 'frozen/manifest.json')['files'].items():
        assert sha(ORIGINAL / name) == expected, name
    for group, base in [('assets', ROOT), ('runtime', REPO), ('historical_artifacts', HISTORY)]:
        for name, expected in manifest[group].items():
            data = (base / name).read_bytes()
            if group == 'runtime':
                data = data.replace(b'\r\n', b'\n')
            assert digest(data) == expected, name
    assert sha(ROOT / 'rubric.json') == sha(ORIGINAL / 'rubric.json')
    subprocess.run(['git', '-C', str(REPO), 'merge-base', '--is-ancestor',
                    IMPLEMENTATION, 'HEAD'], check=True, capture_output=True)
    cfg = read(ROOT / 'provider.json')
    historical = read(HISTORY / 'private/run-config.json')
    for field in ('provider', 'model', 'project_label', 'project_id', 'project_number',
                  'temperature', 'sdk_attempts', 'api_key_env', 'independent_project_confirmed'):
        assert cfg[field] == historical[field], field
    assert cfg['provider'] == 'gemini' and cfg['model'] == 'gemini-3.1-flash-lite'
    assert cfg['project_id'] == 'gen-lang-client-0342254126'
    assert cfg['excluded_projects'] == ['gen-lang-client-0472314693', 'gen-lang-client-0559861169']
    assert cfg['project_id'] not in cfg['excluded_projects']
    cases = packets()
    all_evidence = {name: projected(packet)['evidence'] for name, (_, packet) in cases.items()}
    comparators = saved_comparators()
    known = {case for case in cases if not case.startswith('F')}
    fresh = set(cases) - known
    assert len(known) == len(comparators) == 12 and set(comparators) == known and len(fresh) == 5
    assert len({packet['context']['decision'] for _, packet in cases.values()}) == 17
    assert {case for case, evidence in all_evidence.items() if not evidence} == {'U7'}
    assert sum(bool(evidence) for evidence in all_evidence.values()) == CALL_CAP
    old_papers = {row['arxiv_id'].split('v')[0] for case in known for row in all_evidence[case]}
    fresh_papers = {row['arxiv_id'].split('v')[0] for case in fresh for row in all_evidence[case]}
    assert len(fresh_papers) == 5 and not (fresh_papers & old_papers)
    for receipt in read(ROOT / 'fresh/source-verification.json'):
        passage, = all_evidence[receipt['id']]
        assert sha(pdf_root / receipt['pdf_file']) == receipt['pdf_sha256']
        assert digest(passage['text'].encode()) == receipt['quote_sha256']
        assert passage['source_url'] == receipt['locator']
    return {'manifest_sha256': sha(manifest_path), 'implementation': IMPLEMENTATION,
            'known_cases': 12, 'fresh_cases': 5, 'saved_comparators': 24,
            'planned_calls': CALL_CAP, 'maximum_attempts': CALL_CAP, 'new_control_calls': 0,
            'provider_contacted': False, 'execution_approved_by_this_command': False}


class BudgetViolation(BaseException):
    """Escapes the business adapter's isolated translation failure path."""


class Dispatch:
    def __init__(self, generate, directory, pace, key=None):
        self.generate = generate
        self.directory = directory
        self.pace = pace
        self.key = key
        self.count = 0
        self.last_start = None
        self.stop = False

    def reply(self, case, prompt, record):
        if self.stop or self.count >= CALL_CAP or record['attempts']:
            raise BudgetViolation('Stopped, duplicate case, or budget exhausted.')
        if self.last_start is not None:
            time.sleep(max(0, self.pace - (time.perf_counter() - self.last_start)))
        attempt = self.count + 1
        write(self.directory / f'{attempt:02}.json',
              {'attempt': attempt, 'case': case, 'prompt_sha256': digest(prompt.encode())})
        self.count = attempt
        record['attempts'] = 1
        self.last_start = time.perf_counter()
        try:
            response = self.generate(prompt)
            if self.key and self.key in response:
                raise ValueError('Provider echoed a credential.')
        except Exception:
            self.stop = True
            record['provider_failure'] = True
            raise ValueError('Provider request failed. Remaining generation stopped.') from None
        finally:
            record['provider_latency_seconds'] = time.perf_counter() - self.last_start
        record['raw_response'] = response
        return response


def run_candidates(directory, generate, metadata, *, pace, key=None, order=None):
    cases = packets()
    if order is None:
        order = list(cases)
        random.SystemRandom().shuffle(order)
    assert len(order) == len(set(order)) == len(cases) and set(order) == set(cases)
    directory.mkdir(exist_ok=False)  # One-shot campaign lock. No resume.
    private = directory / 'private'
    private.mkdir()
    ledger = directory / 'ledger'
    ledger.mkdir()
    write(private / 'schedule.json', {'case_order': order, 'cap': CALL_CAP})
    dispatch = Dispatch(generate, ledger, pace, key)
    records = {}
    for case in order:
        _, packet = cases[case]
        record = {'case': case, 'attempts': 0, 'provider_failure': False, 'business_insight': None}
        if dispatch.stop and case != 'U7':
            record['status'] = 'not_run_after_provider_failure'
        else:
            output = translate_result(
                packet['result'], context=packet['context'], metadata=metadata,
                generate=lambda prompt: dispatch.reply(case, prompt, record),
                research_input={'kind': 'source_verified_manual_packet'},
            )
            result = output['result']
            record['business_insight'] = result.get('business_insight')
            record['audit'] = result['provenance']['business_translation']
            record['status'] = ('execution_failed' if output['error'] else
                                'skipped_no_accepted_evidence' if case == 'U7' else
                                record['business_insight']['status'])
            assert record['attempts'] == record['audit']['attempted_calls']
            assert record['attempts'] == (0 if case == 'U7' else 1)
            assert result['summary'] == packet['result']['summary']
            assert result['evidence'] == packet['result']['evidence']
        write(private / f'{case}.json', record)
        records[case] = record
    receipt = {'attempts': dispatch.count, 'cap': CALL_CAP, 'automatic_retries': 0,
               'provider_stop': dispatch.stop, 'research_calls': 0, 'critic_calls': 0,
               'nonempty_replies': sum(bool(row.get('raw_response')) for row in records.values()),
               'statuses': {case: row['status'] for case, row in records.items()},
               'empty_control_attempts': records['U7']['attempts']}
    write(private / 'execution-receipt.json', receipt)
    return records


def export_blind(directory, records):
    cases = packets()
    historical = saved_comparators()
    randomizer = random.SystemRandom()
    order = list(cases)
    randomizer.shuffle(order)
    key = {}
    columns = (ROOT / 'score-columns.csv').read_text(encoding='utf-8').strip().split(',')
    sheet = io.StringIO(newline='')
    writer = csv.DictWriter(sheet, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    with zipfile.ZipFile(directory / 'anonymous-review.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT / 'rubric.json', 'rubric.json')
        archive.write(ROOT / 'review-instructions.md', 'review-instructions.md')
        for number, case in enumerate(order, 1):
            case_alias = f'Q{number:02}'
            archive.writestr(f'{case_alias}-case.json', encode(projected(cases[case][1])))
            comparison = dict(historical.get(case, {}), **{'v1.2': records[case]})
            arms = list(comparison)
            randomizer.shuffle(arms)
            key[case_alias] = {'case': case, 'labels': dict(zip('ABC', arms))}
            for label, arm in key[case_alias]['labels'].items():
                row = comparison[arm]
                neutral = {'blind_case': case_alias, 'output_label': label, 'status': row['status'],
                           'business_insight': row['business_insight']}
                archive.writestr(f'{case_alias}-{label}.json', encode(neutral))
                writer.writerow({'blind_case': case_alias, 'output_label': label})
        archive.writestr('scores.csv', sheet.getvalue())
    write(directory / 'private/blind-key.json', key)
    return directory / 'anonymous-review.zip'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf-dir', type=Path, default=DEFAULT_PDFS)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--approved-manifest-sha256')
    arguments = parser.parse_args()
    readiness = preflight(arguments.pdf_dir)
    if not arguments.execute:
        print(json.dumps(readiness, indent=2))
        return
    if arguments.approved_manifest_sha256 != readiness['manifest_sha256']:
        parser.error('Live execution requires separate user approval identifying this manifest hash.')
    if DESTINATION.exists():
        parser.error('Campaign directory already exists. Review local artifacts.')
    config = read(ROOT / 'provider.json')
    confirmation = read(ROOT.parent / 'runs/local/project-confirmation.json')
    data_use = read(ROOT.parent / 'runs/local/data-use-confirmation.json')
    assert config['project_id'] == confirmation['project_id']
    assert config['project_number'] == confirmation['project_number']
    assert config['excluded_projects'] == [confirmation['production_project_id'], confirmation['s2_r2_project_id']]
    assert confirmation['key_project_verified_in_ai_studio'] and confirmation['model_access_confirmed']
    assert data_use['user_explicit_acknowledgment'] and data_use['generation_allowed']
    assert not any(os.getenv(name) for name in
                   ('GOOGLE_GENAI_USE_VERTEXAI', 'GOOGLE_GEMINI_BASE_URL', 'GOOGLE_VERTEX_BASE_URL'))
    key = os.getenv('BUSINESS_EVAL_API_KEY')
    excluded_keys = ('GOOGLE_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY', 'RESEARCH_API_KEY')
    assert key and all(key != os.getenv(name) for name in excluded_keys)
    excluded_env_file = DEFAULT_PDFS.parents[1] / '.env'
    if excluded_env_file.exists():
        from dotenv import dotenv_values
        excluded = dotenv_values(excluded_env_file)
        assert all(key != excluded.get(name) for name in excluded_keys)
    from src.generation import create_generate
    from src.generation_config import GenerationConfig
    generate, metadata = create_generate(GenerationConfig(config['provider'], config['model'], key))
    records = run_candidates(DESTINATION, generate, metadata,
                             pace=config['minimum_start_spacing_seconds'], key=key)
    write(DESTINATION / 'private/config-and-approval.json', {'config': config, 'manifest': readiness})
    print(export_blind(DESTINATION, records))


if __name__ == '__main__':
    if sys.flags.optimize:
        raise SystemExit('Run with assertions enabled.')
    main()
