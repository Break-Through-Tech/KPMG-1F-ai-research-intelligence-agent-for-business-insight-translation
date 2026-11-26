"""Live research progress for the consultant page (experimental, model-free, 2026-11-17).

The shared ``POST /api/research`` is one synchronous request, so the page could only show one
message for its whole duration. This tracker is fed by thin wrappers in the experimental live
launcher (retrieval, each generation call and the request itself) and read by
``GET /api/progress``. It records stage names, timings and the last provider error; it never
holds prompts, answers or evidence text.

Stages: ``idle`` -> ``retrieval`` -> ``validating`` (between a finished step and the next one:
evidence and citation checks run here) -> ``generation`` (waiting for the AI provider; with
call number, elapsed time and the per-call timeout) -> ... -> ``finished`` / ``failed``.
"""
import threading
import time


class Progress:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._state = {'active': False, 'stage': 'idle', 'stage_started': None, 'request_started': None,
                       'call': None, 'last_error': None, 'retrieval_seconds': None, 'steps': [],
                       'mode': None, 'max_calls': None, 'agent': None}

    def _set(self, **changes):
        with self._lock:
            self._state.update(changes)

    def begin(self, mode='baseline', max_calls=None):
        now = self._clock()
        self._set(active=True, stage='starting', stage_started=now, request_started=now, call=None,
                  last_error=None, retrieval_seconds=None, steps=[], mode=mode, max_calls=max_calls, agent=None)

    def agent(self, name):
        """Multi-agent mode: which agent is working now (a name only, never content)."""
        with self._lock:
            if self._state['active']:
                self._state['agent'] = name

    def stage(self, name):
        with self._lock:
            if self._state['active']:
                self._state.update(stage=name, stage_started=self._clock())

    def retrieval_done(self, seconds, passages):
        with self._lock:
            self._state['retrieval_seconds'] = round(seconds, 2)
            self._state['steps'].append({'step': 'retrieval', 'seconds': round(seconds, 2), 'passages': passages})
            if self._state['active']:
                self._state.update(stage='validating', stage_started=self._clock())

    def call_started(self, number, timeout, prompt_chars=None, compacted_from=None):
        now = self._clock()
        with self._lock:
            self._state.update(stage='generation', stage_started=now,
                               call={'number': number, 'started': now, 'timeout': timeout,
                                     'prompt_chars': prompt_chars, 'compacted_from': compacted_from})

    def call_finished(self, number, seconds, outcome, cause=None):
        with self._lock:
            self._state['steps'].append({'step': f'generation call {number}', 'seconds': round(seconds, 2), 'outcome': outcome})
            if outcome != 'ok':
                kind = 'timeout' if cause and cause.get('type') == 'TimeoutExpired' else 'provider_error'
                self._state['last_error'] = {'call': number, 'kind': kind, 'seconds': round(seconds, 2),
                                             'message': (f'The AI provider did not respond within {round(seconds)} s (call {number}).'
                                                         if kind == 'timeout' else f'The AI provider returned an error on call {number}.')}
            if self._state['active']:
                self._state.update(stage='validating', stage_started=self._clock(), call=None)

    def end(self, failed=False):
        with self._lock:
            self._state.update(active=False, stage='failed' if failed else 'finished', stage_started=self._clock(), call=None)

    def snapshot(self, budget=None):
        now = self._clock()
        with self._lock:
            state = dict(self._state)
            call = dict(state['call']) if state['call'] else None
            steps = [dict(step) for step in state['steps']]
        out = {'active': state['active'], 'stage': state['stage'],
               'stage_seconds': round(now - state['stage_started'], 1) if state['stage_started'] is not None else None,
               'request_seconds': round(now - state['request_started'], 1) if state['request_started'] is not None else None,
               'retrieval_seconds': state['retrieval_seconds'], 'last_error': state['last_error'], 'steps': steps,
               'model_calls': 0, 'mode': state.get('mode'), 'max_calls': state.get('max_calls'), 'agent': state.get('agent')}
        if call:
            out['call'] = {'number': call['number'], 'seconds': round(now - call['started'], 1), 'timeout': call['timeout'],
                           'prompt_chars': call['prompt_chars'], 'compacted_from': call['compacted_from']}
        if budget is not None:
            out['budget'] = budget
        return out
