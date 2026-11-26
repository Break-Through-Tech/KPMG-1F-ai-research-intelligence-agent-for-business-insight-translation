"""Opt-in evidence-scope check inside the existing verifier call (no extra model call, frozen agents untouched).

Failure it targets: a claim is judged "supported" because the cited sentence says something similar, while that
sentence is about a different population, category, dataset, model, task or experimental condition. A typical
case is an explanation stated for one subgroup being applied to others, or to the whole. Numbers and exact quotes
cannot catch this for claims without numbers, and a single holistic verdict does not force the comparison.

For every claim the verifier must also return, before its verdict:
  claim_scope        what the claim applies to, with references such as "these question types" resolved
  evidence_sentence  the one sentence, verbatim from a passage the claim cites, that states the claim's conclusion
                     (for an interpretation: the explanation or attribution itself)
  evidence_scope     what that sentence applies to, read in the context of its passage
  scope_match        same | narrower | different | unclear   (claim scope relative to evidence scope)

Code then decides. The verifier's judgment is never upgraded, only withheld:
  - evidence_sentence absent from every passage the claim cites -> not established
  - scope_match "different"                                   -> overgeneralization
  - interpretation unless scope_match is "same"               -> not established (an explanation of a superset
                                                                 or an unclear scope is not shown for the subset)
  - finding with "unclear" or a missing sentence keeps its verdict: exact quotes and number checks already
    bind findings to their rows, and holding them would create false abstentions.
A withheld claim becomes partially_supported with an issue, so the existing agent holds it and never publishes it.
The scope fields are removed before the existing schema validation. A reply without them raises, so the existing
verifier rejects the whole review and holds every claim (fail closed). Non-JSON replies are left to its own checks.
"""
import copy
import json
import re

from quote_grounding import locate

INSTRUCTIONS = (
    'SCOPE CHECK. For every claim, before its verdict, fill: claim_scope = the population, category, dataset, '
    'model, task or experimental condition the claim applies to; resolve references such as "these results" '
    'or "these question types" using the question and the other claims. evidence_sentence = copy verbatim the '
    'single sentence, from a passage the claim cites, that directly states the claim\'s conclusion; for an '
    'interpretation this is the sentence stating the explanation or attribution itself, not only its premises; '
    '"" if no cited sentence states it. evidence_scope = the population, category, dataset, model, task or '
    'condition that sentence applies to, read in the context of the surrounding passage (preceding sentences, '
    'section, table row). scope_match = same, narrower (the claim covers only part of the evidence scope), '
    'different (another or a broader category or condition), or unclear. A conclusion stated for one '
    'category, dataset or condition does not support the same conclusion for another one.\n')
FIELDS = {'claim_scope': {'type': 'string'}, 'evidence_sentence': {'type': 'string'},
          'evidence_scope': {'type': 'string'},
          'scope_match': {'type': 'string', 'enum': ['same', 'narrower', 'different', 'unclear']}}


def _ws(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def wire_schema(schema):
    """Verifier schema plus the scope fields, placed before the verdict so they are written first."""
    wire = copy.deepcopy(schema)
    item = wire['properties']['verdicts']['items']
    item['properties'] = {'index': item['properties']['index'], **FIELDS,
                          **{k: v for k, v in item['properties'].items() if k != 'index'}}
    item['required'] = ['index', *FIELDS, *[k for k in item['required'] if k != 'index']]
    return wire


def decide(verdict, claim, passages):
    """Return (verdict without scope fields, review record)."""
    scope = {k: verdict.pop(k) for k in FIELDS}
    cited = [passages[cid] for cid in {s['chunk_id'] for s in claim['support']} if cid in passages]
    sentence = scope['evidence_sentence']
    found = bool(_ws(sentence)) and any(locate(sentence, _ws(text)) for text in cited)
    interpretation = claim.get('kind') == 'interpretation'
    if scope['scope_match'] == 'different':
        outcome, issue = 'withheld: evidence applies to a different scope', 'overgeneralization'
    elif interpretation and not found:
        outcome, issue = 'withheld: no cited sentence states the interpretation', 'missing_support'
    elif interpretation and scope['scope_match'] != 'same':
        outcome, issue = f"withheld: interpretation scope is {scope['scope_match']}", 'overgeneralization'
    else:
        outcome, issue = 'unchanged', None
    if issue and verdict['verdict'] == 'supported':
        verdict.update(verdict='partially_supported', issues=sorted(set(verdict['issues']) | {issue}),
                       reason=(f'Scope check: {outcome}. ' + verdict['reason'])[:600])
    return verdict, {'index': verdict['index'], 'kind': claim.get('kind'), 'text': claim['text'], **scope,
                     'evidence_sentence_found_in_cited_passage': found, 'outcome': outcome}


def review(raw, payload):
    """Apply the decisions to a raw verifier reply. Returns (reply for the existing checks, records)."""
    try:
        reply = json.loads(raw)
    except (TypeError, ValueError):
        return raw, []  # the existing verifier rejects it and holds every claim
    claims = payload['claims']
    passages = {p['chunk_id']: p['text'] for p in payload['passages']}
    verdicts = reply.get('verdicts') if isinstance(reply, dict) else None
    if not isinstance(verdicts, list) or not all(
            isinstance(v, dict) and set(FIELDS) <= set(v) and isinstance(v.get('index'), int)
            and 0 <= v['index'] < len(claims) for v in verdicts):
        raise ValueError('Verifier reply lacks a complete scope check.')
    records = []
    for verdict in verdicts:
        _, record = decide(verdict, claims[verdict['index']], passages)
        records.append(record)
    if reply.get('coverage') != 'none' and not any(v['verdict'] == 'supported' and not v['issues'] for v in verdicts):
        reply['coverage'] = 'none'  # keeps the existing consistency rule: no supported claim, no coverage
        reply['retrieval_request'] = {**reply['retrieval_request'], 'needed': False, 'query': ''}
    return json.dumps(reply, ensure_ascii=False), records


def scoped(generate, prompt_prefix, report):
    def call(prompt, *, response_schema=None, **kwargs):
        if not prompt.startswith(prompt_prefix):
            return generate(prompt, response_schema=response_schema, **kwargs)
        payload = json.loads(prompt[len(prompt_prefix):])
        raw = generate(prompt_prefix + INSTRUCTIONS + prompt[len(prompt_prefix):],
                       response_schema=wire_schema(response_schema), **kwargs)
        raw, records = review(raw, payload)
        report.extend(records)
        return raw
    call.supports_response_schema = getattr(generate, 'supports_response_schema', False)
    return call


class _ScopeBudget:
    def __init__(self, budget, prefix, report):
        self.budget, self.prefix, self.report = budget, prefix, report

    def for_agent(self, name):
        return scoped(self.budget.for_agent(name), self.prefix, self.report)


def enable(engine):
    """Opt in on a constructed OrchestratorAgent or EvidenceHandoffOrchestrator."""
    from agents import VERIFIER_PROMPT
    run = engine.verifier.run

    def scoped_run(task, budget):
        report = []
        status, output = run(task, _ScopeBudget(budget, VERIFIER_PROMPT, report))
        return status, {**output, 'scope_review': report}
    engine.verifier.run = scoped_run
    return engine
