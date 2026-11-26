"""Arm B of completion-eval-v1: apply the frozen completion pass to arm A's SAVED Baseline answers.

A's answers are never regenerated. For each completed A question the saved summary, its saved synthesis evidence packet
and the frozen question are passed to experiments/baseline-completion/completion.complete(). Only questions whose
review reports an available-but-omitted detail make calls (re-draft + review, at most 2).

Persistent hard cap: 30 calls (calls.sqlite3, reserved before each call). Resume never repeats finished questions.
Stops on login/quota/rate-limit errors, budget exhaustion and MemoryError. Outputs go to codex-completion-v1-completed.

    python -I apply_completion.py --check
    python -I apply_completion.py --run
"""
import argparse
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import codex_baseline  # noqa: E402
from codex_paired import ROOT, Budget, CodexCalls, EFFORT, MODEL, TIMEOUT  # noqa: E402

SOURCE = 'codex-completion-v1-baseline'
TARGET = 'codex-completion-v1-completed'
CAP = 30


def run(*, generate, receipts, out_root):
    """Apply completion to every completed arm-A question. Injectable generate for offline tests."""
    sys.path.insert(0, str(ROOT / 'experiments/baseline-completion'))
    import completion
    folder, selected = codex_baseline.SETS['completion']
    questions = {q['id']: q['question'] for q in json.loads((folder / 'questions.json').read_text(encoding='utf-8'))}
    source, out = out_root / SOURCE, out_root / TARGET
    a_status = json.loads((source / 'status.json').read_text(encoding='utf-8'))
    out.mkdir(parents=True, exist_ok=True)
    budget = Budget(out / 'calls.sqlite3', cap=CAP)
    calls = CodexCalls(generate, receipts, budget)
    status_path = out / 'status.json'
    status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.is_file() else {}
    for qid in selected:
        if status.get(qid, {}).get('state') in ('complete', 'skipped'):
            continue
        if a_status.get(qid, {}).get('state') != 'complete':
            status[qid] = {'state': 'skipped', 'reason': 'arm A has no completed answer'}
            continue
        saved = json.loads((source / qid / 'result.json').read_text(encoding='utf-8'))
        summary = saved['envelope']['result']['summary']
        passages = json.loads(next((source / qid).glob('*-synthesis.evidence.json')).read_text(encoding='utf-8'))
        calls.question = qid
        print('Completing', qid, flush=True)
        started, before = time.perf_counter(), budget.used()
        try:
            result, record = completion.complete(questions[qid], summary, passages, generate=calls)
        except MemoryError:
            status[qid] = {'state': 'stopped', 'reason': 'MemoryError: free system memory and rerun to resume'}
            break
        target = out / qid
        target.mkdir(exist_ok=True)
        (target / 'result.json').write_text(json.dumps({
            'question': questions[qid], 'seconds': round(time.perf_counter() - started, 3), 'calls': budget.used() - before,
            'record': record, 'summary': result}, ensure_ascii=False, indent=1), encoding='utf-8')
        if record.get('error') == 'BudgetExhausted' or calls.fatal:
            status[qid] = {'state': 'stopped', 'reason': record.get('error') or calls.fatal}
            status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
            break
        status[qid] = {'state': 'complete', 'triggered': record['triggered'], 'added': record.get('added', 0),
                       'error': record.get('error')}
        status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
    status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
    (out / 'run.json').write_text(json.dumps({
        'arm': 'B: frozen completion applied to saved arm-A answers', 'source': SOURCE, 'model': MODEL,
        'reasoning_effort': EFFORT, 'timeout_seconds': TIMEOUT, 'call_cap': CAP, 'calls_used': budget.used(),
        'status': status}, indent=1), encoding='utf-8')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    from prepare import CLI
    import codex_paired
    ready = codex_paired.checks(CLI)
    ready['completion_seal'] = codex_baseline.set_sealed('completion')
    ready['free_commit_gb'] = round(codex_baseline.free_commit_gb(), 1)
    source = ROOT / 'data/processed' / SOURCE
    ready['arm_a_complete'] = sum(v.get('state') == 'complete' for v in json.loads(
        (source / 'status.json').read_text(encoding='utf-8')).values()) if (source / 'status.json').is_file() else 0
    print(json.dumps({**ready, 'call_cap': CAP}, indent=1))
    if args.check:
        return
    if not ready['arm_a_complete']:
        raise SystemExit('Run arm A first (codex_baseline.py --run completion-eval-baseline).')
    from src.codex_generation import create_codex_generate
    receipts = []
    generate, _ = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT, receipts=receipts)
    print(json.dumps(run(generate=generate, receipts=receipts, out_root=ROOT / 'data/processed'), indent=1))


if __name__ == '__main__':
    main()
