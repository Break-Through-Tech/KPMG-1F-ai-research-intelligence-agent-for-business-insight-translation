"""Research workflow v1. Adapters are injected; importing this module is offline."""
from copy import deepcopy
from hashlib import sha256
import json


class PipelineError(RuntimeError):
    """An actionable stage failure, safe for CLI display."""


def _stage(name, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except PipelineError:
        raise
    except Exception as exc:
        # Provider exceptions can contain request bodies/credentials: don't echo them.
        raise PipelineError(f"{name} failed ({type(exc).__name__}). Check the adapter, "
                            "local configuration and provider access; no result was approved.") from None


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _validate_output(output, field, ids):
    if not isinstance(output, dict) or output.get('status') not in {'ok', 'insufficient_evidence'}:
        raise ValueError('Adapter must return status ok or insufficient_evidence')
    rows = output.get(field)
    if not isinstance(rows, list) or (output['status'] == 'ok' and not rows):
        raise ValueError(f'Adapter must return {field}; ok requires at least one item')
    if not isinstance(output.get('limitations'), list) or not all(
            isinstance(x, str) for x in output['limitations']):
        raise ValueError('Adapter limitations must be a list of strings')
    for row in rows:
        if not isinstance(row, dict) or not _text(row.get('text')):
            raise ValueError('Each claim/implication requires text')
        citations = row.get('chunk_ids')
        if not isinstance(citations, list) or not citations or any(
                not isinstance(x, str) or x not in ids for x in citations):
            raise ValueError('Every claim/implication must cite known evidence chunk IDs')
        if field == 'implications' and (not _text(row.get('suggested_action')) or
                not isinstance(row.get('assumptions'), list) or
                not all(isinstance(x, str) for x in row['assumptions'])):
            raise ValueError('Business implications require suggested_action and assumptions')
    if field == 'implications' and (not isinstance(output.get('risks'), list) or
            not all(isinstance(x, str) for x in output['risks'])):
        raise ValueError('Business risks must be a list of strings')


def content_fingerprint(result):
    """Bind reviews to inputs, source content, outputs, and execution versions."""
    content = {k: result.get(k) for k in (
        'schema_version', 'request', 'evidence', 'summary', 'business_insight', 'provenance',
        'regulatory_checkpoint')}
    return sha256(json.dumps(content, sort_keys=True, allow_nan=False).encode()).hexdigest()


def require_current_review(result):
    if result.get('review_fingerprint') != content_fingerprint(result):
        raise ValueError('Research inputs or outputs changed; obtain a new human review')


def run_research(request, *, retrieve, summarize_fn, translate_fn=None, review_fn=None,
                 provenance=None):
    """Run a fresh workflow. Existing/model approval is never carried into a new run.

    summarize_fn(query, passages); translate_fn(summary, passages, *, industry).
    review_fn receives a defensive copy of the complete draft; its returned advisory
    checkpoint is separate from human approval. #81 owns explicit human review.
    """
    request = deepcopy(request)
    if not isinstance(request, dict) or not _text(request.get('query')):
        raise ValueError('query must be nonempty text')
    request.setdefault('top_k', 5)
    k = request['top_k']
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError('top_k must be a positive integer')
    for key in ('industry', 'jurisdiction'):
        if key in request and not _text(request[key]):
            raise ValueError(f'{key} must be nonempty text when supplied')
    if translate_fn is not None and not _text(request.get('industry')):
        raise ValueError('Business mode requires explicit industry context')
    passages = deepcopy(_stage('Retrieval', retrieve, request['query'], k))
    if not isinstance(passages, list):
        raise ValueError('Retrieval must return a list of evidence passages')
    ids = set()
    for p in passages:
        if not isinstance(p, dict) or not _text(p.get('chunk_id')) or not _text(p.get('text')):
            raise ValueError('Evidence requires chunk_id and text')
        if p['chunk_id'] in ids:
            raise ValueError('Duplicate evidence chunk IDs')
        ids.add(p['chunk_id'])
    if passages:
        summary = deepcopy(_stage('Summary', summarize_fn, request['query'], deepcopy(passages)))
        _validate_output(summary, 'claims', ids)
        if summary.get('query') != request['query']:
            raise ValueError('Summary query does not match the request')
    else:
        summary = {'status': 'insufficient_evidence', 'query': request['query'],
                   'claims': [], 'limitations': ['No passages retrieved; generation skipped.']}
    result = {'schema_version': '1.0', 'request': request, 'evidence': passages,
              'summary': summary, 'human_review': {'status': 'pending', 'reviewer': None,
                                                 'notes': None}, 'approved': False,
              'provenance': deepcopy(provenance or {})}
    if translate_fn is not None:
        if summary['status'] == 'ok':
            business = deepcopy(_stage('Business translation', translate_fn, deepcopy(summary),
                                      deepcopy(passages), industry=request['industry']))
            _validate_output(business, 'implications', ids)
            if business.get('industry') != request['industry']:
                raise ValueError('Business industry does not match the request')
        else:
            business = {'status': 'insufficient_evidence', 'industry': request['industry'],
                        'implications': [], 'risks': [],
                        'limitations': ['No supported summary available; translation skipped.']}
        result['business_insight'] = business
    if review_fn is not None:
        result['regulatory_checkpoint'] = deepcopy(_stage('Review checkpoint', review_fn,
                                                         deepcopy(result)))
    result['review_fingerprint'] = content_fingerprint(result)
    return result
