"""Consolidated Baseline-powered research: one foundation, two modes plus an optional adaptive prototype.
(consolidated-v2; v1 is frozen in ../consolidated.)

v2 workflow for every mode: Baseline retrieval (protected packet, checkpoint "base") -> coverage assessment
(adaptive mode only, deterministic, checkpoint "route") -> optional planning and supplementary research ->
consolidated evidence -> shared synthesis -> shared review -> deterministic publication.

  Standard  evidence (protected 6k packet) -> synthesis (1 call) -> review (1 call) -> deterministic publication
  Deep      plan (1 call, reused Multi-Agent planner) -> evidence (protected packet + bounded supplementary searches,
            8k total) -> the SAME synthesis, review and publication

A prompt chain with programmatic gates (Anthropic, "Building Effective Agents"): no agent loop, no extra reviewer,
no repeated synthesis. Durable execution (LangGraph checkpoint idea, reimplemented minimally): each completed stage
is written to the question's checkpoint folder before the next starts; a resumed run loads completed stages and
repeats only the failed one. A failed or invalid plan falls back to Standard evidence and is recorded; that
decision is itself checkpointed, so a resume never re-plans.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import time

import evidence as ev
import publication
import assist_route as route
import review as rv
import synthesis as syn

MODES = {'standard': {'calls': 2, 'budget': ev.STANDARD_TOKENS}, 'deep': {'calls': 3, 'budget': ev.DEEP_TOKENS},
         'adaptive': {'calls': '2 or 3', 'budget': 'standard, or deep when assistance is activated'}}
STAGES = ('base', 'route', 'plan', 'evidence', 'synthesis', 'review')
NO_FALLBACK = {'BudgetExhausted'}  # the call budget is never bypassed by falling back


class CheckpointStore:
    def __init__(self, folder):
        self.folder = Path(folder)
        (self.folder / 'stages').mkdir(parents=True, exist_ok=True)

    def path(self, stage):
        return self.folder / 'stages' / f'{stage}.json'

    def has(self, stage):
        return self.path(stage).is_file()

    def load(self, stage):
        return json.loads(self.path(stage).read_text(encoding='utf-8'))

    def save(self, stage, value):
        tmp = self.path(stage).with_suffix('.tmp')
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding='utf-8')
        os.replace(tmp, self.path(stage))

    def attempts(self):
        path = self.folder / 'attempts.json'
        return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else []

    def record_attempt(self, record):
        attempts = self.attempts() + [record]
        (self.folder / 'attempts.json').write_text(json.dumps(attempts, indent=1), encoding='utf-8')


def default_planner(generate, question):
    """The existing Multi-Agent planner prompt and schema, unchanged (experiments/agentic/agents.py)."""
    from agents import ORCHESTRATOR_PROMPT, _call
    from contracts import PLAN_SCHEMA
    prompt = ORCHESTRATOR_PROMPT + json.dumps({'question': question, 'industry_selected_by_user': False,
                                               'chart_tool_available': False}, ensure_ascii=False)
    return _call(generate, prompt, PLAN_SCHEMA)


class ConsolidatedResearch:
    def __init__(self, mode, *, ranked, count, tables, generate, v2, gate, planner=default_planner,
                 clock=time.perf_counter, parallel_search=True):
        if mode not in MODES:
            raise ValueError(f'mode must be one of {sorted(MODES)}')
        self.mode, self.ranked, self.count, self.tables = mode, ranked, count, tables
        self.generate, self.v2, self.gate, self.planner, self.clock = generate, v2, gate, planner, clock
        self.parallel_search = parallel_search

    def _stage(self, store, name, timings, compute):
        if store.has(name):
            timings[name] = 'checkpoint'
            return store.load(name)
        started = self.clock()
        self._current = name
        value = compute()
        timings[name] = round(self.clock() - started, 3)
        store.save(name, value)
        return value

    def _plan(self, question):
        try:
            plan = self.planner(self.generate, question)
            searches, seen = [], {syn.norm(question).casefold()}
            for sub in plan.get('subquestions', [])[:3]:
                key = syn.norm(sub['query']).casefold()
                if key not in seen:
                    seen.add(key)
                    searches.append({'query': sub['query'], 'purpose': sub['purpose']})
            return {'source': 'planner', 'plan': plan, 'searches': searches, 'fallback': None}
        except Exception as error:
            if type(error).__name__ in NO_FALLBACK:
                raise
            return {'source': 'fallback', 'plan': None, 'searches': [],
                    'fallback': f'planner failed ({type(error).__name__}: {str(error)[:160]}); '
                                'Standard evidence used'}

    def gather_evidence(self, question, store, timings):
        """Baseline retrieval -> (adaptive) coverage assessment -> optional planning -> consolidated evidence."""
        plan, decision = None, None
        base = self._stage(store, 'base', timings,
                           lambda: ev.standard_packet(question, self.ranked, self.count, self.tables))
        assist = self.mode == 'deep'
        if self.mode == 'adaptive':
            decision = self._stage(store, 'route', timings, lambda: route.decide(question, base))
            assist = decision['activate']
        if assist:
            plan = self._stage(store, 'plan', timings, lambda: self._plan(question))

        def gather():
            if not assist or not plan['searches']:
                return {**base, 'supplementary_ids': []}
            return ev.deep_packet(question, plan['searches'], self.ranked, self.count, self.tables, protected=base,
                                  parallel=self.parallel_search)
        packet = self._stage(store, 'evidence', timings, gather)
        return packet, plan, decision

    def answer(self, question, packet, store, timings, *, findings_only=False):
        """Shared synthesis -> shared review -> deterministic publication, on the consolidated evidence."""
        passages, notes = packet['passages'], packet['notes']

        def draft():
            summary, report, raw = syn.synthesize(question, passages, notes, generate=self.generate,
                                                  findings_only=findings_only)
            return {'summary': summary, 'report': report, 'raw': raw}
        drafted = self._stage(store, 'synthesis', timings, draft)
        by_id = {p['chunk_id']: p for p in passages}
        flags = publication.precheck_flags(drafted['summary']['claims'], by_id, self.v2)

        def check():
            result, report, raw = rv.review(question, drafted['summary'], passages, notes, flags,
                                            generate=self.generate)
            result = {**result, 'decisions': {str(k): v for k, v in result['decisions'].items()}}
            return {'review': result, 'report': report, 'raw': raw}
        reviewed = self._stage(store, 'review', timings, check)
        decisions = {int(k): v for k, v in reviewed['review']['decisions'].items()}
        started_publish = self.clock()
        self._current = 'publication'
        summary = publication.publish(drafted['summary'], {**reviewed['review'], 'decisions': decisions},
                                      passages, notes, v2=self.v2, gate=self.gate)
        timings['publication'] = round(self.clock() - started_publish, 3)
        return summary, drafted, reviewed, flags

    def run(self, question, folder, *, findings_only=False):
        """Run or resume one question. Returns the result dict; raises on a stage failure after checkpointing."""
        store = CheckpointStore(folder)
        timings, started = {}, self.clock()
        self._current = 'base'
        attempt = {'attempt': len(store.attempts()) + 1, 'mode': self.mode, 'resumed_from': [
            s for s in STAGES if store.has(s)]}
        try:
            packet, plan, decision = self.gather_evidence(question, store, timings)
            summary, drafted, reviewed, flags = self.answer(question, packet, store, timings,
                                                            findings_only=findings_only)
        except Exception as error:
            attempt.update(status='failed', error=f'{type(error).__name__}: {str(error)[:200]}',
                           failed_stage=self._current,
                           seconds=round(self.clock() - started, 3), timings=timings)
            store.record_attempt(attempt)
            raise
        attempt.update(status='complete', seconds=round(self.clock() - started, 3), timings=timings)
        store.record_attempt(attempt)
        result = self.result(question, packet, plan, decision, summary, drafted, reviewed, flags, store)
        (Path(folder) / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
        return deepcopy(result)

    def result(self, question, packet, plan, decision, summary, drafted, reviewed, flags, store):
        return {'mode': self.mode, 'question': question, 'summary': summary,
                'evidence': [{k: v for k, v in p.items() if k != 'reader'} for p in packet['passages']],
                'evidence_management': {k: packet.get(k) for k in (
                    'protected_ids', 'supplementary_ids', 'searches', 'tokens', 'base_tokens', 'base_budget',
                    'conclusion_tokens', 'conclusion_allowance', 'conclusion_ids', 'conclusion_considered',
                    'trimmed_for_request_size', 'notes')},
                'assistance': {'mode': self.mode, 'activated': plan is not None, 'route': decision},
                'plan': plan, 'synthesis_report': drafted['report'], 'review_report': reviewed['report'],
                'precheck_flags': {str(k): v for k, v in flags.items()},
                'review': {k: reviewed['review'][k] for k in ('coverage', 'gap')},
                'attempts': store.attempts(),
                'human_review': {'status': 'pending', 'reviewer': None}, 'approved': False}
