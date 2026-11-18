"""Test-only Codex generator for approved ui-consult live questions (personal Codex login).

Wraps main's src.codex_generation.create_codex_generate unchanged. Hard cap: the approved
budget set by the launcher, including nested context, quality-review and business calls). No retries: a refused or failed
call is never repeated by this wrapper; after a provider error further calls are refused.
Call metadata only (no prompts, no outputs) is logged to live-calls.jsonl next to this file.
"""
import json
import threading
import time
from pathlib import Path

CAP = 0  # set by the launcher (--max-calls); 0 means no generation is approved
MODEL, EFFORT, TIMEOUT = 'gpt-6.1-sol', 'low', 300
BINARY = r'C:\Users\ngkho\AppData\Local\OpenAI\Codex\bin\f71a721e0e6193a9\codex.exe'
LOG = Path(__file__).resolve().parent / 'live-calls.jsonl'


def configure(cap, log):
    global CAP, LOG
    CAP, LOG = int(cap), Path(log)


def usage():
    with _lock:
        return {'cap': CAP, 'used': _state['calls'], 'remaining': max(0, CAP - _state['calls']), 'stopped': _state['stopped']}
_lock = threading.Lock()
_state = {'calls': 0, 'stopped': False}


def create():
    from src.codex_generation import create_codex_generate
    inner, metadata = create_codex_generate(model=MODEL, binary=BINARY, effort=EFFORT, timeout=TIMEOUT)

    def generate(prompt, *, response_schema=None):
        with _lock:
            if _state['stopped']:
                raise RuntimeError('Stopped after a provider error; no call made (no automatic retries).')
            if _state['calls'] >= CAP:
                raise RuntimeError(f'Approved cap of {CAP} calls reached; no call made.')
            _state['calls'] += 1
            n = _state['calls']
        started = time.perf_counter()
        outcome, cause = 'ok', None
        try:
            return inner(prompt, response_schema=response_schema)
        except Exception as error:
            name = type(error).__name__
            outcome = 'schema_error' if name == 'SchemaResponseError' else 'provider_error' if name == 'PipelineError' else 'other_error:' + name
            if error.__context__ is not None:
                cause = {'type': type(error.__context__).__name__, 'message': str(error.__context__)[:240]}
            with _lock:
                _state['stopped'] = True
            raise
        finally:
            with LOG.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps({'call': n, 'at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                                         'seconds': round(time.perf_counter() - started, 2), 'prompt_chars': len(prompt),
                                         'schema': response_schema is not None, 'outcome': outcome, 'cause': cause}) + '\n')

    generate.supports_response_schema = True
    return generate, {**metadata, 'test_call_cap': CAP}
