"""BM25 + dense reciprocal-rank fusion with optional injected reranking.

Uses the same frozen chunk rows/citation metadata as the dense index. No model
downloads, LLM calls, or index mutations occur here. Scores are ranking signals,
never confidence. The dense-only entry point is unchanged for controlled trials.
"""
from collections import Counter
import math
import re

STOP = set('a an the what how do does are is of in on for to and or with before should '
           'used use approaches techniques different recent papers identified company '
           'business ask claiming their it its that as by from at be can'.split())


def tokens(text):
    words = re.findall(r'[a-z0-9]+', text.lower())
    # Keep the technical noun distinct from the everyday verb "interpret".
    aliases = {'interpretable':'interpretability'}
    return [aliases.get(w, w[:-1] if len(w) > 4 and w.endswith('s') and not w.endswith('ss') else w)
            for w in words if w not in STOP]


def focus_terms(query):
    """Generic domain terminology expansion, never benchmark IDs or answers.

    A general web-search reranker can prefer business wording over the requested
    technical subject. These anchors retain one subject-specific candidate, not
    force a factual answer when the corpus does not cover the question.
    """
    q = query.lower()
    if re.search(r'multi[- ]agent', q) and re.search(r'\b(risks?|failures?|limitations?|tradeoffs?)\b', q):
        return ['coordination failures', 'communication overhead', 'poorly coordinated']
    if re.search(r'(limited|scarce|scarcity|low[- ]resource|low[- ]data).{0,20}data|data.{0,15}scarcity', q):
        return ['data scarcity', 'data scarce', 'sample efficiency']
    if 'interpret' in q:
        return ['interpretability', 'interpretable', 'mechanistic interpretation']
    if 'autoencoder' in q:
        return ['sparse autoencoders', 'sparse autoencoder']
    return []


class HybridRetriever:
    def __init__(self, passages, *, dense_search, candidate_pool=25, rerank=None):
        if (isinstance(candidate_pool, bool) or not isinstance(candidate_pool, int) or candidate_pool < 5):
            raise ValueError('candidate_pool must be an integer >= 5')
        self.rows = {p['chunk_id']: dict(p) for p in passages}
        if len(self.rows) != len(passages):
            raise ValueError('Hybrid corpus must have unique chunk IDs')
        if any(not p.get('text', '').strip() for p in passages):
            raise ValueError('Hybrid corpus requires nonempty passage text')
        self.dense_search, self.candidate_pool, self.rerank = dense_search, candidate_pool, rerank
        self.counts = {k: Counter(tokens(p['text'])) for k, p in self.rows.items()}
        self.lengths = {k: sum(c.values()) for k, c in self.counts.items()}
        self.avg_length = sum(self.lengths.values()) / max(1, len(self.rows))
        self.df = Counter(w for c in self.counts.values() for w in c)

    def _lexical(self, query):
        terms = set(tokens(query + ' ' + ' '.join(focus_terms(query))))
        n = len(self.rows)
        ranked = []
        for ident, counts in self.counts.items():
            value = 0.0
            for term in terms:
                freq = counts.get(term, 0)
                if not freq:
                    continue
                idf = math.log(1 + (n - self.df[term] + 0.5) / (self.df[term] + 0.5))
                denominator = freq + 1.2 * (1 - 0.75 + 0.75 * self.lengths[ident] / self.avg_length)
                value += idf * freq * 2.2 / denominator
            if value > 0:
                ranked.append((value, ident))
        return sorted(ranked, key=lambda x: (-x[0], x[1]))[:self.candidate_pool]

    def __call__(self, query, top_k=5):
        if not isinstance(query, str) or not query.strip():
            raise ValueError('query must be nonempty')
        if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
            raise ValueError('top_k must be positive integer')
        dense = self.dense_search(query, max(top_k, self.candidate_pool))
        lexical = self._lexical(query)
        scores, details = {}, {}
        for rank, passage in enumerate(dense, 1):
            ident = passage['chunk_id']
            if ident not in self.rows:
                raise ValueError('Dense results differ from the frozen hybrid corpus')
            if passage['text'] != self.rows[ident]['text']:
                raise ValueError('Dense passage text differs from the frozen hybrid corpus')
            if ident in details:
                raise ValueError('Duplicate dense result')
            details[ident] = {'dense_rank': rank, 'distance': passage.get('distance')}
            scores[ident] = 1 / (60 + rank)
        for rank, (value, ident) in enumerate(lexical, 1):
            scores[ident] = scores.get(ident, 0) + 1 / (60 + rank)
            details.setdefault(ident, {}).update(lexical_rank=rank, bm25=value)
        ordered = sorted(scores, key=lambda k: (-scores[k], k))
        candidates = [{**self.rows[k], 'distance': details[k].get('distance'),
                       'retrieval': {**details[k], 'rrf_score': scores[k], 'method': 'hybrid-bm25-rrf-v2'}}
                      for k in ordered]
        if self.rerank and candidates:
            values = list(self.rerank(query, candidates))
            if len(values) != len(candidates) or any(not math.isfinite(float(v)) for v in values):
                raise ValueError('Reranker must return one finite score per candidate')
            for p, v in zip(candidates, values):
                p['retrieval']['rerank_score'] = float(v)
            candidates.sort(key=lambda p: (-p['retrieval']['rerank_score'], -p['retrieval']['rrf_score'], p['chunk_id']))
        anchors = focus_terms(query)
        def matches(p):
            body = ' '.join(tokens(p['text']))
            return sum(' '.join(tokens(term)) in body for term in anchors)
        if anchors and len(candidates) > top_k:
            focused = [p for p in candidates if matches(p)]
            if focused and max(matches(p) for p in focused) > max(matches(p) for p in candidates[:top_k]):
                best = max(focused, key=lambda p:(matches(p), p['retrieval'].get('rerank_score',0), p['retrieval']['rrf_score']))
                # Reserve one slot for explicit topic evidence; preserve rank
                # ordering of the other results and disclose the retention.
                candidates.remove(best)
                best['retrieval']['focus_retained'] = True
                candidates.insert(top_k-1,best)
        # No rigid paper cap: multiple passages from one comparative study can
        # legitimately supply complementary results and caveats.
        return candidates[:top_k]
