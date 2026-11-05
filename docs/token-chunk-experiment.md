# Token-aware chunking development experiment

This is a local retrieval-only experiment, separate from the running demo. It
does not modify `data/chroma_db`, re-ingest papers, change ranking defaults,
invoke generation, or claim independent human evaluation.

## Design

Freeze all 877 currently indexed texts, metadata and stored embedding vectors.
Hash them before and after the experiment. Split **existing indexed text**, not
the original HTML/PDF: the experiment cannot recover table bodies or other text
that the parser omitted, and retains overlap inherited from existing chunks.

Compare four routes with the same locally cached all-MiniLM-L6-v2 model:

- Stored original vectors and original text.
- Freshly embedded original text, to control for re-embedding differences.
- Sentence-aware slices with a 192-token budget and 32-token overlap.
- Sentence-aware slices with a 224-token budget and 32-token overlap.

Budgets include special tokens. Prefer sentence ends within the budget; hard-split
overlong sentences. Every slice is an exact parent substring and retains the
parent ID, character start/end and original source locator. Check that every
non-whitespace character is covered and no experimental chunk exceeds its budget.
This is token-aware splitting inside existing source boundaries, not a complete
document-level rechunking strategy.

Build new Chroma collections only under the new experiment output directory.
For the primary comparison, use exact squared L2 ranking of every vector against
the same query embeddings, avoiding differences in approximate-neighbor indexing.
The separate Chroma collections remain available for later integration checks.

## Development questions and measurements

Before experimental retrieval, freeze six source-informed probes covering
trip-planning numerical baselines and orchestration, RMU robustness and utility,
and binary-DPO/CU-DPO data scaling. Each has a literal expected span checked in
the frozen source. These are assistant-inspected development labels, not an
independent gold set. Finding the exact span is a retrieval diagnostic, not proof
that a generated answer would be correct. Other passages may support the question
without containing that exact wording, so a failed span check is not necessarily
a semantic relevance failure.

Also freeze the ten original benchmark questions and the ten Alesha questions
with separate namespaced IDs. Export their top-20 passages for later source
review; do not invent relevance scores for these unlabeled cases.

For each labeled probe, record exact-span presence in top five, top twenty, and
whole-passage context packing within 1,280 tokenizer tokens. The last condition
helps distinguish better retrieval from simply returning more text. A greedy
packing policy may skip a large higher-ranked passage; it is a declared diagnostic,
not an optimized or currently deployed context-selection algorithm.

Report per-case gains and regressions, not only aggregate counts. Multiple slices
from the same parent are not independent relevant facts. Never interpret distances
as confidence or the six-probe hit rate as overall accuracy.

## Reproduce and retained artifacts

```powershell
.\.venv\Scripts\python.exe -m evaluation.test_token_chunks --output data/processed/chunk-experiments/new-run
.\.venv\Scripts\python.exe -m unittest tests.test_token_chunk_experiment -q
```

Outputs refuse directory overwrite. Each run freezes source data, cases, model
weight and implementation hashes, configuration, build counts/times, top-20
results, span metrics and an original-index invariance check. Artifacts stay
under ignored `data/processed/`; source and tests can be reviewed separately.

The initial `dev-20261028-v1` stopped before index construction because Chroma's
configuration included a non-serializable embedding-function object. The harness
was corrected to record the relevant L2 configuration explicitly, preserving the
failed directory and starting `dev-20261028-v2` separately.

Three offline unit tests cover lossless spans, budget limits, sentence boundaries,
long-sentence fallback, Unicode/numbers, overlap progress and invalid budgets.
The real-tokenizer run additionally enforces budgets and source coverage on the
actual corpus. No generation-accuracy or held-out quality claim follows from them.

## Completed results — dev-20261028-v2

| Route | Indexed passages | Over encoder limit | Exact span in top 5 | In top 20 | Within 1,280-token context |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stored original | 877 | 552 | 5/6 | 6/6 | 5/6 |
| Fresh original control | 877 | 552 | 5/6 | 6/6 | 5/6 |
| 192-token slices | 1,993 | 0 | 4/6 | 6/6 | 5/6 |
| 224-token slices | 1,683 | 0 | 4/6 | 6/6 | 4/6 |

All source/indexed-record/vector hashes matched before/after for the original
index. Citation contracts passed for all three experimental collections. Fresh
versus stored original vectors differed by at most 6.52e-8 per component, with
mean cosine approximately 1; the primary results are not explained by replacing
the cached embedding weights. Budgets/source coverage passed on actual text.

| Probe | Original rank | 192-token rank | 224-token rank |
| --- | ---: | ---: | ---: |
| Trip-planning accuracy figures | 4 | 9 | 10 |
| Orchestration-controller role | 9 | 20 | 15 |
| RMU interaction resistance | 1 | 1 | 2 |
| RMU dialogue/utility caveat | 2 | 1 | 2 |
| Binary DPO at 25% data | 2 | 3 | 2 |
| CU-DPO crossover at 50% data | 2 | 4 | 2 |

The smaller slices helped the utility-caveat probe's rank in the 192-token route,
but pushed the trip-planning numerical span outside the top five. That target's
original parent has only 216 tokens: it was already within the encoder limit.
In the 224-token route it stayed intact yet ranked lower among the expanded set
of competing fragments. In the 192-token route, multiple fragments from the same
parents occupied early positions. These are observed ranking patterns; they do
not establish a universal causal effect of chunk size or semantic relevance.

**Decision:** do not replace the demo index with either tested split-only route.
Eliminating truncation is a representation benefit but did not improve this
small top-five diagnostic. Full-document sentence/section-aware chunking, source
deduplication, child retrieval with parent context, and hybrid/cross-encoder
reranking remain separate, untested follow-ups. Freeze each follow-up protocol
and retain this negative result; do not repeatedly tune on six probes and call
the result held-out performance. The 20 additional question outputs remain
unscored and available for independent passage review.
