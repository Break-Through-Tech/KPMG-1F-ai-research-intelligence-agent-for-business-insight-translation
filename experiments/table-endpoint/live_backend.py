"""Isolated live backend for ui-consult: the demo-100 B2 research backend exactly as
src.experimental.demo builds it (same functions, unchanged), plus the read-only
GET /api/evidence-table route and an explicit model-call budget.

    py -3.14 live_backend.py --export <main export> --bundle <demo-100> --encoder <dir> --reranker <dir>
        --library <sqlite> --port 8787 --max-calls 0 [--check-only]

--max-calls defaults to 0: generation is refused until a budget is approved.
A question is refused BEFORE any model call when fewer calls remain than it could need
(3 with an industry chosen, 4 without: the backend may spend one call reading an industry
from the question). The page shows the budget from /api/config. Nothing in src/ is modified.
"""
import argparse
import io
import json
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PER_QUESTION = {'with_industry': 3, 'without_industry': 4}


def main(argv=None):
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
    args = parser.parse_args(argv)
    sys.path.insert(0, str(args.export))
    sys.path.insert(0, str(HERE))
    from evidence_tables import TableIndex
    from recorded_backend import make_handler
    from src.experimental.b2 import open_b2
    from src.experimental.demo import create_research, load_generator
    import capped_codex_ui

    tables = TableIndex(args.bundle / 'parents.jsonl', args.table_audit if args.table_audit.exists() else None)
    retrieval = open_b2(args.bundle, encoder_path=args.encoder, reranker_path=args.reranker)
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
    capped_codex_ui.configure(args.max_calls, args.call_log)
    generate, metadata = load_generator('capped_codex_ui:create', {})
    research = create_research(retrieval, generate, metadata, args.top_k)
    base = make_handler(args.export, tables, args.library)

    def budget():
        use = capped_codex_ui.usage()
        return {**use, 'provider': f"Codex {capped_codex_ui.MODEL} (personal login)",
                'per_question_max': PER_QUESTION['without_industry'], 'per_question': PER_QUESTION}

    class LiveHandler(base):
        def respond(self, status, body, content_type='application/json; charset=utf-8'):
            # Tell the page how many approved calls remain.
            if self.path == '/api/config' and status == 200 and isinstance(body, dict):
                body = {**body, 'call_budget': budget()}
            return super().respond(status, body, content_type)

        def do_POST(self):
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
            industry = isinstance(payload, dict) and isinstance(payload.get('industry'), str) and payload['industry'].strip()
            need = PER_QUESTION['with_industry' if industry else 'without_industry']
            use = capped_codex_ui.usage()
            if use['stopped'] or use['remaining'] < need:
                reason = ('Generation stopped after a provider error; restart with a new approved budget.' if use['stopped'] else
                          f"Not enough approved model calls: {use['remaining']} of {use['cap']} left, and this question can need up to {need}. "
                          'No model call was made. Approve a budget and restart the live backend with --max-calls.')
                return self.respond(429, {'code': 'call_budget', 'error': reason})
            self.rfile = io.BytesIO(raw)
            return super().do_POST()

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
