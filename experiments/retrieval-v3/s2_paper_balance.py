"""S2 with the opt-in paper-balanced selector (B1). Frozen S2 stays the default and fallback.

    engine = S2Research(..., paper_balance=False)   # exactly frozen V2 Standard (default)
    engine = S2Research(..., paper_balance=True)    # B1: balanced window across >= 2 explicitly named papers

Only evidence selection changes, and only when the question names two or more papers present in S2's top-120
candidates (paper_balance.requested_papers). Synthesis, review, publication gates, the 6,000-token budget, the C2
allowance and the passage cap are the frozen V2 code. 2 model calls, no extra searches.
"""
import s3_env  # noqa: F401
import evidence as ev  # frozen V2
from engine import ConsolidatedResearch  # frozen V2
import paper_balance as pb


class S2Research(ConsolidatedResearch):
    def __init__(self, *, paper_balance=False, rows=None, **kwargs):
        super().__init__('standard', **kwargs)
        self.paper_balance = bool(paper_balance)
        self.rows = rows or {}
        self.titles = {}
        for r in self.rows.values():
            self.titles.setdefault(r.get('arxiv_id'), r.get('title', ''))

    def balanced_packet(self, question):
        candidates = self.ranked(question, ev.CANDIDATE_DEPTH)
        rows = {**self.rows, **{p['chunk_id']: p for p in candidates}}  # retrieved metadata wins, as in V2
        packet, papers = pb.packet(question, [p['chunk_id'] for p in candidates], rows, self.count, self.tables,
                                   self.titles, mode='B1')
        return {**packet, 'paper_balance': {'enabled': True, 'requested_papers': papers, 'applied': len(papers) >= 2},
                'protected_ids': [p['chunk_id'] for p in packet['passages']], 'supplementary_ids': [],
                'searches': [{'query': question, 'purpose': 'original question', 'role': 'protected',
                              'chunk_ids': [p['chunk_id'] for p in packet['passages']], 'error': None}]}

    def gather_evidence(self, question, store, timings):
        if not self.paper_balance:
            return super().gather_evidence(question, store, timings)
        packet = self._stage(store, 'evidence', timings, lambda: self.balanced_packet(question))
        return packet, None, None
