"""Separate provider failures from answer-validation rejections, and bound retries.

A provider failure (the model could not be called) always stays an execution
error. A validation rejection (the model replied, but its answer broke a citation,
number, schema or review rule) is recorded with a sanitized reason, retried once
with that reason as feedback, and otherwise becomes a qualified abstention that
never shows the rejected draft. Validators are never relaxed.
"""
import json
import logging

from src.research_pipeline import PipelineError

LOG = logging.getLogger(__name__)
MAX_ATTEMPTS = 2


class ProviderFailure(PipelineError):
    """The model provider call itself failed; never an evidence finding."""

    def __init__(self, cause):
        self.cause = cause
        super().__init__(f'Model provider call failed ({cause}). No answer was accepted; retry later.')


def provider_cause(exc):
    """Coarse, credential-free classification of a provider exception."""
    text = str(exc).lower()
    if any(k in text for k in ('usage limit', 'rate limit', 'quota', '429', 'too many requests')):
        return 'rate_limited'
    if 'timeout' in text or 'timed out' in text or isinstance(exc, TimeoutError):
        return 'timeout'
    return 'provider_error'


def guard_provider(generate):
    """Mark exceptions raised by the provider call so they are never retried as validation."""
    def call(prompt, **kwargs):
        try:
            return generate(prompt, **kwargs)
        except ProviderFailure:
            raise
        except Exception as exc:
            raise ProviderFailure(provider_cause(exc)) from None
    call.supports_response_schema = getattr(generate, 'supports_response_schema', False)
    return call


def describe_rejection(stage, exc):
    """Sanitized reason; never echoes model output or provider payloads."""
    try:
        from jsonschema import ValidationError
    except ImportError:  # pragma: no cover
        ValidationError = ()
    if isinstance(exc, json.JSONDecodeError):
        reason = 'reply was not valid JSON'
    elif ValidationError and isinstance(exc, ValidationError):
        where = '/'.join(str(x) for x in exc.absolute_path) or 'root'
        reason = f'schema rule "{exc.validator}" failed at {where}'
    elif isinstance(exc, (ValueError, KeyError, TypeError)):
        reason = (str(exc) or type(exc).__name__)[:240]
    else:
        reason = type(exc).__name__
    return {'stage': stage, 'type': type(exc).__name__, 'reason': reason}


def feedback_text(rejection):
    return ('AUTOMATED VALIDATION REJECTED THE PREVIOUS ATTEMPT at the ' + rejection['stage']
            + ' stage: ' + rejection['reason'] + '. Follow every output rule exactly: copy quotes '
            'verbatim from the cited passage, put every reported number in its supporting quote, '
            'use only supplied chunk IDs, and keep status consistent with claims. If the passages '
            'cannot answer, return insufficient_evidence.')


def qualified_abstention(query, attempts):
    last = attempts[-1]
    lead = ('No answer is shown because the drafted answer failed automated validation '
            f'{len(attempts)} times (last: {last["stage"]} - {last["reason"][:160]}). '
            'This is not a finding that the evidence is absent; retry or review the sources directly.')
    return {'query': query, 'status': 'insufficient_evidence', 'claims': [], 'limitations': [lead],
            'limitation_support': [], 'answer_scope': 'unavailable', 'answer_lead': lead,
            'generation_method': 'cited-synthesis-v1',
            'validation': {'status': 'rejected', 'attempts': attempts}}
