"""Test-only Codex generator for approved ui-consult live questions (personal Codex login).

Wraps main's src.codex_generation.create_codex_generate unchanged. Hard cap: the approved
budget set by the launcher, including nested context, quality-review and business calls). No retries: a refused or failed
call is never repeated by this wrapper; after a provider error further calls are refused.
Call metadata only (no prompts, no outputs) is logged to live-calls.jsonl next to this file.

Optional cumulative authorization across restarts and processes (--call-ledger, --authorized-calls,
optionally --experiment and --experiment-cap): see call_ledger.py. Each call is reserved in the
SQLite ledger, atomically against both caps and durably committed, BEFORE it reaches the provider,
then marked completed or failed. A ledger that cannot be trusted refuses every call.
"""
import json
import threading
import time
from pathlib import Path

CAP = 0  # set by the launcher (--max-calls); 0 means no generation is approved
MODEL, EFFORT, TIMEOUT = 'gpt-6.1-sol', 'low', 300
BINARY = r'C:\Users\ngkho\AppData\Local\OpenAI\Codex\bin\f71a721e0e6193a9\codex.exe'
LOG = Path(__file__).resolve().parent / 'live-calls.jsonl'


OBSERVER = None  # optional callable(event, info) for live progress; never sees prompts or outputs
LEDGER = None    # call_ledger.CallLedger when a cumulative authorization is configured


def configure(cap, log, observer=None, *, ledger=None, authorized=None, experiment=None, experiment_cap=None, lock_experiment=False):
    global CAP, LOG, OBSERVER, LEDGER
    if (ledger is None) != (authorized is None):
        raise ValueError('A call ledger and its authorized total must be given together.')
    if ledger is None and (experiment is not None or experiment_cap is not None):
        raise ValueError('An experiment cap needs the cumulative call ledger.')
    opened = None
    if ledger is not None:
        if Path(ledger).suffix.lower() == '.jsonl':
            raise ValueError('JSONL ledgers are no longer accepted (they cannot reserve atomically across processes). '
                             'Create the SQLite ledger with call_ledger.py init --seed <the JSONL file>.')
        from call_ledger import CallLedger, LedgerError
        try:
            opened = CallLedger(ledger, authorized=authorized, experiment=experiment, experiment_cap=experiment_cap,
                                lock_experiment=lock_experiment)
        except LedgerError as error:
            raise ValueError(str(error)) from None
    if LEDGER is not None:
        LEDGER.close()
    CAP, LOG, OBSERVER, LEDGER = int(cap), Path(log), observer, opened


def _notify(event, info):
    if OBSERVER is not None:
        try:
            OBSERVER(event, info)
        except Exception:
            pass  # progress reporting must never affect a call


def usage():
    with _lock:
        out = {'cap': CAP, 'used': _state['calls'], 'remaining': max(0, CAP - _state['calls']), 'stopped': _state['stopped']}
        if LEDGER is not None:
            try:
                cumulative = LEDGER.usage()
            except Exception as error:  # an untrusted ledger allows nothing
                cumulative = {'error': str(error), 'remaining': 0}
            out['cumulative'] = cumulative
            out['remaining'] = min(out['remaining'], cumulative['remaining'])
        return out
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
            reservation = None
            if LEDGER is not None:
                # Raises (no call) when either cap is reached or the ledger cannot be trusted.
                reservation = LEDGER.reserve()
            _state['calls'] += 1
            n = _state['calls']
        started = time.perf_counter()
        outcome, cause = 'ok', None
        _notify('call_started', {'number': n, 'timeout': TIMEOUT, 'prompt_chars': len(prompt)})
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
            seconds = round(time.perf_counter() - started, 2)
            if reservation is not None:
                with _lock:
                    try:
                        LEDGER.finish(reservation, 'completed' if outcome == 'ok' else 'failed', outcome=outcome, seconds=seconds)
                    except Exception:
                        _state['stopped'] = True  # the reservation stays counted (unresolved); stop rather than guess
            _notify('call_finished', {'number': n, 'seconds': seconds, 'outcome': outcome, 'cause': cause})
            with LOG.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps({'call': n, 'reservation': reservation, 'at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                                         'seconds': seconds, 'prompt_chars': len(prompt),
                                         'schema': response_schema is not None, 'outcome': outcome, 'cause': cause}) + '\n')

    generate.supports_response_schema = True
    return generate, {**metadata, 'test_call_cap': CAP}
