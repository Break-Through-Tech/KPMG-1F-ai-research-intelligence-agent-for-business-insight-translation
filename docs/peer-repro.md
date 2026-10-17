# Local peer-inspired development comparison

Depends on the opt-in retrieval helper PR. Production defaults are unchanged.

## Retrieval/context comparison

```sh
HF_HUB_OFFLINE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=2 \
  python -m evaluation.run_peer_repro \
  --chunks data/processed/chunks.parquet --output /tmp/peer-repro-new

python -m unittest discover -s tests -p test_peer_retrieval.py -v
```

The historical run used a frozen chunk table (877 chunks, 25 papers).
It remains ignored, not committed. Use the exact chunk-file hash recorded in
the result to repeat these observations; arbitrary regenerated chunks are a
different experiment. Models must already be cached: `sentence-transformers/
all-MiniLM-L6-v2` and `cross-encoder/ms-marco-MiniLM-L6-v2`. Install `requirements.txt` into a Python 3.12 environment and run `python -m pytest -q`.

The runner builds a **new in-memory Chroma L2 index**, with one HNSW thread and
search/construction ef 200. It never opens an existing persistent index. This
controls model, corpus and backend across variants; it is not bitwise replication
of a previously persisted index or its approximate-search graph.

| Variant | Change |
| --- | --- |
| `dense` | Dense-only top five |
| `hybrid_rrf` | Existing chunk BM25/dense fusion without cross-encoder |
| `baseline_cross` | Existing hybrid plus cached local cross-encoder, top five |
| `cross_cap2` | Same baseline ranked pool, optional max two passages per versioned paper |
| `query_fusion_cross` | Original and pinned 1J rewritten query channels, RRF, same original-query cross-encoder |
| `paper_metadata_fusion` | Title/abstract cosine paper ranking plus chunk-derived paper RRF, one closest passage per selected paper |
| `baseline_neighbors` | Same five baseline anchors plus previous/next frozen-table neighbors within paper/source/section, 6,000 passage-text token cap |

The diversity policy can return fewer than five passages when its 25-row input
pool cannot meet the cap; it never secretly expands the pool. Metadata fusion
intentionally changes the evidence policy to one passage per paper and omits the
cross-encoder, following the peer's design. Its observed effects are therefore
not attributable solely to adding title/abstract information. Query fusion may
increase the candidate union; it is not a fixed-candidate-count comparison.

Neighbors retain their own source locators/pages, no invented relevance score,
and explicit anchor provenance. All anchors are reserved before adding context.
Budget overflow drops whole neighbors and reports skipped IDs, never truncating
source text. The token cap sums passage **text** only, not citation formatting,
instructions, or the rest of a future generation prompt. Source-table adjacency
is not complete raw-document continuity; omitted/filtered content is not restored.

Existing 17 questions are consumed development cases. Four added cross-paper
cases are also **development only**, authored after inspecting this corpus, not
an untouched holdout. Three have explicit two-source quote obligations; one
deliberately requires an absent original paper. The runner validates annotations
against source-table text before execution and reports paper/quote presence
separately. These checks are not independent relevance judgements or synthesis
scoring. A missing source is not repaired by citing a secondary mention.

Upstream references (the implementation report contains full source links):

- 1B neighbors: `bc782a8ac0c8104a814d3c2ba83ba53004ac6d52`.
- 1J rerank/diversity: `78e7ba17be7014dd648efca44a1327431923ba8b`.
- 1J metadata fusion: `3b931d89d42ab1324917ecb91978c79acd9900a6`.
- 1J rewriter: `0ac8e869b8c84d9ff1e21fa4327e5e47a5764302`, preserved verbatim
  in `evaluation/peer_sources/j_query_rewriter.py` for inspection/replay.

These are **1F adaptations, not peer benchmark score replications**. The peer's
reranker file uses a differently spelled model identifier; this experiment uses
the already-cached 1F model and records its actual revision/weight hash. No new
model download, provider call or generated answer is part of these comparisons.

Historical results and provenance are recorded in the PR discussion; generated run files remain local, not in source control.
