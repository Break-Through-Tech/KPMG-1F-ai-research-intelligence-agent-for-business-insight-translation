# Issue acceptance reconciliation — October 13, 2026

Audited merged main `eaaf0e819b5c7aeb9a78be08924a506c10620666` and published
follow-up artifacts. Merged code is not automatically full acceptance. Existing
PRs #84–#93 were already merged before this recovery and were not replayed.

| Issue | Verified implementation/evidence | Remaining acceptance / disposition |
|---|---|---|
| #44, quality assessment parent | #40/#43 reports merged in #91/#92; category status and explicit untested boundaries documented | Closed after checking the assessment deliverables. Not a claim that all numeric/table/diagram defects are repaired |
| #76, shared contracts | Pipeline contains structural checks and test fixtures | Dedicated `research_contracts.py`, source-specific schema validation, documented reusable fixtures/versioning still missing; keep open |
| #77, summarizer | Interim Gemini summary adapter merged through #85 | Dedicated evidence-grounded summarizer/acceptance criteria not delivered; interim adapter is not full closure evidence |
| #78, workflow/CLI | Injected pipeline, generation configuration, CLI and docs merged in #84–#87; 86 existing offline tests pass | Actual summary/business/review adapter join and generated-output proof remain; keep open |
| #80, business translation | Prompt candidates in #93 and injected workflow contract | No `business_translation.py` implementation or real bound output; keep open |
| #81, review integration | Existing standalone regulatory checkpoint and pipeline approval safeguards | No dedicated `research_review.py` adapter/review packet; preserve separate regulatory namespace and explicit human approval |
| #82, corpus validation | New locked 25-paper/877-chunk HTML audit, actual-source text/anchor checks, Parquet and persistent deterministic transport; separate real forced-PDF diagnostic | Candidate PR must merge before closure; actual retrieval captured separately; unscored results are not relevance proof |
| #64, benchmark outputs | Runner and frozen exports merged in #89; follow-up captures all 10 questions with real embeddings | Real generation/business stages missing; final combined run still outstanding; keep open |
| #65, scored evaluation | Review validation/scoring tooling merged in #90 | No actual named reviews, double-review/adjudication, end-to-end scores or stakeholder feedback; keep open |
| #57, evaluation framework | Rubrics, coverage rules and instructions merged in #88 | Actual team pilot, reviewer allocation and full-paper answerability confirmation still required; keep open |
| #59, framework parent | Benchmark/rubric definitions and protocol exist | #57's real pilot/allocation/coverage acceptance not complete; keep open |
| #66, retrieval pipeline parent | Ingestion/index/retrieval implementations and frozen real retrieval capture exist | #64 final combined outputs and #65 human scoring remain; keep open |

## Frozen evidence versus quality claims

The real capture uses `all-MiniLM-L6-v2` and audited HTML-first corpus, with exact
commit/input/index/model-weight hashes and package versions. All ten questions
executed successfully. Every returned passage retains source/citation metadata;
all indexed documents and metadata were reconciled to the audited Parquet.

No summary generation was executed: no local `GOOGLE_API_KEY` was configured.
No real business adapter or actual human review was supplied. Summary placeholders
explicitly say generation was not requested. Empty review input leaves scores
null, targets unmet and `approved=false`. This is retrieval execution evidence,
not Precision@5, factual accuracy, business usefulness or KPMG approval.

## Review handoff

1. Use the frozen run and blank passage worksheet, without rewriting the run.
2. Actual teammates claim bounded batches in #65; names/commitments are not
   assigned by this report. Double-review a shared subset per question type.
3. Confirm answerability from original full papers, not metadata keyword absence.
4. Bind actual summary/business adapters and an operator-authorized BYOK provider
   for a **new** frozen combined run. Provider calls may be billed to that key.
5. Score actual outputs and inspect each claim at its original section/page; retain
   abstention judgments, disagreements, absent stages and empirical failure cases.

The BYOK architecture is a separate draft PR and is not assumed merged or
live-provider verified. No historical checkout was deleted: it hosts the shared
Git database for two linked worktrees and cannot be reliably audited while its
filesystem mmap error persists.
