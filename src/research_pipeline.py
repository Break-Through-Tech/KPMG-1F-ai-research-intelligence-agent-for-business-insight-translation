"""Research workflow v1. Adapters are injected; importing this module is offline."""
from copy import deepcopy
from hashlib import sha256
import json

from src.research_contracts import (
    SCHEMA_VERSION, validate_request, validate_evidence, validate_result,
    validate_summary, validate_business_insight, validate_output as _validate_output,
)


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


_LEGACY_FINGERPRINT_FIELDS = (
    'schema_version', 'request', 'evidence', 'summary', 'business_insight',
    'provenance', 'regulatory_checkpoint',
)
_REVIEW_FINGERPRINT_VERSION = 2

def content_fingerprint(result):
    """Hash versioned review content; preserve validation of saved v1 results."""
    version = result.get('review_fingerprint_version', 1)
    if version == 1:
        # Exact historical projection, including nulls for absent optional fields.
        content = {k: result.get(k) for k in _LEGACY_FINGERPRINT_FIELDS}
    elif version == _REVIEW_FINGERPRINT_VERSION:
        content = {k: v for k, v in result.items()
                   if k not in {'human_review', 'approved', 'review_fingerprint',
                                'review_fingerprint_version'}}
    else:
        raise ValueError('Unsupported review fingerprint version')
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
    request = validate_request(request)
    k = request['top_k']
    if translate_fn is not None and not _text(request.get('industry')):
        raise ValueError('Business mode requires explicit industry context')
    passages = deepcopy(_stage('Retrieval', retrieve, request['query'], k))
    ids = validate_evidence(passages)
    if passages:
        summary = deepcopy(_stage('Summary', summarize_fn, request['query'], deepcopy(passages)))
        validate_summary(summary, ids, query=request['query'])
    else:
        summary = {'status': 'insufficient_evidence', 'query': request['query'],
                   'claims': [], 'limitations': ['No passages retrieved; generation skipped.']}
    result = {'schema_version': SCHEMA_VERSION, 'review_fingerprint_version': _REVIEW_FINGERPRINT_VERSION,
              'request': request, 'evidence': passages,
              'summary': summary, 'human_review': {'status': 'pending', 'reviewer': None,
                                                 'notes': None}, 'approved': False,
              'provenance': deepcopy(provenance or {})}
    if translate_fn is not None:
        if summary['status'] == 'ok':
            business = deepcopy(_stage('Business translation', translate_fn, deepcopy(summary),
                                      deepcopy(passages), industry=request['industry']))
            validate_business_insight(business, ids, industry=request['industry'])
        else:
            business = {'status': 'insufficient_evidence', 'industry': request['industry'],
                        'implications': [], 'risks': [],
                        'limitations': ['No supported summary available; translation skipped.']}
        result['business_insight'] = business
    if review_fn is not None:
        result['regulatory_checkpoint'] = deepcopy(_stage('Review checkpoint', review_fn,
                                                         deepcopy(result)))
    validate_result(result)
    result['review_fingerprint'] = content_fingerprint(result)
    return result
