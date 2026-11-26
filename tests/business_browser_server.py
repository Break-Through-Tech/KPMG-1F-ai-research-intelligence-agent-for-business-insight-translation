"""Disposable offline browser QA host: handwritten data/generation, no providers."""
import importlib.util
import json
from pathlib import Path
import tempfile
from threading import Thread
from http.server import ThreadingHTTPServer

from src.business_demo import BusinessHandler
from src.brief_store import BriefStore
from tests.test_downstream_business import business, result_for


def main():
    with tempfile.TemporaryDirectory(prefix='business-browser-offline-') as folder:
        store = BriefStore(Path(folder) / 'briefs.sqlite3')
        store.save({'mode': 'fixture', 'scenario': 'summary-only', 'error': None,
                    'fixture_file': 'handwritten-browser-research', 'result': result_for()},
                   title='Offline business translation QA')
        def generate(prompt):
            if 'FORCE_OFFLINE_FAILURE' in prompt:
                raise RuntimeError('Scripted provider failure; no provider exists.')
            return json.dumps(business())
        handler = type('OfflineBusinessHandler', (BusinessHandler,), {
            'library': store, 'business_generate': staticmethod(generate),
            'business_metadata': {'execution': 'offline_fixture'}})
        backend = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        Thread(target=backend.serve_forever, daemon=True).start()
        path = Path(__file__).resolve().parents[1] / 'ui-consult/serve.py'
        spec = importlib.util.spec_from_file_location('business_browser_proxy', path)
        proxy = importlib.util.module_from_spec(spec); spec.loader.exec_module(proxy)
        proxy.Handler.backend = ('127.0.0.1', backend.server_port)
        frontend = proxy.Server(('127.0.0.1', 0), proxy.Handler)
        print(f'OFFLINE_UI=http://127.0.0.1:{frontend.server_port}', flush=True)
        try:
            frontend.serve_forever()
        finally:
            frontend.server_close(); backend.shutdown(); backend.server_close()


if __name__ == '__main__': main()
