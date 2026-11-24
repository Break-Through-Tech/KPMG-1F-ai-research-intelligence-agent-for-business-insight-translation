# B2 selector handoff

## Scope and reproducibility

The diagnostic imports the existing Baseline/B2 adapter from the pinned research checkout with table comparisons disabled, the recorded demo-100 corpus, its exact local MiniLM encoder/reranker, and two CPU threads. It profiles the return of FacetRetriever.rank_facets to obtain the ranked candidate IDs, cross-encoder rank maps, the index vectors and shortlist. It verifies the index identity and the first 30 IDs against the previous replay. No provider calls, production edits, or external framework installs are required.

compare_selection.py reads only question wording and the previous retrieval trace for replay integrity. The selector has no reference IDs, answers, scores or expected paper identifiers. score_selection.py loads the frozen reference key only after selection. The comparator treats a point as covered only if every member of at least one reference anchor group is present. Historical scores, partial evidence and new exact-anchor counts are separate.

## Tested algorithm

Keep the first 60 existing finalist IDs as the shared shortlist for C and D. A and B are unmodified slices of the existing final list. Relevance is 1/log2(rank+1) from the final B2 rank, which already incorporates the cross-encoder, rank fusion and existing anchor selection. This avoids calibrating raw logits across facets.

C uses the existing query-nearest search view for each parent; normalize its vector, then compute cosine between candidates. Greedily select 8 using 0.75 * relevance - 0.25 * maximum cosine to selected evidence. Candidate order breaks ties.

D uses the existing deterministic facet rankings. For each facet, weight its top-20 candidates by 1/sqrt(facet rank). It also checks named entities against normalized titles or, if no title matches, abstracts in the original paper shortlist. Only uniquely resolved names can add aspects, and only when two distinct papers were identified. For these paper aspects, the weight is 1/sqrt(within-paper rank). For diversity, D compares token-set Jaccard of parent text or table row labels, and penalizes overlap only within a paper.

    coverage[aspect] = 0
    selected = []
    repeat up to 8 times:
        gain = max over aspects of max(0, weight(candidate, aspect) - coverage[aspect])
        redundancy = max Jaccard with a selected passage from the same paper
        choose argmax(relevance + 0.35 * gain - 0.20 * redundancy)
        update each aspect's best weight
        append chosen parent ID

These are experimental heuristics with one fixed parameter set. D does not require that a paper receive a slot, and its aspect scores are only relevance proxies. It does not assemble table pairs, generate new facets, or rescue items outside the existing reranked pool. The name heuristic omits common single-uppercase and short aliases; title and abstract substring matching can also misidentify names. Do not treat this prototype as validated entity resolution.

## Code integration points if a later variant passes

- src/experimental/balanced_retriever.py, FacetRetriever.rank_facets: expose final IDs and masked per-facet ranks after calculating the current ordering, immediately before return. Keep the existing path as the default.
- src/experimental/b2.py, open_b2.retrieve: apply an opt-in packet selection policy before engine.resolve, and include its explicit identity, passage cap, and parameters in provenance. Preserve existing API bounds and behavior for default callers.
- src/experimental/evidence_coverage.py, comparison_pair: reuse the existing fail-closed, same-table pairing as a separate test arm. Preserve versioned source and cell identity. Add distinct table-metric/configuration matching only after independent offline evidence shows it helps.
- Do not change chunking, synthesis, table extraction, or citation validation for this experiment. NumPy and the existing MiniLM models suffice. Use unchanged parent rows returned by resolve, including exact arXiv version and cell IDs.

## Acceptance gates for a new selector

Freeze the rule, weights, corpus and an eight-passage cap before a fresh, independently source-reviewed set is seen. Include both single-paper multi-part questions and explicit multi-paper comparisons, table pairs with setting confounders, near-duplicate passages with different numbers, and evidence-insufficient questions. Measure exact and independently reviewed equivalent-anchor coverage, full packets, recovered and displaced points, off-topic selections, and p90 cost. Predeclare a minimum meaningful gain and require no loss of critical controls or increase in unsupported publication before rollout. Check determinism, no duplicate IDs, source and table identity, bounded memory, unknown entities, missing facets and repeatable default ordering. No benchmark answer text enters selection. Do not tune weights against C01–C15.

Multi-Agent could reuse a proven packet selector before synthesis, with verified anchors from earlier rounds pinned and remaining slots bounded. This study tests first-pass Baseline packets only. It supplies no evidence about Multi-Agent retries or final-answer accuracy.

## Research sources

- [CoveR paper and benchmark comparisons](https://arxiv.org/html/2605.28522v1#S5) and [training/inference repository](https://github.com/DylanJoo/CoveR). CoveR learns sub-question answerability with a new encoder and compares MMR and multi-query fusion. This experiment borrows the coverage objective and uses existing B2 ranks. It does not run the trained checkpoint or claim its benchmark gains.
- [PaperQA2 Docs.retrieve_texts](https://github.com/Future-House/paper-qa/blob/main/src/paperqa/docs.py) oversamples and invokes its vector-store MMR selector (fetch_k = 2k). Our C uses B2's existing candidate pool and B2 rank relevance. No PaperQA2 index, embeddings, or generative evidence stage are needed.

## Decision and verified results

| Arm | Exact points | Full evidence packets | Gained / lost vs. A | Median passage tokens | Off-reference-paper slots | Median added selector wall time | Peak traced allocation |
|---|---:|---:|---:|---:|---:|---:|---:|
| A: B2 / 8 | 22/41 | 5/15 | 0 / 0 | 2,303 | 9/120 | reference | — |
| B: B2 / 16 | 31/41 | 9/15 | 9 / 0 | 4,521 | 32/240 | same ranking, larger slice | no additional ranking allocation measured |
| C: MMR / 8 | 22/41 | 4/15 | 1 / 1 | 2,321 | 18/120 | 1.28 ms | 394 KiB |
| D: facet/paper coverage / 8 | 22/41 | 5/15 | 0 / 0 | 2,287 | 12/120 | 14.19 ms | 880 KiB |

CPU-only selector timing excludes B2, scoring, serialization and provider inference. Peak allocations are from tracemalloc and exclude untracked native/process memory. Token counts use the existing index tokenizer on passage text and exclude prompt framing, metadata, and provider tokenization. Every packet had zero within-packet token-set Jaccard pairs at or above 0.65 (table labels used for table rows). This conservative proxy does not rule out semantic redundancy. Off-reference-paper counts measure paper identity, not semantic irrelevance.

C07: A and C failed to deliver any KG²RAG passage; B delivered both research papers and recovered C07.2; D delivered both papers but its KG²RAG passage was related-work background and scored zero. C15 included both papers in every arm but each retained only one full required point. C14: all arms retained both authors’ discussion anchors and narrative F1/directional latency evidence, but neither exact Table 1 latency row. C08.2 never reached reranking, so no selection arm could recover it.

Targeted equivalent-source check: C02's conclusion supplies fail-closed behavior and negligible trade-off for unrestricted content across arms, but omits the full comparator/configuration requirements. C14's narrative F1 evidence is present in all arms and lacks both precise latency values. C15's abstract gives general fine-tuning gains, without the required detailed French and smaller-model comparison. These fragments receive no extra full-point credit here. Equivalent passages were spot-checked, not exhaustively scored across the 41 requirements.

Prior controls: all four kept the CU-DPO abstract. A, B and D kept the AgreeMate fairness row; C dropped it. Willow remained an evidence-insufficient control. C introduced a paper row mentioning an unrelated fictional place with the same name. No pipeline answer was generated on these controls.

E was deferred: D has no fixed-budget gain and lacks a calibrated detector for uncovered evidence, so there is no basis yet for shipping a D-based adaptive policy.

**Recommendation: keep A as default, reject C and D as tested, and trial B as an explicit, isolated top-16 option on genuinely fresh data.** Existing open_b2.retrieve already accepts 16 and uses the same final order. For the first trial set the existing research top_k through the isolated launcher. Do not edit FacetRetriever or the shared application for a depth-only trial. Predeclare a runtime token ceiling and instrument prompt bytes before the first live comparison. Because the provider context increases, validate complete supported answers, citation entailment, abstentions, latency and unsupported claims before adoption. Add tests for the default eight, opt-in sixteen, stable eight-ID prefix, short candidate pools, byte/token ceilings, and unchanged citation and review behavior. B is an evidence-coverage improvement only. C07 and C14 merit a later test of role-aware paired evidence, separately from C08 candidate discovery. Do not change weights on C01–C15.
