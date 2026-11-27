"""Shared quality review for Standard and Deep Research: one model call.

Foundation: src.answer_quality (Improved Baseline's review, policy text reused unchanged as POLICY). The extension
stays inside the same call:
  - quotes_entail: ALCE-style citation recall judged against the claim's ATTACHED quotes (plus any added_support),
    not the full passage. The full passages are context only. (combined-v1 G03-C F1: the Multi-Agent verifier read
    the whole passage and accepted a fact that was not in the attached quote.)
  - supported_text: FActScore-style partial retention. If only some facts of a claim are entailed, the reviewer
    returns a reduced claim with only those facts; it is re-checked deterministically before publication.
  - added_support: up to 2 exact quotes from passages already in the evidence, to attach a fact the drafter used but
    did not quote (combined-v1 G03-B F2: Table 7 rows were in the evidence but not cited). Checked for membership.
  - flag_resolutions: the deterministic number checker's attribution flags are shown per claim; a flag is cleared
    only by an exact quote span that states the number, checked deterministically (see publication.py).
Parsing is per decision: a missing, duplicate or invalid decision withholds only that claim. A reply that is not a
JSON object fails the stage (nothing is published; the checkpoint keeps the synthesis for a resume).
"""
from copy import deepcopy
import json

from jsonschema import Draft202012Validator

from src.answer_quality import POLICY
from synthesis import _obj, _strict_loads, norm, quote_problems, support_schema

EXTENSION = (
    'CONSOLIDATED REVIEW EXTENSION (applies with the policy above; where they differ, this extension wins). '
    'This schema has no retained_claim_indices field: retention is computed from your decisions. '
    'For EVERY claim also decide quotes_entail: true only if the claim\'s ATTACHED quotes, plus any added_support you '
    'give, together state every fact in the claim, including every number, model or dataset name, metric, condition '
    'and qualifier. The full passages are context for reading the quotes, not a substitute for them: a fact that is '
    'elsewhere in a passage counts only if you attach it as added_support (an exact substring of a passage in the '
    'evidence, at most 2 per claim). If only part of a claim is entailed, set supported_text to a rewrite that keeps '
    'ONLY the entailed facts, copying numbers exactly; never add facts, never strengthen wording; otherwise set '
    'supported_text to an empty string. A claim may carry deterministic_flags from the number checker, which can '
    'misread subjects in long sentences. For each flag, either show it is a false alarm with a flag_resolution whose '
    'quote is an exact span of the attached or added quotes stating that number for the claim\'s subject, metric and '
    'condition, or treat the flagged part as unsupported (remove it in supported_text, or reject the claim). '
    'For an interpretation, quotes_entail refers to its factual premises. Rebuild limitations as the policy says. '
    'Return only JSON matching the schema.\n')


def review_schema(ids, count):
    support = support_schema(ids)
    decision = _obj({
        'index': {'type': 'integer', 'minimum': 0, 'maximum': max(count - 1, 0)},
        'supported': {'type': 'boolean'}, 'relevant': {'type': 'boolean'}, 'quotes_entail': {'type': 'boolean'},
        'reason': {'type': 'string', 'minLength': 1, 'maxLength': 600},
        'supported_text': {'type': 'string', 'maxLength': 600},
        'added_support': {'type': 'array', 'maxItems': 2, 'items': support},
        'flag_resolutions': {'type': 'array', 'maxItems': 8, 'items': _obj({
            'number': {'type': 'string', 'maxLength': 40},
            'quote': {'type': 'string', 'minLength': 1, 'maxLength': 600},
            'reason': {'type': 'string', 'maxLength': 300}})}})
    limitation = _obj({'text': {'type': 'string', 'minLength': 1, 'maxLength': 600},
                       'support': {'type': 'array', 'minItems': 1, 'maxItems': 4, 'items': support}})
    return _obj({'coverage': {'type': 'string', 'enum': ['full', 'partial', 'none']},
                 'gap': {'type': 'string', 'maxLength': 300},
                 'decisions': {'type': 'array', 'maxItems': max(count, 0), 'items': decision},
                 'limitations': {'type': 'array', 'maxItems': 6, 'items': limitation}}), decision, limitation


def build_prompt(question, summary, passages, notes, flags):
    draft = {'claims': [{'index': i, 'text': c['text'], 'kind': c['kind'], 'support': c['support'],
                         'deterministic_flags': flags.get(i, [])} for i, c in enumerate(summary['claims'])],
             'limitations': summary.get('limitation_support', [])}
    payload = {'question': question, 'evidence_notes': [n['text'] for n in notes], 'draft': draft,
               'passages': [{k: v for k, v in p.items() if k != 'reader'} for p in passages]}
    return POLICY + EXTENSION + json.dumps(payload, ensure_ascii=False)


def parse(raw, summary, passages):
    """Returns (review, report). Raises only when the reply is not a JSON object."""
    claims = summary['claims']
    ids = sorted(p['chunk_id'] for p in passages)
    _schema, decision_schema, limitation_schema = review_schema(ids, len(claims))
    texts = {p['chunk_id']: norm(p['text']) for p in passages}
    reply = _strict_loads(raw)
    if not isinstance(reply, dict):
        raise ValueError('Review reply is not a JSON object.')
    report = {'withheld_no_decision': [], 'invalid_decisions': [], 'duplicate_decisions': [], 'repairs': [],
              'dropped_limitations': []}
    decisions, seen = {}, set()
    for position, decision in enumerate(reply.get('decisions') or []):
        errors = list(Draft202012Validator(decision_schema).iter_errors(decision))
        if errors:
            report['invalid_decisions'].append({'position': position, 'error': errors[0].message[:160]})
            continue
        index = decision['index']
        if index in seen:
            report['duplicate_decisions'].append(index)
            decisions.pop(index, None)  # ambiguous: withhold the claim rather than pick one decision
            continue
        seen.add(index)
        decisions[index] = deepcopy(decision)
    for index in range(len(claims)):
        if index not in decisions:
            report['withheld_no_decision'].append(index)
    coverage, gap = reply.get('coverage'), reply.get('gap') if isinstance(reply.get('gap'), str) else ''
    if coverage not in ('full', 'partial', 'none'):
        report['repairs'].append(f'invalid coverage {coverage!r} treated as partial')
        coverage = 'partial'
    if coverage == 'full' and gap.strip():
        report['repairs'].append('full coverage with a gap treated as partial')
        coverage = 'partial'
    if coverage != 'full' and not gap.strip():
        gap = 'The reviewer did not name the unanswered part.'
        report['repairs'].append('missing gap text filled with a neutral note')
    limitations = []
    raw_limits = reply.get('limitations')
    if not isinstance(raw_limits, list):
        report['repairs'].append('no limitations list; the validated draft limitations are kept')
        raw_limits = summary.get('limitation_support', [])
    for position, item in enumerate(raw_limits):
        errors = list(Draft202012Validator(limitation_schema).iter_errors(
            {k: v for k, v in item.items() if k in ('text', 'support')} if isinstance(item, dict) else item))
        if errors or quote_problems(item, texts):
            report['dropped_limitations'].append({'position': position,
                                                  'reason': errors[0].message[:160] if errors else 'quote not found'})
            continue
        item = {'text': item['text'], 'support': deepcopy(item['support'])}
        item['chunk_ids'] = list(dict.fromkeys(s['chunk_id'] for s in item['support']))
        limitations.append(item)
    return {'coverage': coverage, 'gap': gap[:300], 'decisions': decisions, 'limitations': limitations}, report


def review(question, summary, passages, notes, flags, *, generate):
    """One model call (skipped when there is nothing to review). Returns (review, report, raw)."""
    if not summary['claims']:
        return ({'coverage': 'none', 'gap': 'No claim could be drafted from the supplied passages.', 'decisions': {},
                 'limitations': deepcopy(summary.get('limitation_support', []))},
                {'skipped': 'no claims to review'}, None)
    ids = sorted(p['chunk_id'] for p in passages)
    schema = review_schema(ids, len(summary['claims']))[0]
    raw = generate(build_prompt(question, summary, passages, notes, flags), response_schema=schema)
    result, report = parse(raw, summary, passages)
    return result, report, raw
