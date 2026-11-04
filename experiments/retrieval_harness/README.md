# Retrieval harness ablations (offline, opt-in)

This follow-up to semantic calibration changes retrieval, not model weights,
production chunking, or ingestion defaults. It reuses **fixed E5-small-v2 original
semantic chunks and vectors** from the preceding experiment, on the same 19
versioned papers in PDF, HTML and cached parsed raw TeX. TeX is not rendered prose.

## Predeclared arms

Each arm independently modifies a rank-and-pack baseline; `combined` composes all
8. Every arm receives 800 and 1600 tokenizer-token caps, including passage prefix
and special-token overhead per emitted interval, but not generation-prompt framing.

| Idea | Concrete implementation | Important limit |
| --- | --- | --- |
| Selective expansion | Add one neighboring source sentence on either side only when it shares query terms and the window remains at most 400 tokens | Lexical affinity is not entailment |
| Budget allocation | MMR packing: .7 normalized relevance minus .3 maximum cosine similarity to accepted seeds, scanning 200 candidates | Seed diversity, not learned token allocation |
| Deduplication | Merge overlapping/contiguous source intervals only within the same original block, then recompute exact token cost | Does not remove paraphrased duplicates |
| Hybrid search | BM25 (k1=1.2, b=.75) plus dense reciprocal-rank fusion (k=60) | No tuned weights |
| Reranking | Rerank the dense top 40 by .5 seed cosine + .5 highest query/sentence cosine, using E5 | Late interaction, not a cross-encoder; cannot rescue candidates outside top 40 |
| Question-aware retrieval | Split query clauses at and/or/punctuation; maximum E5 clause similarity | No learned question classifier or oracle decomposition |
| Evidence-gap retrieval | After three accepted seeds, perform one lexical residual-query-term reorder | Missing query terms are only a proxy for missing facts; no gold anchors |
| Source-aware context | Heading/file-name rank fusion plus snapping seed offsets to whole source sentences or atomic TeX math | Stays inside PDF page/HTML section/TeX include block; no rendering or cross-file expansion |

The `baseline` intentionally packs raw seed passages without deduplication, to
isolate deduplication's effect. **The previous calibration selector already
performed interval deduplication**: compare against the `deduplication` arm when
judging improvements over that incumbent, not just against the new raw baseline.
All source-aware boundary restrictions apply even to controls: no fabricated
page or heading locators. Non-deduplicating arms count repeated tokens in full.
Combined includes heading fusion, reranking, clause retrieval, selective
expansion, source snapping, MMR, residual-term reordering and interval merging.
Composing heuristics need not outperform simpler arms.

## Evaluation boundaries

- These 38 questions and 19 papers have already been inspected. Split labels are
  retained for descriptive continuity (20 tuning / 18 validation), **not** as a
  fresh blind test. No new policy selection or tuning is performed.
- Retrieval receives only the query, source corpus and embeddings. Paper targets,
  answer anchors and splits are used only after retrieval for scoring.
- Scores are normalized exact designated-span coverage, not fact entailment or
  generated-answer quality. Prior documented wording false negatives still apply.
- Source availability is reported: PDF lacks anchors for two validation cases.
- Timing is descriptive and includes shared embedding work; not a production
  latency benchmark. The fixed source chunks can exceed E5's encoder limit:
  this experiment does not claim to fix existing embedding truncation.
- Same-model clause/sentence vectors are computed offline; no paid generation
  APIs, model downloads, training, production stores or index mutations.

## Reproduce

From repository root with the declared project requirements installed and E5's
pinned snapshot cached:

```sh
python -m experiments.retrieval_harness.run \
  --corpus /path/to/semantic-calibration/corpus.json \
  --cache /path/to/semantic-calibration/results \
  --output /path/to/new-output
python -m pytest tests/test_retrieval_harness.py
```

The cache must contain `e5/{html,tex,pdf}/{report.json,variants.json,
chunk-texts.json,chunk-vectors.npy,query-vectors.npy}` from the earlier runner.
Exact corpus hash/model revision mismatches fail rather than silently rebuilding.
Full retrieved source intervals and locators are saved in the output; compact
scores, per-query outcomes, verification and artifact hashes are committed here.
