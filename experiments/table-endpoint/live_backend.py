"""Isolated live backend for ui-consult: the demo-100 B2 research backend exactly as
src.experimental.demo builds it (same functions, unchanged), plus the read-only
GET /api/evidence-table route and an explicit model-call budget.

    py -3.14 live_backend.py --export <main export> --bundle <demo-100> --encoder <dir> --reranker <dir>
        --library <sqlite> --port 8787 --max-calls 0 [--check-only]

--max-calls defaults to 0: generation is refused until a budget is approved.
A question is refused BEFORE any model call when fewer calls remain than it could need
(3 with an industry chosen, 4 without: the backend may spend one call reading an industry
from the question). The page shows the budget from /api/config. Nothing in src/ is modified.

Chart-first additions (experimental, 2026-11-17; all model-free):
- POST /api/chart-preview: the same B2 retrieval plus audit-verified complete tables, so an explicit
  chart question shows a verified chart in seconds, independently of the generated explanation.
- GET /api/progress: the current stage (retrieval, validating, waiting for generation call N with its
  elapsed time and timeout) and the last provider error.
- Evidence compaction (evidence_compaction.py): the synthesis and quality-review prompts carry each
  passage's ID, paper, section and text only; validation still uses the full records.
  --no-compact-evidence restores the full payload.
The per-call timeout, the call cap and the stop-after-provider-error rule are unchanged.
"""
import argparse
import copy
import io
import json
import sys
import threading
import time
from collections import OrderedDict
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PER_QUESTION = {'with_industry': 3, 'without_industry': 4}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--encoder', type=Path, required=True)
    parser.add_argument('--reranker', type=Path, required=True)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--top-k', type=int, default=8)
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--max-calls', type=int, default=0, help='Approved model-call budget for this run (default 0).')
    parser.add_argument('--call-log', type=Path, default=HERE / 'live-calls.jsonl')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--table-audit', type=Path, default=HERE / 'table-audit-demo-100.json',
                        help='Extractor audit from build_table_audit.py. Missing or mismatched: every table fails closed.')
    parser.add_argument('--no-compact-evidence', action='store_true',
                        help='Send full passage records to the model (default: compact them; see evidence_compaction.py).')
    parser.add_argument('--agentic', action='store_true',
                        help='Also serve the experimental POST /api/agentic-research (experiments/agentic). Off by default; '
                             '/api/research is unchanged either way.')
    parser.add_argument('--call-ledger', type=Path,
                        help='Existing SQLite call ledger (call_ledger.py init) for a cumulative authorization across '
                             'restarts and processes. Requires --authorized-calls.')
    parser.add_argument('--authorized-calls', type=int,
                        help='Cumulative authorized model calls; must equal the value recorded in the ledger.')
    parser.add_argument('--experiment', help='Name of a capped experiment (for example the A/B run) inside the authorization.')
    parser.add_argument('--experiment-cap', type=int, help='Calls allowed for --experiment; recorded once, never raised.')
    parser.add_argument('--profile', choices=['ab-agentic-1'],
                        help='Approved execution profile (ab_profile.py). ab-agentic-1 requires the authorization ledger, '
                             '--authorized-calls 40, --experiment ab-agentic-1 and --experiment-cap 14, and locks the ledger to it.')
    parser.add_argument('--budget-check-only', action='store_true',
                        help='Validate the call budget and profile against the ledger (read-only), print it and exit. '
                             'Loads no index or model.')
    return parser


def validate_budget(parser, args):
    """Check the call-budget flags before anything is loaded. Every problem exits (fails closed)."""
    if (args.call_ledger is None) != (args.authorized_calls is None):
        parser.error('--call-ledger and --authorized-calls must be given together.')
    if (args.experiment is None) != (args.experiment_cap is None):
        parser.error('--experiment and --experiment-cap must be given together.')
    sys.path.insert(0, str(HERE))
    from ab_profile import PROFILES
    profile_experiments = {p['experiment']: name for name, p in PROFILES.items()}
    if args.experiment in profile_experiments and args.profile != profile_experiments[args.experiment]:
        parser.error(f'--experiment {args.experiment} belongs to an approved profile; launch with '
                     f'--profile {profile_experiments[args.experiment]} so its cap and lock are enforced.')
    if args.profile:
        from ab_profile import profile_errors
        errors = profile_errors(args.profile, ledger=args.call_ledger, authorized=args.authorized_calls,
                                experiment=args.experiment, experiment_cap=args.experiment_cap)
        if errors:
            parser.error(f'profile {args.profile} refused: ' + ' '.join(errors))
    if args.call_ledger is not None:
        import call_ledger
        try:
            status = call_ledger.status(args.call_ledger)
        except Exception as error:
            parser.error(f'call ledger refused: {error}')
        from ab_profile import unapproved_experiment
        unapproved = unapproved_experiment(status.get('seed_sha256'), args.experiment)
        if unapproved:
            parser.error(f'call ledger refused: {unapproved}')
        locked = status.get('locked_experiment')
        registered = [name for name in status.get('experiment_caps', {}) if name in profile_experiments]
        if registered and args.experiment not in registered:
            parser.error(f'call ledger refused: it records the approved experiment {registered[0]!r}; '
                         f'launch with --profile {profile_experiments[registered[0]]}.')
        if locked is not None and args.experiment != locked:
            parser.error(f'call ledger refused: it is locked to experiment {locked!r}; '
                         f'launch with --profile {locked} --experiment {locked} and its recorded cap.')
        return status
    return None


def configure_call_budget(args, wrapper, observer=None):
    """The launcher's exact budget setup (also used by the tests). A profile locks the ledger to its experiment."""
    wrapper.configure(args.max_calls, args.call_log, observer=observer,
                      ledger=args.call_ledger, authorized=args.authorized_calls,
                      experiment=args.experiment, experiment_cap=args.experiment_cap,
                      lock_experiment=bool(args.profile))


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    status = validate_budget(parser, args)
    if args.budget_check_only:
        print(json.dumps({'profile': args.profile, 'ledger': status, 'max_calls': args.max_calls, 'model_calls': 0}, indent=2))
        return
    sys.path.insert(0, str(args.export))
    sys.path.insert(0, str(HERE))
    from evidence_tables import TableIndex
    from recorded_backend import make_handler
    from progress import Progress
    from evidence_compaction import compacting
    from src.experimental.b2 import open_b2
    from src.experimental.demo import create_research, load_generator
    import capped_codex_ui

    tables = TableIndex(args.bundle / 'parents.jsonl', args.table_audit if args.table_audit.exists() else None)
    retrieval = open_b2(args.bundle, encoder_path=args.encoder, reranker_path=args.reranker)
    progress = Progress()
    base_retrieve = retrieval[0]
    retrieval_lock = threading.Lock()
    cache = OrderedDict()  # (query, top_k) -> passages; retrieval is deterministic for one index

    def cached_retrieve(query, top_k):
        # One retrieval at a time (the encoder and reranker are shared by the chart preview and
        # the research request); an identical query reuses the result instead of re-ranking.
        key = (query, top_k)
        with retrieval_lock:
            if key in cache:
                cache.move_to_end(key)
                return copy.deepcopy(cache[key])
            passages = base_retrieve(query, top_k)
            cache[key] = copy.deepcopy(passages)
            while len(cache) > 16:
                cache.popitem(last=False)
            return passages

    def research_retrieve(query, top_k):
        progress.stage('retrieval')
        started = time.perf_counter()
        passages = cached_retrieve(query, top_k)
        progress.retrieval_done(time.perf_counter() - started, len(passages))
        return passages

    retrieval = (research_retrieve, *retrieval[1:])
    identity = retrieval[1]()
    summary = {'tables': len(tables.tables), 'completeness_audit': tables.audit_problem or 'loaded', 'table_index_sha256': tables.index_sha256,
               'retrieval_indexed_records_sha256': identity.get('indexed_records_sha256'),
               'identities_match': identity.get('indexed_records_sha256') == tables.index_sha256,
               'method': retrieval[3].get('method'), 'model_calls': 0}
    if args.check_only:
        print(json.dumps(summary, indent=2))
        return
    if not summary['identities_match']:
        sys.exit('Table index and retrieval index differ; refusing to start.')
    last_compaction = {}

    def observe(event, info):
        if event == 'call_started':
            progress.call_started(info['number'], info['timeout'], info['prompt_chars'],
                                  last_compaction.get('chars_before') if last_compaction.get('compacted') else None)
        elif event == 'call_finished':
            progress.call_finished(info['number'], info['seconds'], info['outcome'], info['cause'])

    configure_call_budget(args, capped_codex_ui, observe)
    generate, metadata = load_generator('capped_codex_ui:create', {})
    if not args.no_compact_evidence:
        generate = compacting(generate, on_compact=lambda stats: (last_compaction.clear(), last_compaction.update(stats)))
        metadata = {**metadata, 'evidence_compaction': 'experimental: passage text, IDs, title and section only'}
    research = create_research(retrieval, generate, metadata, args.top_k)

    def budget():
        use = capped_codex_ui.usage()
        return {**use, 'provider': f"Codex {capped_codex_ui.MODEL} (personal login)",
                'per_question_max': PER_QUESTION['without_industry'], 'per_question': PER_QUESTION,
                'call_timeout_seconds': capped_codex_ui.TIMEOUT}

    base = make_handler(args.export, tables, args.library, preview_retrieve=cached_retrieve,
                        progress=progress, budget=budget, top_k=args.top_k)
    # One research request at a time across BOTH modes: the call budget, the ledger and /api/progress
    # all describe a single request. A second request gets 409 before any model call.
    research_lock = threading.Lock()
    # An approved profile may be research-only (ab-agentic-1 is): no industry, inferred business context or risk
    # step in EITHER mode, so the A/B compares research answers and Business Translation cannot run.
    from ab_profile import PROFILES
    research_only = bool(args.profile) and PROFILES[args.profile].get('research_only', False)

    def research_only_refusal(payload):
        if not isinstance(payload, dict):
            return None
        reasons = [name for name, present in (('industry', bool(str(payload.get('industry') or '').strip())),
                                               ('interpret_context', bool(payload.get('interpret_context'))),
                                               ('risk_assessment', bool(payload.get('risk_assessment')))) if present]
        return (f"The {args.profile} profile is research-only; remove {', '.join(reasons)}. No model call was made."
                if reasons else None)

    orchestrator = agentic_route = None
    if args.agentic:
        sys.path.insert(0, str(HERE.parent / 'agentic'))
        from agents import OrchestratorAgent
        import route as agentic_route
        import chart_preview
        agentic_route._lock = research_lock
        orchestrator = OrchestratorAgent(
            generate=generate, retrieve=research_retrieve, top_k=args.top_k,
            chart_tool=agentic_route.chart_tool_for(tables, chart_preview.preview),
            available_calls=lambda: capped_codex_ui.usage()['remaining'],
            on_stage=progress.agent,
            # Charts are shown only when they come from the same index as the answer's evidence.
            index_sha256=research.provenance['index'].get('indexed_records_sha256'),
            research_only=research_only)

    class LiveHandler(base):
        def respond(self, status, body, content_type='application/json; charset=utf-8'):
            # Tell the page how many approved calls remain.
            if self.path == '/api/config' and status == 200 and isinstance(body, dict):
                body = {**body, 'call_budget': budget(), 'agentic_mode': orchestrator is not None}
            return super().respond(status, body, content_type)

        def agentic_research(self):
            """Experimental orchestrated research. Pending human review; never approved here."""
            if not self.local_request():
                return self.respond(403, {'error': 'Use the local research page.'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                length = 0
            try:
                payload = json.loads(self.rfile.read(length) if 0 < length <= 196608 else b'')
            except ValueError:
                payload = None
            if agentic_route is None:
                return self.respond(404, {'code': 'agentic_disabled', 'error': 'Start the live backend with --agentic.'})
            status, body = agentic_route.handle(payload, orchestrator=orchestrator, research=research,
                                                usage=capped_codex_ui.usage, top_k=args.top_k, progress=progress,
                                                library=self.library, research_only=research_only)
            return self.respond(status, body)

        def do_POST(self):
            if self.path == '/api/agentic-research':
                return self.agentic_research()
            if self.path != '/api/research' or not self.local_request():
                return super().do_POST()
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                length = 0
            raw = self.rfile.read(length) if 0 < length <= 196608 else b''
            try:
                payload = json.loads(raw or b'{}')
            except ValueError:
                payload = {}
            if research_only:
                refusal = research_only_refusal(payload)
                if refusal:
                    return self.respond(400, {'code': 'research_only', 'error': refusal})
            industry = isinstance(payload, dict) and isinstance(payload.get('industry'), str) and payload['industry'].strip()
            need = PER_QUESTION['with_industry' if industry else 'without_industry']
            use = capped_codex_ui.usage()
            if use['stopped'] or use['remaining'] < need:
                reason = ('Generation stopped after a provider error; restart with a new approved budget.' if use['stopped'] else
                          f"Not enough approved model calls: {use['remaining']} of {use['cap']} left, and this question can need up to {need}. "
                          'No model call was made. Approve a budget and restart the live backend with --max-calls.')
                return self.respond(429, {'code': 'call_budget', 'error': reason})
            if not research_lock.acquire(blocking=False):
                return self.respond(409, {'code': 'busy', 'error': 'Another research request (baseline or multi-agent) is running. '
                                                                   'Wait for it to finish. No model call was made.'})
            self.rfile = io.BytesIO(raw)
            progress.begin(mode='baseline', max_calls=need)
            try:
                return super().do_POST()
            finally:
                progress.end(failed=progress.snapshot()['last_error'] is not None)
                research_lock.release()

    LiveHandler.research = research
    with ThreadingHTTPServer(('127.0.0.1', args.port), LiveHandler) as server:
        print(json.dumps({**summary, 'url': f'http://127.0.0.1:{server.server_port}', 'library': str(args.library),
                          'generator': f'capped_codex_ui (cap {args.max_calls}, no retries)',
                          'call_log': str(args.call_log)}), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
