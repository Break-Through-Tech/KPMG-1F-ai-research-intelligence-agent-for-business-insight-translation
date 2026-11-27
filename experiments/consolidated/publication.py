"""Deterministic publication gates shared by Standard and Deep Research (no model calls). Fail closed per claim.

A finding is published only if ALL hold, evaluated on the claim as it will be published:
  P1 review: a valid decision exists, supported and relevant, and either quotes_entail or a non-empty supported_text.
  P2 quotes: every attached quote (original and added_support) is an exact substring of a passage in the evidence.
     An added_support that fails membership withholds the claim (its entailment may have relied on it).
  P3 reduction: a supported_text may only remove content: its numbers must be a subset of the draft's numbers.
  P4 number recall (ALCE-style, per claim): every reported number in the claim occurs in the claim's OWN attached
     quotes. Digits inside names (Llama-2-7B, GPT-4, Qwen2.5, sub-4-second) are names when the token appears in a
     cited passage, as in numeric_checks_v2 R4. Finding the number elsewhere in the corpus is not enough.
     (combined-v1 G03-B F2: 3- and 4-shot Table 7 figures cited only to the 2-shot row.)
  P5 attribution flags: numeric_checks_v2 is run on the published text. 'numbers_absent' is cleared when P4 proved the
     value is in the attached quotes (G07 'sub-4-second'). Every other contradiction (subject, negation, condition,
     direction, denominator, range) must be cleared by a reviewer flag_resolution whose quote is an exact span of the
     attached quotes containing that number, with every named entity of the claim clause present in the attached
     quotes. Unresolved flags withhold the claim. (combined-v1 M1 G03/G04 false rejections came from v2 misreading
     subjects in bundled multi-result sentences; the flags are kept, but can now be resolved with checkable evidence.)
Interpretations additionally pass verification-repair/interpretation_gate (G1-G7) and are published with a label.
Limitations must pass P2 and P4. Status is derived from what is published.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import re

from synthesis import norm, quote_problems

NUMBER = re.compile(r'(?<![\w.])(?:\d+(?:,\d{3})*|(?=\.\d))(?:\.\d+)?')
ANY_NUMBER = re.compile(r'\d+(?:,\d{3})*(?:\.\d+)?|\.\d+')
TOKEN_CHARS = re.compile(r'[A-Za-z0-9.\-]')
ENTITY = re.compile(r'\b(?=[A-Za-z0-9\-.]*[A-Z0-9])[A-Za-z][A-Za-z0-9\-.]*[A-Za-z0-9]\b')
COMMON = {'For', 'The', 'In', 'On', 'At', 'A', 'An', 'This', 'These', 'It', 'Its', 'With', 'Across', 'Under', 'When',
          'Both', 'Each', 'All', 'Average', 'Overall', 'However', 'Compared', 'Using', 'After', 'Before', 'During'}
LABEL = 'Interpretation: inferred from the cited findings for this decision; not a research result.'


def _dec(text):
    try:
        return Decimal(text.replace(',', ''))
    except InvalidOperation:
        return None


def _token(text, start, end):
    while start > 0 and TOKEN_CHARS.match(text[start - 1]):
        start -= 1
    while end < len(text) and TOKEN_CHARS.match(text[end]):
        end += 1
    return text[start:end].strip('.-')


def reported_numbers(text, cited_text):
    """Numbers the claim reports, excluding digits inside names that appear in the cited passages."""
    out, folded = [], cited_text.casefold()
    for match in NUMBER.finditer(text):
        token = _token(text, match.start(), match.end())
        if re.search(r'[A-Za-z]', token) and token.casefold() in folded:
            continue
        value = _dec(match.group())
        if value is not None:
            out.append((match.group(), value))
    return out


def quote_values(quotes):
    return {v for q in quotes for m in ANY_NUMBER.finditer(q) if (v := _dec(m.group())) is not None}


def _clause(text, number):
    for clause in re.split(r'[;.](?:\s|$)|,\s+(?:and|while|whereas|but)\s+|\s+versus\s+|\s+vs\.?\s+', text):
        if number in clause:
            return clause
    return text


def _entities(clause):
    return {e for e in ENTITY.findall(clause) if e not in COMMON and not re.fullmatch(r'[\d.,%]+', e)}


def respectively_consistent(claim_text, span):
    """When the span maps values to names with 'respectively' ("64.3% and 34.8% ... the GPT-3.5 and GPT-4 version,
    respectively"), the claim must pair each value with the same name. The names are the entities between the last
    value and 'respectively'; each value in the claim is paired with its nearest such name, preferring a name that
    follows it ("64.3% on GPT-3.5"). Returns False on a swapped mapping."""
    lower = span.casefold()
    if 'respectively' not in lower:
        return True
    values = [raw for raw, _ in reported_numbers(span, span)]
    last = max((m.end() for m in NUMBER.finditer(span) if m.group() in values), default=0)
    segment = span[last:lower.index('respectively', last) if 'respectively' in lower[last:] else len(span)]
    found = [e for e in dict.fromkeys(ENTITY.findall(segment))
             if e not in COMMON and e.casefold() in claim_text.casefold() and not re.fullmatch(r'[\d.,%]+', e)]
    names = [e for e in found if not any(e != o and e.casefold() in o.casefold() for o in found)]
    if len(values) < 2 or len(values) != len(names):
        return True  # no clean one-to-one mapping to compare against
    for value, name in zip(values, names):
        spots = [m.start() for m in re.finditer(re.escape(value), claim_text)]
        if not spots:
            continue

        def distance(other):
            places = [m.start() for m in re.finditer(re.escape(other), claim_text)]
            return min(((p - s) if p > s else 2 * (s - p) for p in places for s in spots), default=10**9)
        if min(names, key=distance) != name:
            return False
    return True


def number_recall(item, cited_text):
    """P4. Returns the reported numbers absent from the item's own quotes."""
    quotes = [norm(s['quote']) for s in item['support']]
    have = quote_values(quotes)
    return [raw for raw, value in reported_numbers(item['text'], cited_text) if value not in have]


def unresolved_flags(item, grounding, resolutions, presence_ok):
    """P5. Returns the v2 contradictions that remain after deterministic and quote-anchored resolution."""
    quotes = [norm(s['quote']) for s in item['support']]
    joined = ' '.join(quotes).casefold()
    open_flags = []
    mention_issues = set()
    for mention in grounding.get('mentions', []):
        if mention['status'] != 'contradicted':
            continue
        mention_issues.update(mention['issues'])
        issues = [i for i in mention['issues'] if not (i == 'numbers_absent' and presence_ok)]
        if not issues:
            continue
        value = _dec(mention['number'])
        resolved = False
        for res in resolutions:
            span = norm(res.get('quote'))
            if (len(span) >= 10 and any(span in q for q in quotes) and _dec(res.get('number', '') or 'x') == value
                    and value in quote_values([span]) and respectively_consistent(item['text'], span)
                    and all(e.casefold() in joined for e in _entities(_clause(item['text'], mention['number'])))):
                resolved = True
                break
        if not resolved:
            open_flags.append({'number': mention['number'], 'issues': issues, 'subject': mention.get('subject')})
    for issue in sorted(set(grounding.get('contradictions', [])) - mention_issues):
        resolved = any(not (res.get('number') or '').strip() and len(norm(res.get('quote'))) >= 15
                       and any(norm(res.get('quote')) in q for q in quotes) for res in resolutions)
        if not resolved:
            open_flags.append({'number': '', 'issues': [issue], 'subject': None})
    return open_flags


def precheck_flags(claims, passages_by_id, v2):
    """Flags shown to the reviewer: v2 contradictions on the draft claims (findings only)."""
    flags = {}
    for index, claim in enumerate(claims):
        if claim['kind'] != 'finding':
            continue
        grounding = v2.ground_claim(claim, passages_by_id)
        cited = ' '.join(passages_by_id[c]['text'] for c in claim['chunk_ids'] if c in passages_by_id)
        missing = set(number_recall(claim, cited))
        found = []
        for mention in grounding.get('mentions', []):
            issues = [i for i in mention['issues'] if not (i == 'numbers_absent' and mention['number'] not in missing)]
            if mention['status'] == 'contradicted' and issues:
                found.append({'number': mention['number'], 'issues': issues})
        for issue in grounding.get('contradictions', []):
            if not any(issue in f['issues'] for f in found) and issue != 'numbers_absent':
                found.append({'number': '', 'issues': [issue]})
        if found:
            flags[index] = found
    return flags


def publish(summary, review, passages, notes, *, v2, gate):
    """Apply P1-P5 per claim, the interpretation gate, and limitation checks. Returns the published summary."""
    by_id = {p['chunk_id']: p for p in passages}
    texts = {cid: norm(p['text']) for cid, p in by_id.items()}
    findings, interpretations, held = [], [], []

    def hold(claim, reasons, text=None):
        held.append({'draft_index': claim.get('draft_index'), 'kind': claim['kind'], 'text': text or claim['text'],
                     'reasons': reasons})

    pending_interpretations = []
    for index, claim in enumerate(summary['claims']):
        decision = review['decisions'].get(index)
        if decision is None:
            hold(claim, ['P1: no valid review decision'])
            continue
        if not (decision['supported'] and decision['relevant']):
            hold(claim, [f"P1: review rejected ({'unsupported' if not decision['supported'] else 'not relevant'}): "
                         f"{decision['reason'][:200]}"])
            continue
        reduced = decision['supported_text'].strip()
        if not decision['quotes_entail'] and not reduced:
            hold(claim, ['P1: attached quotes do not entail the claim and no supported part was given'])
            continue
        item = deepcopy(claim)
        added = decision.get('added_support', [])
        if added:
            if quote_problems({'support': added}, texts):
                hold(claim, ['P2: an added quote is not in its passage'])
                continue
            item['support'] = item['support'] + [s for s in added if s not in item['support']]
            item['chunk_ids'] = list(dict.fromkeys(s['chunk_id'] for s in item['support']))
        cited = ' '.join(by_id[c]['text'] for c in item['chunk_ids'] if c in by_id)
        if not decision['quotes_entail']:
            original = {v for _, v in reported_numbers(claim['text'], cited)}
            if not {v for _, v in reported_numbers(reduced, cited)} <= original:
                hold(claim, ['P3: supported_text adds a number the draft did not state'], reduced)
                continue
            item['text'], item['reduced_from'] = reduced, claim['text']
        missing = number_recall(item, cited)
        if missing:
            hold(claim, [f'P4: number(s) not in the attached quotes: {", ".join(missing)}'], item['text'])
            continue
        grounding = v2.ground_claim(item, by_id)
        if item['kind'] == 'finding':
            flags = unresolved_flags(item, grounding, decision.get('flag_resolutions', []), presence_ok=True)
            if flags:
                hold(claim, ['P5: unresolved number-attribution flag(s): ' +
                             '; '.join(f"{f['number'] or '-'} {'/'.join(f['issues'])}" for f in flags)], item['text'])
                continue
            item['verification'] = {'review': {k: decision[k] for k in ('quotes_entail', 'reason')},
                                    'number_grounding': grounding['status'],
                                    'flags_resolved': [r for r in decision.get('flag_resolutions', [])]}
            findings.append(item)
        else:
            pending_interpretations.append((claim, item, decision))
    verified_texts = [f['text'] for f in findings]
    for claim, item, decision in pending_interpretations:
        row = {'deterministic': {'quote_membership': 'passed'},
               'automated': {'verdict': 'supported', 'issues': [] if decision['quotes_entail'] else ['missing_support']}}
        failed = gate(row, item, v2, [by_id[c] for c in item['chunk_ids'] if c in by_id], verified_texts)
        if failed:
            hold(claim, ['interpretation gate: ' + ' '.join(failed)], item['text'])
            continue
        interpretations.append({**item, 'label': LABEL})
    limitations, dropped_limits = [], []
    for item in review['limitations']:
        cited = ' '.join(by_id[c]['text'] for c in item['chunk_ids'] if c in by_id)
        missing = number_recall(item, cited)
        if quote_problems(item, texts) or missing:
            dropped_limits.append({'text': item['text'], 'reason': f'number(s) not in quotes: {missing}' if missing
                                   else 'quote not found'})
            continue
        limitations.append(item)
    coverage = review['coverage'] if findings else 'none'
    lead = review['gap'] if coverage != 'full' else ''
    if held and coverage == 'full':
        coverage, lead = 'partial', ''
    if held and any(h['reasons'][0].startswith(('P2', 'P3', 'P4', 'P5')) for h in held):
        lead = (lead + ' ' if lead else '') + 'Some drafted findings could not be verified against their attached quotes and are withheld.'
    return {'status': 'ok' if findings else 'insufficient_evidence',
            'claims': findings + interpretations, 'held_claims': held,
            'limitation_support': limitations, 'limitations': [l['text'] for l in limitations],
            'dropped_limitations': dropped_limits, 'evidence_notes': [n['text'] for n in notes],
            'answer_scope': {'full': 'full', 'partial': 'partial', 'none': 'unavailable'}[coverage],
            'answer_lead': lead.strip(),
            'support_check': 'exact quotes; per-claim number recall against attached quotes; numeric_checks_v2 '
                             'attribution flags (quote-anchored resolution); model review of quote entailment; '
                             'not human verification'}
