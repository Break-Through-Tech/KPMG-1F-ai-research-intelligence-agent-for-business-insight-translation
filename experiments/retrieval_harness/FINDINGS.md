# Retrieval harness findings

All eight ideas were implemented as bounded offline heuristics and run on the
same fixed E5 chunk index. 8 isolated arms + raw baseline + combined = 10 arms,
2 budgets, 3 source formats: **60 experiment cells / 2,280 query contexts**.

## Most promising next step: hybrid retrieval

At 1,600 tokens on the 18 descriptive validation questions:

| Format | Existing deduplicated selection | Hybrid BM25 + E5 | E5 sentence reranking |
| --- | ---: | ---: | ---: |
| HTML | 15 | 17 | 17 |
| Parsed raw TeX | 12 | 16 | 14 |
| PDF | 13 | 14 | 11 |

Hybrid also improves all three formats at 800 tokens (9→14, 9→14, 7→12).
This makes it the most consistent candidate for a **new evaluation**, not a
production acceptance decision. Reranking helps the clean-source diagnostic but
regresses PDF at 1,600; it should not be enabled globally from these results.

## What the eight experiments tell us

1. **Selective expansion:** small clean-source improvements, HTML 15→16 and TeX
   12→13; PDF unchanged at 13. Query-term overlap is a modest first heuristic,
   not a test of whether neighboring text supplies a missing premise.
2. **Budget allocation:** this MMR recipe regresses at 1,600 in every format.
   Penalizing related passages can discard complementary supporting evidence.
   This is a plausible mechanism, not a proven causal diagnosis from the score.
3. **Deduplication:** no change in complete-span counts on this fixed original
   semantic index, which has little seed overlap. It remains a source/budget
   hygiene operation; no new quality gain is claimed. Prior harness already did it.
4. **Hybrid search:** gains at both budgets in all formats; strongest consistent
   signal. Keyword retrieval complements E5 on this question set.
5. **Reranking:** gains on HTML/TeX, mixed PDF. The implementation is same-E5
   sentence-max late interaction, not a stronger cross-encoder model.
6. **Question-aware retrieval:** naive clause-max scoring is flat or worse at
   1,600. It can favor one clause instead of covering the whole question.
7. **Evidence-gap retrieval:** query-term residual reordering regresses at 1,600.
   Missing words are not reliable evidence of missing facts; a more semantic
   coverage check would be a different experiment.
8. **Source-aware context:** this heading/file-name fusion and atomic-boundary
   snapping arm drops HTML 15→5, and is unchanged on TeX/PDF. Do not conflate
   preservation of citations (required in every arm) with heading-based ranking
   (the experimental heuristic here). Further isolate the two components before
   assigning causality.

The **combined arm is not a winner**: HTML 5, TeX 13, PDF 14 at 1,600.
Combining heuristics compounds their failure modes. No experimental arm is wired
into production, and none of these results justifies switching on all eight.

## Measurement and reproducibility

- Same 19 matched papers and 38 already-inspected development questions, with
  the existing 20/18 paper-separated split. This is not new held-out evidence.
- Fixed snapshot, original chunks, candidate cap and budgets. No threshold or
  arm selection was tuned on these results. Full arm table is disclosed.
- Exact designated-span containment remains the scoring proxy. Alternative
  wording can be answerable yet scored as a miss, as documented in the preceding
  calibration experiment. No generated answers or human fact-coverage labels.
- PDF anchors exist for 16/18 validation questions; HTML/TeX for all 18.
- Verifier independently recomputed all token costs and span outcomes and checked
  **11,088 source intervals**, exact source text, citation locators and cache
  query order. All **2,280 contexts** obey their token caps.
- Encoder truncation in existing cached chunk vectors remains; larger context
  tokenizer counts used for packing are not fed back into E5 as whole contexts.
- Full contexts and cache hashes are recorded in `results/artifact-hashes.json`;
  compact per-query outcomes, protocol, environment and source question labels
  are committed. Source archives/large vector files are not duplicated in Git.

Next: test the fixed hybrid recipe on newly reserved papers with fact-coverage
labels; then separately test hybrid plus reranking and selective expansion.
