# Adaptive depth engineering handoff

## Reproduction

Run compare_depth.py from this directory in the existing B2-capable Python environment with HF_HUB_OFFLINE and TRANSFORMERS_OFFLINE set. It uses the same local demo-100 bundle, encoder, reranker, B2 code hashes, and table-comparisons-off setting as the saved C01–C15 replay. It checks the existing index identity and exact first 30 IDs. No generation provider is initialized. The separate score_depth.py consumes the sealed reference anchors only after packet selection.

The four fixed arms deliver the original prefix of 8, 16, 20 or 30. The live B2 adapter currently limits top_k to 20. Depth 30 is an offline slice of its internal order. Adaptive arms preserve the original order and drop the tail if it exceeds 30 passages or 8,000 passage-text MiniLM tokens. This is a separate text-only budget. It does not account for the provider's tokenizer, prompt structure, serialized fields, or output reserve. Fixed policies are uncapped comparators. If all observed fixed packets also fit, the quota is nonbinding here.

## Tested rules

- Complexity: derive existing B2 facets from the question. Use 30 for two facets or a facet plus a comparison cue, 16 for a facet or comparison cue, and 8 otherwise. Comparison cues are each, both, versus, vs, compare-family words, and trade-off. This routing heuristic borrows the Adaptive-RAG idea. It does not run its trained classifier or iterative generation.
- Facet/paper proxy: at 8, 16, 20 then 30, stop when each existing facet has at least one of its top-three cross-encoder candidates and, when the same comparison cues occur, the prefix represents at least two shortlisted papers. Use 30 if no earlier checkpoint passes, then apply the separate text budget. This is a low-cost coverage proxy rather than a semantic sufficiency certificate. A query with no facets can pass vacuously; two retrieved papers need not be the requested papers and a same-paper comparison need not involve two papers.
- Score gap: sort the first 60 B2 finalists by the main-question raw cross-encoder logit; find the largest adjacent gap at positions 8–30; map the leading IDs to the shortest prefix of the original B2 order, then cap it. This borrows Adaptive-k but changes the score type, search window and output ordering. Scores across questions or facets are not calibrated probabilities. A cross-encoder can give related-work passages a high relevance score even when they cannot supply a requested number or caveat.

Pseudocode:

    rank once using existing B2
    scores, facets, versioned candidates = ranking trace
    intent = depth_policy(question, scores, facets, candidates)
    prefix = candidates[:min(intent, 30)]
    while passage_tokens(prefix) > 8000: remove last passage
    return original parent rows in B2 order

## Interpretation and integration

Unnecessary expansion means a packet exceeding eight passages that adds zero complete exact-anchor groups. This proxy can miss equivalent or useful partial evidence. Premature stopping means a subset of points visible at fixed 30 is missing at the chosen depth; the result table counts affected questions and points. Irrecoverable anchors outside the top-30 window are excluded from this specific error metric. Passage count and token p90 use nearest rank for percentiles. No result establishes final answer quality.

All policies pay the same existing retrieval/reranker cost; there is no savings in encoder/cross-encoder compute. Record rule-only time separately. Larger text may change generation latency and quality, but this study executes no generation.

For any approved fixed-depth pilot, use existing top_k configuration in src/experimental/demo.py create_research and src/experimental/b2.py open_b2.retrieve. Defaults remain intact. Depth 30 would require a reviewed opt-in API limit change or a separate launcher using the existing FacetRetriever.rank_facets order and resolve. Preserve the cap and original citation IDs downstream. Check the actual full provider payload against a predeclared budget before any live trial. For future adaptive work, expose a bounded internal trace at src/experimental/balanced_retriever.py FacetRetriever.rank_facets with per-facet rank maps, main CE scores, and versioned candidate IDs. Keep confidence reporting out of user-facing claims until independently calibrated.

For validation, pre-register complete packet coverage, expected shortfall, p90 token cost, and allowable regressions on fresh independently reviewed single-paper, multi-paper, numerical table, and insufficient-evidence questions. Fit any calibration on separate data and evaluate once on an untouched split. Keep all-or-none table pairs and version identity, decline low-confidence role bindings, and test no-facet, irrelevant high-scoring, flat-gap and token-bound cases. For Multi-Agent, apply any validated policy to initial evidence only first; test preservation of previously verified claims before applying it to retries. Do not increase context in both stages by default.

## Research

- [Adaptive-RAG](https://aclanthology.org/2024.naacl-long.389/) and [classifier](https://github.com/starsuzi/Adaptive-RAG/blob/main/classifier/run_classifier.py). Learned routing between no retrieval, single retrieval and iterative retrieval. Our rule is an inexpensive proxy, with none of the paper's learned complexity calibration.
- [Adaptive-k](https://aclanthology.org/2025.emnlp-main.1017/) and [largest-gap source](https://github.com/megagonlabs/adaptive-k-retrieval/blob/main/adaptive-k-retrieval/retriever.py). Largest adjacent gap in sorted scores gives a single-pass cutoff; reference code has optional excluded tails. A score transition estimates relevance, not jointly sufficient evidence.
- [Tail-Aware Adaptive-k](https://arxiv.org/abs/2606.11907) estimates a relevant-versus-noise boundary under distribution assumptions. Useful comparison only after checking calibration on B2's score distribution; no published finding here verifies a complete evidence packet on B2.
- [CRAG](https://arxiv.org/abs/2401.15884) and [upstream inference](https://github.com/HuskyInSalt/CRAG/blob/main/scripts/CRAG_Inference.py). A trained evaluator routes by retrieval confidence and can invoke corrective retrieval. Local evaluator inference is possible, but adding it brings a new model and calibration; doc relevance is not set-level completeness.
- [Sufficient Context](https://github.com/hljoren/sufficientcontext) uses a generative autorater benchmarked against human labels. Borrow its labeling protocol offline, not its runtime gate. [TRAQ](https://aclanthology.org/2024.naacl-long.210/) supplies a calibration template; its answer-level guarantees do not carry over to missing-evidence detection, especially on a 15-question development set.
## Token-window comparison

Within each saved first-30 ranking, compare longest consecutive prefix with skip-fit packing at 4,000, 6,000, and 8,000 tokens. Skip-fit scans in rank order, keeps a whole parent only when its cost fits, and continues after a non-fitting row. Neither approach edits text, cuts table cells, changes order, or uses labels. The budgets do not search beyond rank 30. The follow-up applies the same budgets to each adaptive decision.

| Policy | Exact points / 41 | Full / 15 | Mean/max passages | Median/p90 tokens | Points per 1k tokens |
|---|---:|---:|---:|---:|---:|
| Fixed 8 | 22 | 5 | 8/8 | 2,303/2,633 | .655 |
| Fixed 16 | 31 | 9 | 16/16 | 4,521/4,988 | .458 |
| Fixed 20 | 32 | 9 | 20/20 | 5,770/6,189 | .380 |
| Fixed 30 | 37 | 11 | 30/30 | 8,129/9,701 | .300 |
| Prefix 4k | 26 | 7 | 13.87/18 | 3,898/3,985 | .447 |
| Skip-fit 4k | 26 | 7 | 14.60/19 | 3,955/3,992 | .439 |
| Prefix 6k | 32 | 9 | 21.13/27 | 5,790/5,951 | .367 |
| Skip-fit 6k | 34 | 10 | 22.00/28 | 5,951/5,992 | .381 |
| Prefix 8k | 37 | 11 | 27.87/30 | 7,836/7,925 | .323 |
| Skip-fit 8k | 37 | 11 | 28.13/30 | 7,859/7,985 | .322 |

The tokenizer-only pass over all 30 entries cost 17.8 ms median and 21.9 ms p90. It included no reranking; hot-cache timings or tokenizer changes may alter it. Cache counts under chunk content hash and tokenizer revision. MiniLM counts are a development proxy. Before dispatch use the chosen provider's tokenization or bounded estimator over the serialized request, including metadata, schema, system instructions, previous/verified context and output reserve.

A reference-aware oracle only for diagnosis picks the shortest prefix of at least eight preserving everything the fixed 30 contained. It would average 15.07 passages with median 2,796 tokens and 37 exact points. No production policy can use these labels. This shows how much headroom better gap signals might offer.

6k skip-fit recovered C03.3 and C08.1 beyond 6k prefix, with no exact-anchor displacement vs that prefix. C08.2 remains outside the pool. It still cannot recover the missing C14 pair. Preserve whole original parent rows. Skip-fit introduces a general risk of dropping a long methods passage or splitting a paired table, so do not ship it based on this small set. Group indivisible evidence pairs before packing in a later separately scoped experiment. Lexical near-duplicates use Jaccard >=.65 on token sets, using table row labels to avoid repeated captions creating false matches. High-depth arms can carry more near duplicates and more papers outside the reference set, while semantic redundancy and relevance still need adjudication.

### Larger libraries

Measured only the pinned 100-paper bundle. Per-request passage cap and token-packing scan stay bounded after ranking. At 500 and 1,000 papers the current dense distance scan, lexical scoring, and table/candidate indexes still operate on a larger corpus. A fixed three-paper shortlist and facet/role heuristics can become bottlenecks even when the prompt cap holds. At the observed 11,030 384-d float32 views per 100 papers, raw vector storage would extrapolate from about 17 MB to 85 MB and 169 MB if view density stays constant. This excludes corpus text, Python objects, temporary arrays, models and non-linear reranking costs. It is not RAM or latency measured on those libraries.

Test on version-compatible nested 100/500/1,000-paper bundles, using identical anchored queries plus newly in-scope and still out-of-scope controls. Separately measure shortlist and rerank-pool recall, final packet recall, p50/p90 retrieval latency, peak RSS and serialized token cost. Recheck any threshold calibration as the library changes. Keep the depth and budget policy opt-in and compare it against a fixed prefix at the same provider token budget.

## Adaptive verdict

Replayed all 15 C cases and three prior controls with the pinned B2 runtime. An early execution failed the exact-order assertion for C07 because Windows decoded KG²RAG using its default code page. Both input paths now explicitly use UTF-8. Only C07 differed under the default decoding, so completed C01–C06 results were reused. All final C case ranks and token counts matched the independently processed saved trace. All adaptive outputs passed the 30-passage and 8,000-token caps.

| Policy with 8k cap | Exact points | Full | Mean/max depth | Median/p90 tokens | Expanded without gain / expanded | Premature questions / points |
|---|---:|---:|---:|---:|---:|---:|
| Complexity | 33/41 | 10/15 | 17.87/30 | 4,709/7,890 | 7/13 | 3/4 |
| Facet/paper | 22/41 | 5/15 | 11.07/30 | 2,379/6,115 | 3/3 | 9/15 |
| Score gap | 35/41 | 10/15 | 22.27/30 | 6,346/7,867 | 8/15 | 2/2 |

The 8k cap removed no exact points from those policies and lowered p90 versus their uncapped equivalents. Score gap and complexity did find all three C07 points, but both facet/paper and score gap miss recoverable evidence elsewhere. For C11 the complexity rule and facet rule stop at 8 despite two points available at 30. For C14 the score gap misses the single latency row recoverable at 30, while the second exact row remains outside the 30 window. All checked modes kept the exact AgreeMate and CU-DPO anchors. The gap rule expanded both simple controls and expanded Willow to 17; the latter is an evidence-insufficient control, not verified abstention in this replay.

Shared retrieval median/p90 were 11.63/20.74 seconds on the local replay. Added rule medians: complexity .049 ms, facet/paper .019 ms, score gap .041 ms, excluding text tokenization. The skip-fit budget loop over precomputed lengths cost ~1.75 microseconds median in a local repeated microbenchmark. No additional generator calls, ranking passes, index builds or generator timing.

Keep fixed 8 as default. Validate fixed 16 and 6k skip-fit (same original ranking, first 30 window) once on fresh independently reviewed questions before choosing a wider default. Fixed 16 remains the strongest measured fixed depth if the practical ceiling is roughly 5k at p90. For pure recall fixed 30 is highest, but 8k rank prefix matched it here with a deterministic text ceiling; use 8k prefix as an offline upper reference. Reject facet/paper as a sufficiency gate. Keep score gap as a diagnostic only: its 35 points do not establish an advantage over 6k skip-fit at lower p90, or over 8k prefix on recall. Freeze the deployment budget and thresholds before looking at fresh judgments. No change to Baseline, Multi-Agent, or previous evaluation artifacts.
