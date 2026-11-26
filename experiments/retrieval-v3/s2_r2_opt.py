"""S2-R2 (optimized): identical evidence selection to validated S2-R2 (commit 1d0e0ae), with the original-question
search computed ONCE per request and reused by paper resolution, the B1 route and the fusion route.

Validated S2-R2 ran the original search twice per question (once to resolve named papers, again inside
balanced_packet / s3_packet). This subclass passes a request-scoped memo of `ranked` instead. The memo lives only for
one r2_packet call: no global cache, no cross-request or cross-user state. Component searches are unchanged (each is a
different query). Selection, ranking weights, budgets, generation, review and gates are untouched.
"""
import s3_env  # noqa: F401
import evidence as ev  # frozen V2
import paper_balance as pb
import s3_evidence as se
from s2_r2 import S2R2Research


class S2R2OptResearch(S2R2Research):
    def r2_packet(self, question):
        memo = {}

        def ranked(query, n):  # request-scoped memo keyed by (query, depth); B2 ranking is deterministic
            if (query, n) not in memo:
                memo[(query, n)] = self.ranked(query, n)
            return memo[(query, n)]
        candidates = ranked(question, ev.CANDIDATE_DEPTH)
        papers = pb.requested_papers(question, [p['chunk_id'] for p in candidates], self.titles)
        if len(papers) >= 2:  # same as S2Research.balanced_packet, but on the already-computed ranking
            rows = {**self.rows, **{p['chunk_id']: p for p in candidates}}
            packet, papers = pb.packet(question, [p['chunk_id'] for p in candidates], rows, self.count, self.tables,
                                       self.titles, mode='B1')
            packet = {**packet, 'paper_balance': {'enabled': True, 'requested_papers': papers, 'applied': True},
                      'protected_ids': [p['chunk_id'] for p in packet['passages']], 'supplementary_ids': [],
                      'searches': [{'query': question, 'purpose': 'original question', 'role': 'protected',
                                    'chunk_ids': [p['chunk_id'] for p in packet['passages']], 'error': None}]}
            return {**packet, 'r2': {'route': 'b1', 'requested_papers': papers}}
        packet = se.s3_packet(question, ranked, self.count, self.tables, budget=ev.STANDARD_TOKENS,
                              parallel=self.parallel_search)
        routed = 'fusion' if packet.get('components') else 's2-window (single ask)'
        return {**packet, 'r2': {'route': routed, 'requested_papers': papers,
                                 'component_searches': len(packet.get('components', []))}}
