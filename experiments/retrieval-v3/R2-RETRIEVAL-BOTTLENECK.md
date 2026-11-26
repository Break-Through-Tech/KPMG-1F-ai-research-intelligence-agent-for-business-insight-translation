# S2-R2 remaining retrieval losses and latency: read-only investigation

**Date:** 2026-11-26.

**Method:** saved R2 run artifacts plus local offline retrieval on the validation index; 0 LLM calls. Script: `r2_loss_probe.py`; output: `r2-loss-probe.json`.

**Status:** S2, S2-R2 (`1d0e0ae`), generation and Azure are untouched. No tuning on the 8 questions.

## The lost points (R2 unseen run: 9 points, 6.0 lost)

Every anchor exists in the index as one complete passage (verified by the key build), so **chunking preserved the information in all cases**.

| Point (lost) | Anchor | Rank: original query / within its paper / best component | In R2 packet | Cause |
|---|---|---|---|---|
| U1.2 (0.5), U1.3 (1) | HaloGuard c0033 (465 tok) | 17 / 17 / 9 | no | **B1 displacement**: B1 gives each named paper at most 15 window slots, and this passage is the paper's 17th |
| U1.5 (0.5) | 3-passage group incl. PGuard c0026 | c0026: 133 / – / 8 | 2 of 3 | **Measurement**: the key requires a settings passage outside the pool; the answer got 0.5 from the other two |
| U2.2 (0.5) | MedPsy c0017 | 16 / 14 / – | no | **6k budget**: inside B1's window, cut by skip-fit (packet 6,157 tokens) |
| U2.5 (0.5) | MatMoE c0024 | 35 / 11 / – | no | **6k budget**: inside the window, cut by skip-fit |
| U3.1 (0.5), U3.2 (1) | RAG-TRACE c0013 | 83 / 55 / 25 | no | **Ranking miss**: low for every query wording; no bounded window reaches it |
| U6.1 (0.5) | DP paper paragraph | 38 / 28 / 8 | no | **Fusion dilution and budget**: top-8 for one component, but averaged over 4 |
| U6.3 (1) | DP paper c0013 | 80 / 46 / 4 | no | **Fusion dilution and budget**: top-4 for one component, but averaged over 4 |

**Summary of the 6.0 lost points:**

| Cause | Points |
|---|---|
| B1 per-paper cap or the 6k budget | 2.5 |
| Ranking miss | 1.5 |
| Fusion averaging and budget | 1.5 |
| Measurement limitation | 0.5 |

**Partial credit from other passages:** the scorer gave 0.5 on five of these points, so equivalent evidence from other passages was used where it existed.

**No single cause dominates**, and each remaining fix acts on the fixed 6k budget. These have all been tested before at the same budget, and each displaced other points:

| Earlier fixed-budget variant | Result |
|---|---|
| Max-fusion (FM) | 149 vs mean-fusion 152 of 185 |
| Per-paper scoped expansion (B2) | displaced 2 points |
| Per-component quota (PC) | flat |
| MMR diversity | regressed |

The losses are now spread across budget, cap and ranking limits. **I found no low-risk fixed-budget change with evidence of a meaningful net gain.**

## Latency: 7.8 to 24.4 s median retrieval

Offline timings on the same CPU, with the reranker warm:

| Question | Original search | Component searches (sequential sum) | Component searches with 3 threads |
|---|---|---|---|
| U1 | 11.8 s | 16.3 s (3) | 16.5 s |
| U3 | 7.1 s | 13.8 s (4) | 13.6 s |
| U6 | 9.3 s | 12.1 s (4) | 11.9 s |
| U2 | 3.9 s | none | – |

**Finding 1: the 3-thread parallelism gives no speed-up.** Parallel time equals the sequential sum. The CPU-bound searches (reranker inference) compete rather than overlap, so the threads only add overhead.

**Finding 2: there is a redundant search.**
- `S2R2Research.r2_packet` runs the original-question search to resolve paper names.
- It then calls `balanced_packet` (B1 route) or `s3_packet` (fusion route), each of which **runs the same original search again**.
- Every R2 question therefore pays for the original search twice, about 4–12 s.
- This plus the component searches explains the +16.6 s.
- B1-route questions run no component searches, so on those the duplicate is most of the overhead.

## Recommendation

**Retrieval coverage:** **stop optimizing** at the fixed 6k budget. The evidence supports no further low-risk coverage gain: the remaining losses are spread across budget, cap and ranking limits, and every tested reordering trades points.

**The one change worth making is purely operational, with zero behaviour change:** reuse the original-question ranking within a request, so it is computed once instead of twice.

| | |
|---|---|
| **Expected benefit** | About −4 to −12 s retrieval per question. Estimated R2 median retrieval about 16 s instead of 24.4 s. Byte-identical evidence packets |
| **Evaluation** | Offline only. The packet must be byte-identical before and after on all development sets and the unseen set, with the timing measured. No live calls needed |
| **Risk** | Minimal: memoization within one request |

**Next step: proceed to Gemini validation of S2 and S2-R2.**
- Run it on a new reserved unseen set, with the Azure application's Gemini configuration, in an authorised isolated environment.
- That is where the remaining uncertainties lie: provider transfer, absolute latency and the 85% target. More retrieval tuning would not address them.
