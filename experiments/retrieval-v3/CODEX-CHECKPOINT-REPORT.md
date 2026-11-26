## Checkpoint continuation

The earlier stop below is historical. The project lead approved per-path Git attributes. The index now preserves evaluated bytes, including the five shared dependencies. All protected blobs matched their verified working copies. Credential patterns and excluded paths were screened. The confidentiality marker in the fresh-diagnostic references was a published discussion of privacy risks. The comparator manifest was added for the historical B1 readiness check.
# Codex checkpoint and integration review

Date: 2026-11-25 (America/Chicago).

## Status: STOPPED — frozen Git-blob hash mismatch

No commit or push was made. No merge, deployment, paid provider call, live model call, or frozen-file edit was made. Existing backend, frontend and Render application code was not edited. Both requested handoff documents were read in full.

Selected demo: S2 consolidated-v2 Standard. B1 is experimental opt-in only. Original Baseline remains the current application default until integration testing passes. This project-lead decision overrides the handoff's ambiguous use of “S2 default.”

## Verification and offline tests

Working-tree checks from experiments/retrieval-v3:
- `python -I seal_s3.py`: `verified`.
- `python -I run_b1_diagnostic.py --check`: `b1_freeze: verified`, ChatGPT login true, no missing CLI flags; no model invocation. The reported 6 calls used is historical ledger state, not calls made during this task.

All five working-tree dependency hashes exactly match CODEX-HANDOFF-MESSAGE.md:

| File | Evaluated and observed working-tree SHA-256 |
|---|---|
| src/experimental/b2.py | 476518d6a2424c229d2afd78cef5b281e85dbc766eee9ada5f4963bb35aa9fc3 |
| src/experimental/balanced_retriever.py | 267ff7113339a262c15669ae09d4058f4e6d869918650b12636963cb43d66307 |
| src/experimental/evidence_coverage.py | f177c97a502727ccd4b57cd3ea5d20637c5e789d2f346ef4b244ed7d0d8549ff |
| src/codex_generation.py | 93946a22a852001ea57d5340584772225921e5ce9ee4233bbb49c955a2a923e7 |
| src/generation.py (not sealed) | bb10b4ce7fc3c043243c06bf53e68ab98ee9fe688d75cbcdf9a08d083b43d38a |

Regression commands used D:/KPMG-venvs/stage-a-py314/Scripts/python.exe with `-X utf8`:
- consolidated-v2: `-m unittest test_v2 test_consolidated test_runner`: **90 tests, OK**, 78.609 seconds.
- retrieval-v3: `-m unittest test_s2_paper_balance test_s3`: **51 tests, OK**, 8.803 seconds (11 B1 + 40 S3).
- Total: **141 tests passed**, no reported skips. The handoff's “about 134” for the first suite does not match the current observed 90.

### Blocking hash failure in the proposed Git checkpoint

Before committing, raw Git index blobs were checked against the frozen manifests. Checking s3-freeze.json stopped at `src/answer_quality.py`:
- Expected frozen / actual working-tree SHA-256: `c115ff8e8357bf0ca3db99995604727f507dabece2f1d5b5df014e24713545f2`.
- Actual staged Git-blob SHA-256: `8ccedd73e902fa15b487a787ee08b85b6ed971678c896e48f7aad63093fe1b2d`.
- Working file has 114 CRLF line endings; Git blob has zero CRLF. Normalizing only CRLF to LF makes the bytes identical.

This is an existing tracked blob whose checkout bytes satisfy the seal but whose repository bytes do not. Staging the new engine files with `core.autocrlf=false` preserves their bytes but does not replace unchanged tracked blobs. No normalization, restaging of this file, seal rewrite, or other repair was attempted after the mismatch. Further index verification and the planned staged credential-pattern scan did not complete. A clean checkout with different line-ending settings cannot yet be claimed to reproduce the frozen hashes.

## Branch, commit and files

- Created local branch: `checkpoint/s2-engine-b1` from `claude/source-grounded-quotes`.
- Current HEAD / source base: `9994eed920d0afd9ee5f36769077a05137763d6e`.
- New checkpoint commit SHA: **none**. Remote checkpoint: **not pushed**. Post-push verification: **not applicable / not performed**.
- 220 implementation, test, evaluation, dependency and documentation paths were staged before the blocker; exact staged manifest is below. This report is an additional untracked deliverable and was not committed.
- Included transitive legacy seal/test dependencies beyond the handoff's short list: consolidated-v1 files (fresh-v3 seal references them), fresh-diagnostic preflight/sealed inputs and agentic Python files (the preflight seal references them), measure/tables.py and trace diagnostics, baseline-decomposition/question_parts.py (rank_cache import), and older question sets/keys used by offline coverage. These preserve evaluation provenance and are not engines selected for integration.
- Excluded: retrieval-v3/cache/, fresh-v4/html/, fresh-v4/discovery/, fresh-v4/passages/, all data/processed/ outputs and validation bundle, blind scorer folders, bytecode, logs, ZIP archives, login state and environment files. No external blind folders were opened for this task. Unrelated pre-existing table-endpoint changes, other experiments and tests remain uncommitted.

### src/generation.py decision

Include its exact evaluated version: the evaluated S2 runner imports `src.codex_generation` (experiments/consolidated-v2/run_consolidated.py:129), and `src/codex_generation.py:18` imports `SchemaResponseError` from `src.generation`. Production provider construction also uses this module (latest Render server.py:25,248-249). The adapter itself accepts an injected generator; it does not independently select a provider. The file was staged, never edited.

## Read-only compatibility findings (ranked)

Review scope: fetched origin without merging. Latest relevant source refs inspected were backend/Render `origin/khoi/research-progress-checkpoint` at `332d057`, UI `origin/khoi/ui-refresh-v2-checkpoint` at `11ae22d`, and main at `8274afe`. References below use repository path:line; Render/UI references refer to those remote checkpoint versions. This is source review, not verification of a running Render service. Review stopped at the Git-blob mismatch; integration readiness is not approved.

1. **BLOCKER — frozen repository bytes are not reproducible yet.** See failed src/answer_quality.py Git-blob hash above. No checkpoint can be represented as verified or pushed until the project lead resolves how to preserve evaluated bytes without editing frozen content. Further mismatches may exist; the scan stopped at the first one.

2. **HIGH — Render packaging does not include S2 or its dependency folders.** experiments/render-staging/stage.py:107-115 copies src, three table-endpoint modules, prompts and the Render server, but not consolidated-v2, retrieval-v3, verification-repair, evidence-budget or agentic/statistical_reports.py. Dockerfile:11-14 copies only the staged context. Selecting S2 in that image would lack its modules. Any approved packaging change needs a narrow runtime allowlist, not the full evaluation repository or data outputs.

3. **HIGH — frozen default paths are Windows-specific.** experiments/consolidated-v2/env.py:12 hardcodes D:/KPMG-demo-corpus/.../parents.jsonl; s2_adapter.py:25 reads these rows unless injected. experiments/measure/common.py:9-17 points to desktop corpus/model locations. Render already stages the pinned demo-100 index and local models (stage.py:97-106), and server.py:109-115 uses snapshot/artifacts. An approved external integration wrapper must pass those explicit paths and `rows`/tables to S2, preserving frozen engine files. Confirm tables come from the same pinned index.

4. **HIGH — regulatory wiring is not preserved automatically.** Existing src/experimental/demo.py:19-26 constructs IndexedResearch with `regulatory_assessor=assess_regulatory`. experiments/retrieval-v3/s2_adapter.py:72-74 constructs it without an assessor or arXiv callback. In the general app, opting into regulatory analysis would reach IndexedResearch.finish's missing-assessor failure (src/indexed_research.py:258-261). Render deliberately blocks industry/context/risk requests (server.py:183-189), so this is chiefly an application integration issue, not a reason to alter Render's current preview restrictions. Preserve these behaviors through an approved wrapper and explicit tests; do not claim every downstream feature is unchanged merely because execute is inherited.

5. **HIGH — production provider and deadline behavior remain unvalidated.** Render source fixes Gemini `gemini-3.1-flash-lite` (server.py:39,248-249), guarded by dedicated-free-project checks (240-242), not the evaluated Codex provider. src/generation.py:45,64,98 sets 60-second provider limits. S2's measured total 93-second median / 141-second p90 does not itself prove either individual call will exceed 60 seconds, but warrants per-stage validation. Latest UI allows a long indexed request (ui-consult/app.js:2711); this does not establish reverse-proxy or provider deadlines. Server socket timeout 15 seconds (server.py:201) governs socket I/O, not a 15-second model budget. Verify complete request/proxy behavior without assuming those deadlines are interchangeable. No live tests were run. Provider smoke test remains approval-gated: 3 S2 questions, 6 calls, hard cap 10.

6. **HIGH — memory, Python and cold-start evidence does not transfer to Linux.** Evaluation uses Python 3.14; Render Dockerfile:1 uses Python 3.11, with pinned CPU dependencies in its Dockerfile/requirements.txt. Handoff reports retrieval around 1.5 GB/process; latest Render uses one warm model pair, one research lock and bounded request threads (server.py:191,195-205), with plan standard and one instance (render.yaml:12-13). Do not create a second retrieval model pair when switching engines. The handoff's “plus local models” wording leaves total RSS unclear; profile peak RSS, startup and concurrency on the approved Linux image. Render README.md:15 explicitly says Linux build/runtime memory validation is outstanding. Existing index/model staging is present but S2 warmup and health readiness are unmeasured.

7. **MEDIUM — default selection flags are proposed, not implemented.** No RESEARCH_ENGINE or S2_PAPER_BALANCE selection is wired in the reviewed Render startup. server.py:116-117 constructs the existing Baseline. An approved switch should default to baseline; initialize S2 only for an explicit `s2` selection and parse B1 strictly (default false, reject invalid values). Preserve Baseline construction, quotas, authentication, table audit, review fingerprint and saved-work behavior. S2 is the selected demo choice, not permission to change the application default.

8. **MEDIUM — resume/session and extra-call behavior need integration tests.** s2_adapter.py:34-44 stores session/query/variant/index/context; consolidated-v2/adapter.py:40-43 falls back to session “anonymous.” Verify the deployed handler passes a stable session identity before claiming cross-user checkpoint isolation. Configure a private checkpoint directory on the persistent state disk, retention and permissions; test failed review resume and two sessions. S2's two calls cover engine synthesis/review only; IndexedResearch.resolve_context:196-202 and finish:226-250 can add context/business calls in the full app. Render's existing research-only restrictions and provider quota wrapper (server.py:85-96) must stay intact. Same-session concurrent writes and restart persistence need explicit validation.

9. **MEDIUM — offline regression success depends on deliberately excluded local assets.** test_consolidated.py:26-31, test_v2.py:30 and test_s3.py:19 read data/processed replay results; test_s2_paper_balance.py:131-147 uses excluded rank caches/validation corpus and older references. These tests passed against this machine's assets, not a fresh self-contained clone. Do not add prohibited outputs to Git to hide this gap. Obtain approval for a CI fixture/artifact provisioning strategy and verify exact hashes before claiming portable CI reproduction. bs4 is imported by measure/tables.py:8-10 during prepare imports, so evaluation/preflight environments need it even though core runtime ingestion is not required.

10. **LOW — summary seam and optional UI fields are largely compatible.** The relevant backend contract files have no differences between this base and fetched backend checkpoint. src/indexed_research.py:369-390 still uses injected retrieval and self.summary, then finish/validate_result; research_contracts.py:272-291 validates summary and evidence without rejecting all extra summary keys. Latest UI uses optional answer_lead (app.js:1944-1945), answer_scope (1594,2339), and quality_review (1950). It does not directly render held_claims, evidence_notes or paper_balance; these extras are ignored by the inspected renderer. generation_method is optional and indexed mode already identifies synthesis (357). This tolerance is source-level evidence, not end-to-end browser validation of S2 output. Preserve pending human review and approved:false. Any later display of held claims must clearly distinguish them from published findings.

## Proposed integration work — awaiting project-lead approval

- Decide a byte-preserving checkpoint approach for existing frozen CRLF files. Do not change seals or frozen contents. Re-audit every staged sealed blob, complete credential screening, commit the allowed checkpoint, push, verify remote SHA and re-run both required checks on its checkout.
- Add an isolated runtime wrapper and default-preserving server-side flags; inject snapshot paths, rows/tables, existing provider/quota hooks, required regulatory wiring and private checkpoint storage. No such code was written.
- Extend the private image runtime allowlist and run approved offline Python 3.11/Linux compatibility tests, memory/warmup profiling, response-contract/UI tests, rollback/default tests, timeout/resume and concurrent-session isolation tests.
- Seek separate approval before the provider smoke test, any live calls, build/publication incurring charges or deployment. Keep B1 disabled pending unseen multi-paper validation and zero new safety flags.

Stopped for project-lead decision. No repair was attempted.

## Exact staged manifest (not committed)
- `experiments/agentic-handoff/codex_baseline.py`
- `experiments/agentic-handoff/codex_paired.py`
- `experiments/agentic/ab_eval.py`
- `experiments/agentic/ab_run.py`
- `experiments/agentic/agents.py`
- `experiments/agentic/contracts.py`
- `experiments/agentic/envelope.py`
- `experiments/agentic/fake_provider.py`
- `experiments/agentic/numeric_checks.py`
- `experiments/agentic/route.py`
- `experiments/agentic/statistical_reports.py`
- `experiments/agentic/test_ab_dryrun.py`
- `experiments/agentic/test_ab_harness.py`
- `experiments/agentic/test_adversarial.py`
- `experiments/agentic/test_agentic.py`
- `experiments/agentic/test_audit2.py`
- `experiments/agentic/test_audit3.py`
- `experiments/agentic/test_audit4.py`
- `experiments/agentic/test_audit5.py`
- `experiments/agentic/test_integration.py`
- `experiments/baseline-decomposition/question_parts.py`
- `experiments/combined-v1/answer-key.md`
- `experiments/combined-v1/questions.json`
- `experiments/combined-v1/references.json`
- `experiments/combined-v1/rules.json`
- `experiments/combined-v1/seal.json`
- `experiments/completion-eval-v1/answer-key.md`
- `experiments/completion-eval-v1/questions.json`
- `experiments/completion-eval-v1/references.json`
- `experiments/completion-eval-v1/rules.json`
- `experiments/completion-eval-v1/seal.json`
- `experiments/consolidated-v2/BLIND-PACKET-v3.md`
- `experiments/consolidated-v2/CLAUDE-AUDIT-v3.md`
- `experiments/consolidated-v2/FINAL-REPORT.md`
- `experiments/consolidated-v2/FRESH-V3-FINAL-REPORT.md`
- `experiments/consolidated-v2/FRESH-V3-READINESS.md`
- `experiments/consolidated-v2/FRESH-V3-RESULTS.md`
- `experiments/consolidated-v2/KEY-REVIEW-PACKET-v3.md`
- `experiments/consolidated-v2/SIGN-OFF-v3.md`
- `experiments/consolidated-v2/VALIDATION-PROPOSAL.md`
- `experiments/consolidated-v2/accounting.py`
- `experiments/consolidated-v2/adapter.py`
- `experiments/consolidated-v2/assist_route.py`
- `experiments/consolidated-v2/blind-sheet-v3.json`
- `experiments/consolidated-v2/build_key_review_packet_v3.py`
- `experiments/consolidated-v2/engine.py`
- `experiments/consolidated-v2/env.py`
- `experiments/consolidated-v2/evidence.py`
- `experiments/consolidated-v2/fresh-v3/AMBIGUITIES.md`
- `experiments/consolidated-v2/fresh-v3/KEY-REVIEW-RECORD.md`
- `experiments/consolidated-v2/fresh-v3/OVERLAP.md`
- `experiments/consolidated-v2/fresh-v3/answer-key.md`
- `experiments/consolidated-v2/fresh-v3/build_set.py`
- `experiments/consolidated-v2/fresh-v3/questions.json`
- `experiments/consolidated-v2/fresh-v3/references.json`
- `experiments/consolidated-v2/fresh-v3/rules.json`
- `experiments/consolidated-v2/fresh-v3/seal.json`
- `experiments/consolidated-v2/fresh3-audit.json`
- `experiments/consolidated-v2/fresh3-blind-key.json`
- `experiments/consolidated-v2/fresh3-coverage.json`
- `experiments/consolidated-v2/fresh3-results.PROVISIONAL.json`
- `experiments/consolidated-v2/fresh3_arms.py`
- `experiments/consolidated-v2/fresh3_scoring.py`
- `experiments/consolidated-v2/measure_prompts.py`
- `experiments/consolidated-v2/prompt-sizes.json`
- `experiments/consolidated-v2/publication.py`
- `experiments/consolidated-v2/review.py`
- `experiments/consolidated-v2/run_consolidated.py`
- `experiments/consolidated-v2/run_fresh3_b0.py`
- `experiments/consolidated-v2/run_fresh3_s1.py`
- `experiments/consolidated-v2/seal_v3.py`
- `experiments/consolidated-v2/synthesis.py`
- `experiments/consolidated-v2/test_consolidated.py`
- `experiments/consolidated-v2/test_runner.py`
- `experiments/consolidated-v2/test_v2.py`
- `experiments/consolidated/AMBIGUITIES.md`
- `experiments/consolidated/BLIND-PACKET.md`
- `experiments/consolidated/CITATION-ADJUDICATION.md`
- `experiments/consolidated/FINAL-EVALUATION.md`
- `experiments/consolidated/IMPLEMENTATION-REPORT.md`
- `experiments/consolidated/IMPROVEMENT-PLAN.md`
- `experiments/consolidated/KEY-REVIEW-PACKET.md`
- `experiments/consolidated/KEY-REVIEW-RECORD.md`
- `experiments/consolidated/RESULTS.md`
- `experiments/consolidated/TECHNIQUES.md`
- `experiments/consolidated/VALIDATION-PROPOSAL.md`
- `experiments/consolidated/blind-score-sheet.json`
- `experiments/consolidated/build_key_review_packet.py`
- `experiments/consolidated/engine.py`
- `experiments/consolidated/env.py`
- `experiments/consolidated/evidence.py`
- `experiments/consolidated/fresh-v2/OVERLAP.md`
- `experiments/consolidated/fresh-v2/answer-key.md`
- `experiments/consolidated/fresh-v2/build_set.py`
- `experiments/consolidated/fresh-v2/peek.py`
- `experiments/consolidated/fresh-v2/questions.json`
- `experiments/consolidated/fresh-v2/references.json`
- `experiments/consolidated/fresh-v2/rules.json`
- `experiments/consolidated/fresh-v2/seal.json`
- `experiments/consolidated/fresh-v2/show.py`
- `experiments/consolidated/offline-check.json`
- `experiments/consolidated/offline_check.py`
- `experiments/consolidated/publication.py`
- `experiments/consolidated/review.py`
- `experiments/consolidated/run_consolidated.py`
- `experiments/consolidated/scoring/answers/H01.md`
- `experiments/consolidated/scoring/answers/H02.md`
- `experiments/consolidated/scoring/answers/H03.md`
- `experiments/consolidated/scoring/answers/H04.md`
- `experiments/consolidated/scoring/answers/H05.md`
- `experiments/consolidated/scoring/answers/H06.md`
- `experiments/consolidated/scoring/answers/H07.md`
- `experiments/consolidated/scoring/answers/H08.md`
- `experiments/consolidated/scoring/blind-key.json`
- `experiments/consolidated/scoring/build_blind_packet.py`
- `experiments/consolidated/scoring/extract.py`
- `experiments/consolidated/scoring/mechanics.json`
- `experiments/consolidated/scoring/results.json`
- `experiments/consolidated/scoring/scores.json`
- `experiments/consolidated/synthesis.py`
- `experiments/consolidated/test_consolidated.py`
- `experiments/consolidated/test_runner.py`
- `experiments/evidence-budget/budgeted_research.py`
- `experiments/evidence-budget/check_real_retrieval.py`
- `experiments/evidence-budget/evidence_budget.py`
- `experiments/evidence-budget/request_guard.py`
- `experiments/evidence-budget/test_combined.py`
- `experiments/heldout-v1/answer-key.md`
- `experiments/heldout-v1/questions.json`
- `experiments/heldout-v1/references.json`
- `experiments/heldout-v1/rules.json`
- `experiments/heldout-v1/seal.json`
- `experiments/measure/common.py`
- `experiments/measure/fresh-diagnostic-v1/README.md`
- `experiments/measure/fresh-diagnostic-v1/capture.py`
- `experiments/measure/fresh-diagnostic-v1/cases.json`
- `experiments/measure/fresh-diagnostic-v1/config.json`
- `experiments/measure/fresh-diagnostic-v1/offline-retrieval.json`
- `experiments/measure/fresh-diagnostic-v1/preflight.py`
- `experiments/measure/fresh-diagnostic-v1/prepare.py`
- `experiments/measure/fresh-diagnostic-v1/questions.json`
- `experiments/measure/fresh-diagnostic-v1/references.json`
- `experiments/measure/fresh-diagnostic-v1/rules.json`
- `experiments/measure/fresh-diagnostic-v1/seal.json`
- `experiments/measure/fresh-diagnostic-v1/test_capture.py`
- `experiments/measure/tables.py`
- `experiments/measure/trace-diagnostics/diagnose.py`
- `experiments/retrieval-v3/B1-DIAGNOSTIC-CRITERIA.md`
- `experiments/retrieval-v3/B1-DIAGNOSTIC-RESULTS.md`
- `experiments/retrieval-v3/B1-LIVE-DIAGNOSTIC-PLAN.md`
- `experiments/retrieval-v3/BLIND-PACKET-v4.md`
- `experiments/retrieval-v3/CODEX-HANDOFF-MESSAGE.md`
- `experiments/retrieval-v3/FINAL-REPORT-fresh-v4.md`
- `experiments/retrieval-v3/INTEGRATION-HANDOFF.md`
- `experiments/retrieval-v3/PAPER-BALANCE-REPORT.md`
- `experiments/retrieval-v3/PLAN.md`
- `experiments/retrieval-v3/READINESS-fresh-v4.md`
- `experiments/retrieval-v3/SIGN-OFF-fresh-v4.md`
- `experiments/retrieval-v3/analyze.py`
- `experiments/retrieval-v3/b1-blind-key.json`
- `experiments/retrieval-v3/b1-freeze.json`
- `experiments/retrieval-v3/blind-sheet-v4.json`
- `experiments/retrieval-v3/components.py`
- `experiments/retrieval-v3/coverage.json`
- `experiments/retrieval-v3/diagnose.py`
- `experiments/retrieval-v3/eval_paper_balance.py`
- `experiments/retrieval-v3/fresh-v4/KEY-REVIEW-RECORD.md`
- `experiments/retrieval-v3/fresh-v4/KEY-REVIEW-REPORT.md`
- `experiments/retrieval-v3/fresh-v4/SELECTION-RULE.md`
- `experiments/retrieval-v3/fresh-v4/answer-key.md`
- `experiments/retrieval-v3/fresh-v4/build_set.py`
- `experiments/retrieval-v3/fresh-v4/build_validation_bundle.py`
- `experiments/retrieval-v3/fresh-v4/bundle-record.json`
- `experiments/retrieval-v3/fresh-v4/coverage-fresh-v4.json`
- `experiments/retrieval-v3/fresh-v4/dump_passages.py`
- `experiments/retrieval-v3/fresh-v4/questions.json`
- `experiments/retrieval-v3/fresh-v4/references.json`
- `experiments/retrieval-v3/fresh-v4/rules.json`
- `experiments/retrieval-v3/fresh-v4/seal.json`
- `experiments/retrieval-v3/fresh-v4/select_papers.py`
- `experiments/retrieval-v3/fresh-v4/selection-log.json`
- `experiments/retrieval-v3/fresh-v4/sources.json`
- `experiments/retrieval-v3/fresh4-adjudication.json`
- `experiments/retrieval-v3/fresh4-audit.json`
- `experiments/retrieval-v3/fresh4-blind-key.json`
- `experiments/retrieval-v3/fresh4-results.json`
- `experiments/retrieval-v3/fresh4_scoring.py`
- `experiments/retrieval-v3/fresh_coverage.py`
- `experiments/retrieval-v3/offline-acceptance.json`
- `experiments/retrieval-v3/offline_acceptance.py`
- `experiments/retrieval-v3/paper-balance.json`
- `experiments/retrieval-v3/paper_balance.py`
- `experiments/retrieval-v3/rank_cache.py`
- `experiments/retrieval-v3/run_b1_diagnostic.py`
- `experiments/retrieval-v3/run_fresh4.py`
- `experiments/retrieval-v3/s2_adapter.py`
- `experiments/retrieval-v3/s2_paper_balance.py`
- `experiments/retrieval-v3/s3-freeze.json`
- `experiments/retrieval-v3/s3_answer.py`
- `experiments/retrieval-v3/s3_engine.py`
- `experiments/retrieval-v3/s3_env.py`
- `experiments/retrieval-v3/s3_evidence.py`
- `experiments/retrieval-v3/seal_s3.py`
- `experiments/retrieval-v3/test_s2_paper_balance.py`
- `experiments/retrieval-v3/test_s3.py`
- `experiments/verification-repair/FINDINGS.md`
- `experiments/verification-repair/diagnose.py`
- `experiments/verification-repair/interpretation_gate.py`
- `experiments/verification-repair/numeric_checks_v2.py`
- `experiments/verification-repair/patch_v2.py`
- `experiments/verification-repair/replay.py`
- `experiments/verification-repair/run_frozen_suites.py`
- `experiments/verification-repair/test_interpretation_gate.py`
- `experiments/verification-repair/test_numeric_v2.py`
- `experiments/verification-repair/verification_v2.py`
- `src/codex_generation.py`
- `src/experimental/b2.py`
- `src/experimental/balanced_retriever.py`
- `src/experimental/evidence_coverage.py`
- `src/generation.py`

## Checkpoint recovery

The evaluation inputs remain on the authorized evaluation machine. Use the pinned demo-100 bundle and two model snapshots identified in INTEGRATION-HANDOFF.md and the fresh-diagnostic seal. Restore replay outputs and rank caches from the existing evaluation-machine artifacts for full replay regressions. The fresh-v4 selection log, source list, build scripts and bundle record describe how to reconstruct derived HTML, passages and the validation bundle. Verify reconstructed assets against the recorded hashes. Blind scoring folders and local login state stay outside Git. Use an authorized local Codex login for the historical preflight, without copying credentials.

