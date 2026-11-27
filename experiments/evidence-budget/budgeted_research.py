"""Multi-Agent ResearchAgent with a budgeted initial packet (opt-in; agents.py stays unchanged).

Differences from agents.ResearchAgent.run, nothing else:
  - First round (no existing passages): the planner's original-question search returns the evidence-budget packet
    (top-16 or 6k skip-fit) instead of top-8, and that packet is kept whole and first. The other planned searches
    stay top-8 and are added round-robin after it.
  - Every round: the merged evidence is bounded by MERGED_TOKENS (skip-fit in merge order, at most 40 passages,
    synthesize's own limit) instead of 14 passages. Targeted rounds keep the original order (retained citations,
    new passages, earlier evidence), so later rounds never get a larger budget than the first.
"""
import copy

import agents
from agents import ResearchAgent, RESERVED_NEW, _public
from evidence_budget import select, skip_fit

MERGED_TOKENS = 8000
MAX_PASSAGES = 40


class BudgetedResearchAgent(ResearchAgent):
    def __init__(self, retrieve, top_k, initial_retrieve, count, numerical_shadow=None):
        super().__init__(retrieve, top_k, numerical_shadow)
        self.initial_retrieve, self.count = initial_retrieve, count

    def _bounded(self, ordered):
        return select(ordered, skip_fit(MERGED_TOKENS, MAX_PASSAGES), self.count)

    def run(self, task, budget):
        from src.research_chat import synthesize
        payload = task['payload']
        existing = [copy.deepcopy(p) for p in payload.get('existing_passages', [])]
        existing_ids = {p['chunk_id'] for p in existing}
        first_round = not existing
        searches, batches = [], []
        for position, search in enumerate(payload['searches']):
            entry = {'query': search['query'], 'purpose': search['purpose'], 'chunk_ids': [], 'error': None}
            initial = first_round and (search['purpose'] == 'original question' or
                                       (position == 0 and search['query'] == payload['question']))
            try:
                found = self.initial_retrieve(search['query']) if initial else self.retrieve(search['query'], self.top_k)
            except ValueError as error:
                entry['error'] = str(error)[:200]
                found = []
            entry['chunk_ids'] = [p['chunk_id'] for p in found]
            entry['budgeted'] = initial
            searches.append(entry)
            batches.append((initial, found))
        fresh, seen = [], set(existing_ids)
        for _initial, batch in [b for b in batches if b[0]]:  # the budgeted packet first, whole
            for passage in batch:
                if passage['chunk_id'] not in seen:
                    fresh.append(copy.deepcopy(passage))
                    seen.add(passage['chunk_id'])
        others = [batch for initial, batch in batches if not initial]
        for depth in range(max((len(b) for b in others), default=0)):
            for batch in others:
                if depth < len(batch) and batch[depth]['chunk_id'] not in seen:
                    fresh.append(copy.deepcopy(batch[depth]))
                    seen.add(batch[depth]['chunk_id'])
        pinned_ids = list(dict.fromkeys(payload.get('pinned_ids', [])))
        by_id = {p['chunk_id']: p for p in existing}
        pinned = [by_id[cid] for cid in pinned_ids if cid in by_id]
        reserve = min(len(fresh), RESERVED_NEW) if payload.get('require_new') else 0
        pinned = pinned[:MAX_PASSAGES - reserve]
        rest = [p for p in existing if p['chunk_id'] not in {q['chunk_id'] for q in pinned}]
        merged = self._bounded(pinned + fresh + rest)
        fresh_ids = {p['chunk_id'] for p in fresh}
        if reserve and sum(p['chunk_id'] in fresh_ids for p in merged) < reserve:
            # The original guarantee: up to RESERVED_NEW new passages reach synthesis even if citations fill the budget.
            merged = self._bounded(fresh[:reserve] + pinned + fresh[reserve:] + rest)
        merged_ids = {p['chunk_id'] for p in merged}
        new_in_context = [p['chunk_id'] for p in fresh if p['chunk_id'] in merged_ids]
        output = {'searches': searches, 'passages': merged, 'new_passage_ids': new_in_context,
                  'dropped_passage_ids': [p['chunk_id'] for p in existing + fresh if p['chunk_id'] not in merged_ids],
                  'evidence_tokens': sum(self.count(p) for p in merged)}
        if payload.get('require_new') and (not new_in_context or merged_ids == set(existing_ids)):
            return 'no_new_evidence', {**output, 'passages': existing, 'claims': [], 'limitations': [], 'limitation_support': []}
        if not merged:
            return 'insufficient_evidence', {**output, 'claims': [], 'limitation_support': [],
                                             'limitations': ['No passages were retrieved for any planned search.']}
        summary = synthesize(payload['question'], merged, generate=budget.for_agent(self.name),
                             findings_only=payload.get('findings_only', False))
        if self.numerical_shadow is not None:
            try:
                output['shadow_batch'] = self.numerical_shadow.produce(
                    copy.deepcopy(summary['claims']), copy.deepcopy([_public(p) for p in merged]))
            except Exception as error:
                output['shadow_error'] = type(error).__name__
        return summary['status'], {**output, 'claims': summary['claims'], 'limitations': summary['limitations'],
                                   'limitation_support': summary.get('limitation_support', [])}


def enable(orchestrator, initial_retrieve, count):
    """Swap in the budgeted research agent on a constructed OrchestratorAgent."""
    old = orchestrator.research
    orchestrator.research = BudgetedResearchAgent(old.retrieve, old.top_k, initial_retrieve, count, old.numerical_shadow)
    assert agents.MAX_EVIDENCE == 14  # the frozen module is untouched; this agent uses its own bound
    return orchestrator
