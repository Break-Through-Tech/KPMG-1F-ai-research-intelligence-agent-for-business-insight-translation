# Consolidated Baseline-powered Deep Research: implementation report

**Status: built and validated offline only. No live model calls, merges, deployments or shared-app changes.**

- The Original Baseline remains the default. The Original Baseline, Improved Baseline (B1) and previous Multi-Agent (M1) are untouched and stay available as controls and fallbacks.
- Everything new is in `experiments/consolidated/`, behind an opt-in runner. No reliability improvement is claimed before live validation.

## 1. Architecture implemented

```
                 ┌── Standard ────────────────────────────────────────────────────────────────────┐
question ──► [evidence: protected 6k packet] ─► [synthesis: 1 call] ─► [review: 1 call] ─► [publication gates]
                 └── Deep: [planner: 1 call] ─► [protected packet + ≤3 planned searches, 8k] ─► same three stages ┘
   every completed stage is checkpointed; a resume repeats only the failed stage
```

- **One foundation, two modes** (`engine.ConsolidatedResearch`). Both modes call the same `synthesis`, `review` and `publication` functions; Deep differs only in the planner call and the supplementary evidence.
- **Call counts:** normally 2 (Standard) and 3 (Deep). With no evidence or no claims, the later calls are skipped.
- **No other model calls:** no agent loop, no extra reviewer, no repeated synthesis.

| Module | Role |
|---|---|
| `evidence.py` | Protected packet, Deep merge, table groups, request-size bound |
| `synthesis.py` | One call; atomic findings; per-item validation; derived status |
| `review.py` | One call; Baseline review policy plus quote-entailment, partial-retention, added-support and flag-resolution fields |
| `publication.py` | Deterministic gates P1–P5 per claim, interpretation gate, limitation checks |
| `engine.py` | Stages, checkpoints, planner fallback |
| `run_consolidated.py` | Sealed runner: caps, one resume, usage recording |

## 2. Existing components reused, unchanged

| Component | Used for |
|---|---|
| B2 retrieval and `evidence_budget.open_ranked` / `skip_fit` (6k, window 30) | Ranked candidates and MiniLM token counts |
| `src/answer_quality.POLICY` (Improved Baseline review policy) | The review prompt's base text, verbatim |
| Improved Baseline synthesis rules from `src/research_chat.synthesize` | Kept in `synthesis.BASELINE_RULES` |
| Baseline schema conventions | Chunk-ID enum, exact quotes, `insufficient_evidence` with cited limitations |
| Multi-Agent planner: `ORCHESTRATOR_PROMPT`, `PLAN_SCHEMA`, `_call` | The Deep planning call, unchanged |
| `numeric_checks_v2` plus statistical-report rule, `interpretation_gate` (G1–G7), `advice_issues` | Attribution checks and interpretation gating |
| `codex_paired.Budget` / `CodexCalls`, `request_guard.RequestGuard`, Codex adapter | Persistent call caps, request-size guard, provider calls |

## 3. Components changed or added, and why

| Change | Why (evidence) |
|---|---|
| **Atomic findings:** one result per finding, up to 14 | M1 lost correct figures bundled with unquoted ones (G03, G04, G08). Bundled sentences also caused v2's subject misreads (G03, G04 false rejections) |
| **Attached-quote rule** in synthesis, review and gate P4 | The two Codex citation-grounding failures. G03-B F2: B1 published 3- and 4-shot Table 7 figures cited only to the 2-shot row, because Baseline's number check runs only when the arXiv fallback is configured. G03-C F1: M1's verifier read the whole passage |
| **Review extension, same call:** `quotes_entail`, `supported_text`, `added_support`, `flag_resolutions` | Withhold or reduce only the unsupported part (FActScore-style), and let correct figures be properly attached, without adding a call |
| **v2 flags resolved by quote anchoring** (P5) instead of auto-hold | M1's 3 false rejections (G03, G04, G07). The flags are still enforced; one is cleared only by an exact quote span containing the number, the clause's named entities present in the quotes, and a "respectively"-consistent mapping. `numbers_absent` is cleared only when P4 proves the value is quoted |
| **Status derived from validated claims;** per-item validation | M1 G10: one contract inconsistency discarded the whole answer. Each item is still fully validated |
| **Per-decision review parsing** | A missing or duplicate decision withholds only that claim. Inconsistent coverage is repaired and recorded |
| **Table groups** (≤ 12 rows), with incomplete-table notes | Every combined-v1 arm missed half of a table pair (G07.2, G07.3). Partial tables are now flagged to synthesis and published as evidence notes |
| **Deep evidence bound** by the guard's estimate (38k) as well as 8k MiniLM tokens | Table-heavy packets serialize to about 6× their MiniLM count. An 8k Deep packet could exceed the 40k guard cap and fail the question |
| **Stage checkpoints;** planner fallback; one-resume runner | combined-v1 had 9 of 30 timeouts, and every resume restarted from scratch. A failed or invalid plan now falls back to Standard evidence instead of failing |

## 4. Known failures addressed (and how each is tested)

| Failure | Engine behaviour now | Test (kind) |
|---|---|---|
| G03-B F2: extra figures cited to the wrong row | Withheld by P4, which names 59.4/59.5/78.0/81.4. Published only if reduced to the 2-shot figures, or if the rows are attached and every flag is anchored | 4 replay tests |
| G03-C F1: fact from the passage, not the quote | Withheld or reduced when the review finds the quotes do not entail it; published if the proper c0027 sentence is attached. **Deterministic code alone cannot catch this**; it depends on the review judgment | replay (simulated review decisions) |
| M1 false rejection G07 ("sub-4-second") | Cleared deterministically | replay |
| M1 false rejections G03 and G04 | Flags kept without resolution; published with quote-anchored resolutions | replay (simulated resolutions) |
| Wrong subject, swapped "respectively" mapping, unsupported number | Withheld; a wrong resolution cannot clear them | unit |
| G10 output contract | Validated claims recovered; repair recorded | replay + simulated engine run |
| Bundled claim sinks unrelated findings | Only the failing claim is withheld; status ok, scope partial, with a note | unit |
| Planner invalid or timeout; budget exhausted | Fallback to Standard evidence (recorded); budget exhaustion is never a fallback | simulated |
| Timeout at synthesis or review | Checkpoint kept; resume repeats only that stage; at most two attempts | simulated |
| Oversized request; call cap; combined cap | Refused before a call is reserved; persistent ledgers; combined 50 enforced | simulated |

## 5. Offline regression and replay results (2026-11-24)

| Suite | Result | Kind |
|---|---|---|
| `test_consolidated` (40) + `test_runner` (4) | 44 / 44 pass | replay of saved combined-v1 drafts and evidence; simulated provider; unit |
| Frozen Multi-Agent suites under v2, and under the original checker | 206 / 206 pass each | unit / simulated |
| `test_numeric_v2` + `test_interpretation_gate` | 30 / 30 pass | unit |
| `evidence-budget/test_combined` | 13 / 13 pass | simulated |
| Runner suites: `test_codex_baseline`, `test_codex_multiagent`, `test_codex_paired` | pass | simulated |
| Baseline `src` tests: research_chat, answer_quality, indexed_research, experimental_b2_retrieval, business_evidence_handoff | pass | unit |
| `tests.test_experimental_b2_integration` | 12 / 12 pass, run with the main repository's existing `.venv` (Python 3.11, pandas installed; the stage-a venv has no pandas) | unit / integration |
| `offline_check.py`: real B2 on fresh-v2 | Every Standard synthesis request is within the guard (max about 39k estimated tokens); 0 model calls | real retrieval, no generation |

**Kinds of evidence:**

- **Replay:** real model drafts and evidence saved from combined-v1. Every review decision a replay needed was simulated.
- **Simulated:** scripted provider replies.
- **Not measured:** how the live model behaves with the new prompts. Whether it decomposes claims, judges quote entailment correctly and provides valid flag resolutions is untested until the live validation.

## 6. Remaining risks and limitations

1. **Non-numeric over-claims** (the G03-C F1 type) are caught only by the review model's `quotes_entail` judgment. Deterministic gates cover numbers, quotes and attribution flags, not general entailment.
2. **Wrong flag resolutions:** the reviewer could supply a span that passes the checks while the claim's meaning is wrong. Spans must be exact, contain the number and the clause's entities, and keep "respectively" mappings consistent, but this narrows the risk rather than removing it.
3. **v2 false alarms on serialized table rows** remain (header words read as negation or unit mismatch). If the reviewer does not anchor them, correct table facts are withheld, which is information loss rather than a safety failure. Atomic claims reduce the risk.
4. **Spelled-out numbers** ("four models") are outside the number-recall gate.
5. **Timeouts** remain the main execution risk; checkpoints reduce their cost but not their frequency. The longer atomic output and the larger review request (flags plus decisions) may raise latency.
6. **Tables over 12 rows** are not expanded; they are noted as incomplete. The offline check shows up to 12 notes for one question, which adds prompt noise.
7. **Token estimates:** the request guard uses ceil(bytes / 3), not the provider's tokenizer; actual usage is recorded from receipts.
8. **Scope:** research-only. Business translation and the regulatory stages are not part of this experiment, as in combined-v1.
9. **Validation limits:**
   - the fresh-v2 key is AI-assisted;
   - there are only 8 questions;
   - three papers each serve two questions;
   - the comparison is Standard vs Deep only, not against the Original Baseline; and it measures planning *together with* Deep's larger evidence budget, not planning alone.

## 7. Expected live usage, files and commands

See `VALIDATION-PROPOSAL.md`. In brief:

- **Calls:** 40 expected (16 Standard + 24 Deep), hard cap 50 (20 + 30).
- **Tokens:** about 1.3–1.4M estimated input tokens.
- **Commands:**

  ```powershell
  D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_consolidated.py --check standard
  D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_consolidated.py --run standard
  D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_consolidated.py --run deep
  ```

  Run them from `experiments/consolidated`.

**Files:**

| Area | Files |
|---|---|
| Engine | `engine.py`, `evidence.py`, `synthesis.py`, `review.py`, `publication.py`, `env.py` |
| Runner | `run_consolidated.py` |
| Tests | `test_consolidated.py`, `test_runner.py` |
| Offline check | `offline_check.py` → `offline-check.json` |
| Docs | `TECHNIQUES.md`, `VALIDATION-PROPOSAL.md`, this report |
| Fresh set | `fresh-v2/`: `questions.json`, `references.json`, `answer-key.md`, `rules.json`, `OVERLAP.md`, `build_set.py`, `seal.json` |

**Re-run all offline tests** (from `experiments/consolidated`):

```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -m unittest test_consolidated test_runner
```
