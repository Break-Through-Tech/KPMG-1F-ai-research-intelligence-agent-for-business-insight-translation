"""Opt-in question decomposition for Baseline/B2 retrieval. No model calls; Baseline synthesis is unchanged.

The original question is searched first. Then each deterministic part from question_parts (retrieval-v3 splitter,
at most 3) is searched with the same top_k. Results are merged round-robin: rank 1 of every search, then rank 2,
and so on. Duplicates are removed by chunk_id, keeping the first copy unchanged, so passage IDs, provenance and
citations are untouched. The merged result is capped at `cap` passages (14, as in Multi-Agent).

Round-robin with the original question first means its top results are never pushed out by part searches. With
3 parts and a cap of 14, at least its top 3 survive. A part search that raises or returns nothing is skipped; the
original search's failure still propagates.
"""
from question_parts import question_parts

CAP = 14


def decompose(question, splitter=question_parts):
    parts = [p for p in splitter(question) if p.strip() and p.strip().lower() != question.strip().lower()]
    return [question] + list(dict.fromkeys(parts))


def decomposed(retrieve, *, cap=CAP, splitter=question_parts, log=None):
    """Wrap a B2 retrieve(query, top_k) so Baseline receives a merged, capped, deduplicated packet."""
    def search(query, top_k):
        queries = decompose(query, splitter)
        batches = [retrieve(queries[0], top_k)]  # the original question must succeed
        for part in queries[1:]:
            try:
                batches.append(retrieve(part, top_k))
            except Exception:
                batches.append([])
        merged, seen = [], set()
        for depth in range(max(len(b) for b in batches)):
            for batch in batches:
                if depth < len(batch) and batch[depth]['chunk_id'] not in seen:
                    merged.append(batch[depth])
                    seen.add(batch[depth]['chunk_id'])
        if log is not None:
            log.append({'queries': queries, 'per_query': [[p['chunk_id'] for p in b] for b in batches]})
        return merged[:cap]
    return search
