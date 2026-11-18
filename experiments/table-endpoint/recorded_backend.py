"""Experimental loopback backend: recorded briefs + read-only full-table endpoint.

Isolated prototype (2026-11-17). It imports the unchanged shared ``DemoHandler`` and
``BriefStore`` from a clean export of ``main`` and adds exactly one route:

    GET /api/evidence-table?chunk_id=<table-row passage ID>&index=<parents.jsonl SHA-256>

No retrieval models are loaded and no generation provider is configured, so
``/api/research`` answers 503 exactly as the shared handler does without a provider.
Saved briefs are served from a COPY of the recorded brief database; the original is opened
read-only once to make the copy and is never written.
"""
import argparse
import json
import shutil
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from evidence_tables import TableIndex, TableUnavailable  # noqa: E402


MAX_DRAIN = 65536  # a refused request body larger than this is not read; the connection is closed


def drain_request_body(handler):
    """Consume a declared request body (up to MAX_DRAIN bytes). Returns False if it was not read."""
    try:
        length = int(handler.headers.get('Content-Length') or 0)
    except ValueError:
        return False
    if length < 0 or length > MAX_DRAIN:
        return False
    while length:
        chunk = handler.rfile.read(min(length, 8192))
        if not chunk:
            return False
        length -= len(chunk)
    return True


def make_handler(export_root, tables, library_path):
    sys.path.insert(0, str(export_root))
    from src.research_demo import DemoHandler
    from src.brief_store import BriefStore

    class RecordedHandler(DemoHandler):
        def do_GET(self):
            parts = urlsplit(self.path)
            if parts.path != '/api/evidence-table':
                return super().do_GET()
            if not self.local_request():
                return self.respond(403, {'error': 'Use the local research page.'})
            if tables is None:
                return self.respond(404, {'code': 'evidence_table_disabled', 'error': 'Full-table lookup is not enabled.'})
            if len(parts.query) > 400:
                return self.respond(400, {'code': 'bad_request', 'error': 'Request too long.'})
            try:
                # strict_parsing and max_num_fields raise ValueError; bad percent-escapes raise
                # UnicodeDecodeError with errors='strict'. All become a structured 400.
                query = parse_qs(parts.query, strict_parsing=True, max_num_fields=4, errors='strict')
            except (ValueError, UnicodeDecodeError):
                return self.respond(400, {'code': 'bad_request', 'error': 'The query string could not be parsed.'})
            if set(query) != {'chunk_id', 'index'} or any(len(v) != 1 for v in query.values()):
                return self.respond(400, {'code': 'bad_request', 'error': 'Pass exactly chunk_id and index.'})
            try:
                table = tables.table(query['chunk_id'][0], query['index'][0])
            except TableUnavailable as error:
                return self.respond(error.status, {'code': error.code, 'error': error.reason})
            self.respond(200, table)

        def _method_not_allowed(self):
            # The table route is read-only: only GET is accepted, whatever the shared handler does.
            if urlsplit(self.path).path == '/api/evidence-table':
                # Read the request body before answering. Closing a socket that still holds unread
                # bytes makes Windows send a reset, which can discard this response before the
                # client reads it (WinError 10053, seen in about 1 in 5 refusals with a body).
                drained = drain_request_body(self)
                self.send_response(405)
                body = json.dumps({'code': 'method_not_allowed', 'error': 'Use GET for /api/evidence-table.'}).encode()
                self.send_header('Allow', 'GET')
                if not drained:
                    self.send_header('Connection', 'close')
                    self.close_connection = True
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return True
            return False

        def do_POST(self):
            if not self._method_not_allowed():
                return super().do_POST()

        def do_PUT(self):
            if not self._method_not_allowed():
                drain_request_body(self)
                self.send_error(501)

        def do_DELETE(self):
            if not self._method_not_allowed():
                drain_request_body(self)
                self.send_error(501)

    RecordedHandler.research = None
    RecordedHandler.saved_result = None
    RecordedHandler.presentation_generate = None
    RecordedHandler.library = BriefStore(library_path) if library_path else None
    return RecordedHandler


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True, help='Clean export of main (not modified).')
    parser.add_argument('--bundle', type=Path, required=True, help='Bundle directory containing parents.jsonl (read-only).')
    parser.add_argument('--recorded-briefs', type=Path, help='Recorded brief database; copied, never written.')
    parser.add_argument('--working-copy', type=Path, default=HERE / 'recorded-briefs-working.sqlite3')
    parser.add_argument('--fresh-copy', action='store_true', help='Replace the working copy from the recorded database.')
    parser.add_argument('--table-audit', type=Path, default=HERE / 'table-audit-demo-100.json',
                        help='Extractor audit from build_table_audit.py. Missing or mismatched: every table fails closed.')
    parser.add_argument('--port', type=int, default=8786)
    args = parser.parse_args(argv)
    tables = TableIndex(args.bundle / 'parents.jsonl', args.table_audit if args.table_audit.exists() else None)
    library = None
    if args.recorded_briefs:
        if args.fresh_copy or not args.working_copy.exists():
            shutil.copyfile(args.recorded_briefs, args.working_copy)
        library = args.working_copy
    handler = make_handler(args.export, tables, library)
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
        print(json.dumps({'url': f'http://127.0.0.1:{server.server_port}', 'index_sha256': tables.index_sha256,
                          'tables': len(tables.tables), 'completeness_audit': tables.audit_problem or 'loaded', 'library': str(library) if library else None,
                          'research': 'disabled (recorded replay; no provider)', 'model_calls': 0}), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
