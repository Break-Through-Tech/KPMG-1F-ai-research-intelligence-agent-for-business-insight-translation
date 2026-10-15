# BTT Weeks 7–12: Six Parallel Delivery Lanes

**Status:** Proposal for team discussion; not a board assignment or commitment.
**Prepared:** 2026-10-14

## Planning premise

The canonical Challenge Project Overview places prompt work in Week 7, evaluation in Week 8, refinement in Week 9, UI in Weeks 10–11, and delivery in Week 12. Treating those as a strict sequence delays useful UI and reliability work. Start independent lanes together against fixed fixtures, then integrate through the existing CLI/result contract. The overview does not assign exact calendar dates to Weeks 7–12.

## Evidence to plan from

- **Ingestion E2E:** [PR #69](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/pull/69) records a successful locked-sample validator run: 25 cached PDFs, 693 pages, 1,671 chunks. It did not test fresh live downloads, embeddings, or retrieval relevance.
- **Local model/index/CLI E2E:** [PR #101](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/pull/101) contains an opt-in end-to-end path and a real local-model attempt. That was not model-acceptance success: the ten-question capture had zero accepted summaries (four malformed responses, six generation failures); the local-model test is skipped in ordinary offline CI unless enabled.
- **Bounded baseline evaluation:** [PR #111](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/pull/111) reports predeclared rubric results of Precision@5 0.96 (target 0.70), summary mean 4.60/5, and business mean 4.17/5; it says these clear its scoped advisory gates. The same PR explicitly says no production Gemini/OpenAI/Bedrock call, real-paper retrieval-relevance judgment, or stakeholder review occurred. q03 dialogue-history outcomes, broader q09 risk coverage, and general q10 reliability remain limited; the consulting transfer is conditional. Preserve both the reported scores and their limits; do not call them KPMG acceptance or universal reliability.
- **Current pipeline:** PRs #108–#111 have merged; #109 added exact-once candidate-ID ranking. The scoped q03/q10 proof is not a substitute for broader benchmark coverage.
- **Open work:** [#76](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/76) (source-specific shared contracts) and [#81](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/81) (research-review bridge) are Ready; #81 is assigned to Teegawende12, #76 is unassigned. [#106](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/106) remains open for retrieval-quality acceptance.

## Six parallel lanes

### 1. UI/UX interface

**Owner:** seek a volunteer; repo history does not establish a UI owner. Start from fixed JSON fixtures; do not wait for evaluation or #76.

- **Week 7:** Map the user flow and wireframe query → evidence/source inspection → research result → business implications/limitations → review-pending state.
- **Week 8:** Build a thin local or clickable prototype. Include full, partial, abstention, insufficient-evidence, and provider-error states.
- **Weeks 9–10:** Connect through a thin adapter to the CLI/result contract; citations link to source locators. The interface must not imply that citation presence proves semantic support or that drafts are approved.
- **Week 11:** Internal usability pass and highest-friction fixes.
- **Week 12:** Freeze the demo path and provide operator/demo instructions.

**Exit:** A teammate can run it, submit a query, inspect evidence, distinguish output states, and see that review is pending. No hosted deployment or production-auth scope.

### 2. Evaluation design and reporting

**Owner candidate:** Alesha (ralesh10), based on benchmark-question work and #111; confirm capacity. Add an independent source/claim reviewer.

- **Week 7:** Freeze code/config/corpus identity and capture the current baseline. Preserve #111’s bounded reported metrics with their explicit limits.
- **Week 8:** Score outcomes per question and stage: retrieval, source/quote support, answer coverage, abstention, and business-claim grounding. Keep synthetic, teammate, and KPMG review separate.
- **Weeks 9–10:** Compare proposed changes against a development set and predeclared adverse/paraphrased queries. Keep a held-out slice out of tuning.
- **Week 11:** Run the frozen regression set against the integrated candidate; publish regressions and missing judgments.
- **Week 12:** Publish provenance-backed results and state which criteria are met, unmet, or unmeasured.

**Exit:** Reproducible run, per-case scorecard, source receipts for semantic judgments, retained failures, and explicit scope limits—not a single blended score.

### 3. Retrieval and ranking quality

**Owner candidate:** Jacqueline, based on #106/#109, if she wants this technical-review lane; implementation ownership/capacity to be confirmed.

- **Week 7:** Freeze query sets and current retrieval/ranking baseline after #109. Separate development queries from holdout/adverse queries.
- **Week 8:** Diagnose misses by intent and evidence type; distinguish ranking failure from corpus absence and downstream extraction failure.
- **Weeks 9–10:** Test bounded retrieval/ranking changes only on development cases; verify exact-once IDs and preserve source text. Evaluate on the untouched holdout after changes are frozen.
- **Week 11:** Run retrieval regressions on the full frozen set and report per-question changes, including security/evidence counterexamples.
- **Week 12:** Keep only improvements that survive the frozen evaluation; document remaining retrieval gaps.

**Exit:** Comparison is reproducible; no benchmark expectations or corpus contents are changed to inflate results; relevance claims are supported by inspected sources.

### 4. Evidence-grounded research and business output

**Jooheon**, based on evidence-grounded summarization in #99; confirm availability and coordinate with the business-translation owner.

- **Week 7:** Define stage-specific checks for extraction, factual research claims, gaps/limitations, and conditional business recommendations.
- **Week 8:** Review fixed q03/q10 traces and representative baseline cases; classify exact-quote failures separately from semantic overreach.
- **Weeks 9–10:** Test bounded prompt/contract refinements on development evidence. Research claims stay factual; recommendations and transfer assumptions stay in the business stage.
- **Week 11:** Re-run the frozen set and adverse probes; preserve any abstentions/failures rather than retrying until a pass.
- **Week 12:** Document examples of supported, partial, and correctly rejected outputs with their provenance.

**Exit:** Claims remain bound to original evidence; limitations are visible; business actions are conditional and do not masquerade as paper findings. No semantic acceptance claim without source review.

### 5. Shared contracts, citations, and corpus reliability

**Owner candidate:** Khoi, based on HTML/Chroma citation validation in #102; #76 is currently unassigned, so confirm capacity before assignment.

- **Week 7:** Complete #76’s concrete gaps: positive 1-based PDF pages; valid HTML page/heading links; versioned request/result shapes; fixtures for normal, empty, insufficient, and invalid-citation cases.
- **Week 8:** Add offline tests for malformed/unknown IDs, duplicate ranking entries, missing source metadata, and provider failure. Keep fail-closed behavior.
- **Weeks 9–10:** Serve as contract owner for UI, retrieval, and generation adapters; prefer additive schema changes and coordinate any breaking changes.
- **Week 11:** Run failure injection through the integrated local workflow; verify errors remain inspectable and no bad output is accepted.
- **Week 12:** Finalize contract docs and recovery notes.

**Exit:** Offline fixtures cover critical boundaries; invalid citations/locators reject; failures remain diagnosable; no source or corpus scope expansion without review.

### 6. Review workflow and human handoff

**Owner:** Teegawende12 is assigned to #81; confirm current capacity and keep the scope separate from evaluation scoring.

- **Week 7:** Reconfirm #81’s scope and fixed input/result shape; start from fixtures, not a dependency on live generation.
- **Week 8:** Build the research-review packet from source passages, claims, business implications, limitations, and pending status.
- **Weeks 9–10:** Add explicit approve/revise/reject recording bound to the full result fingerprint; separate regulatory-source IDs from research chunk IDs; invalidate stale decisions after edits.
- **Week 11:** Exercise pending, revise, reject, stale, and conflicting cases in the integrated UI/pipeline.
- **Week 12:** Document reviewer handoff and package a demonstrable review flow. Human or KPMG review occurs only if reviewers actually perform it; no approval is inferred.

**Exit:** Review state is explicit, traceable, and invalidated when the reviewed result changes. Generated content never marks itself approved.

## Integration checkpoints

| Week | Parallel starts/progress | Cross-lane checkpoint |
|---|---|---|
| 7 | UI wireframes; eval baseline; retrieval diagnosis; output-stage rubric; #76 contracts; #81 fixture shape | Confirm owners/capacity and freeze shared JSON fixture; no lane blocks another |
| 8 | Fixture UI; per-case evidence review; retrieval failure taxonomy; output traces; offline contract tests; review packet | Publish baseline limitations and agree additive result boundary |
| 9 | UI adapter; bounded retrieval and prompt experiments; contract consumers begin integration; review-state prototype | First vertical slice with fixtures; candidate changes remain on development data |
| 10 | Partial/error UI; held-out retrieval and answer checks; citation/failure injection; stale-review handling | Compare frozen candidates with baseline; do not tune on holdout |
| 11 | Internal usability; frozen evaluation; integrated local E2E; review-flow regression | Resolve critical failures and retain a reproducible evidence bundle |
| 12 | Demo/runbook; final evaluation; reliability fixes; review handoff | Package prototype, results, limits, and presentation; no unsupported acceptance claims |

## Operating rules

- All six lanes may start in Week 7 using fixtures; only integration waits for the shared result boundary.
- Do not change benchmark expectations or corpus scope to improve scores. Do not tune on held-out cases.
- Tests and CI establish software behavior, not semantic correctness or stakeholder approval.
- Preserve model/config/corpus provenance and every relevant failure. Synthetic review, teammate review, usability feedback, and KPMG acceptance are different evidence classes.
- Candidate owners are suggestions grounded in prior work, not assignments or claims of availability.

## Ownership discussion

1. Find a UI volunteer; pair with a pipeline consumer for the Week 9 adapter.
2. Ask Alesha whether she can lead evaluation and identify an independent reviewer.
3. Ask whether Jacqueline wants to own or review retrieval/ranking acceptance.
4. Confirm Jooheon for the evidence-grounded output lane and Khoi for #76 consumer/contract work.
5. Keep Teegawende12 on assigned #81 unless she requests a change.
6. Nominate an integration coordinator for the Week 11 E2E and Week 12 package; no availability is assumed.

This proposal does not create issues, move board cards, or assign teammates.

## References

- [Canonical challenge overview and timeline](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/blob/main/Challenge-Project-Overview.md)
- [Project board](https://github.com/orgs/Break-Through-Tech/projects/190)
- [PR #69 ingestion validation](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/pull/69)
- [PR #101 local-model/index/CLI E2E](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/pull/101)
- [PR #111 baseline RAG/evaluation evidence](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/pull/111)
- [Issue #76 shared contracts](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/76)
- [Issue #81 review bridge](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/81)
- [Issue #106 retrieval-quality acceptance](https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/issues/106)
