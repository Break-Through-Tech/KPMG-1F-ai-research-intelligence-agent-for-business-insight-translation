# Consolidated Standard vs Deep: final reconciled evaluation (CLOSED 2026-11-24)

- **Primary scores:** the independent blind review (automated reviewer), unblinded with `scoring/blind-key.json`. The packet hash was verified unchanged before unblinding.
- **Transparency record:** automated reviewer’s non-blind scores (`scoring/scores.json`) are kept.
- **Unchanged:** nothing was re-run, and no acceptance criterion was changed. `RESULTS.md` is the historical non-blind report.

## Final results (primary: blind)

| | Standard | Deep |
|---|---|---|
| **Completeness** | **26.5 / 36 (73.6%)** | **28.0 / 36 (77.8%)** |
| Fully answered questions | 0 | 1 (H01) |
| Citation-grounding failures | 0 recorded (see adjudication item 1) | **1** (H01 L1) |
| Misleading or fabricated claims | 0 | 0 |
| Business interpretations, blind scores | all 2 / 2 | all 2 / 2 |

**Interpretations:** there were 11 in total (5 Standard, 6 Deep).

**Per question (Standard / Deep):**

| Question | Points | Question | Points |
|---|---|---|---|
| H01 | 4.5 / 5 | H05 | 3.5 / 3.5 |
| H02 | 3.5 / 4.0 | H06 | 3.5 / 2.5 |
| H03 | 2.5 / 3.0 | H07 | 3 / 3 |
| H04 | 3.5 / 3.5 | H08 | 2.5 / 3.5 |

**Execution:** both arms answered 8/8 on the first pass, with 0 timeouts and 40 of 50 calls.

| | Median latency | p90 latency |
|---|---|---|
| Standard | 119 s | 140 s |
| Deep | 140 s | 143 s |

## Scoring disagreements (blind vs automated reviewer): 7 point-answers

The independent scores stand.

| Point | Arm | Blind | automated reviewer | Note |
|---|---|---|---|---|
| H02.5 | S, D | 1 | 0.5 | automated reviewer accepted the benchmark-only scope conveyed in the cited limitations |
| H03.4 | S | 0.5 | 1 | Black-box scope not stated |
| H03.5 | S, D | 0.5 | 0 | Partial credit for the published outcome rates |
| H04.3 | S, D | 0.5 | 1 | The H100 and 600-second conditions are absent, so only the single-turn component earns credit |

None of the disagreements changes a verdict.

## Citation grounding: the H01-A L1 failure, and consistency

- **The failure automated reviewer recorded:** Deep's H01 L1 says the evaluation "used three-turn conversations". Its own quote states only that "longer conversations (5–7 turns) were not evaluated"; the three-turn detail is supported only by a different item's citation (F0).
- **How it is classified:** under the established rule this is a **citation-grounding failure, not fabrication**. The statement is correct but unsupported by its own attached evidence.
- **Root cause in v1:** the deterministic number-recall gate checked digits only. "three-turn" spells the count out, so it passed, and the reviewer did not catch it.

**Needs human adjudication (independent scores not changed):**

1. **Two more items with the identical defect, not flagged by automated reviewer.** Standard's H01 L1 ("The evaluation used three-turn conversations…", citing the same c0009 sentence) and Deep's H07 L2 ("bounded to three-turn evaluation", same quote) carry the same defect.
   - **If the rule is applied consistently:** Standard also has 1 citation-grounding failure (and Deep 2), and **both arms fail the safety gate**.
   - **Under the blind record as scored:** only Deep fails it.

## Frozen acceptance verdict (unchanged criteria, `fresh-v2/rules.json`)

| Criterion: Deep as the optional deep mode | Result |
|---|---|
| Points ≥ Standard + 3.6 | **Fail** (+1.5) |
| More fully answered questions | Pass (1 vs 0) |
| Both arms pass the safety gate | **Fail** (Deep has 1 citation-grounding failure; Standard as well if adjudication item 1 is upheld) |
| Median total latency ≤ 2× Standard | Pass (1.18×) |
| p90 ≤ 300 s | Pass |
| ≤ 1 execution error after the resume | Pass (0) |

**Verdict:**

- **Deep:** does not qualify as the optional deep mode.
- **Consolidated Standard:** this comparison was never a promotion test for it.
- **Production default:** the Original Baseline remains the default.
- **Status:** the evaluation is closed. fresh-v2 has since informed engineering changes, so it is now regression data only.

## Updated root-cause analysis (blind scores)

| Points lost | Standard (9.5) | Deep (8.0) |
|---|---|---|
| Retrieval: anchor not in the evidence | 6.0 (H03.2, H03.3, H04.2, H04.3, H04.5, H06.2, H07.1, H08.2, H08.3) | 4.5 |
| Synthesis: in the evidence, not or only partly stated | 2.0 (H02.2, H03.4, H03.5, H05.4) | 3.5 |
| Verification: a correct reduction discarded (V1) | 0.5 (H01.1) | – |
| Review relevance: same-study variant rejected (V3) | 1.0 (H02.4) | – |

**Changes from `IMPROVEMENT-PLAN.md`:**

- H02.5 is no longer a loss.
- H04.3 is now a retrieval loss: the 600-second and H100 passage (c0025) was not in either packet.
- H03.4 (Standard) is a synthesis omission (black-box scope).
- H03.5 is a partial synthesis loss.
- The totals by class are unchanged for Standard.
