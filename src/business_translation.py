"""Offline-importable business translation adapter using the #79 baseline prompt.

Boundary: translate(summary, passages, *, industry, generate). The injected
generator takes prompt text and returns JSON text. Structural validation cannot
establish semantic support, business value, or human approval.
"""
from hashlib import sha256
import json
from pathlib import Path
from string import Template

from src.research_pipeline import PipelineError, _validate_output

PROMPT_ID = 'business-translation/baseline'
PROMPT_VERSION = '1.0'
PROMPT_PATH = Path(__file__).resolve().parents[1] / 'prompts/business_translation/baseline-v1.txt'
BUSINESS_KEYS = {'status', 'industry', 'implications', 'risks', 'limitations'}
IMPLICATION_KEYS = {'text', 'chunk_ids', 'suggested_action', 'assumptions'}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value, field):
    if not isinstance(value, list) or not all(_text(item) for item in value):
        raise ValueError(f'{field} must be an array of nonempty strings')


def _citations(value, ids):
    if (not isinstance(value, list) or not value or
            any(not _text(item) or item not in ids for item in value) or
            len(set(value)) != len(value)):
        raise ValueError('Citations must contain unique known evidence chunk IDs')


def _abstain(industry, limitations):
    return {'status': 'insufficient_evidence', 'industry': industry,
            'implications': [], 'risks': [], 'limitations': limitations}


def prompt_provenance():
    """Optional artifact metadata; no keys, provider calls, or input data."""
    try:
        template = PROMPT_PATH.read_bytes()
    except OSError:
        raise PipelineError('Business translation prompt unavailable; restore the '
                            'versioned baseline-v1.txt artifact.') from None
    return {'prompt_id': PROMPT_ID, 'prompt_version': PROMPT_VERSION,
            'template_sha256': sha256(template).hexdigest()}


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON object key')
        result[key] = value
    return result


def _nonfinite(value):
    raise ValueError('Nonfinite JSON value')


def _business(output, *, industry, ids):
    if not isinstance(output, dict) or set(output) != BUSINESS_KEYS:
        raise ValueError('Business response must contain exactly the BusinessInsight fields')
    if not isinstance(output['status'], str):
        raise ValueError('Business status must be ok or insufficient_evidence')
    _validate_output(output, 'implications', ids)
    if output['industry'] != industry:
        raise ValueError('Business industry does not match the supplied context')
    for field in ('risks', 'limitations'):
        _strings(output[field], field)
    if output['status'] == 'insufficient_evidence':
        if output['implications'] or not output['limitations']:
            raise ValueError('Abstention requires empty implications and explicit limitations')
    for row in output['implications']:
        if set(row) != IMPLICATION_KEYS:
            raise ValueError('Implications must contain exactly text, chunk_ids, '
                             'suggested_action, and assumptions')
        _citations(row['chunk_ids'], ids)
        _strings(row['assumptions'], 'assumptions')
    return output


def translate(summary, passages, *, industry, generate):
    """Render the versioned baseline and validate a pending business-advisory draft.

    No evidence or an insufficient summary skips generation. Conflicting evidence
    is passed intact to the prompt, which requires bounded disagreement and both
    citations; semantic conflict detection/source support remain human checks.
    Inputs are serialized without modification. Unknown/duplicate citations,
    extra output fields (including approval/confidence), and malformed JSON fail.
    """
    if not _text(industry):
        raise ValueError('Business translation requires explicit nonempty industry context')
    if not callable(generate):
        raise ValueError('generate must be a callable returning JSON text')
    if not isinstance(passages, list):
        raise ValueError('Evidence must be a list of passages')
    ids = set()
    for passage in passages:
        if (not isinstance(passage, dict) or not _text(passage.get('chunk_id')) or
                not _text(passage.get('text'))):
            raise ValueError('Each evidence passage requires nonempty chunk_id and text')
        if passage['chunk_id'] in ids:
            raise ValueError('Duplicate evidence chunk IDs')
        ids.add(passage['chunk_id'])
    if (not isinstance(summary, dict) or not isinstance(summary.get('status'), str) or
            summary['status'] not in {'ok', 'insufficient_evidence'} or
            not _text(summary.get('query'))):
        raise ValueError('Summary requires status and a nonempty query')
    _strings(summary.get('limitations'), 'Summary limitations')
    claims = summary.get('claims')
    if not isinstance(claims, list) or (summary['status'] == 'ok' and not claims):
        raise ValueError('Summary requires claims; ok requires at least one claim')
    if summary['status'] == 'insufficient_evidence' and claims:
        raise ValueError('Insufficient summary must have empty claims')
    for claim in claims:
        if not isinstance(claim, dict) or not _text(claim.get('text')):
            raise ValueError('Summary claims require nonempty text')
        # With no retrieved evidence, abstain rather than attempting translation.
        if ids:
            _citations(claim.get('chunk_ids'), ids)
        elif not isinstance(claim.get('chunk_ids'), list) or not claim['chunk_ids']:
            raise ValueError('Summary claims require chunk_ids')
    if not passages:
        return _abstain(industry, ['No evidence passages supplied; translation skipped.'])
    if summary['status'] == 'insufficient_evidence':
        return _abstain(industry, summary['limitations'] +
                        ['No supported summary available; translation skipped.'])
    try:
        prompt = Template(PROMPT_PATH.read_text(encoding='utf-8')).substitute(
            industry=industry,
            summary_json=json.dumps(summary, allow_nan=False),
            evidence_json=json.dumps(passages, allow_nan=False))
    except (OSError, UnicodeError, KeyError):
        raise PipelineError('Business translation prompt unavailable or invalid; '
                            'restore the versioned baseline-v1.txt artifact.') from None
    except (TypeError, ValueError):
        raise ValueError('Summary and evidence must contain finite JSON-compatible data') from None
    try:
        raw = generate(prompt)
    except Exception:
        # Even an injected provider's PipelineError can contain credentials.
        raise PipelineError('Business translation generation failed; check local '
                            'provider configuration and access. No result was approved.') from None
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError('Business translation provider must return nonempty JSON text')
    try:
        output = json.loads(raw, object_pairs_hook=_object, parse_constant=_nonfinite)
    except (ValueError, RecursionError):
        raise ValueError('Business translation provider returned malformed JSON; '
                         'return one strict JSON object without markdown or duplicate keys') from None
    return _business(output, industry=industry, ids=ids)
