# S2-R2 implementation report and proposed unseen evaluation

**Date:** 2026-11-26.

**Branch:** `exp/s2-r2-fusion`.

**Status:**
- **Done:** offline verification. 0 model calls.
- **Not run:** no live evaluation.
- **Not touched:** frozen S2, the deploy/azure-vm branch and the hosted application.

## Implementation

**Code:** `s2_r2.py`, `S2R2Research(retrieval_strategy='s2'|'b1'|'r2')`. The default is `'s2'`, which is exactly frozen S2.

**`r2` routing:**

| Question type | Route |
|---|---|
| Two or more named papers resolved | B1, unchanged |
| Otherwise, two or more question components | component-rank fusion |
| A single ask | S2's own window, with no extra searches |

**Component-rank fusion** reuses `s3_evidence.s3_packet` at `budget=6000`: the frozen `select_grouped`, the C2 allowance of 800 tokens, the request guard, and the original top-4 first.

**Unchanged:** synthesis, review, citation checks, publication gates and the 2 LLM calls.

**Dependencies, configuration and index:**
- No new dependencies.
- No index change: the same demo-100 B2 bundle.
- One new constructor argument, `retrieval_strategy`.

## Offline verification through the engine wrapper

Script: `eval_r2.py`; results in `r2-offline.json`.

| Set (points) | S2 | B1 | R2 |
|---|---|---|---|
| heldout-v1 (27) | 27 | 27 | 27 |
| completion-eval-v1 (41) | 34 | 34 | 35 |
| combined-v1 (44) | 30 | 30 | 36 |
| fresh-v2 (36) | 28 | 28 | 30 |
| fresh-v3 (38) | 23 | 25 | 26 |
| fresh-v4 (50) | 36 | 40 | 42 |
| **Total (236)** | **178** | **184** | **196** |

This reproduces the proposal exactly.

**Routes across the 61 questions:**
- 51 fusion;
- 6 B1;
- 4 single-ask questions, which got S2's own window.

## Retrieval cost (measured; local CPU, no LLM)

| Measure | S2 | R2 |
|---|---|---|
| Retrieval operations per question | 1 | 3.44 mean (at most 7: 1 original + up to 6 components, run 3 in parallel) |
| Added retrieval wall time | — | median **+4.3 s**, max +11.6 s (cached per-search CPU timings, 3 workers) |
| Evidence tokens (passage text, MiniLM) | 6,006 mean | 5,980 mean (same 6k cap) |
| LLM calls | 2 | 2 |
| CPU | 1 reranked search, about 3–13 s | 3–7 reranked searches; about +4 s of single-core time each, parallelised |

## The five displaced points (documented, not tuned away)

| Point | Anchor's rank in S2 | What happened | Severity |
|---|---|---|---|
| C11.1 (FMTI 100 indicators) | 15 | Fusion promoted 2 component passages; the anchor fell below the 6k cut | moderate: one core finding |
| G05.5 (interactive LLMs < 50% of upper bound) | 16 | 7 component passages promoted | moderate |
| G09.3 (EN/EU performance not established) | 18 / 45 | 5 promoted | moderate: an evidence-limit point |
| H04.4 (continuous AT mechanism) | 11 | 14 promoted; a large reshuffle | moderate |
| K10.1 (PGuard multimodal F1) | 17 | 4 promoted | moderate: one core result |

**Common cause:**
- Each anchor ranked 11th–18th for the whole question but did not rank in any component search.
- Fusion averages component ranks, so passages that are strong for the whole question but not for any single part lose ground to passages that are top-ranked for one part.
- The budget is fixed, so something has to drop out.

**Severity:** this is the expected price of reordering at a fixed budget: 18 points gained for 5 lost, a net +12 over B1. None of the lost points is a safety issue, but each is a real, answerable fact. I did not tune weights against these known questions.

## Regression tests

**New:** `test_s2_r2.py`, 8 tests.

| Area | What is covered |
|---|---|
| Default and flag-off | equal to frozen S2; an invalid strategy is rejected |
| Simple single-ask question | equals S2, with no searches |
| Named cross-paper question | routes to B1 |
| Unnamed multi-part question | routes to fusion and promotes component evidence |
| Single-paper multi-part question | 6k cap, C2 cap, passage cap and the original top-4 head all hold |
| Ordering | deterministic across repeats and between parallel and sequential runs |
| Wrapper reproduction | fresh-v4 gives S2 36, B1 40, R2 42 through the engine |

**Total with the existing suites:** 59 tests, all passing (R2 8, B1 11, S3 40). The frozen seals (`s3-freeze.json` and `b1-freeze.json`) still verify.

## Latency: why allow 1.25× instead of 1.10×

**Previous expectations, kept visible:**
- **B1 diagnostic:** limit 1.10×; measured median 1.21× (90 s for saved S2, 109 s for B1).
- **Frozen product limits:** median ≤ 120 s, p90 ≤ 180 s.

**Why 1.10× was the wrong bar:**
- Saved runs show call time = output tokens ÷ about 46 tokens/s, with r = 1.00 and constant provider speed.
- More complete answers are longer, so any coverage gain costs generation time.
- 1.10× effectively forbids the improvement the change is meant to make.

**What 1.25× allows:** answers about 25% longer, plus about 4 s of retrieval.

**The binding limits are absolute:** S2's 93 s median would become about 116 s, still inside the existing **120 s median and 180 s p90** product limits.

**Reporting:** relative and absolute latency will both be reported, separately for named two-paper questions.

## Proposed unseen live evaluation (needs approval; criteria freeze before running)

**Questions:** 8 new questions, written and sealed before any engine sees them.
- 3 named two-paper questions;
- 3 unnamed multi-part single-paper questions;
- 2 simple or evidence-limit controls.

**Papers:** written against the existing corpus, using facts and sections that **no existing key point uses**.

> **Disclosure:** the corpus cannot be expanded this round, so the questions are new but the papers are not. This is unseen-question evidence, not unseen-paper evidence.

**Key review:** one independent AI key review, then your sign-off.

**Arms:** frozen S2 vs S2-R2 on the same questions and the same provider (Codex, gpt-6.1-sol, low).

**Budget:** 32 calls expected, **hard cap 40**.

**Scoring:**
- a blind A/B packet for a fresh Codex scorer;
- the programmatic audit (quotes, numbers, uncited absence claims);
- my check of every flag;
- your adjudication.

**Acceptance criteria (proposed, to freeze):**
1. R2 points ≥ S2 points + 2 (on about 35–40 points).
2. Zero new citation-grounding, numerical, misleading or unsupported claims.
3. Median latency ≤ 1.25× S2 **and** ≤ 120 s absolute; p90 ≤ 180 s.
4. Input tokens ≤ 1.10× S2.
5. Displaced points are reported per question; this is not a gate.

**Outcome:**
- **Pass:** R2 becomes the experimental candidate for integration, with S2 still the default.
- **Fail:** keep S2 and B1 as they are.

**Target:** the 85% completeness objective remains an eventual goal, not a claimed result.
