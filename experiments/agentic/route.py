"""Request handling for POST /api/agentic-research, kept free of HTTP and model loading for testing.

``handle(payload, ...)`` returns (HTTP status, JSON body). The live backend supplies the orchestrator,
the existing IndexedResearch object (for its context check and provenance), the capped generator's
usage() and the progress tracker.
"""
import threading

from agents import MAX_CALLS, MIN_CALLS
from envelope import to_envelope

MAX_QUERY_CHARS = 2000
# One research request at a time. The live backend passes the SAME lock to its baseline
# /api/research handler, so the two modes can never interleave calls under one call budget or
# overwrite each other's progress.
RESEARCH_LOCK = threading.Lock()
_lock = RESEARCH_LOCK


def chart_tool_for(tables, preview):
    """Model-free chart tool. Without a loaded table audit, charts are reported unavailable, not attempted."""
    def tool(query, passages):
        problem = getattr(tables, 'audit_problem', None) if tables is not None else 'No table index is loaded.'
        if problem:
            return {'status': 'unavailable', 'model_calls': 0,
                    'reason': f'Chart evidence is unavailable on this backend: {problem} Text answers are unaffected.'}
        return preview(query, passages, tables, tables.index_sha256)
    return tool


def _check_revision(payload, library):
    """Same contract as the baseline /api/research: validate the revision target BEFORE any model call.

    Returns (revision or None, error response or None). A revision is never silently dropped.
    """
    revision = payload.get('library_revision')
    if revision is None:
        return None, None
    if (library is None or not isinstance(revision, dict) or set(revision) != {'brief_id', 'expected_version'}
            or not isinstance(revision.get('brief_id'), str) or not isinstance(revision.get('expected_version'), str)):
        return None, (400, {'code': 'bad_revision', 'error': 'Invalid revision target (or saved briefs are disabled). No model call was made.'})
    import sqlite3
    from src.brief_store import BriefConflict
    try:
        library.check_current(revision['brief_id'], revision['expected_version'])
    except BriefConflict as error:
        return None, (409, {'code': 'brief_conflict', 'error': f'{error} No model call was made.'})
    except KeyError:
        return None, (404, {'code': 'brief_not_found', 'error': 'Brief not found. No model call was made.'})
    except sqlite3.Error:
        return None, (503, {'code': 'library_unavailable', 'error': 'Saved-work storage unavailable. No model call was made.'})
    return dict(revision), None


def _save(body, library, revision):
    """Save like the baseline: every answer with a result is saved (as a new version when revising)."""
    if library is None or not body.get('result'):
        return body
    import sqlite3
    try:
        saved = library.save(body, **(revision or {}))
        body['library'] = {**saved['library'], 'replayed': False}
    except (sqlite3.Error, OSError, ValueError, TypeError, KeyError):
        # Never discard an accepted answer or encourage a second model call.
        body['library_error'] = ('Answer retained but not saved. Storage may be unavailable or the revision target changed. '
                                 'Export the snapshot or save it again without regenerating.')
    return body


def handle(payload, *, orchestrator, research, usage, top_k, progress=None, library=None, research_only=False):
    if orchestrator is None:
        return 404, {'code': 'agentic_disabled', 'error': 'Multi-agent research is not enabled. Start the live backend with --agentic.'}
    if not isinstance(payload, dict):
        return 400, {'code': 'bad_request', 'error': 'Send a JSON object.'}
    if payload.get('history') not in (None, []):
        return 400, {'code': 'bad_request', 'error': 'Indexed queries are independent; client history is not accepted.'}
    query, industry = payload.get('query'), payload.get('industry')
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_QUERY_CHARS:
        return 400, {'code': 'bad_request', 'error': 'Enter a question up to 2000 characters.'}
    if industry is not None and (not isinstance(industry, str) or len(industry) > 300):
        return 400, {'code': 'bad_request', 'error': 'Industry must be text up to 300 characters.'}
    if payload.get('risk_assessment'):
        return 400, {'code': 'unsupported', 'error': 'Risk and compliance assessment is not available in multi-agent mode yet. Turn it off or use Baseline RAG.'}
    if research_only and isinstance(industry, str) and industry.strip():
        return 400, {'code': 'research_only', 'error': 'This run is research-only; remove the industry. No model call was made.'}
    try:
        research.check_context(payload.get('context_id'))
    except Exception as error:
        return 409, {'code': 'indexed_context_changed', 'error': str(error)}
    revision, refusal = _check_revision(payload, library)
    if refusal is not None:
        return refusal
    use = usage()
    if use['stopped'] or use['remaining'] < MIN_CALLS:
        cumulative = use.get('cumulative') or {}
        detail = (f"; cumulative authorization {cumulative['used']} of {cumulative['authorized']} used" if 'authorized' in cumulative
                  else f"; call ledger unavailable ({cumulative['error']})" if 'error' in cumulative else '')
        return 429, {'code': 'call_budget', 'error':
                     ('Generation stopped after a provider error; restart with a new approved budget.' if use['stopped'] else
                      f"Multi-agent research needs at least {MIN_CALLS} approved model calls; {use['remaining']} left{detail}.")
                     + ' No model call was made.'}
    if not _lock.acquire(blocking=False):
        return 409, {'code': 'busy', 'error': 'Another research request (baseline or multi-agent) is running. Wait for it to finish.'}
    if progress is not None:
        progress.begin(mode='agentic', max_calls=MAX_CALLS)
    failed = True
    try:
        agentic = orchestrator.run(query, industry=industry or None)
        try:
            # The index must be the one the run started with: never return evidence from a changed index.
            research.check_context(payload.get('context_id'))
        except Exception as error:
            return 409, {'code': 'indexed_context_changed', 'error': f'{error} No answer was accepted.'}
        body = to_envelope(agentic, top_k=top_k, provenance=research.provenance, context_id=research.context_id)
        failed = body['result'] is None
        return 200, _save(body, library, revision)
    except Exception:
        return 500, {'code': 'agentic_failed', 'error': 'The multi-agent run failed unexpectedly. No answer was accepted.'}
    finally:
        if progress is not None:
            progress.end(failed=failed)
        _lock.release()
