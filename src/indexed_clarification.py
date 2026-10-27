"""Tab-scoped, bounded clarification sessions for the indexed research host."""
from copy import deepcopy
from functools import partial
from secrets import token_urlsafe
from threading import Lock
from time import monotonic

from src.indexed_research import IndexedResearch, IndexedContextError, fingerprint
from src.research_pipeline import PipelineError
from src.query_clarification import ClarifyingResearch, clarification_with_generation


class ClarifyingIndexedResearch(IndexedResearch):
    """Opaque tab tokens reference server-owned intent state, never client history.

    The HTTP host serializes generation; a separate short lock protects creation
    and expiry during config requests. Pending work isn't evicted while running.
    """
    def __init__(self, *, clarify_fn=None, clock=monotonic, ttl=1800, max_sessions=32, **kwargs):
        super().__init__(**kwargs)
        self.provenance['history_policy'] = 'server_owned_bounded_intent_only'
        self.provenance['clarification'] = {'adapter': 'query-clarification-v1'}
        self.context_id = fingerprint(self.provenance)
        self.clarify = clarify_fn or partial(clarification_with_generation, generate=self.generate)
        self.clock, self.ttl, self.max_sessions = clock, ttl, max_sessions
        self.sessions = {}
        self.session_lock = Lock()

    def _expire(self):
        for key, entry in list(self.sessions.items()):
            if not entry['busy'] and self.clock() - entry['touched'] > self.ttl:
                del self.sessions[key]

    def config(self):
        with self.session_lock:
            self._expire()
            if len(self.sessions) >= self.max_sessions:
                # Do not silently evict another active or pending conversation.
                raise ValueError('Session capacity reached. Wait for idle sessions to expire or restart the local host.')
            token = token_urlsafe(32)
            entry = {'touched': self.clock(), 'busy': False, 'passages': []}
            def retrieve(query, top_k):
                passages = self.retrieve(query, top_k)
                entry['passages'] = deepcopy(passages)
                return passages
            entry['research'] = ClarifyingResearch(context_id=self.context_id,
                clarify_fn=self.clarify, retrieve=retrieve, summarize_fn=self.summary,
                provenance=self.provenance)
            self.sessions[token] = entry
        return {**super().config(), 'clarification': True,
                'history_policy': 'server_owned_bounded_intent_only',
                'conversation_id': token, 'session_ttl_seconds': self.ttl}

    def execute(self, payload, *, session_id=None):
        self.check_context(payload.get('context_id'))
        if payload.get('action', 'ask') not in {'ask', 'resume'}:
            raise ValueError('Use ask or resume.')
        token = payload.get('conversation_id')
        if not isinstance(token, str):
            raise IndexedContextError('No research conversation. Start a new conversation.')
        with self.session_lock:
            self._expire()
            entry = self.sessions.get(token)
            if entry is None:
                raise IndexedContextError('Research conversation expired. Start a new conversation.')
            if entry['busy']:
                raise IndexedContextError('A question is already running in this conversation.')
            entry['busy'] = True
        request = None
        try:
            request = self.resolve_context(self.prepare_request(payload), payload)
            session = entry['research']
            if payload.get('action') == 'resume':
                response = session.resume(request['query'], context_id=self.context_id)
            else:
                response = session.ask(request, context_id=self.context_id)
            self.check_context(payload.get('context_id'))
            submitted = response['original_request']
            if response['status'] == 'clarification_required':
                return {'mode': 'indexed', 'scenario': 'clarification', 'result': None,
                    'submitted_request': submitted, 'error': None,
                    'clarification': response['clarification'], 'phase': response['phase'],
                    'clarification_evidence': deepcopy(entry['passages']) if response['phase'] == 'post' else [],
                    'context_id': self.context_id, 'history_policy': self.provenance['history_policy']}
            response = self.finish(response['result'], submitted)
            self.check_context(payload.get('context_id'))
            response['history_policy'] = self.provenance['history_policy']
            return response
        except PipelineError as error:
            label = str(error)
            stage = next((name for name in ('Clarification (pre)', 'Clarification (post)', 'Retrieval', 'Summary')
                          if label.startswith(name)), 'Research')
            return {'mode': 'indexed', 'scenario': 'execution-error', 'result': None,
                'submitted_request': request, 'fixture_file': None,
                'error': {'stage': stage, 'code': 'research_stage_failed',
                    'message': f'{stage} failed or did not validate. No answer accepted. Retry, or start a new conversation.'},
                'provenance': {**deepcopy(self.provenance), 'stages': {stage: 'failed'}}}
        except ValueError:
            if request is None:
                raise ValueError('Question or business context did not validate. No answer accepted; retry your question.') from None
            raise IndexedContextError('Invalid conversation state; answer the pending clarification or start a new conversation.') from None
        finally:
            with self.session_lock:
                entry['busy'] = False
                entry['touched'] = self.clock()
