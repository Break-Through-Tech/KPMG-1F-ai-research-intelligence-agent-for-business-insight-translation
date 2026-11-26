"""Current Multi-Agent on the frozen business set (completion-eval-v1 C01-C15), as a possible optional Deep Research mode.

The architecture is unchanged from the Codex paired runs (current arm only; no handoff):
  - OrchestratorAgent, research_only=True, top_k 8, max_calls 5 (planner, synthesis, verification, at most one
    targeted round);
  - the frozen B2 route from preflight.open_route (table comparisons on, as in all earlier Multi-Agent runs);
  - quote grounding, the deterministic interpretation policy and the statistical-report correction, all enabled;
  - gpt-6.1-sol at low effort through the existing Codex adapter (ChatGPT login, tools disabled, schema-validated).

Baseline results for C01-C15 are reused from codex-completion-v1-baseline and are never regenerated.

Persistent hard cap: 75 calls (5 per question). Resume never repeats finished questions. Stops on login/quota/rate
limits, budget exhaustion and MemoryError; refuses to start below 6 GB of free system commit or if the frozen set
changed. Each question saves the agentic trace, the envelope, every synthesis evidence packet and every raw reply.

    python -I codex_multiagent.py --check
    python -I codex_multiagent.py --run

combined-v1 arms on the fresh set (experiments/combined-v1/questions.json + seal.json):
    python -I codex_multiagent.py --check --fresh top16 v2      # EVIDENCE top8|top16|skipfit6k, VERIFICATION frozen|v2
    python -I codex_multiagent.py --run --fresh top16 v2
The evidence budget applies to the first-round original-question search only (budgeted_research.py); merged evidence
is bounded at 8,000 passage tokens / 40 passages in every round.
"""
import argparse
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'evidence-budget'), str(HERE.parent / 'verification-repair')]
import codex_baseline  # noqa: E402
from codex_baseline import Recording  # noqa: E402
from codex_paired import ROOT, Budget, BudgetExhausted, CodexCalls, EFFORT, MODEL, TIMEOUT  # noqa: E402

TARGET = 'codex-business-v1-multiagent'
CAP_PER_QUESTION = 5


def engine(generate, retrieve, index_sha256):
    """Current Multi-Agent with the three previously tested safeguards; nothing else changes."""
    from agents import OrchestratorAgent
    import interpretation_policy
    import quote_grounding
    import statistical_reports
    statistical_reports.enable()  # process-wide, opt-in for this run only
    orchestrator = OrchestratorAgent(generate=generate, retrieve=retrieve, top_k=8, max_calls=CAP_PER_QUESTION,
                                     index_sha256=index_sha256, research_only=True)
    quote_grounding.enable(orchestrator)
    interpretation_policy.enable(orchestrator)
    return orchestrator


EVIDENCE = ('top8', 'top16', 'skipfit6k')


def fresh_engine(verification, initial_retrieve=None, count=None):
    """combined-v1 arms. verification: 'frozen' (number check + interpretation policy, as the business run) or 'v2'
    (numeric_checks_v2 + interpretation gate). initial_retrieve/count: the budgeted first packet (None = top-8)."""
    def build(generate, retrieve, index_sha256):
        from agents import OrchestratorAgent
        import quote_grounding
        import statistical_reports
        statistical_reports.enable()
        orchestrator = OrchestratorAgent(generate=generate, retrieve=retrieve, top_k=8, max_calls=CAP_PER_QUESTION,
                                         index_sha256=index_sha256, research_only=True)
        if initial_retrieve is not None:
            import budgeted_research
            budgeted_research.enable(orchestrator, initial_retrieve, count)
        quote_grounding.enable(orchestrator)
        if verification == 'v2':
            import verification_v2
            verification_v2.enable(orchestrator)
        else:
            import interpretation_policy
            interpretation_policy.enable(orchestrator)
        return orchestrator
    return build


def fresh_target(evidence, verification):
    return f'combined-v1-multiagent-{evidence}-{verification}'


def run(*, generate, receipts, retrieve, index_sha256, out_root, build=engine, target=TARGET, question_set='completion'):
    from envelope import to_envelope
    folder, selected = codex_baseline.question_set(question_set)
    questions = {q['id']: q['question'] for q in json.loads((folder / 'questions.json').read_text(encoding='utf-8'))}
    out = out_root / target
    out.mkdir(parents=True, exist_ok=True)
    cap = codex_baseline.FRESH_ARM_CAP['multiagent'] if question_set == 'fresh' else CAP_PER_QUESTION * len(selected)
    budget = Budget(out / 'calls.sqlite3', cap=cap)
    calls = CodexCalls(generate, receipts, budget)
    from request_guard import RequestGuard
    guard = RequestGuard(calls)  # checked before the budget reserves a call
    recording = Recording(guard)
    status_path = out / 'status.json'
    status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.is_file() else {}
    timing = {'seconds': 0.0, 'calls': 0}

    def timed_retrieve(query, top_k):
        started = time.perf_counter()
        try:
            return retrieve(query, top_k)
        finally:
            timing['seconds'] += time.perf_counter() - started
            timing['calls'] += 1
    for qid in selected:
        if status.get(qid, {}).get('state') == 'complete':
            continue
        qdir = out / qid
        if question_set == 'fresh' and not codex_baseline.resumes_left(out, qid):
            print('Skipping', qid, '(its one resume is used)', flush=True)
            continue
        if qdir.exists():
            attempt = 1 + sum(1 for _ in out.glob(f'{qid}.attempt-*'))
            qdir.rename(out / f'{qid}.attempt-{attempt}')
        qdir.mkdir()
        calls.question, calls.stopped, recording.folder, recording.count, guard.records = qid, None, qdir, 0, []
        timing.update(seconds=0.0, calls=0)
        print('Running', qid, flush=True)
        started, before = time.perf_counter(), budget.used()
        result = envelope = None
        try:
            result = build(recording, timed_retrieve, index_sha256).run(questions[qid])
            if result.get('status') == 'execution_error':
                state = {'state': 'execution_error', 'error': (result.get('error') or {}).get('cause'), 'codex': calls.fatal}
            else:
                envelope = to_envelope(result, top_k=8, provenance={'index': {'indexed_records_sha256': index_sha256},
                                                                   'generation': {'model': MODEL}},
                                       context_id='business-multiagent')
                state = {'state': 'complete'}
        except BudgetExhausted as error:
            status[qid] = {'state': 'stopped', 'reason': str(error)}
            status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
            break
        except MemoryError:
            status[qid] = {'state': 'stopped', 'reason': 'MemoryError: free system memory and rerun to resume'}
            status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
            break
        except Exception as error:
            state = {'state': 'execution_error', 'error': type(error).__name__, 'codex': calls.fatal}
        (qdir / 'result.json').write_text(json.dumps({
            'question': questions[qid], 'seconds': round(time.perf_counter() - started, 3),
            'retrieval_seconds': round(timing['seconds'], 3), 'retrieval_invocations': timing['calls'],
            'calls': budget.used() - before, 'requests': guard.records, 'agentic': result, 'envelope': envelope},
            ensure_ascii=False, indent=1),
            encoding='utf-8')
        status[qid] = state
        status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
        if calls.fatal:
            break
    (out / 'run.json').write_text(json.dumps({
        'architecture': target, 'questions': f'{question_set}: {", ".join(selected)}',
        'route': 'B2, table comparisons on, top_k 8 per search' + ('' if target == TARGET else f' ({target})'), 'model': MODEL,
        'reasoning_effort': EFFORT, 'timeout_seconds': TIMEOUT, 'call_cap': budget.cap, 'calls_used': budget.used(),
        'status': status}, indent=1), encoding='utf-8')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--run', action='store_true')
    parser.add_argument('--fresh', nargs=2, metavar=('EVIDENCE', 'VERIFICATION'),
                        help=f'combined-v1 arm on the fresh set: EVIDENCE in {EVIDENCE}, VERIFICATION in frozen|v2')
    args = parser.parse_args()
    from prepare import BUNDLE, CLI, ENCODER, PIN, RERANKER
    import codex_paired
    if args.fresh and (args.fresh[0] not in EVIDENCE or args.fresh[1] not in ('frozen', 'v2')):
        parser.error('--fresh EVIDENCE VERIFICATION')
    question_set = 'fresh' if args.fresh else 'completion'
    target = fresh_target(*args.fresh) if args.fresh else TARGET
    ready = codex_paired.checks(CLI)
    ready[f'{question_set}_seal'] = codex_baseline.set_sealed(question_set)
    ready['free_commit_gb'] = round(codex_baseline.free_commit_gb(), 1)
    _, selected = codex_baseline.question_set(question_set)
    cap = codex_baseline.FRESH_ARM_CAP['multiagent'] if args.fresh else CAP_PER_QUESTION * len(selected)
    print(json.dumps({**ready, 'call_cap': cap, 'output': target}, indent=1))
    if args.fresh:
        print(json.dumps(codex_baseline.check_combined_cap(ROOT / 'data/processed', target, cap)))
    if args.check:
        return
    if ready['free_commit_gb'] < codex_baseline.MIN_FREE_COMMIT_GB:
        raise SystemExit(f"Only {ready['free_commit_gb']} GB of system commit is free; free at least "
                         f"{codex_baseline.MIN_FREE_COMMIT_GB} GB, then rerun. Nothing was run.")
    from src.codex_generation import create_codex_generate
    receipts = []
    generate, _ = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT, receipts=receipts)
    build = engine
    if args.fresh:
        import evidence_budget
        retrieve, identity, ranked, count, *_ = evidence_budget.open_ranked(
            BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=True)  # the Multi-Agent route
        policy = {'top8': None, 'top16': evidence_budget.fixed(16), 'skipfit6k': evidence_budget.skip_fit(6000, 30)}[args.fresh[0]]
        initial = evidence_budget.budgeted_retrieve(ranked, count, policy) if policy else None
        build = fresh_engine(args.fresh[1], initial, count)
    else:
        from preflight import open_route
        retrieve, identity = open_route()
    if identity()['indexed_records_sha256'] != PIN:
        raise SystemExit('Unexpected B2 index')
    print(json.dumps(run(generate=generate, receipts=receipts, retrieve=retrieve, index_sha256=PIN,
                         out_root=ROOT / 'data/processed', build=build, target=target, question_set=question_set), indent=1))


if __name__ == '__main__':
    main()
