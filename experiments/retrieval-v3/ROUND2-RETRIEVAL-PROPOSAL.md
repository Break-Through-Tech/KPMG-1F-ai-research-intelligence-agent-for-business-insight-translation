# Research round 2 (retrieval coverage and B1): findings and one proposal

**Date:** 2026-11-26.

**Status:**
- **Done:** a read-only investigation of saved artifacts and offline ranking replays, with 0 model calls.
- **Not touched:** frozen S2, the deploy/azure-vm branch and the live application.

## Findings

### 1. Why B1 is slower: longer answers, nothing else

Across every saved live run, call time tracks **output** tokens almost perfectly:

| Run | Calls | Output throughput | corr(output tokens, seconds) | corr(input tokens, seconds) |
|---|---|---|---|---|
| fresh-v3 S2 | 16 | 46.0 tok/s | 1.00 | -0.46 |
| fresh-v4 S2 | 20 | 46.1 tok/s | 1.00 | -0.46 |
| fresh-v4 S3 | 20 | 47.3 tok/s | 1.00 | -0.52 |
| B1 diagnostic | 6 | 46.5 tok/s | 1.00 | -0.61 |

**Provider speed was constant**, at 46–47 tokens/s across days. So **provider variability does not explain B1's latency**, and the input size does not matter.

**Retrieval time did not change**: 6.6/13.9/9.9 s for S2 against 13.1/13.9/4.0 s for B1, with no added searches.

**The entire difference is output length.** On K05 and K07, B1's synthesis and review wrote 1.5–2.1× more tokens because they had evidence from two papers to cover.

**Implication:** B1's latency is the cost of more complete answers, not overhead. Any retrieval change that broadens the evidence will lengthen answers in the same way.

### 2. What is still missing on fresh-v4 with B1

**Status:** retrospectively 41/50. 9 points are still lost:
- **5.5 points: evidence never reached synthesis.** K04.3, K05.1, K05.5, K07.3, K07.5, K08.5, K09.5, K10.2 and K10.3.
- **3.5 points: evidence present, but the answer was incomplete.** K02.1, K03.4, K04.5, K05.2, K06.1, K06.4 and K09.1. This is out of scope for this round.

**Where the missing anchors rank:**

| Point | Rank in the original query | Best rank in a component search |
|---|---|---|
| K10.3 | 59 | 2 |
| K10.2 | 46 | 3 |
| K08.5 | 30 | 4 |
| K04.3 | 25 | 1 |
| K09.5 | 26 | 12 |
| K07.3 / K07.5 / K05.5 | 78–103 | 41 or not found |
| K05.1 | not found | not found |

**What this means:** most of the recoverable misses are **depth within one paper**. The passage ranks below the 30-slot window for the whole question but at the top when one part of the question is searched alone.

### 3. Does B1's mechanism generalize beyond named papers? It does not need to.

In all **8 cross-paper development questions that name no title**, every referenced paper already has 4–24 passages in S2's top-30 (H04, C07, C15, G03, G04, G05, fresh-v2 H04, J08). Starvation, which B1 fixes, happens only when a named paper is crowded out. A name-free B1 would therefore recover nothing on these. Their misses are depth or synthesis problems.

### 4. Can coverage improve without more LLM calls or more budget? Yes: rank fusion at the same 6k budget

Offline replay, using the frozen selection code and the same 6,000 + 800 token budget:

| Set (points) | S2 | B1 | Fusion at 6k | **B1 if 2+ papers named, else fusion** |
|---|---|---|---|---|
| heldout-v1 (27) | 27 | 27 | 27 | 27 |
| completion-eval-v1 (41) | 34 | 34 | 35 | 35 |
| combined-v1 (44) | 30 | 30 | 36 | 36 |
| fresh-v2 (36) | 28 | 28 | 30 | 30 |
| fresh-v3 (38) | 23 | 25 | 24 | 26 |
| fresh-v4 (50) | 36 | 40 | 38 | **42** |
| **Total (236)** | **178** | **184** | **190** | **196 (+18 vs S2; +12 vs B1)** |
| Points lost vs S2 | — | 0 | 6 | 5 |
| Evidence tokens vs S2 | — | ≈1.00 | 0.99 | ≈1.00 |

**Fusion** is S3's retrieval component, tested here alone at S2's budget, without S3's 8k budget or synthesis checklist. It scores each passage by its rank in the original query plus the mean of its ranks in the per-component searches, restricted to the question's papers. It costs CPU component searches (about +4–10 s retrieval), but **no LLM calls**.

## Proposal: one change, "S2-R2"

| | |
|---|---|
| **Problem** | Within-paper evidence that ranks 25–60 for the whole question but in the top 1–4 for one part of it never enters the 30-slot window. This accounts for about 3–4 of the 5.5 retrieval-missed fresh-v4 points |
| **Evidence** | §2 rank table. Offline replay: +12 covered points over B1 across 6 sets at an unchanged token budget |
| **Change** | Evidence selection only, behind a flag: B1 when two or more papers are named (unchanged), otherwise **component-rank fusion** ordering the 30-candidate window. The frozen skip-fit at 6,000 tokens, C2, the passage cap, synthesis, review and gates are all unchanged. No new dependencies, index changes or LLM calls |
| **Expected benefit** | Evidence coverage 184 → 196 of 236 on development sets; on fresh-v4 40 → 42 of 50. A realistic answer-level gain of about 1–2 points per 50 |
| **Regressions** | 5 previously covered points lost offline: crowding by fusion-promoted passages. Retrieval +4–10 s from component searches. **Longer answers, so more latency**, by the same mechanism as §1 |
| **Evaluation** | (1) Offline: done; reproduce through the real engine wrapper with tests, as for B1. (2) Live, needs approval: **unseen questions only** (the reserved integration set of named and unnamed multi-part questions), S2 vs S2-R2 on the same questions, blind-scored |
| **Acceptance (proposed, to freeze before the live run)** | Higher answer points than S2 by ≥ 2 per 50 points; zero new safety flags; median latency ≤ 1.25× S2, reported separately for named two-paper questions; input tokens ≤ 1.10× S2 |

## Honesty notes

- **Development data only:** fusion was chosen on these same development sets in round 1, and fresh-v4 has now been seen. The table above is development evidence, **not generalization**. Only the unseen integration questions can show generalization.
- **The 85% target:** S2 + B1 + R2 projects to roughly 42–43 of 50 (84–86%) on fresh-v4. That is retrospective and optimistic. The remaining gap is the 3.5 synthesis-side points, the next component for a later round.

## Branch

- **Proposed branch:** `exp/s2-r2-fusion`, created from the evaluated checkpoint.
- **Not created yet:** no files are committed and no branch is created until you approve, to avoid colliding with Codex's checkpoint work in the shared worktree.
- **Integration and rollback:** a flag; default off, which equals frozen S2.
