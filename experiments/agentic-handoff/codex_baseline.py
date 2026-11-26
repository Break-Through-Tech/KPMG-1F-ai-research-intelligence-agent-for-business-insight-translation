"""Baseline/B2 on the frozen F01-F10 questions with the same Codex model, for a head-to-head against current Multi-Agent.

Baseline is constructed exactly as the KPMG app builds it: src.experimental.demo.create_research on B2, which uses
quality_check=True (one synthesis call plus one answer-quality review call per question) and the unchanged
src.research_chat.synthesize path. Baseline gets no quote grounding and no interpretation policy, because it has
none in production. Nothing in Baseline/B2 is modified.

Variants (separate output directories; never mixed with Gemini or the Multi-Agent run directories):
  deployed  B2 as the app opens it (table comparisons off), top_k 8      -> codex-baseline-v1-deployed
  tables    B2 with table comparisons on, the route the Multi-Agent arms used -> codex-baseline-v1-tables

The persistent budget, resume and stop rules are those of codex_paired.py. Each question records its synthesis evidence
packet, raw replies, envelope, call receipts and wall time. report.json is written at the end.

    python -I codex_baseline.py --check deployed
    python -I codex_baseline.py --run deployed      # at most 30 calls (3 per question; 2 expected)
    python -I codex_baseline.py --run tables
"""
import argparse
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import codex_paired  # noqa: E402  (sets sys.path for src, agents and the frozen diagnostic)
from codex_paired import ROOT, Budget, BudgetExhausted, CodexCalls, EFFORT, MODEL, TIMEOUT  # noqa: E402

# variant: (output directory, table comparisons, deterministic question decomposition, question set)
VARIANTS = {'deployed': ('codex-baseline-v1-deployed', False, False, 'dev'),
            'tables': ('codex-baseline-v1-tables', True, False, 'dev'),
            'heldout-baseline': ('codex-heldout-v1-baseline', False, False, 'heldout'),
            'heldout-decomposed': ('codex-heldout-v1-decomposed', False, True, 'heldout'),
            'completion-eval-baseline': ('codex-completion-v1-baseline', False, False, 'completion'),
            # combined-v1 (fresh set): the same Baseline engine; only the evidence budget differs (see EVIDENCE).
            'fresh-top8': ('combined-v1-baseline-top8', False, False, 'fresh'),
            'fresh-top16': ('combined-v1-baseline-top16', False, False, 'fresh'),
            'fresh-skipfit6k': ('combined-v1-baseline-skipfit6k', False, False, 'fresh')}
EVIDENCE = {'fresh-top16': 'fixed-16', 'fresh-skipfit6k': 'skip-fit-6000-w30'}  # all others: top_k 8
QUESTIONS = tuple(f'F{i:02d}' for i in range(1, 11))
SETS = {'dev': (ROOT / 'experiments/measure/fresh-diagnostic-v1', QUESTIONS),
        'heldout': (ROOT / 'experiments/heldout-v1', tuple(f'H{i:02d}' for i in range(1, 11))),
        'completion': (ROOT / 'experiments/completion-eval-v1', tuple(f'C{i:02d}' for i in range(1, 16))),
        'fresh': (ROOT / 'experiments/combined-v1', None)}  # IDs read from questions.json once the set exists
SET_CAPS = {'completion': 2, 'fresh': 2}
# combined-v1 preliminary validation: hard cap of 100 model calls across ALL fresh-set arms, retries included.
COMBINED_CAP = 100
FRESH_ARM_CAP = {'baseline': 22, 'multiagent': 55}
# 2026-11-24, user-approved after the first pass: one spare call moved from M1 to B1. B0 22 + B1 23 + M1 55 = 100.
FRESH_VARIANT_CAP = {'fresh-skipfit6k': 23}
FRESH_MAX_RESUMES = 1  # user-approved: failed questions are retried once only


def fresh_cap(variant):
    return FRESH_VARIANT_CAP.get(variant, FRESH_ARM_CAP['baseline'])


def resumes_left(out, qid):
    """False once a fresh-set question has used its one resume (a preserved .attempt-N folder exists)."""
    return sum(1 for _ in out.glob(f'{qid}.attempt-*')) < FRESH_MAX_RESUMES


def combined_calls_used(out_root):
    """Calls already reserved by every combined-v1 arm (persistent ledgers under data/processed)."""
    import sqlite3
    from contextlib import closing
    used = {}
    for path in sorted(Path(out_root).glob('combined-v1-*/calls.sqlite3')):
        with closing(sqlite3.connect(path)) as db:
            used[path.parent.name] = db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
    return used


def check_combined_cap(out_root, arm_dir, arm_cap):
    """Refuse to start an arm whose remaining allowance could push all combined-v1 arms past COMBINED_CAP."""
    used = combined_calls_used(out_root)
    own = used.get(arm_dir, 0)
    worst = sum(used.values()) + max(0, arm_cap - own)
    if worst > COMBINED_CAP:
        raise SystemExit(f'combined-v1 cap: {sum(used.values())} calls used across arms; this arm may use up to '
                         f'{arm_cap - own} more, exceeding {COMBINED_CAP}. Nothing was run.')
    return {'combined_used': sum(used.values()), 'arm_remaining': arm_cap - own, 'combined_cap': COMBINED_CAP}  # completion-eval-v1: Baseline makes exactly 2 calls per question; hard cap 30
PER_QUESTION_CAP = 3
SEPARATOR = 'Return only JSON matching the supplied schema.\n'


def question_set(name):
    folder, selected = SETS[name]
    if selected is None:
        selected = tuple(q['id'] for q in json.loads((folder / 'questions.json').read_text(encoding='utf-8')))
    return folder, selected


class Recording:
    """Saves the evidence packet and raw reply of every call into the question folder."""
    supports_response_schema = True

    def __init__(self, inner):
        self.inner, self.folder, self.count = inner, None, 0

    def __call__(self, prompt, *, response_schema=None):
        self.count += 1
        stage = 'synthesis' if prompt.startswith('Synthesize an answer') else 'review'
        if stage == 'synthesis' and SEPARATOR in prompt:
            packet = json.loads(prompt.split(SEPARATOR, 1)[1]).get('paper_passages', [])
            (self.folder / f'{self.count}-{stage}.evidence.json').write_text(
                json.dumps(packet, ensure_ascii=False, indent=1), encoding='utf-8')
        raw = self.inner(prompt, response_schema=response_schema)
        (self.folder / f'{self.count}-{stage}.reply.json').write_text(
            json.dumps({'provider_text': raw}, ensure_ascii=False), encoding='utf-8')
        return raw


def run(variant, *, research, generate, receipts, out_root):
    """Run or resume one variant. `research` is a create_research(...) engine. Injectable for offline tests."""
    directory, _, _, question_set = VARIANTS[variant]
    folder_of_set, selected = globals()['question_set'](question_set)
    out = out_root / directory
    out.mkdir(parents=True, exist_ok=True)
    cap = fresh_cap(variant) if question_set == 'fresh' else SET_CAPS.get(question_set, PER_QUESTION_CAP) * len(selected)
    budget = Budget(out / 'calls.sqlite3', cap=cap)
    calls = CodexCalls(generate, receipts, budget)
    sys.path.insert(0, str(ROOT / 'experiments/evidence-budget'))
    from request_guard import RequestGuard
    guard = RequestGuard(calls)  # checked before the budget reserves a call
    recording = Recording(guard)
    research.generate = recording
    timing = {'seconds': 0.0, 'calls': 0}
    inner_retrieve = research.retrieve

    def timed_retrieve(query, top_k):
        started = time.perf_counter()
        try:
            return inner_retrieve(query, top_k)
        finally:
            timing['seconds'] += time.perf_counter() - started
            timing['calls'] += 1
    research.retrieve = timed_retrieve
    questions = {q['id']: q for q in json.loads((folder_of_set / 'questions.json').read_text(encoding='utf-8'))}
    status_path = out / 'status.json'
    status = json.loads(status_path.read_text(encoding='utf-8')) if status_path.is_file() else {}
    for qid in selected:
        if status.get(qid, {}).get('state') == 'complete':
            continue
        folder = out / qid
        if question_set == 'fresh' and not resumes_left(out, qid):
            print('Skipping', qid, '(its one resume is used)', flush=True)
            continue
        if folder.exists():
            attempt = 1 + sum(1 for _ in out.glob(f'{qid}.attempt-*'))
            folder.rename(out / f'{qid}.attempt-{attempt}')
        folder.mkdir()
        calls.question, recording.folder, recording.count, guard.records = qid, folder, 0, []
        print('Running', qid, flush=True)
        started, before = time.perf_counter(), budget.used()
        timing.update(seconds=0.0, calls=0)
        try:
            envelope = research.execute({'query': questions[qid]['question'], 'context_id': research.context_id,
                                         'interpret_context': False})
            if (envelope or {}).get('scenario') == 'execution-error' or (envelope or {}).get('error'):
                state = {'state': 'execution_error', 'error': (envelope.get('error') or {}).get('code'),
                         'codex': calls.fatal}
            else:
                state = {'state': 'complete'}
        except BudgetExhausted as error:
            status[qid] = {'state': 'stopped', 'reason': str(error)}
            status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
            break
        except MemoryError:
            # Machine-wide commit exhaustion: every later question would fail the same way. Stop and resume later.
            status[qid] = {'state': 'stopped', 'reason': 'MemoryError: free system memory and rerun to resume'}
            status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
            break
        except Exception as error:
            envelope, state = None, {'state': 'execution_error', 'error': type(error).__name__, 'codex': calls.fatal}
        (folder / 'result.json').write_text(json.dumps({
            'question': questions[qid]['question'], 'seconds': round(time.perf_counter() - started, 3),
            'retrieval_seconds': round(timing['seconds'], 3), 'retrieval_invocations': timing['calls'],
            'calls': budget.used() - before, 'requests': guard.records, 'envelope': envelope}, ensure_ascii=False, indent=1),
            encoding='utf-8')
        status[qid] = state
        status_path.write_text(json.dumps(status, indent=1), encoding='utf-8')
        if calls.fatal:
            break
    (out / 'run.json').write_text(json.dumps({
        'variant': variant, 'architecture': 'Baseline/B2 (src.experimental.demo.create_research, quality_check=True)',
        'table_comparisons': VARIANTS[variant][1], 'question_decomposition': VARIANTS[variant][2],
        'question_set': question_set, 'evidence': EVIDENCE.get(variant, 'fixed-8'), 'model': MODEL, 'reasoning_effort': EFFORT,
        'timeout_seconds': TIMEOUT, 'call_cap': budget.cap, 'calls_used': budget.used(), 'status': status},
        indent=1), encoding='utf-8')
    return status


MIN_FREE_COMMIT_GB = 6  # B2 with the models loaded commits about 1.4 GB; the Codex CLI and OS need headroom


def free_commit_gb():
    import ctypes

    class Status(ctypes.Structure):
        _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong), ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong), ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong), ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong), ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
    status = Status()
    status.dwLength = ctypes.sizeof(Status)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.ullAvailPageFile / 2 ** 30  # commit still available system-wide


def report(out, question_set='dev'):
    """Per question: status, published claims with citations, limitations, required-point screen, time, calls."""
    from stage_a_report import EXPLANATORY, required_points
    folder_of_set, selected = globals()['question_set'](question_set)
    rows = {}
    for qid in selected:
        path = out / qid / 'result.json'
        if not path.is_file():
            continue
        saved = json.loads(path.read_text(encoding='utf-8'))
        summary = ((saved.get('envelope') or {}).get('result') or {}).get('summary') or {}
        claims = summary.get('claims', [])
        arm = {'published_claims': [c['text'] for c in claims], 'published_cited': [c.get('chunk_ids', []) for c in claims]}
        evidence = []
        for path in sorted((out / qid).glob('*-synthesis.evidence.json')):
            evidence += [p['chunk_id'] for p in json.loads(path.read_text(encoding='utf-8'))]
        rows[qid] = {'status': summary.get('status'), 'seconds': saved['seconds'], 'calls': saved['calls'],
                     'retrieval_seconds': saved.get('retrieval_seconds'), 'evidence_ids': list(dict.fromkeys(evidence)),
                     'claims': [{'text': c['text'], 'kind': c.get('kind'), 'support': c.get('support'),
                                 'explanatory_wording': sorted({m.group(0).lower() for m in EXPLANATORY.finditer(c['text'])})}
                                for c in claims],
                     'limitations': summary.get('limitations', []),
                     'required_points': required_points(qid, arm, folder_of_set / 'references.json'),
                     'error': ((saved.get('envelope') or {}).get('error') or {}).get('code')
                     if saved.get('envelope') else 'execution_error'}
    return rows


def set_sealed(question_set):
    """Refuse to run if any frozen file (or the frozen completion code) changed after sealing."""
    import hashlib
    folder = SETS[question_set][0]
    seal = json.loads((folder / 'seal.json').read_text(encoding='utf-8'))
    paths = {name: folder / name for name in seal if name not in ('index_parents_sha256', 'completion_py_sha256')}
    if 'completion_py_sha256' in seal:
        paths['completion_py_sha256'] = ROOT / 'experiments/baseline-completion/completion.py'
    for name, path in paths.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != seal[name]:
            raise SystemExit(f'Frozen file changed after sealing: {name}')
    return 'verified'


def heldout_sealed():
    """Refuse to run the held-out comparison if any frozen file changed after sealing."""
    import hashlib
    folder = SETS['heldout'][0]
    seal = json.loads((folder / 'seal.json').read_text(encoding='utf-8'))
    for name, digest in seal.items():
        if name == 'index_parents_sha256':
            continue
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != digest:
            raise SystemExit(f'Held-out file changed after sealing: {name}')
    return 'verified'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', choices=VARIANTS)
    mode.add_argument('--run', choices=VARIANTS)
    args = parser.parse_args()
    variant = args.check or args.run
    from prepare import BUNDLE, CLI, ENCODER, PIN, RERANKER
    ready = codex_paired.checks(CLI)
    if VARIANTS[variant][3] == 'heldout':
        ready['heldout_seal'] = heldout_sealed()
    if VARIANTS[variant][3] in ('completion', 'fresh'):
        ready[f'{VARIANTS[variant][3]}_seal'] = set_sealed(VARIANTS[variant][3])
    ready['free_commit_gb'] = round(free_commit_gb(), 1)
    if ready['free_commit_gb'] < MIN_FREE_COMMIT_GB:
        raise SystemExit(f"Only {ready['free_commit_gb']} GB of system commit is free; close browsers or other heavy "
                         f"programs until at least {MIN_FREE_COMMIT_GB} GB is free, then rerun. Nothing was run.")
    print(json.dumps({**ready, 'variant': variant, 'table_comparisons': VARIANTS[variant][1],
                      'question_decomposition': VARIANTS[variant][2], 'question_set': VARIANTS[variant][3],
                      'evidence': EVIDENCE.get(variant, 'fixed-8'),
                      'call_cap': fresh_cap(variant) if VARIANTS[variant][3] == 'fresh' else
                      SET_CAPS.get(VARIANTS[variant][3], PER_QUESTION_CAP) * len(question_set(VARIANTS[variant][3])[1])},
                     indent=1))
    if VARIANTS[variant][3] == 'fresh':
        print(json.dumps(check_combined_cap(ROOT / 'data/processed', VARIANTS[variant][0], fresh_cap(variant))))
    if args.check:
        return
    from src.codex_generation import create_codex_generate
    from src.experimental.b2 import open_b2
    from src.experimental.demo import create_research
    receipts = []
    generate, metadata = create_codex_generate(model=MODEL, binary=str(CLI), effort=EFFORT, timeout=TIMEOUT,
                                               receipts=receipts)
    retrieval = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=VARIANTS[variant][1])
    if retrieval[1]()['indexed_records_sha256'] != PIN:
        raise SystemExit('Unexpected B2 index')
    if VARIANTS[variant][2]:
        sys.path.insert(0, str(ROOT / 'experiments/baseline-decomposition'))
        from decomposed_retrieval import decomposed
        retrieve, identity, path, provenance = retrieval
        retrieval = (decomposed(retrieve), identity, path,
                     {**provenance, 'question_decomposition': 'question_parts@retrieval-v3-f6efa05; original + <=3 parts; '
                                                              'round-robin; cap 14'})
    top_k = 8
    if variant == 'fresh-top16':
        top_k = 16  # open_b2.retrieve allows up to 20
    elif variant == 'fresh-skipfit6k':
        sys.path.insert(0, str(ROOT / 'experiments/evidence-budget'))
        import evidence_budget
        retrieve, identity, ranked, count, path, provenance = evidence_budget.open_ranked(
            BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=False)
        retrieval = (evidence_budget.budgeted_retrieve(ranked, count, evidence_budget.skip_fit(6000, 30)), identity, path,
                     {**provenance, 'evidence_budget': 'skip-fit 6000 MiniLM passage tokens, window 30'})
        top_k = 20  # nominal; the budgeted retrieve decides the packet
    research = create_research(retrieval, generate, metadata, top_k)
    out = ROOT / 'data/processed' / VARIANTS[variant][0]
    status = run(variant, research=research, generate=generate, receipts=receipts, out_root=ROOT / 'data/processed')
    (out / 'report.json').write_text(json.dumps(report(out, VARIANTS[variant][3]), indent=1, ensure_ascii=False),
                                     encoding='utf-8')
    print(json.dumps(status, indent=1))
    print(f'Report: {out / "report.json"}')


if __name__ == '__main__':
    main()
