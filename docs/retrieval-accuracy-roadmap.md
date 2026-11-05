# Research-backed retrieval and accuracy roadmap

Prepared October 28, 2026. This document proposes experiments and acceptance
criteria; it does not change the corpus, index, ranking defaults or team assignments.

First experiment completed: [token-aware splitting results](token-chunk-experiment.md).
Both tested smaller-chunk routes eliminated truncation but reduced exact-span
top-five hits on six development probes. No default/index replacement is justified
by that run; retain the current baseline while evaluating subsequent methods.

## Findings from our current implementation

1. The indexed UI uses `src.retrieval.search`, a dense top-k search. The repository
   already has `HybridRetriever` (BM25 + dense + reciprocal-rank fusion, optional
   reranker), source-checked intent reranking, and comparison harnesses. Evaluate
   those implementations before writing a second retrieval stack.
2. Read-only inspection of the existing 877-record `arxiv_papers` collection with
   the locally cached all-MiniLM-L6-v2 tokenizer found 552 passages longer than its
   256-token input limit (62.9%). Median length including special tokens was 307;
   maximum was 775. These are raw token counts, not a fresh embedding/index run.
   No index was rebuilt. The tokenizer warned about lengths because truncation
   was deliberately disabled for counting; no overlong tensor was sent to the model.
3. The model author documents default truncation beyond 256 word pieces. Current
   indexing uses `model.encode(texts)`, so unseen passage tails are a plausible
   contributor to retrieval misses, not a proven explanation for any specific case.
   Source: [author model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).
4. `src/data_ingestion/html_parser.py` keeps figure/table captions but removes
   their bodies. It also drops display equations and proofs. Newer preview/TeX
   features are separate paths; do not assume they repaired the existing index.
5. The current quality check validates model judgments, not independent source
   support. It cannot recover omitted evidence and may share generator errors.
6. A measured live pair took 41.97 then 34.89 seconds, with retrieval around 0.016
   seconds. More retrieval computation may be affordable, but model-call latency
   remains the dominant observed cost. This single pair is not a latency guarantee.

## Priority 0 — Freeze an evaluation set and diagnose failures

Reuse the existing evaluation runner, contracts, frozen-run capture and review
records. Keep all examples already inspected or tuned on in development. Propose
20 development questions and 10 separately authored held-out questions as an
initial pilot, not an official benchmark or statistically adequate final study.
Include factual lookup, numerical comparison, limitations, conflicting evidence,
multi-paper synthesis, business transfer, partial support and no-answer cases.

Review original papers to label answerability and required evidence spans before
tuning. Keep original source/version/section/page and span-level references so
labels survive re-chunking; do not define correctness only by current chunk IDs.
Two independent people should review a shared subset and material failures, with
disagreements retained and adjudicated. The coding assistant does not assign or
impersonate reviewers. A held-out question over familiar papers is not evidence
of generalization to unseen papers.

Classify failure at the earliest supported cause: outside corpus, extraction loss,
chunk/embedding representation, candidate retrieval miss, reranking miss,
generation omission/distortion, or unsupported business transfer. Do not conflate
execution errors with missing evidence. Maintain an oracle-evidence experiment:
give the generator human-selected correct passages to distinguish retrieval from
generation failure.

Measure evidence Recall@20 in a pooled, labeled candidate set, nDCG@5/Precision@5,
required-fact coverage, claim support, citation correctness and completeness,
numerical accuracy, correct abstention and false abstention. Report answer rate
alongside error rate so abstaining on everything cannot look successful. Measure
latency distributions and failure counts, not only successful averages.

Sources: [RAGChecker](https://arxiv.org/html/2408.08067v2) motivates separate
retriever/generator diagnosis, claim recall and noise sensitivity;
[ALCE](https://aclanthology.org/2023.emnlp-main.398/) treats citation quality as an
evaluation target beyond producing citation markers. Automated judges require
human calibration and should not label their own training/development outcomes
as independent ground truth.

## Priority 1 — Repair representation and recover scientific evidence

### Token-aware chunks

Keep sentence/section boundaries and original HTML/PDF citation locations. Test
128-, 192- and 224-token passage budgets with modest token overlap, reserving room
for special tokens and any title/section prefixes. These are candidate settings,
not a claim that one size is optimal. Validate the complete embedded input with
the actual tokenizer; target zero silent truncation. Avoid splitting a result
away from its subject, baseline, units, uncertainty or adverse condition.

Test retrieval on smaller chunks with bounded source-adjacent expansion for
generation. Every expanded passage retains its own ID and locator; do not cite a
neighbor's text under the originally selected chunk ID. Compare against existing
neighbor-context helpers before adding another implementation.

Build a separate versioned index; preserve the current 877-record baseline.
Freeze source bytes, parser/chunker code hashes, tokenizer/model identity,
embedded input identity and citation mappings. Re-map evidence-span labels rather
than treating changed chunk IDs as different facts.

### Tables, equations and captions

Start with table-backed numerical questions from known papers. Retain table IDs,
caption, headers, row labels, cells, units and footnotes; serialize rows with the
headers needed to interpret them. Keep source/version/anchor or PDF page and
traceable canonical text. Missing cells must be marked unavailable, never filled
by a language model. Keep narrative and structured evidence distinguishable.
Evaluate comparisons, directions and units, not merely whether a number survived.

Prefer existing version-matched HTML structure. Test a layout-aware PDF fallback
only where needed; do not add OCR/VLM services or compile untrusted TeX merely
because a benchmark exists. Track excluded proofs/equations as coverage limits
and recover them only with a citation-preserving, tested parser path.

Source: [OmniDocBench](https://arxiv.org/abs/2412.07626) evaluates document parsing
across layouts and document types. It supports structure-sensitive evaluation;
it does not identify a universally best parser for our corpus or establish that
changing parsers fixes our retrieval results.

## Priority 2 — Compare existing retrieval routes fairly

First use one frozen representation to compare dense-only, BM25-only, existing
hybrid RRF, and hybrid plus the existing local cross-encoder. Retrieve a candidate
pool of about 20–50, then select a small final evidence budget. These sizes must
be evaluated, not fixed as optimal. Keep generator, prompt, model/effort and final
context-token budget constant. Separately compare the old versus token-aware
representation so effects are not attributed to the wrong change.

Pool candidate results for human relevance judgments, including missed results;
do not judge only the final five from the preferred method. Evaluate related-
topic traps, paraphrases, sparse technical terms, numerical comparisons and
negative results. Never force known paper IDs or benchmark-specific source slots.
Cross-encoder scores and vector distances remain ranking signals, not confidence.

Only then test MMR as an optional redundancy penalty. Preserve complementary
passages from the same study and conflicting evidence across studies; no rigid
one-paper cap. MMR is for diversity, not evidence sufficiency or truth.

Sources: [BEIR](https://arxiv.org/abs/2104.08663) shows BM25 is a robust baseline
and reranking can improve average retrieval at additional computational cost;
[MMR](https://aclanthology.org/X98-1025/) explicitly balances relevance and novelty.
Neither establishes which route wins on our scientific corpus.

## Priority 3 — Evaluate evidence sufficiency and claim-level accuracy

Build independent labels for full/partial/absent support for the actual subject,
comparison and requested setting. Distinguish a useful conditional transfer from
a demonstrated industry result. Retain negative findings, uncertainty and
alternative explanations. Check all material clauses and numbers in a sentence,
not only whether its quote exists. Evaluate limitations and proposed business
actions as well as research findings.

Use our current review as one candidate, plus blinded human checks and optionally
a separately calibrated entailment model/judge. Different models are not by
themselves independent ground truth. Review retained and rejected claims to
detect false rejection. Preserve correct partial answers rather than making
abstention the only way to avoid errors. No automatic approval.

Source: [Sufficient Context](https://arxiv.org/abs/2411.06037) distinguishes missing
context from failure to use sufficient context and studies guided abstention.
This is a better next diagnostic than adding another uncalibrated critic call.

## Priority 4 — Pack context carefully and reduce waiting

Select complementary evidence covering each subquestion, including results and
limitations. Test evidence order and bounded expansion. Do not automatically
increase top-k or feed entire papers: useful evidence can be diluted by adjacent
text and position effects. Source: [Lost in the Middle](https://arxiv.org/abs/2307.03172)
reports sensitivity to evidence position in its tested models; re-test our model
rather than assuming the same magnitude of effect today.

Keep existing timings. Repeat randomized/interleaved medium/low-effort comparisons
on identical evidence; report median and tail latency plus support and abstention
quality. Add progress/streaming only with honest provisional-versus-checked labels:
never display an unchecked draft as an accepted finding. For repeats, prefer
explicit saved-result replay; any future cache must bind exact query, corpus,
index, model, prompts and configuration and disclose replay. Never reuse approval.

[FrugalGPT](https://arxiv.org/abs/2305.05176) motivates measured cost/quality routing;
our low-effort option is not a learned cascade. A calibrated small local reranker
may avoid another remote model call, but replacing the quality reviewer requires
evidence. Multiple agents belong only in genuinely independent work, not as an
assumed remedy for sequential dependencies.

## Release gates and order

1. Freeze labels/baseline and publish failure taxonomy; independent checks first.
2. Run token-aware chunking and table-recovery experiments on separate indexes.
3. Compare existing hybrid/reranking routes, then optional diversity/context packing.
4. Evaluate the best supported combination on untouched cases once; report all
   failures and uncertainty, including adverse supported/abstention outcomes.
5. Promote only changes with evidence of better retrieval/required-fact coverage,
   no material support/numerical/false-abstention regressions in the reviewed set,
   valid source locators and reproducible latency/provenance. Agree numerical
   thresholds before the comparison, based on the baseline and review budget.

These are proposed team acceptance gates, not guarantees or stakeholder approval.
No owners, deadlines, accuracy percentages or completed experiments are invented.
An overall RAG best-practices study also supports evaluating interacting choices
rather than stacking every technique: [Wang et al.](https://arxiv.org/abs/2407.01219).
