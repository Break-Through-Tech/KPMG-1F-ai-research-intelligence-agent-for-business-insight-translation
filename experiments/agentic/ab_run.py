"""Guarded runner for the controlled research-only A/B (ab-agentic-1). It talks to an ALREADY RUNNING live backend
started with the approved profile; it never starts a backend, never touches the ledger directly, and never retries.

  preflight (read-only, 0 model calls):
    py -3.14 -I -B ab_run.py preflight --backend http://127.0.0.1:8787
  run (spends up to 14 provider calls; refused without the exact approval phrase):
    py -3.14 -I -B ab_run.py run --backend http://127.0.0.1:8787 --run-dir <NEW dir> --approve "ab-agentic-1 14 calls"

The run sends, one at a time, in the order of ab_questions.json: Q2 baseline, Q2 multi-agent, Q3 baseline, Q3 multi-agent.
Both modes get the same question text. Baseline: {query, context_id, interpret_context: false}. Multi-agent: {query,
context_id}. No industry, no risk assessment (the profile refuses them anyway).

After EVERY request, before the next one, the full response, request, wall latency and the ledger snapshots before and after
are written to a new record file (never overwritten). The run STOPS (writes STOPPED.json, exits non-zero) on: a non-200
response; an execution error (provider or budget failure); a calls-used increase above that step's maximum or a negative
one; the backend reporting generation stopped; a ledger / experiment / index mismatch with the pinned spec; a citation
or provenance failure in the answer (unknown cited ID, quote absent from its passage, wrong index). A clean abstention
(insufficient evidence) is a result, not a stop.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ab_eval  # noqa: E402

APPROVAL = 'ab-agentic-1 14 calls'
ENDPOINT = {'baseline': '/api/research', 'agentic': '/api/agentic-research'}


class Stop(RuntimeError):
    pass


def http(backend, method, path, body=None, timeout=1900):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(backend.rstrip('/') + path, data=data, method=method,
                                     headers={'Content-Type': 'application/json'} if data is not None else {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b'null')
    except urllib.error.HTTPError as error:
        payload = error.read()
        try:
            return error.code, json.loads(payload or b'null')
        except ValueError:
            return error.code, {'raw': payload[:500].decode(errors='replace')}


def budget_problems(config, spec, *, need=None):
    """Reasons the backend's budget/profile/index state is not the approved one (empty = fine)."""
    problems = []
    if not isinstance(config, dict) or not config.get('live'):
        return ['The backend is not a live research backend.']
    if config.get('agentic_mode') is not True:
        problems.append('The backend was not started with --agentic.')
    budget = config.get('call_budget') or {}
    cumulative = budget.get('cumulative') or {}
    experiment = cumulative.get('experiment') or {}
    if 'error' in cumulative:
        problems.append(f"The call ledger is unavailable: {cumulative['error']}")
    if cumulative.get('authorized') != 40:
        problems.append(f"The ledger authorization is {cumulative.get('authorized')}, not 40.")
    if experiment.get('name') != spec['experiment'] or experiment.get('cap') != spec['max_calls']['total']:
        problems.append(f"The backend is not running experiment {spec['experiment']!r} with cap {spec['max_calls']['total']} (got {experiment}).")
    if budget.get('stopped'):
        problems.append('Generation is stopped after a provider error.')
    if need is not None and (budget.get('remaining') or 0) < need:
        problems.append(f"Only {budget.get('remaining')} calls remain; this step can need {need}.")
    index = (config.get('index') or {}).get('indexed_records_sha256')
    if index is not None and index != spec['corpus']['parents_sha256']:
        problems.append(f'The backend index {index} is not the pinned corpus.')
    return problems


def preflight(backend, spec):
    status, config = http(backend, 'GET', '/api/config', timeout=30)
    if status != 200:
        return {'ok': False, 'problems': [f'/api/config answered {status}.']}
    problems = budget_problems(config, spec, need=spec['max_calls']['total'])
    experiment = ((config.get('call_budget') or {}).get('cumulative') or {}).get('experiment') or {}
    if experiment.get('used') not in (0, None):
        problems.append(f"The A/B allocation already used {experiment.get('used')} calls; start only on a fresh allocation.")
    return {'ok': not problems, 'problems': problems, 'call_budget': config.get('call_budget'),
            'index': config.get('index'), 'context_id': config.get('context_id'), 'model_calls': 0}


def answer_problems(record, spec):
    """Citation and provenance stop conditions for one saved record."""
    analysis = ab_eval.analyze(record, spec)['automatic']
    problems = []
    if analysis['status'] == 'error':
        problems.append(f"Execution error: {analysis['error']}")
    if analysis['index_matches_pinned_corpus'] is False:
        problems.append('The answer was produced from a different index.')
    if analysis['citation_ids_valid'] is False:
        problems.append('An answer claim cites an ID that is not in its evidence.')
    if analysis['quotes_in_passages'] is False:
        problems.append('An answer quote is absent from its cited passage.')
    if analysis['business_insight_present']:
        problems.append('Business translation ran in a research-only experiment.')
    return problems


def run(backend, spec, run_dir, *, approval, sleep=time.sleep, clock=time.perf_counter):
    if approval != APPROVAL:
        raise Stop(f'Refused: the live run needs --approve "{APPROVAL}" exactly. No request was sent.')
    run_dir = ab_eval.new_directory(run_dir)
    check = preflight(backend, spec)
    ab_eval.write_new(run_dir / 'preflight.json', check)
    if not check['ok']:
        ab_eval.write_new(run_dir / 'STOPPED.json', {'at': ab_eval.now(), 'step': 0, 'reasons': check['problems']})
        raise Stop('Preflight failed: ' + ' '.join(check['problems']))
    run_id = f'live-{uuid.uuid4().hex[:12]}'
    ab_eval.write_new(run_dir / 'run.json', {'run_id': run_id, 'started_at': ab_eval.now(), 'backend': backend,
                                             'experiment': spec['experiment'], 'sequence': spec['sequence'],
                                             'max_calls': spec['max_calls'], 'corpus': spec['corpus']})
    for sequence, (qid, mode) in enumerate(spec['sequence'], 1):
        need = spec['max_calls'][mode]
        status, before = http(backend, 'GET', '/api/config', timeout=30)
        problems = [f'/api/config answered {status}.'] if status != 200 else budget_problems(before, spec, need=need)
        if problems:
            ab_eval.write_new(run_dir / 'STOPPED.json', {'at': ab_eval.now(), 'step': sequence, 'before_request': True, 'reasons': problems})
            raise Stop(f'Stopped before step {sequence}: ' + ' '.join(problems))
        body = {'query': spec['questions'][qid]['text'], 'context_id': before.get('context_id')}
        if mode == 'baseline':
            body['interpret_context'] = False
        started_at, started = ab_eval.now(), clock()
        status, response = http(backend, 'POST', ENDPOINT[mode], body)
        latency = round(clock() - started, 3)
        after_status, after = http(backend, 'GET', '/api/config', timeout=30)
        record = ab_eval.make_record(
            run_id=run_id, sequence=sequence, question_id=qid, question=body['query'], mode=mode, endpoint=ENDPOINT[mode],
            request=body, response=response, http_status=status, started_at=started_at, finished_at=ab_eval.now(),
            latency_seconds=latency, budget_before=before, budget_after=after if after_status == 200 else None,
            backend_config={k: before.get(k) for k in ('context_id', 'index', 'mode')} | {
                'provider': (before.get('call_budget') or {}).get('provider'),
                'call_timeout_seconds': (before.get('call_budget') or {}).get('call_timeout_seconds')},
            source='live')
        ab_eval.write_new(ab_eval.record_path(run_dir, sequence, qid, mode), record)  # saved BEFORE any further request
        problems = []
        if status != 200:
            problems.append(f'{ENDPOINT[mode]} answered {status}: {response}')
        used = record['model_calls_actual']
        if used is None:
            problems.append('The ledger snapshot after the request is missing; actual calls cannot be confirmed.')
        elif used < 0 or used > need:
            problems.append(f'Budget discrepancy: this step used {used} calls (allowed 0-{need}).')
        reported = ((response or {}).get('result') or {}).get('provenance', {}).get('agentic', {}).get('model_calls', {}).get('used') \
            if mode == 'agentic' and isinstance(response, dict) else None
        if reported is not None and used is not None and reported != used:
            problems.append(f'Budget discrepancy: the orchestrator reports {reported} calls, the ledger shows {used}.')
        if status == 200:
            problems += answer_problems(record, spec)
        if after_status == 200 and (after.get('call_budget') or {}).get('stopped'):
            problems.append('The backend stopped generation after a provider error.')
        if problems:
            ab_eval.write_new(run_dir / 'STOPPED.json', {'at': ab_eval.now(), 'step': sequence, 'reasons': problems})
            raise Stop(f'Stopped after step {sequence} ({qid} {mode}): ' + ' '.join(problems))
    ab_eval.write_new(run_dir / 'COMPLETED.json', {'at': ab_eval.now(), 'run_id': run_id})
    return run_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('preflight')
    p.add_argument('--backend', required=True)
    p.add_argument('--questions', type=Path, default=HERE / 'ab_questions.json')
    r = sub.add_parser('run')
    r.add_argument('--backend', required=True)
    r.add_argument('--questions', type=Path, default=HERE / 'ab_questions.json')
    r.add_argument('--run-dir', type=Path, required=True)
    r.add_argument('--approve', default='')
    args = parser.parse_args(argv)
    spec = ab_eval.load_questions(args.questions)
    if args.command == 'preflight':
        result = preflight(args.backend, spec)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result['ok'] else 2)
    try:
        print(run(args.backend, spec, args.run_dir, approval=args.approve))
    except (Stop, ab_eval.HarnessError) as error:
        sys.exit(str(error))


if __name__ == '__main__':
    main()
