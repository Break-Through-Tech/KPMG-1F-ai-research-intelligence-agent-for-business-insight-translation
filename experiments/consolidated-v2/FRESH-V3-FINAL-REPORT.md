# fresh-v3 final validation: qualification report and delivery recommendation

**Date:** 2026-11-25.

**Inputs:**
- sealed fresh-v3 set and arms (seal verified);
- persistent ledgers;
- programmatic audit (`fresh3-audit.json`);
- Claude audit (`CLAUDE-AUDIT-v3.md`, completed before any blind score existed);
- independent blind scores from a fresh Codex session (`D:\KPMG-blind-v3\blind-sheet-v3.scored.json`, scorer "GPT-6", sha256 `4c7a179a…2ee0`).

The packet and blank sheet were unchanged after scoring (hashes match). Results are unblinded with `fresh3-blind-key.json`.

**What was not done:** no research-provider calls, no engine changes and no new experiments. The frozen criteria are applied as written.

## Verdict

| | Qualifies? | Binding failures |
|---|---|---|
| **S2: V2 Standard** | **No** | completeness 65.8% < 80%; 0/8 fully answered (needs ≥ 4); 25.0 vs S1 25.5 (regression by 0.5) |
| **D2: V2 Deep** | **No** | completeness 69.7% < 80%; S2 + 3.9 pp (needs + 10 pp) |

**Robust to adjudication.** The verdict holds for any outcome of the pending human adjudication:

- Granting every upward call Codex left open would add 2.5 points to S2 (27.5, 72.4%) and 2.0 to D2 (28.5, 75.0%). Both stay below 80%.
- The safety items still open concern only B0 and S1, which the criteria do not gate.

Under the frozen decision rule: no promotion, the Original Baseline stays the production default, D2 is not adopted as a deep mode, and at most one bounded corrective round follows.

## 1. Scores (blind, unblinded)

| Arm | Points / 38 | % | Fully answered |
|---|---|---|---|
| B0 Original Baseline | 17.5 | 46.1 | 0 |
| S1 Consolidated v1 | 25.5 | 67.1 | 0 |
| **S2 V2 Standard** | **25.0** | **65.8** | 0 |
| **D2 V2 Deep** | **26.5** | **69.7** | 0 |

Per question (points):

| | J01/5 | J02/4 | J03/5 | J04/5 | J05/5 | J06/4 | J07/6 | J08/4 |
|---|---|---|---|---|---|---|---|---|
| B0 | 4.5 | 2.5 | 2.5 | 0.5 | 3.5 | 0 (exec. error) | 2.0 | 2.0 |
| S1 | 3.5 | 3.0 | 2.5 | 2.5 | 4.5 | 3.5 | 4.0 | 2.0 |
| S2 | 4.0 | 3.0 | 2.5 | 2.5 | 4.0 | 3.0 | 4.0 | 2.0 |
| D2 | 4.0 | 3.0 | 3.0 | 2.5 | 4.5 | 3.0 | 4.0 | 2.5 |

**S2 versus B0:** +19.7 pp. Excluding B0's failed J06, it is still +13.2 pp (S2 22.0/34 vs B0 17.5/34).

## 2. Frozen criteria

| Criterion | S2 | Result | D2 | Result |
|---|---|---|---|---|
| Completeness ≥ 80% | 65.8% | **fail** | 69.7% | **fail** |
| Fully answered | 0/8 (≥ 4) | **fail** | 0 ≥ S2's 0 | pass |
| vs B0 + 10 pp | +19.7 pp | pass | — | — |
| vs S1 (no regression) | 25.0 < 25.5 | **fail** | — | — |
| vs S2 + 10 pp | — | — | +3.9 pp | **fail** |
| Safety | 0 / 0 / 0 / 0 | pass | 0 / 0 / 0 / 0 | pass |
| Execution | 8/8, 8/8 first pass | pass | 0 errors | pass |
| Latency | median 94.8 s, p90 145.8 s | pass | median 108.3 s (≤ 189.6), p90 152.4 s | pass |
| Tokens ≤ 0.80 × S1 | 0.664 | pass | — | — |

## 3. Safety: three independent passes

| Arm | Programmatic | Claude audit | Codex blind | Proposed confirmed |
|---|---|---|---|---|
| **S2** | 0 | 0 | 0 | **0** |
| **D2** | 0 | 0 | 0 | **0** |
| S1 | 0 | 1 plausible (J03 L0) | 1 (J03 L0) | 1 citation-grounding |
| B0 | 3 number flags | J02 F0, J07 L1; J02 F3 plausible misleading | J05 F0, J07 L1 | 3 citation-grounding (J02 F0, J05 F0, J07 L1); 1 misleading pending (J02 F3) |

**Agreement between the passes:**
- Both reviewers independently found S1 J03 L0 and B0 J07 L1.
- Codex also found B0 J05 F0 ("few-shot" not in its own quotes), which I missed. I agree with it.
- My B0 J02 F0 and J02 F3 were not flagged by Codex.

**What remains for you:** confirming the S1 and B0 counts. They do not affect either verdict.

**What the safety result shows:**
- S2 and D2 produced 239 published items with 363 quotes and no grounding, misleading or numerical failures in any pass.
- On fresh-v2, v1 Standard and Deep failed the safety gate with 1 and 2 adjudicated failures.
- The v2 publication gates (V1–V5) did what they were built for.

## 4. Why completeness failed: retrieval coverage, not synthesis

`fresh3-coverage.json` checks, for every required point, whether a complete anchor group was in the evidence the synthesis call actually saw. It uses saved run files only.

| Arm | Points with full anchor evidence | Points lost: evidence missing | Points lost: evidence present |
|---|---|---|---|
| B0 | 16 / 38 | 15.0 | 5.5 |
| S1 | 23 / 38 | 8.5 | 4.0 |
| S2 | 23 / 38 | 8.5 | 4.5 |
| D2 | 25 / 38 | 7.0 | 4.5 |

**Why S2 could not reach 80%:**
- S2 saw complete evidence for only 23 of 38 points.
- Even perfect synthesis on that evidence would score about 23 + 6.5 points of partial credit it earned on partly covered points ≈ 29.5 (77.6%). That is short of 80% without any synthesis error.
- So the shortfall is mainly retrieval coverage of multi-part questions within the fixed evidence budget. It is not mainly key severity, which was the concern flagged before the run.

**Points lost for missing evidence (S2):** J01.5, J02.3, J03.2, J03.3, J03.4, J04.2, J04.3, J04.5, J07.5, J08.1, J08.2 and J08.4. For example:
- the CliBench scores and gaps;
- the fine-tuned-judge and 91% critique-quality figures;
- the catalyst no-RAG ablation and k = 20 sources for J08;
- the MARASON 0.2/0.3 switching rule for J08.

**Points lost with evidence present (S2):** J01.2, J02.2, J05.4, J05.5, J06.3, J06.4 and J07.2 at 0.5, and J07.4 at 0. Mostly a component missing from otherwise correct items, such as the band gap, "learned affinities" or the 10B/37 GB example. Several Codex marked as provisional strict calls.

**Deep's planner** added complete evidence for 2 more points and 1.5 more scored points. It did not change the outcome. On J01 and J02 its searches added nothing: the synthesis prompt was byte-identical to S2's.

**S2 versus S1:** 25.0 vs 25.5 is a 0.5-point difference on a sample where earlier run-to-run noise moved five points by 0.5 each (methodology note 3). On practical terms S2 matches S1, with 34% fewer input tokens, an 11% lower median latency and a cleaner safety record. Under the frozen exact comparison it is a regression, and that ruling stands.

## 5. Execution and cost

| Arm | Calls | Complete | Median s | p90 s | Input tokens |
|---|---|---|---|---|---|
| B0 | 15 (1 timeout) | 7/8 (J06 contract failure, twice) | 68.9 | 365.8 | 256,666 |
| S1 | 16 | 8/8 | 107.0 | 119.7 | 505,844 |
| S2 | 16 | 8/8 | 94.8 | 145.8 | 335,683 |
| D2 | 24 | 8/8 | 108.3 | 152.4 | 453,573 |

**Totals:** 71 of the 90 allowed calls. Every arm stayed within its cap.

## 6. Delivery recommendation

1. **Production:** keep the Original Baseline as the default. Neither V2 engine is promoted, and D2 is not offered as a deep mode.
2. **What this evaluation does establish for delivery:**
   - The v2 grounding and publication layer is safe on unseen material: 0 failures across three independent passes.
   - It is cheaper and faster than v1, and roughly 20 pp more complete than the Baseline.
   - That is a sound basis for one corrective round. It is not a release.
3. **One bounded corrective round, per the frozen rule:**
   - **Target:** retrieval coverage only, meaning the evidence reaching synthesis for each sub-part of a multi-part question. That is where 8.5 of S2's 13 lost points sit.
   - **Unchanged:** synthesis, review, the publication gates and the safety design.
   - **No repeated tuning on fresh-v3:** it is spent, and it must not be used to tune or re-score the corrected engine.
   - **Validation:** on genuinely fresh material (new papers or a new corpus), with the same frozen criteria and a pre-stated call cap.
   - **Stopping rule:** if the corrected engine does not qualify, stop engine development and deliver the Baseline.
4. **Production-provider smoke test (6 calls, cap 10):** remains separate. It is only worth running if a corrected engine is later a candidate for promotion.

## 7. Open items for the project lead

- **Confirm the safety adjudication for S1 and B0** (§3). Record the counts in `fresh3-adjudication.json`, then run `fresh3_scoring.py criteria`.
- **Results so far are provisional:** `fresh3-results.PROVISIONAL.json` holds the same S2 and D2 verdicts, computed with the proposed counts.
- **Codex's open scoring questions** (band gap for J01.2, learned affinities for J02.2, and others) can be resolved or left as scored. None changes either verdict (§ Verdict).

Nothing has been committed, merged or deployed.
