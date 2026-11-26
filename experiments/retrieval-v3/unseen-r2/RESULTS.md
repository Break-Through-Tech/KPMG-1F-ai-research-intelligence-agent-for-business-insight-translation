# Unseen evaluation results: S2 vs S2-R2 (passed)

**Date:** 2026-11-26.

**Setup:**
- 8 sealed unseen questions; maximum score 36.
- Provider: Codex `gpt-6.1-sol`, low effort, for both arms.
- Corpus: the validation index.
- Execution: fully automated and counterbalanced.
- Blind scoring: a fresh Codex CLI session (scorer "GPT-6"). The packet hash matches the label map (`cfd8dc28…`).

**Disclosure:** the questions are new, but the papers are not, because the corpus was not expanded.

## Result

**R2 passes all six frozen criteria.**

| Criterion | S2 | R2 | Result |
|---|---|---|---|
| 1. R2 ≥ S2 + 2 points | 25.0 / 36 (69.4%) | **29.5 / 36 (81.9%)** | **pass** (+4.5) |
| 2. Zero new safety flags | 0 blind, 0 audit | 0 blind, 0 audit | **pass** |
| 3. Median ≤ 1.25× S2 and ≤ 120 s | 105.2 s | 118.5 s (1.13×) | **pass** |
| 4. p90 ≤ 180 s | 153.4 s | 166.4 s | **pass** |
| 5. Input tokens ≤ 1.10× S2 | 346,947 | 341,961 (0.99×) | **pass** |
| 6. No silent failures or exclusions | 8/8 recorded | 8/8 recorded | **pass** |

**Stricter 1.10× latency reference, not a gate:** R2 would **fail** it, at 1.13×.

**Questions fully answered (reported, not gated):** S2 3/8, R2 4/8.

## Per question

| Question | S2 | R2 | Point changes, R2 vs S2 |
|---|---|---|---|
| U1 (named: HaloGuard and PGuard) | 3.0 | 3.0 | U1.4 +1, U1.5 +0.5; **U1.2 −0.5, U1.3 −1** |
| U2 (named: MedPsy and MatMoE) | 2.5 | 3.5 | U2.4 +1, U2.5 +0.5; **U2.2 −0.5** |
| U3 (named: RAG-TRACE and ECGJev) | 2.0 | 3.5 | U3.3 +0.5, U3.4 +1 |
| U4 (unnamed: translation benchmark) | 5.0 | 5.0 | — |
| U5 (unnamed: compiled harness) | 4.0 | 5.0 | U5.2 +0.5, U5.5 +0.5 |
| U6 (unnamed: DP audit) | 2.5 | 3.5 | U6.2 +0.5, U6.4 +0.5 |
| U7 (simple control) | 3.0 | 3.0 | — |
| U8 (evidence-limit control) | 3.0 | 3.0 | — |

**Totals:** +6.5 gained and −2.0 lost, so **net +4.5**.

**Regressions:**
- U1.2 and U1.3 (HaloGuard per-language weakness and false-negative reduction) were displaced when B1 shared the window with PGuard.
- U2.2 (MedPsy token efficiency) was partly lost.

## Evidence, grounding and safety

**Evidence coverage** (anchored points in the live packets): S2 23/36, R2 24/36.

The answer gain (+4.5) exceeds the coverage gain (+1). Some recovered facts were cited from passages other than the key's anchors, so anchored coverage is a conservative proxy.

**Grounding and safety:**
- **Blind scorer:** 0 citation-grounding, 0 misleading and 0 numerical flags in either arm.
- **Programmatic audit:** 0 inexact quotes, 0 number-recall failures and 0 uncited absence claims in either arm.

## Latency and tokens

| | S2 | R2 |
|---|---|---|
| Median retrieval | 7.8 s | **24.4 s** |
| Median generation (synthesis + review) | 96.8 s | 89.2 s |
| Median total | 105.2 s | 118.5 s |
| p90 total | 153.4 s | 166.4 s |
| Input tokens | 346,947 | 341,961 |
| Output tokens | 35,827 | 33,539 |

**Live retrieval cost is higher than the offline estimate.** The offline estimate was a median of +4.3 s; live, the median was +16.6 s.

The component searches run as 3 parallel threads, and on this CPU they contend with each other and with the reranker. **This is now R2's main latency cost**, more than generation. Answers were not longer in this run.

## Execution

| Measure | Value |
|---|---|
| Model calls | 32 of 40 (16 per arm) |
| Failed calls | 0 |
| Retries / resumes | 0 |
| Completed on first pass | 8/8 in both arms |

Every attempt is logged in `data/processed/unseen-r2-*`, `unseen-r2-progress.log` and `unseen-r2-order.json`.

## Conclusions and limits

**What R2 delivered:** it improved independently measured answer completeness on unseen questions, from 69.4% to **81.9%**, with no safety cost and within all frozen limits.

**Limits:**
- **Sample size:** only 8 questions and 36 points. One point is 2.8 pp.
- **Not unseen papers:** the questions are new but the papers are not.
- **Provider:** Codex only. The result is not yet confirmed on Azure's Gemini.
- **85% target:** not yet reached; 81.9% here.
- **Retrieval cost:** R2's live retrieval cost (+16.6 s median) should be reduced or accepted before integration. A cache or lighter reranking of component searches would be a separate, later change.

**Status:** R2 is preserved as a validated candidate for Azure integration. It is **not deployed**, and frozen S2 remains the default.
