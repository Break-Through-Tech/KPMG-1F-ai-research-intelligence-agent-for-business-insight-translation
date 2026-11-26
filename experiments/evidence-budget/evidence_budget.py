"""Shared evidence-budget selection for Baseline and Multi-Agent (opt-in; src and both engines stay unchanged).

Policies (Codex retrieval handoff, b2-adaptive-handoff.md):
  fixed(k)               the first k passages of B2's original order.
  skip_fit(tokens, 30)   scan the first `window` passages in B2 order; keep a whole passage only if it still fits
                         the passage-text token budget; continue past one that does not fit.
Whole parent rows only, original order, original chunk IDs, no text edits. Token counts use B2's own MiniLM
tokenizer on the passage text (the development proxy Codex used). The provider payload is separately bounded
by src.research_chat.synthesize (at most 40 passages and 120,000 characters, fails closed).

B2's public retrieve() caps top_k at 20, so window 30 comes from open_ranked(), which builds the same
FacetRetriever over the same index and models and returns its ranked order. Its first 20 must equal retrieve(q, 20).
"""
from copy import deepcopy
from pathlib import Path


def fixed(k):
    return {'name': f'fixed-{k}', 'k': k}


def skip_fit(tokens, window=30):
    return {'name': f'skip-fit-{tokens}-w{window}', 'tokens': tokens, 'window': window}


def select(ranked, policy, count):
    """ranked: passages in B2 order. count(passage) -> tokens. Returns the chosen passages (deep copies), in order."""
    if 'k' in policy:
        return [deepcopy(p) for p in ranked[:policy['k']]]
    chosen, used = [], 0
    for passage in ranked[:policy['window']]:
        cost = count(passage)
        if used + cost <= policy['tokens']:
            chosen.append(deepcopy(passage))
            used += cost
    return chosen


def depth_needed(policy):
    return policy['k'] if 'k' in policy else policy['window']


def open_ranked(bundle, *, encoder_path, reranker_path, table_comparisons):
    """B2 exactly as open_b2 builds it, plus ranked(query, n) beyond the public 20 cap and count(passage).

    Returns (retrieve, identity, ranked, count). retrieve and identity are open_b2's own; ranked reuses the same
    encoder, reranker and index files through a second FacetRetriever (rank order is deterministic).
    """
    import numpy as np
    from src.experimental.b2 import open_b2
    from src.experimental.balanced_retriever import FacetRetriever
    from src.experimental.search_index import SearchViewIndex
    from sentence_transformers import SentenceTransformer, CrossEncoder
    encoder = SentenceTransformer(str(Path(encoder_path).resolve()), local_files_only=True, device='cpu')
    reranker = CrossEncoder(str(Path(reranker_path).resolve()), local_files_only=True, device='cpu')
    retrieve, identity, path, provenance = open_b2(bundle, encoder_path=encoder_path, reranker_path=reranker_path,
                                                   encoder=encoder, reranker=reranker, table_comparisons=table_comparisons)
    index = SearchViewIndex(path, model=encoder)
    engine = FacetRetriever(index, reranker, encoder, table_comparisons=table_comparisons)
    cache = {}

    def ranked(query, n):
        identity()  # same integrity checks as retrieve()
        if not isinstance(query, str) or not query.strip():
            raise ValueError('Nonempty question required.')
        if index.token_count(query) > encoder.max_seq_length:
            raise ValueError('Query would truncate; shorten it before retrying.')
        vector = np.asarray(encoder.encode([query], show_progress_bar=False), dtype=np.float32)
        if vector.shape != (1, 384) or not np.isfinite(vector).all():
            raise ValueError('Invalid query embedding.')
        order, _ = engine.rank_facets(query, vector[0])
        return engine.resolve(order, n)

    def count(passage):
        key = passage['chunk_id']
        if key not in cache:
            cache[key] = index.token_count(passage['text'])
        return cache[key]
    return retrieve, identity, ranked, count, path, provenance


def budgeted_retrieve(ranked, count, policy):
    """retrieve(query, top_k) for an engine: ignores top_k and returns the policy's packet."""
    def retrieve(query, _top_k=None):
        return select(ranked(query, depth_needed(policy)), policy, count)
    return retrieve
