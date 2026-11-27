# KPMG Research Intelligence: optimized consolidated engine (consolidated-v2) final report

**Status: implemented and offline-tested only.**

- **Not done:** no live model calls, merges, deployments or shared-app changes. The Original Baseline remains the production default.
- **Isolation:** everything new is in `experiments/consolidated-v2/`. The evaluated engines and every historical result are untouched and reproducible:
  - Original Baseline (`src`) and Improved Baseline (`codex_baseline` skip-fit);
  - the old Multi-Agent (`experiments/agentic` + `agentic-handoff`);
  - consolidated v1 Standard and Deep (`experiments/consolidated`, sealed).
- **Labels used throughout:** **[implemented]**, **[proposed]**, **[offline-tested]**, **[live-tested]**, **[measured]**, **[estimate]**.

## 1. Final reconciled blind evaluation (consolidated v1, fresh-v2; closed)

Details are in `../consolidated/FINAL-EVALUATION.md`. The primary scores are the independent blind review (Codex).

| | Standard | Deep |
|---|---|---|
| Completeness | 26.5 / 36 (73.6%) | 28.0 / 36 (77.8%) |
| Fully answered | 0 | 1 |
| Citation-grounding failures | 0 recorded* | 1 (H01 L1) |
| Misleading or fabricated claims | 0 | 0 |
| Interpretations (11 in total), blind scores | 2 / 2 each | 2 / 2 each |

- **Disagreements:** 7 point-answers differ between the blind and non-blind scores (H02.5, H03.4, H03.5, H04.3). None changes a verdict.
- **\*Needs human adjudication:** Standard's H01 L1 and Deep's H07 L2 have the same "three-turn" defect as the recorded failure. Applying the rule consistently would fail the safety gate for both arms.
- **Frozen verdict:** Deep fails the rule (+1.5 points against the required +3.6; one citation-grounding failure). The Original Baseline stays the default, and the evaluation is closed.

## 2. Updated root-cause analysis (blind scores)

| Standard: 9.5 points lost | Points | Addressed in v2 by |
|---|---|---|
| Retrieval: anchor outside the 6k packet (ranks 20–65 or beyond) | 6.0 | C2 conclusion coverage for the CLINIC and CAT conclusions (H07.1, H08.3, and part of H04.5). The rest is unaddressed by design: no brute-force budget increase (C3) |
| Synthesis: point in the evidence but omitted; the finding cap was full in 15 of 16 answers | 2.0 | C1 coverage-first synthesis, capacity 18 |
| Verification: a correct reduction discarded by gate ordering (H01.1) | 0.5 | V1 |
| Review relevance: same-study RAG variant rejected (H02.4) | 1.0 | V3 |
| Citation grounding: spelled-out count not in its own quote (H01 L1) | (safety) | V5 |

**Caveat:** the targeted points come from fresh-v2, so improvement on them cannot be claimed. Only fresh-v3 can measure it.

## 3. Architecture after optimization [implemented, offline-tested]

```
question
  → Baseline retrieval: protected 6k group-aware skip-fit packet            (checkpoint "base")
  → + bounded conclusion coverage (≤ 2 papers, ≤ 800 tokens, reported separately)
  → coverage assessment: Adaptive prototype only, deterministic, no LLM call (checkpoint "route")
  → optional Multi-Agent planner (1 call) + ≤ 3 targeted searches, run in parallel, ≤ 8k
                                                                              (checkpoints "plan", "evidence")
  → shared synthesis (1 call) → shared review (1 call)                         (checkpoints "synthesis", "review")
  → deterministic publication gates → source-grounded answer
```

| Mode | Calls | Planner |
|---|---|---|
| Standard | 2 | never |
| Deep | 3 | always |
| Adaptive (prototype, never the default) | 2 or 3 | only when a checkable coverage gap is found |

The Baseline core owns evidence, synthesis, review and publication in every mode. Multi-Agent assistance only adds evidence.

## 4. Exact implementation changes (all in `experiments/consolidated-v2/`)

| File | Change |
|---|---|
| `synthesis.py` | **C1:** coverage-first rules; capacity 18 (not a target); grouping of one subject's values within a table row only when every value is quoted. **L1:** shortest sufficient quote, about 300 characters preferred and never truncated misleadingly. **V5:** the attached-quote rule applies to limitations. **T1/T2:** `compact_passage`. Business-mode `findings_only` |
| `review.py` | **V1:** `reduced_entailed` confirmation. **V3:** relevance policy for same-study variants, ablations and comparators, plus a `related` flag. **V5:** limitations must be entailed by their own quotes, and the gap may not assert facts. **L2:** reasons of about 160 characters. Compact passages |
| `publication.py` | **V1:** a confirmed reduction is evaluated through P2–P5 even when `supported=false`; unconfirmed rewrites are never published. **V2:** flag resolution needs the number's own subject in the quoted span; other names must be in the item's quotes; title names are context; the respectively mapping, prose negation polarity (table-header labels exempt), unit and condition-overlap checks all apply. **V3:** related variants published with `scope=related_variant`; irrelevant claims stay unpublished. **V5:** spelled-out counts are checked in findings, limitations and interpretations; a gap asserting an unsupported value is replaced |
| `evidence.py` | **C2:** `conclusion_coverage`, with base, allowance and actual usage reported separately and dropped if the request guard would be exceeded. **C3:** incomplete-table notes consolidated per paper, each table still named. **L3:** `run_searches` in parallel (at most 3 threads, ordered results, isolated errors). The size bound now measures the compact form actually sent |
| `engine.py` | Baseline-first stages (`base` → `route` → `plan` → `evidence` → `synthesis` → `review`); `gather_evidence` and `answer` split for the backend seam; adaptive mode; exact failed-stage labels |
| `assist_route.py` | Adaptive prototype (named entity missing from the packet; multi-entity concentration). Never activates on complexity alone |
| `accounting.py` | **T4:** `ProviderGuard` with per-provider profiles; estimated, bounded and actual usage kept separately; calibration summary |
| `adapter.py` | Opt-in `create_consolidated_research(mode)` subclassing `IndexedResearch`; `RequestCheckpoints` isolation |
| `run_consolidated.py` | v2 outputs go to `consolidated-v2-*`; fresh-v3; `ProviderGuard` |
| `test_v2.py`, `measure_prompts.py`, ported `test_consolidated.py` / `test_runner.py` | Tests and measurement |

## 5. Reliability and verification improvements [offline-tested; live behaviour untested]

Each fix below has positive and negative tests:

| Fix | Positive test | Negative tests |
|---|---|---|
| **V1** | The live H01 reviewer reduction publishes once confirmed | Unconfirmed reduction, reduction with a new number (P3), reduction with an unquoted value (P4), and an irrelevant claim are all withheld |
| **V2** | The live GPT-5 resolution publishes; Pandora's "respectively" claim publishes; G03 publishes when it keeps "(no defense)" | Wrong model (Claude Opus 4.1), unquoted model (Llama-3), wrong unit (%), negation, swapped respectively mapping, a non-title "context" name, and G03 without its qualifier are all withheld |
| **V3** | MedES RAG figures publish as `related_variant` | The same claims judged irrelevant are withheld |
| **V4** | Table-header and number-parsing protections retained; all 206 frozen Multi-Agent tests pass under both checkers | — |
| **V5** | A count that is in its quote ("3 turns each") is kept; meta counts ("two studies") are exempt; a gap without values is kept | The H01-A L1 replay and the identical Standard H01 L1 are dropped ("three" is not in the quote); a gap with an unsupported value is replaced |

## 6. Completeness improvements [implemented; effect not measured]

- **C1:** coverage-first prompting with capacity 18.
- **C2:** conclusion coverage. On real B2 it adds the CLINIC conclusion (c0024) to the H08 packet within the 800-token allowance [offline-tested].
- **C3:** no global budget increase; table warnings consolidated without hiding any table.

**Expected effect:** if the live model follows C1/C2/V1/V3, up to about 4–5 of Standard's 9.5 lost fresh-v2 points are addressable **[estimate; contaminated set]**. About 3.5 retrieval points remain out of reach.

## 7. Measured offline prompt-size reductions [measured on the saved v1 packets and drafts]

| | v1 | v2 | Reduction |
|---|---|---|---|
| Serialized evidence (454 passages) | 1,453,678 bytes | 532,247 bytes | **63.4%** |
| Standard synthesis prompt (median guard estimate) | 28.6k | 13.1k | **54%** |
| Standard review prompt | 32.7k | 17.6k | **46%** |
| Deep synthesis / review | 35.3k / 39.7k | 15.8k / 20.6k | **55% / 48%** |

These are guard estimates of our own prompt text, not provider tokens. v2 packets also add the conclusion allowance (≤ 800 MiniLM tokens).

## 8. Estimated latency and token benefits [estimate, unmeasured]

- **Provider input per Standard question:**
  - v1: about 77k actual (two calls, each carrying about 10k of Codex CLI overhead).
  - v2 estimate: about 50–58k (−25–35%).
- **Latency:** dominated by output tokens. L1/L2 shrink quotes and reasons, but C1/C2 can add findings, so net output change is uncertain.
  - **Estimate:** Standard median about 95–115 s (v1: 119 s), and Deep about 2 s less for its searches through parallelism.
  - **Measured offline:** a fixed B2 query set returns identical results in parallel and sequentially.
- **Caching (T3), not implemented:**
  - Gemini (context caching), OpenAI (automatic prompt caching on long prefixes) and Bedrock (prompt caching on some models) offer caching. **To be verified for the production model.**
  - Benefit would require synthesis and review to share a prompt prefix. No benefit is claimed.

## 9. Regression and replay results [offline]

| Suite | Result |
|---|---|
| `consolidated-v2`: `test_v2` (46, incl. real-B2 checks) + ported `test_consolidated` (40) + `test_runner` (4) | **90 / 90 pass** |
| Frozen `consolidated` v1 tests | 44 / 44 pass (unchanged) |
| Frozen Multi-Agent suites under the v2 checker and under the original checker | 206 / 206 each |
| `test_numeric_v2` + `test_interpretation_gate` | 30 / 30 |
| `evidence-budget/test_combined` | 13 / 13 |
| Runner suites: `codex_baseline`, `codex_multiagent`, `codex_paired` | pass |
| Baseline `src`: research_chat, answer_quality, indexed_research, experimental_b2_retrieval, business_evidence_handoff | pass |
| `tests/test_experimental_b2_integration.py` (pandas), run with the main repo's existing `.venv` | 12 / 12 |

- **Skipped:** none.
- **Environment note:** the stage-a venv has no pandas, hence the second interpreter.
- **Scripted, not proof:** review decisions in tests are scripted and do not prove the live reviewer will make them.

## 10. Remaining risks and unresolved weaknesses

1. **Untested on a live model:** the C1, L1, V1, V3 and V5 behaviour depends on the live model following the new prompt rules.
2. **Coverage limits:** about 3.5 Standard points (fresh-v2) were outside any bounded retrieval window. C2 covers only conclusions.
3. **Reviewer-dependent checks:** V2 flag resolution and non-numeric entailment still depend on the reviewer. The deterministic checks narrow, but do not remove, wrong-resolution risk. Where v2 raises no flag, wrong-unit or negation errors fall back to the review.
4. **Spelled-count false holds:** the spelled-count check (V5) could withhold correct items that use words like "four" informally. Meta counts of sources are exempt.
5. **Production timeouts:** production adapters time out at 60 s; v1 synthesis took 73.5 s on Codex. This is unmeasured for v2 and is not changed without approval.
6. **Output limits:** the adapters set no maximum output. Some provider defaults (for example Bedrock at 4,096) may truncate a long synthesis reply.
7. **Token accounting:** direct-API overhead profiles are unmeasured conservative defaults.

## 11. Optional Multi-Agent assistance and adaptive routing

- **Deep [implemented, offline-tested]:** Deep remains a development mode. It did not qualify on fresh-v2.
- **Adaptive [prototype; NOT validated, NOT a default]:**
  - **Retrospective check on fresh-v2:** it fired only on H02, a false positive caused by a same-paper model name, and missed H03 and H08, where Deep's supplementary evidence actually helped.
  - **Prior evidence:** the earlier routing study had already rejected the complexity, facet-coverage and score-gap signals as sufficiency predictors.
  - **Conclusion:** the available evidence does not support a trustworthy routing decision. The prototype logs its signals and reasons, so that it can be validated on new data later. It should not be put into production.

## 12. Production integration readiness

**Ready (offline-tested):**

- **Adapter:** `adapter.create_consolidated_research(mode)` runs through the **real** `IndexedResearch.execute`, so the existing `validate_result`, business translation, regulatory stages, fingerprints and UI fields (`status`, `claims`, `kind`, `support`, `chunk_ids`, `limitations`, `limitation_support`, `answer_lead`, `answer_scope`, `quality_review`) all apply.
- **Deep evidence handling:** supplementary passages are gathered in the retrieve phase, because `run_research` fixes the evidence list there.
- **Business mode:** returns findings only.
- **Checkpoints:** isolated per session, query, mode, index and context. A tampered or stale fingerprint is refused. A retry after a review timeout repeats only the review.

**Blockers and coordination:**

| Blocker | Detail |
|---|---|
| Production provider untested | Run the smoke test (proposal) |
| 60 s adapter timeout | Against Codex-measured synthesis times |
| No explicit max output | Should be ≥ 8k; verify provider limits (Gemini 2.5 Flash and current OpenAI models exceed 8k; some Bedrock defaults are lower) |
| Frontend changes | Showing evidence notes, related-variant labels, interpretation labels, a Deep/assist toggle, progress and retry is the UI owner's work, not done here |
| Production checkpoint storage | Needs a hosting decision (local folders today) |
| Merge | Needs your approval: the adapter lives in `experiments/` and is not wired into `src` |

## 13. Proposed final fresh validation

See `VALIDATION-PROPOSAL.md`:

- **Design:** B0 Original Baseline vs S2 optimized Standard, with S1 (v1) as control, on 8 fresh-v3 questions from the last 8 clean papers.
- **Budget:** **48 expected calls, hard cap 60.** Optional Deep v2 adds 24 calls (cap 90 in total).
- **Qualification:** requires zero citation-grounding failures, zero misleading claims, 100% numerical correctness and +10% points over B0.
- **Smoke test:** a separate production-provider smoke test of 6 calls (cap 10).

## 14. Files, location and commands

- **Worktree:** `D:\KPMG-source-grounded` (branch `claude/source-grounded-quotes`). Nothing committed or merged.
- **New:**
  - `experiments/consolidated-v2/*`
  - `experiments/consolidated/FINAL-EVALUATION.md`
- **Unchanged:** `experiments/consolidated/*` sealed v1 code, results and `fresh-v2` (the seal still verifies); `src/*`; `ui/*`.

Run the offline commands from `D:\KPMG-source-grounded\experiments\consolidated-v2`:

```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -m unittest test_v2 test_consolidated test_runner
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I measure_prompts.py
```
