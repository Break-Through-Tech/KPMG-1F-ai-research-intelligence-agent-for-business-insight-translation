"""Semantic business-intent classification: one Flash-Lite call per new research question.

The classifier reads only the question. It runs beside research and never feeds into it. Its output is
untrusted: every field is validated against the original question before use. Any failure (provider,
budget, timeout, schema or validation) yields a recorded failure, and the deterministic rules in
src.business_insights take over. Prompt: prompts/business_intent/semantic-v1.txt, piloted unchanged.
"""
import json
import re
from hashlib import sha256
from pathlib import Path
from string import Template

PROMPT = Path(__file__).resolve().parents[1] / 'prompts/business_intent/semantic-v1.txt'
VERSION = 'semantic-v1'
SECTORS = ('financial services', 'banking', 'insurance', 'healthcare', 'pharmaceuticals', 'logistics', 'retail',
           'manufacturing', 'telecommunications', 'legal', 'accounting', 'energy', 'aviation', 'hospitality',
           'government', 'education', 'transportation', 'real estate', 'media', 'agriculture', 'construction',
           'automotive', 'software', 'unspecified')
CONTEXT_SCHEMA = {'type': 'object', 'additionalProperties': False,
                  'properties': {'is_business': {'type': 'boolean'},
                                 'industry': {'type': 'string', 'enum': list(SECTORS)},
                                 'workflow': {'type': 'string'}, 'decision': {'type': 'string'},
                                 'confidence': {'type': 'string', 'enum': ['high', 'medium', 'low']}},
                  'required': ['is_business', 'industry', 'workflow', 'decision', 'confidence']}
SCHEMA = {'type': 'object', 'additionalProperties': False, 'properties': {'business_context': CONTEXT_SCHEMA},
          'required': ['business_context']}
ACCEPTED_CONFIDENCE = {'high', 'medium'}


def _norm(text):
    return ' '.join(str(text).split()).casefold()


def _span(value, question, limit):
    """Return the value only when it is a verbatim span of the question (case/whitespace-insensitive)."""
    value = ' '.join(value.split()).strip(' ?.,;:') if isinstance(value, str) else ''
    if not value or len(value) > limit or _norm(value) not in _norm(question):
        return ''
    return value


def build_prompt(question):
    return Template(PROMPT.read_text(encoding='utf-8')).substitute(
        question_json=json.dumps({'question': question}, ensure_ascii=False))


def validate(raw, question):
    """Validate model output against the question. Returns a clean dict or raises ValueError."""
    data = json.loads(raw) if isinstance(raw, str) else raw
    value = data.get('business_context') if isinstance(data, dict) else None
    if not isinstance(value, dict) or set(value) != set(CONTEXT_SCHEMA['required']):
        raise ValueError('schema')
    if not isinstance(value['is_business'], bool) or value['industry'] not in SECTORS \
            or value['confidence'] not in {'high', 'medium', 'low'}:
        raise ValueError('schema')
    return {'is_business': value['is_business'], 'industry': value['industry'],
            # Anything not literally in the question is dropped, never repaired.
            'workflow': _span(value['workflow'], question, 600), 'decision': _span(value['decision'], question, 600),
            'workflow_rejected': bool(value['workflow']) and not _span(value['workflow'], question, 600),
            'confidence': value['confidence']}


def classify(question, generate):
    """One attempt, no retry. Returns a sanitized record that is safe to store with the answer."""
    record = {'version': VERSION, 'prompt_sha256': sha256(PROMPT.read_bytes()).hexdigest()}
    try:
        raw = generate(build_prompt(question), response_schema=SCHEMA)
    except Exception as error:  # isolated: research is unaffected
        name = type(error).__name__
        return {**record, 'status': 'unavailable', 'reason': 'local_budget' if name == 'QuotaExhausted' else 'provider'}
    try:
        return {**record, 'status': 'ok', 'value': validate(raw, question)}
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return {**record, 'status': 'invalid', 'reason': 'validation'}


def trusted_value(record, question):
    """Re-validate a stored record (it travels inside the saved envelope) before relying on it."""
    if not isinstance(record, dict) or record.get('status') != 'ok' or record.get('version') != VERSION:
        return None
    value = record.get('value')
    try:
        clean = validate({'business_context': {k: value[k] for k in CONTEXT_SCHEMA['required']}}, question)
    except (ValueError, TypeError, KeyError):
        return None
    return clean
