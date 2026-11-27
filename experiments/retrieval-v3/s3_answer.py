"""S3 synthesis C: component-complete synthesis, semantic component check and coverage validator (no extra calls).

The frozen V2 modules are imported and used unchanged: synthesis.parse / synthesis_schema / build_prompt,
review.parse / review_schema / build_prompt and publication.publish (P1-P5, V1-V5, interpretation gate, limitation
checks). S3 only ADDS:

  synthesis  The deterministic component list is appended to V2's prompt, and the reply carries a component_map
             (each component: answered by claim indices | not_established with a cited scope limitation |
             not_retrieved). The map is removed before V2's own parser sees the reply.
  review     The same review call also returns component_checks: for each component, whether the claims it names
             actually answer it (semantic check by the reviewer; a mapping alone proves nothing), or which rebuilt
             limitation's OWN quotes show the study's scope excludes it.
  validator  Deterministic, after V2 publication:
               answered/partial  only if the reviewer said so AND at least one claim it named was PUBLISHED as a
                                 finding (held or unpublished claims never count)
               not_established   only if the reviewer named a limitation that was PUBLISHED (so it passed exact-quote
                                 and number-recall gates); otherwise downgraded to not_retrieved
               not_retrieved     everything else; rendered from a fixed template that is explicitly about the
                                 retrieved evidence, never about the paper
             Coverage entries are display metadata only: they never add claims, citations or limitations.
  lead guard The uncited answer lead (V2: the reviewer's gap text) may not assert what a paper, study or its
             authors do not report/establish unless it is scoped to the supplied/retrieved evidence. Otherwise it is
             replaced by a fixed neutral sentence. Nothing uncited can assert absence from a paper.
"""
from copy import deepcopy
import json
import re

import s3_env  # noqa: F401
import publication  # frozen V2
import review as rv  # frozen V2
import synthesis as syn  # frozen V2

STATUSES = ('answered', 'not_established', 'not_retrieved')
VERDICTS = ('answered', 'partial', 'not_established', 'not_retrieved')

SYNTHESIS_EXTENSION = (
    '\nREQUESTED COMPONENTS (S3). The question has been split deterministically into the numbered COMPONENTS below. '
    'Cover EVERY component before adding detail. For each component, report every detail the passages give for it '
    '(values with their conditions, examples, named items and qualifiers), each in a finding that follows all rules '
    'above. Then fill component_map with exactly one entry per component: '
    'status "answered" with the indices (0-based, in your claims array) of the findings that answer it; '
    'status "not_established" ONLY when a passage states the study\'s own scope or limitation that excludes the '
    'component (for example: evaluated only on its own database; experiments only on one model; reports model size, '
    'not cost) - then write a cited limitation that quotes that scope and says the passages do not establish the '
    'requested item, and give its index in limitation_indices; '
    'status "not_retrieved" when the supplied passages do not address the component. Never write that a paper, study '
    'or its authors do not report or establish something unless a quote states that scope; absence from the supplied '
    'passages is not absence from the paper. Use empty index lists where none apply.\n')

REVIEW_EXTENSION = (
    '\nCOMPONENT CHECK (S3, same reply). COMPONENTS lists the parts of the question and the drafter\'s component_map. '
    'For EVERY component return one component_checks entry. verdict "answered" only if the claims you list (indices in '
    'the draft claims array) are claims you judged supported and together actually answer that component; "partial" '
    'if they answer part of it; "not_established" only if one of YOUR rebuilt limitations (give its index in your '
    'limitations array) has OWN quotes stating the study\'s scope or limitation that excludes the component; '
    'otherwise "not_retrieved". A mapping by the drafter is not evidence: judge the content. Keep reasons short. '
    'The gap must describe what is missing from the SUPPLIED PASSAGES, never claim what a paper does not contain.\n')

_ABSENCE = re.compile(
    r"\b(?:the|this|that|these|those|both|its|their|either|neither|each)\s+"
    r"(?:paper|papers|study|studies|survey|surveys|authors?|article|articles|work|benchmark|source|sources)\b"
    r"[^.;]{0,40}?\b(?:does|do|did|has|have|is|are|was|were)\s*n[o']t\b"
    r"|\bnot\s+(?:reported|provided|mentioned|given|stated|included|evaluated|measured|studied|discussed)\s+"
    r"(?:in|by|anywhere in)\s+(?:the|this|these|any)\s+(?:paper|papers|study|studies|survey|authors?|literature)\b"
    r"|\b(?:paper|papers|study|studies|survey|authors?)\s+(?:lacks?|omits?|never)\b"
    r"|\b(?:neither|no(?:ne of the)?)\s+(?:paper|papers|study|studies|survey|surveys|authors?|source|sources)\b",
    re.I)
_SCOPED = re.compile(r'\b(?:supplied|retrieved|provided|available|these)\s+(?:passages?|evidence|excerpts?)\b', re.I)
NEUTRAL_LEAD = ('Some requested components were not found in the retrieved evidence; this does not mean the papers '
                'do not report them.')
NOT_RETRIEVED_NOTE = ('Not found in the retrieved evidence: {component} This does not mean the paper does not '
                      'report it.')


def asserts_paper_absence(text):
    """True when text claims something is absent from a paper/study/its authors without scoping that claim to the
    supplied or retrieved evidence."""
    # Clause by clause: a scoped clause does not excuse an unscoped absence claim elsewhere in the text.
    return any(_ABSENCE.search(c) and not _SCOPED.search(c) for c in re.split(r'[.;:]\s+|\n', text or ''))


# ---------------------------------------------------------------- synthesis

def _ints(maximum):
    return {'type': 'array', 'maxItems': 12, 'items': {'type': 'integer', 'minimum': 0, 'maximum': maximum}}


def component_map_schema(n_components):
    entry = syn._obj({'component': {'type': 'integer', 'minimum': 0, 'maximum': max(n_components - 1, 0)},
                      'status': {'type': 'string', 'enum': list(STATUSES)},
                      'claim_indices': _ints(syn.MAX_FINDINGS + 2),
                      'limitation_indices': _ints(syn.MAX_LIMITATIONS - 1)})
    return {'type': 'array', 'maxItems': max(n_components, 0), 'items': entry}


def synthesis_schema(ids, n_components):
    schema = syn.synthesis_schema(ids)
    if n_components:
        schema['properties']['component_map'] = component_map_schema(n_components)
        schema['required'] = list(schema['properties'])
    return schema


def build_synthesis_prompt(question, passages, notes, comps):
    prompt = syn.build_prompt(question, passages, notes)
    if not comps:
        return prompt
    listing = json.dumps({'components': [{'index': i, 'text': c} for i, c in enumerate(comps)]}, ensure_ascii=False)
    return prompt + SYNTHESIS_EXTENSION + listing


def split_reply(raw, field):
    """Remove an S3-only field from a JSON reply so the frozen V2 parser sees exactly the V2 contract."""
    obj = syn._strict_loads(raw)
    if not isinstance(obj, dict):
        return raw, None
    extra = obj.pop(field, None)
    return json.dumps(obj, ensure_ascii=False), extra


def parse_entries(entries, n_components, schema_item, report, label):
    from jsonschema import Draft202012Validator
    out = {}
    for position, entry in enumerate(entries if isinstance(entries, list) else []):
        errors = list(Draft202012Validator(schema_item).iter_errors(entry))
        if errors:
            report.append({'field': label, 'position': position, 'error': errors[0].message[:160]})
            continue
        if entry['component'] in out:  # ambiguous: drop both, the component falls back to not_retrieved
            report.append({'field': label, 'position': position, 'error': 'duplicate component'})
            out[entry['component']] = None
            continue
        out[entry['component']] = deepcopy(entry)
    return {k: v for k, v in out.items() if v is not None and k < n_components}


def synthesize(question, passages, notes, comps, *, generate, findings_only=False):
    """One model call, as V2. Returns (summary, report, raw); summary gains 'component_map' (by draft index)."""
    if not passages:
        summary, report, raw = syn.synthesize(question, passages, notes, generate=generate)
        return {**summary, 'component_map': {}}, report, raw
    schema = synthesis_schema(sorted(p['chunk_id'] for p in passages), len(comps))
    if findings_only:
        schema['properties']['claims']['items']['properties']['kind']['enum'] = ['finding']
    raw = generate(build_synthesis_prompt(question, passages, notes, comps), response_schema=schema)
    v2_raw, cmap = split_reply(raw, 'component_map')
    summary, report = syn.parse(v2_raw, passages)
    if findings_only:
        summary['claims'] = [c for c in summary['claims'] if c['kind'] == 'finding']
    report['component_map_errors'] = []
    item = component_map_schema(len(comps))['items'] if comps else None
    summary['component_map'] = parse_entries(cmap, len(comps), item, report['component_map_errors'],
                                             'component_map') if comps else {}
    return summary, report, raw


# ---------------------------------------------------------------- review

def component_checks_schema(n_components, n_claims):
    entry = syn._obj({'component': {'type': 'integer', 'minimum': 0, 'maximum': max(n_components - 1, 0)},
                      'verdict': {'type': 'string', 'enum': list(VERDICTS)},
                      'claim_indices': _ints(max(n_claims - 1, 0)),
                      'limitation_index': {'type': 'integer', 'minimum': -1, 'maximum': 5},
                      'reason': {'type': 'string', 'maxLength': 240}})
    return {'type': 'array', 'maxItems': max(n_components, 0), 'items': entry}


def review(question, summary, passages, notes, flags, comps, *, generate):
    """One model call, as V2. Returns (review, report, raw); review gains 'component_checks'."""
    v2_summary = {k: v for k, v in summary.items() if k != 'component_map'}
    if not summary['claims'] or not comps:
        result, report, raw = rv.review(question, v2_summary, passages, notes, flags, generate=generate)
        return {**result, 'component_checks': {}}, report, raw
    ids = sorted(p['chunk_id'] for p in passages)
    schema = rv.review_schema(ids, len(summary['claims']))[0]
    schema['properties']['component_checks'] = component_checks_schema(len(comps), len(summary['claims']))
    schema['required'] = list(schema['properties'])
    draft_map = [{'component': i, 'text': c, **{k: v for k, v in (summary['component_map'].get(i) or {}).items()
                                                  if k != 'component'}}
                 for i, c in enumerate(comps)]
    # The drafter's map uses draft indices; the review sees claims by position, so translate.
    position = {c['draft_index']: i for i, c in enumerate(summary['claims'])}
    for entry in draft_map:
        entry['claim_indices'] = [position[d] for d in entry.get('claim_indices', []) if d in position]
    prompt = (rv.build_prompt(question, v2_summary, passages, notes, flags) + REVIEW_EXTENSION
              + json.dumps({'components': draft_map}, ensure_ascii=False))
    raw = generate(prompt, response_schema=schema)
    v2_raw, checks = split_reply(raw, 'component_checks')
    result, report = rv.parse(v2_raw, v2_summary, passages)
    report['component_check_errors'] = []
    result['component_checks'] = parse_entries(checks, len(comps), schema['properties']['component_checks']['items'],
                                               report['component_check_errors'], 'component_checks')
    return result, report, raw


# ---------------------------------------------------------------- validator and lead guard

def coverage(comps, summary, review_result, published):
    """Deterministic component coverage from the reviewer's semantic checks and what V2 actually published."""
    published_findings = {c.get('draft_index') for c in published['claims'] if c.get('kind') == 'finding'}
    published_limits = {syn.norm(l['text']) for l in published.get('limitation_support', [])}
    rebuilt = review_result.get('limitations', [])
    out = []
    for i, comp in enumerate(comps):
        check = review_result.get('component_checks', {}).get(i)
        status, items, why = 'not_retrieved', [], 'no reviewer confirmation'
        if check and check['verdict'] in ('answered', 'partial'):
            drafts = [summary['claims'][p]['draft_index'] for p in check['claim_indices']
                      if p < len(summary['claims'])]
            kept = [d for d in drafts if d in published_findings]
            if kept:
                status, items, why = check['verdict'], kept, 'reviewer-confirmed, published finding(s)'
            else:
                why = 'reviewer named no published finding'
        elif check and check['verdict'] == 'not_established':
            li = check['limitation_index']
            if 0 <= li < len(rebuilt) and syn.norm(rebuilt[li]['text']) in published_limits:
                status, items, why = 'not_established', [rebuilt[li]['text']], 'published cited scope limitation'
            else:
                why = 'scope limitation not published; downgraded'
        entry = {'component': comp, 'status': status, 'basis': why}
        if status in ('answered', 'partial'):
            entry['finding_draft_indices'] = items
        elif status == 'not_established':
            entry['limitation'] = items[0]
        else:
            entry['note'] = NOT_RETRIEVED_NOTE.format(component=comp)
        out.append(entry)
    return out


def guard_lead(published):
    lead = published.get('answer_lead', '')
    if lead and asserts_paper_absence(lead):
        return {**published, 'answer_lead': NEUTRAL_LEAD,
                'answer_lead_check': ((published.get('answer_lead_check') or '') +
                                      ' S3: lead asserted absence from a paper without scoping it to the retrieved '
                                      'evidence; replaced').strip()}
    return published


def publish(summary, review_result, passages, notes, comps, *, v2, gate):
    """V2 publication unchanged, then the S3 lead guard and coverage metadata (which never add published items)."""
    v2_summary = {k: v for k, v in summary.items() if k != 'component_map'}
    v2_review = {k: v for k, v in review_result.items() if k != 'component_checks'}
    published = publication.publish(v2_summary, v2_review, passages, notes, v2=v2, gate=gate)
    published = guard_lead(published)
    published['component_coverage'] = coverage(comps, summary, review_result, published) if comps else []
    return published
