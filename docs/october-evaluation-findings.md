# October evaluation handoff — no actual human scores yet

Status: preparation only, October 12, 2026. This report does **not** claim retrieval
quality, generated-answer accuracy, business usefulness, or KPMG stakeholder approval.
No actual review records have been supplied; `evaluation/reviews/empty_reviews.json`
intentionally contains an empty list. Keep #65 open for real frozen-run review.

## Run and review

Use the original ten questions and the [shared review protocol](../notebooks/docs/evaluation_framework.md).
Create one new output directory per frozen run:

```bash
python -m evaluation.run_benchmarks --demo --mode business --industry banking --output /tmp/kpmg-fixture-run
python -m evaluation.run_benchmarks --mode retrieval --output /tmp/kpmg-real-retrieval-run
python -m evaluation.reviews.score_reviews --run /tmp/kpmg-fixture-run/run.json --reviews evaluation/reviews/empty_reviews.json --output /tmp/kpmg-unscored-report.json
```

The real-retrieval command needs an already built local index. Summary mode can
use configured Gemini; actual business/review output requires a bound
`--research-adapter module:function`. Neither indexing nor keys are needed for
the synthetic demo. New run directories/report files refuse overwrites.

The CSV is a blank passage-review worksheet, not scores. Save actual completed
JSON review records outside tracked fixture files, using the protocol’s fields.
`run_id` is the full frozen export’s content hash; editing query, evidence,
outputs or provenance invalidates it. Reviewer kind is a declaration, not
identity authentication. A machine-generated review must use `fixture`, never
pretend to be a teammate or KPMG stakeholder.

The scoring tool validates IDs/rating ranges and computes Precision@5 with a
fixed denominator of five. It reports scored-stage counts, failures, incomplete
queries and disagreements; absent scores stay null. Fixture records are retained
but excluded from actual human aggregates. Missing rubric dimensions are rejected.
The tooling cannot establish full factual support from chunk-level checks alone;
reviewers must inspect every claim against original linked paper pages/sections.

For independent reviews, preserve one record per actual query/reviewer. Different
scores, coverage or support checks create an unresolved disagreement, not an
averaged score. A resolver may add a separate record with `adjudicates` listing
all independent reviewer names and notes explaining the evidence-based resolution.
Original records stay intact. Final end-to-end target attainment additionally
requires a non-fixture persistent-corpus run, complete scoring, all three output
metrics, no failed queries/unresolved
disagreements, and double-reviewed question types. `approved` remains false;
metric targets are not research approval or legal clearance.

## Current observations and limits

- Synthetic transport checks exercise mixed HTML/PDF metadata, cited draft
  output, pending approval, no hits, errors, frozen identities and review mechanics.
  They do not establish semantic relevance or actual model quality.
- The locked-metadata screen identifies partial coverage and possible topic gaps.
  Full-paper confirmation is still required; absent abstract matches are not proof
  of absence from every paper body.
- Current Parquet hashes identify input files, not verified Chroma contents.
  The final real run must reconcile index/corpus versions through #82.
- Actual reviewer allocation, a team pilot, second reviews and stakeholder feedback
  are not available. They have not been assigned by assumption or invented.

## Prioritized next work

1. Verify the corpus/index and bind one actual integrated run to SHA/model/prompt
   settings; retain failed queries and absent stages rather than dropping them.
2. Teammates claim bounded question batches in #65. Double-review a shared subset
   per type and every material failure/abstention; avoid sole review of own features.
3. Check every generated claim and business assumption/action against original
   evidence. Record actual ratings and explicit abstention judgments.
4. Publish scored counts, denominators, resolved/disputed examples and bounded
   evidence-backed bugs. Distinguish team assessment from received stakeholder
   validation. There are no empirical quality-driven Week 9 bugs to file yet.
