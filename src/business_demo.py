"""Opt-in saved-answer endpoint for staged hosting or a standalone local preview."""
import json
import sqlite3
from threading import Lock
from pathlib import Path
from http.server import ThreadingHTTPServer

from src.brief_store import BriefStore, BriefConflict
from src.business_handoff import accepted_research
from src.business_insights import automatic_business_context, derive_business_context, translate_result


def automatic_offer(response, *, allow_replayed=False):
    """Offer automatic translation only for a newly saved, eligible answer."""
    result = response.get('result')
    library = response.get('library') or {}
    if (response.get('mode') != 'indexed' or response.get('error') or not result
            or not library.get('version') or (library.get('replayed') and not allow_replayed)
            or 'business_insight' in result):
        return False
    try:
        question = response.get('submitted_request', result['request'])['query']
        if automatic_business_context(question) is None:
            return False
        summary, evidence, _ = accepted_research(result['summary'], result['evidence'])
        return bool(summary['claims'] and evidence)
    except (KeyError, TypeError, ValueError):
        return False
from src.research_demo import DemoHandler


class BusinessHandler(DemoHandler):
    research = None
    presentation_generate = None
    business_generate = None
    business_metadata = None
    business_lock = Lock()

    def respond(self, status, body, content_type='application/json; charset=utf-8'):
        if self.path == '/api/config' and status == 200 and isinstance(body, dict):
            body = {**body, 'business_translation': type(self).business_generate is not None}
        if (self.path == '/api/research' and status == 200 and isinstance(body, dict)
                and type(self).business_generate is not None and automatic_offer(body)):
            body = {**body, 'business_auto': True}
        super().respond(status, body, content_type)

    def do_POST(self):
        if self.path != '/api/business':
            return super().do_POST()
        if not self.local_request():
            return self.respond(403, {'error': 'Use the local research page.'})
        if self.library is None or type(self).business_generate is None:
            return self.respond(503, {'error': 'Downstream business translation is not configured.'})
        if self.headers.get_content_type() != 'application/json':
            return self.respond(415, {'error': 'Use application/json.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 8192:
                raise ValueError('Invalid business request size.')
            payload = json.loads(self.rfile.read(size))
            required = {'brief_id', 'expected_version', 'fingerprint', 'context'}
            if (not isinstance(payload, dict) or not required <= set(payload) <= required | {'automatic'}
                    or not isinstance(payload.get('automatic', False), bool)):
                raise ValueError('Use a saved research version and business context.')
            if not all(isinstance(payload[k], str) and payload[k] for k in ('brief_id', 'expected_version', 'fingerprint')):
                raise ValueError('Invalid saved research reference.')
            self.library.check_current(payload['brief_id'], payload['expected_version'])
            source = self.library.load(payload['brief_id'], payload['expected_version'])
        except BriefConflict:
            return self.respond(409, {'error': 'Saved research changed. Reload before translating.'})
        except KeyError:
            return self.respond(404, {'error': 'Saved research not found.'})
        except (ValueError, TypeError):
            return self.respond(400, {'error': 'Select a current saved research version and valid business context.'})
        except sqlite3.Error:
            return self.respond(503, {'error': 'Saved research is unavailable. No translation attempted.'})
        try:
            if payload.get('automatic'):
                if payload['context'] != {} or not automatic_offer(source, allow_replayed=True):
                    return self.respond(400, {'error': 'Automatic business insights are unavailable for this answer.'})
                context = automatic_business_context(source['submitted_request']['query'])
            else:
                context = derive_business_context(source['submitted_request']['query'], payload['context'])
        except ValueError as error:
            return self.respond(400, {'error': str(error)})
        if not self.business_lock.acquire(blocking=False):
            return self.respond(409, {'error': 'A translation is running. Wait before trying again.'})
        try:
            # Another request can save a new version between the first check and lock acquisition.
            self.library.check_current(payload['brief_id'], payload['expected_version'])
            response = translate_result(source['result'], context=context,
                generate=type(self).business_generate, metadata=type(self).business_metadata,
                expected_fingerprint=payload['fingerprint'],
                research_input={'kind': 'fixture' if source.get('fixture_file') or source.get('mode') == 'fixture' else 'recorded_research',
                                'mode': source.get('mode'), 'fixture_file': source.get('fixture_file')})
            response['submitted_request'] = source['submitted_request']
            try:
                response = self.library.save(response, brief_id=payload['brief_id'],
                    expected_version=payload['expected_version'])
            except (ValueError, sqlite3.Error, OSError):
                response['library_error'] = 'Translation retained but not saved. Export this snapshot; do not regenerate to save it.'
            return self.respond(200, response)
        except BriefConflict:
            return self.respond(409, {'error': 'Saved research changed. Reload before translating.'})
        except (ValueError, TypeError, KeyError):
            return self.respond(400, {'error': 'Research integrity or business context did not validate. No translation was generated.'})
        except Exception:
            return self.respond(502, {'error': 'Business translation is unavailable. The saved research is retained.'})
        finally:
            self.business_lock.release()


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8791)
    parser.add_argument('--configured-provider', action='store_true', required=True,
                        help='Explicit provider selection; business requests make a model call.')
    args = parser.parse_args()
    from src.business_generation import create_business_generate
    generate, metadata = create_business_generate()  # Hydrogen only; never the research model.
    BusinessHandler.business_generate = staticmethod(generate)
    BusinessHandler.business_metadata = metadata
    BusinessHandler.library = BriefStore(args.library)
    with ThreadingHTTPServer(('127.0.0.1', args.port), BusinessHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
