# Handoff for Khoi — Alesha retrieval baseline

I reviewed the frozen retrieval-only run `79ba9c5b875fd85eeed8c019cb31fef1830d241810a75f2aa45ff7b11a2c4749` (10 queries, top 5; generation not requested). All 50 retrieved passage texts were available in `run.json` and rated. Mean Precision@5 is **0.86 (43/50 relevant passages; 10 queries, 5 passages each)**. The per-query results and passage-level reasons are in [scorecard.md](./scorecard.md); ratings are in [review_completed.csv](./review_completed.csv).

**Start with Q3:** ranks 4–5 (`2604.00324v1_c0071`, `2604.00324v1_c0099`) are about adversarial training/jailbreak behaviors, not multi-turn unlearning. Q4 ranks 1–4 contain relevant ACDC/mechanistic-interpretability text, but the run metadata labels them as *The Persistent Vulnerability of Aligned AI Systems* (`2604.00324v1`); verify document boundaries and chunk-to-paper metadata. Q4 rank 5 is a references passage. Also check bibliography retrieval on Q5 rank 3, Q6 rank 4, Q7 rank 2, and Q10 rank 1; those are verified irrelevant results.

The run record says `dirty: true`, `corpus_mode: unverified_local_index`, and `indexed_corpus_sha256: null`. Its source hash for `data/processed/chunks.parquet` is recorded, but that file was unavailable in the inspected workspace, so exact index identity/reproduction cannot be confirmed. The historical raw [run.json](./run.json) and [review.csv](./review.csv) are unchanged. Please investigate against a copy or a new run; do not overwrite this baseline.

This is retrieval relevance only—not a measurement of summary, citation-grounding, or business-implication accuracy.
