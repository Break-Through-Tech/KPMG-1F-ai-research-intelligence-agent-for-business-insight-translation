"""S2-R2: opt-in retrieval ordering for frozen S2 (evidence selection only).

    S2R2Research(retrieval_strategy='s2')   exactly frozen S2 (default)
    S2R2Research(retrieval_strategy='b1')   B1 paper balance only (as in s2_paper_balance)
    S2R2Research(retrieval_strategy='r2')   B1 when >= 2 named papers are resolved; otherwise component-rank fusion

Component-rank fusion = s3_evidence.s3_packet at S2's budget (6,000 passage tokens; C2 800; frozen select_grouped and
request guard): the 30-candidate window is ordered by 1/(20+rank_original) + mean over question components of
1/(20+rank_component) (components restricted to papers in the original top-30), original top-4 first. A question
with no components (a single ask) gets no component searches, so its window is S2's window.
Synthesis, review, publication gates, budget, C2 and the 2-call structure are frozen S2. No LLM calls are added;
component searches are local CPU retrieval (at most 6, 3 in parallel).
"""
import s3_env  # noqa: F401
import evidence as ev  # frozen V2
import paper_balance as pb
import s3_evidence as se
from s2_paper_balance import S2Research

STRATEGIES = ('s2', 'b1', 'r2')


class S2R2Research(S2Research):
    def __init__(self, *, retrieval_strategy='s2', **kwargs):
        if retrieval_strategy not in STRATEGIES:
            raise ValueError(f'retrieval_strategy must be one of {STRATEGIES}')
        super().__init__(paper_balance=retrieval_strategy in ('b1', 'r2'), **kwargs)
        self.strategy = retrieval_strategy

    def r2_packet(self, question):
        candidates = self.ranked(question, ev.CANDIDATE_DEPTH)
        papers = pb.requested_papers(question, [p['chunk_id'] for p in candidates], self.titles)
        if len(papers) >= 2:
            packet = self.balanced_packet(question)
            return {**packet, 'r2': {'route': 'b1', 'requested_papers': papers}}
        packet = se.s3_packet(question, self.ranked, self.count, self.tables, budget=ev.STANDARD_TOKENS,
                              parallel=self.parallel_search)
        routed = 'fusion' if packet.get('components') else 's2-window (single ask)'
        return {**packet, 'r2': {'route': routed, 'requested_papers': papers,
                                 'component_searches': len(packet.get('components', []))}}

    def gather_evidence(self, question, store, timings):
        if self.strategy != 'r2':
            return super().gather_evidence(question, store, timings)
        packet = self._stage(store, 'evidence', timings, lambda: self.r2_packet(question))
        return packet, None, None
