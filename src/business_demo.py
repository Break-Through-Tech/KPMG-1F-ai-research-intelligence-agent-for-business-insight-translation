"""Opt-in saved-answer endpoint for staged hosting or a standalone local preview."""
import json
import sqlite3
from threading import Lock
from pathlib import Path
from http.server import ThreadingHTTPServer

from src.brief_store import BriefStore, BriefConflict
from src.business_handoff import accepted_research
from src.business_insights import derive_business_context, resolve_business_intent, translate_result


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
        if resolve_business_intent(question, response.get('business_intent'),
                                   response.get('business_context_inherited'))['context'] is None:
            return False
        summary, evidence, _ = accepted_research(result['summary'], result['evidence'])
        return bool(summary['claims'] and evidence)
    except (KeyError, TypeError, ValueError):
        return False


def research_business_flags(body):
    """Mark a fresh research answer for automatic business insights, or attach a prefill hint
    when the question shows business intent but no workflow. Spends no call."""
    if automatic_offer(body):
        return {**body, 'business_auto': True}
    if body.get('mode') == 'indexed' and not body.get('error') and body.get('library'):
        question = (body.get('submitted_request') or {}).get('query', '')
        hint = resolve_business_intent(question, body.get('business_intent'), body.get('business_context_inherited'))['hint']
        if hint:
            return {**body, 'business_hint': hint}
    return body
from src.research_demo import DemoHandler
from src.conversation_store import ConversationStore
from urllib.parse import parse_qs, urlsplit
import re

CONVERSATION_PATH = re.compile(r'/api/conversations/([0-9a-f]{32,33})(/delete)?')
BRIEF_PATH = re.compile(r'/api/briefs/([0-9a-f]{32})')


def record_conversation_turn(library, body):
    """Attach a saved research turn to its conversation (creating one for a first question)."""
    turn = body.get('conversation_turn')
    if not isinstance(turn, dict) or library is None:
        return body
    conversations = ConversationStore(library)
    saved = (body.get('library') or {}).get('brief', {}).get('id')
    if not saved:
        if turn.get('conversation_id'):
            body = {**body, 'conversation': {'id': turn['conversation_id'], 'awaiting_clarification': True}}
        return body
    conversation_id = turn.get('conversation_id') or conversations.create(turn['original_question'] or 'Research')
    recorded = conversations.append_turn(conversation_id, saved, original_question=turn['original_question'],
                                         resolved_question=turn['resolved_question'], resolution=turn['resolution'])
    return {**body, 'conversation': recorded}


class BusinessHandler(DemoHandler):
    research = None
    presentation_generate = None
    business_generate = None
    business_metadata = None
    business_lock = Lock()

    def respond(self, status, body, content_type='application/json; charset=utf-8'):
        if self.path == '/api/config' and status == 200 and isinstance(body, dict):
            body = {**body, 'business_translation': type(self).business_generate is not None}
        if self.path == '/api/research' and status == 200 and isinstance(body, dict):
            try:
                body = record_conversation_turn(self.library, body)
            except (sqlite3.Error, KeyError, ValueError):
                body = {**body, 'conversation_error': 'Answer saved, but it could not be added to the conversation.'}
            deleted = (body.get('conversation') or {}).get('deleted')
            if type(self).business_generate is not None and not deleted:
                body = research_business_flags(body)
        super().respond(status, body, content_type)

    def conversations(self):
        if self.library is None:
            raise LookupError
        return ConversationStore(self.library)

    def do_GET(self):
        parts = urlsplit(self.path)
        try:
            if parts.path == '/api/conversations':
                params = parse_qs(parts.query)
                return self.respond(200, {'conversations': self.conversations().list(
                    archived=params.get('archived', ['0'])[0] == '1', query=params.get('q', [''])[0],
                    offset=int(params.get('offset', ['0'])[0]))})
            match = CONVERSATION_PATH.fullmatch(parts.path)
            if match and not match[2]:
                return self.respond(200, self.conversations().load(match[1]))
            match = BRIEF_PATH.fullmatch(parts.path)
            if match and self.library is not None:
                owner = self.conversations().conversation_of_brief(match[1])
                if owner and owner['deleted']:
                    return self.respond(404, {'error': 'This conversation was deleted from history.'})
        except KeyError:
            return self.respond(404, {'error': 'Conversation not found.'})
        except (LookupError, sqlite3.Error):
            return self.respond(503, {'error': 'Saved conversations are unavailable.'})
        except ValueError as error:
            return self.respond(400, {'error': str(error)})
        return super().do_GET()

    def conversation_write(self, conversation_id, delete):
        if not self.local_request():
            return self.respond(403, {'error': 'Use the local research page.'})
        if self.headers.get_content_type() != 'application/json':
            return self.respond(415, {'error': 'Use application/json.'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                raise ValueError('Invalid conversation request size.')
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError('Use a JSON object.')
            store = self.conversations()
            if delete:
                if payload != {'confirm': True}:
                    raise ValueError('Deleting a conversation requires confirmation.')
                result = store.soft_delete(conversation_id)
                forget = getattr(getattr(type(self).research, 'execute', None), 'forget', None)
                if callable(forget):
                    forget(conversation_id)
                return self.respond(200, result)
            if not payload or set(payload) - {'title', 'archived'}:
                raise ValueError('Use title and/or archived.')
            return self.respond(200, store.update(conversation_id, title=payload.get('title'), archived=payload.get('archived')))
        except KeyError:
            return self.respond(404, {'error': 'Conversation not found.'})
        except (LookupError, sqlite3.Error):
            return self.respond(503, {'error': 'Saved conversations are unavailable. Nothing changed.'})
        except ValueError as error:
            return self.respond(400, {'error': str(error)})

    def do_POST(self):
        match = CONVERSATION_PATH.fullmatch(urlsplit(self.path).path)
        if match:
            return self.conversation_write(match[1], bool(match[2]))
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
            owner = ConversationStore(self.library).conversation_of_brief(payload['brief_id'])
            if owner and owner['deleted']:
                return self.respond(409, {'error': 'This conversation was deleted from history. No business insight was generated.'})
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
                # Reuse the classification saved with the answer; never classify again here.
                resolved = resolve_business_intent(source['submitted_request']['query'], source.get('business_intent'),
                                                   source.get('business_context_inherited'))
                context = resolved['context']
                provenance = {'source': resolved['source']}
                if resolved['source'] == 'inherited':
                    carried = source['business_context_inherited']
                    provenance.update({k: carried[k] for k in ('from_position', 'from_brief_id', 'source', 'reason') if k in carried})
                    provenance['source'], provenance['inherited_from'] = 'inherited', carried.get('source')
            else:
                context = derive_business_context(source['submitted_request']['query'], payload['context'])
                provenance = {'source': 'user_context' if any(payload['context'].values()) else 'derived'}
        except ValueError as error:
            return self.respond(400, {'error': str(error)})
        if not self.business_lock.acquire(blocking=False):
            return self.respond(409, {'error': 'A translation is running. Wait before trying again.'})
        try:
            # Another request can save a new version between the first check and lock acquisition.
            self.library.check_current(payload['brief_id'], payload['expected_version'])
            owner = ConversationStore(self.library).conversation_of_brief(payload['brief_id'])
            if owner and owner['deleted']:
                return self.respond(409, {'error': 'This conversation was deleted from history. No business insight was generated.'})
            response = translate_result(source['result'], context=context,
                generate=type(self).business_generate, metadata=type(self).business_metadata,
                expected_fingerprint=payload['fingerprint'], context_provenance=provenance,
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
