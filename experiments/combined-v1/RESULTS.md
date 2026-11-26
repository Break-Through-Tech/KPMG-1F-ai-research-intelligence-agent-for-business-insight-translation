# combined-v1 preliminary live validation: results

**Status: FINAL (preliminary evaluation, closed 2026-11-24). Neither improved engine qualified under the frozen acceptance criteria. The Original Baseline (B0) remains the default.**

- **Primary scores:** automated reviewer’s independent blind scores. automated reviewer’s original (non-blind) scores and its reconciled scores are kept for transparency in "Blind re-score outcome".
- **Answer key:** approved for preliminary use. Its final corrections were not independently re-reviewed.
- **Nothing changed after results:** no engine, threshold or scoring rule. Nothing was retried beyond the single approved resume. There will be no further scoring rounds, retries or experiments in this phase.

## Final verdict (primary: automated reviewer blind scores)

| Arm | Points / 44 | Fully answered | Safety gate | Latency (successful attempt, frozen basis) | Verdict |
|---|---|---|---|---|---|
| B0 Original Baseline | 24.0 (54.5%) | 1 | Pass | median 51.5 s, p90 189.8 s | Default (control) |
| B1 Improved Baseline | **32.0 (72.7%)** | 2 | **Fail**: 1 citation-grounding failure (G03 F2) | p90 175.9 s, over the 120 s limit | **Not qualified** |
| M1 Improved Multi-Agent | 26.5 (60.2%) | 1 | **Fail**: 1 citation-grounding failure (G03 F1) | median 71.9 s, p90 104.2 s | **Not qualified** |

**Why each improved engine did not qualify:**

- **B1:** it leads answer completeness by +8.0 points over B0. It fails the p90 latency limit and the safety gate.
- **M1:** it fails three requirements:
  - points: +2.5 over B0 against the required +4.4;
  - full answers: 1, no more than B0's 1;
  - the safety gate.

  It also fails both latency limits once the failed first attempts are counted.

**About the citation-grounding failures:**

- The user ruled that both G03 gaps count under the safety gate. These are citation-grounding failures: a correct statement that the claim's attached quote does not fully support.
- They are **not** fabricated or factually incorrect claims. Both statements match the source paper: M1's appears in a cited passage outside the quoted span; B1's figures come from Table 7 rows that were retrieved but not cited.
- No arm published a fabricated, numerically wrong or misattributed claim. No arm invented an answer to the parts the papers don't cover (G09.3, G09.4, G10.4).

**What the evaluation showed:**

| Engine | Strength | Weakness |
|---|---|---|
| B1 | Leads answer completeness | Fails the latency requirement |
| M1 | Retrieves the most evidence: 5.0 points lost to retrieval, against 9.0 for B1 and 14.0 for B0 | Loses about 9.5 points through verification and output-contract failures: false number-check rejections, over-reaching drafts held, and the G10 contract abstention |

The analysis sections below use automated reviewer’s per-point causes. Their point totals are automated reviewer’s original scores; the primary totals are in the table above.

## Execution

- **Calls:** 79 of 100 (B0 18/22, B1 23/23, M1 38/55).
- **First-pass failures:** 9 of 30 questions failed. Every failure was a single Codex CLI call that hit the 300 s timeout; nothing else failed.

  | Arm | Questions that timed out |
  |---|---|
  | B0 | G04, G08 |
  | B1 | G02, G04, G08 |
  | M1 | G02, G03, G06, G08 |

- **No automatic retries:** the runners never retry a call inside a run. The only retries were the approved single resume, which recovered all 9 questions. No execution errors remain.
- **Records kept:** the failed attempts are preserved as `.attempt-1` folders.
- **Cap change:** one spare call was moved from M1 to B1 after the first pass, with approval. Caps became 22/23/55, still 100 in total.

## Latency

**Successful attempt** is the runner-recorded wall time of the attempt that produced the answer; the frozen criteria use this figure (rules.json). **Total** adds the failed first attempt that preceded the resume, which is the wait a user would have experienced. Each failed attempt is one 300 s timeout plus its retrieval and the calls made before it.

| Seconds per question | B0 | B1 | M1 |
|---|---|---|---|
| Successful attempt: median | 51.5 | 69.7 | 71.9 |
| Successful attempt: p90 | 189.8 | 175.9 | 104.2 |
| Successful attempt: max | 197.9 | 186.5 | 230.4 |
| **Total (failed + successful attempt): median** | **53.3** | **171.3** | **156.2** |
| **Total: p90** | **351.4** | **381.1** | **423.1** |
| Total: max | 372.5 | 395.1 | 590.6 |

**Wall time for all 10 questions:**

| | B0 | B1 | M1 |
|---|---|---|---|
| Successful attempts | 735 s | 946 s | 883 s |
| Failed attempts | 619 s | 978 s | 1,449 s |
| **Total** | **1,354 s** | **1,924 s** | **2,332 s** |

**Per question:** successful attempt / failed attempt / total, in seconds. A dash means the question did not fail.

| Question | B0 | B1 | M1 |
|---|---|---|---|
| G01 | 55 / – / 55 | 66 / – / 66 | 75 / – / 75 |
| G02 | 39 / – / 39 | 49 / 330 / 380 | 59 / 300 / 359 |
| G03 | 24 / – / 24 | 176 / – / 176 | 83 / 508 / 591 |
| G04 | 58 / 315 / 373 | 74 / 307 / 381 | 82 / – / 82 |
| G05 | 190 / – / 190 | 87 / – / 87 | 230 / – / 230 |
| G06 | 51 / – / 51 | 187 / – / 187 | 104 / 319 / 423 |
| G07 | 52 / – / 52 | 65 / – / 65 | 60 / – / 60 |
| G08 | 47 / 304 / 351 | 55 / 340 / 395 | 63 / 322 / 385 |
| G09 | 198 / – / 198 | 167 / – / 167 | 58 / – / 58 |
| G10 | 22 / – / 22 | 22 / – / 22 | 68 / – / 68 |

- **Slow successful calls:** they were slow because single successful automated reviewer calls took 145–190 s, for example B0 G05 and G09. Even the smallest-prompt arm (B0) has a p90 above 120 s.
- **M1's failed attempts cost the most time:** 1,449 s across the 10 questions, because a Multi-Agent attempt makes several calls before the one that times out.

## Scores (P = 44)

| | B0 Original Baseline | B1 Improved Baseline | M1 Improved Multi-Agent |
|---|---|---|---|
| **End-to-end, after the one resume** | **23.5** | **33.0** | **28.0** |
| Fully answered questions | 1 (G02) | 2 (G02, G08) | 2 (G02, G06) |
| End-to-end, first pass only (timeouts score 0) | 16.0 | 20.5 | 13.0 |
| Quality on the 5 questions every arm completed on the first pass (G01, G05, G07, G09, G10; max 21) | 10.0 | 13.0 | 12.5 |
| Estimated request tokens per question | 18.7k | 51.6k (2.76 × B0) | 65.5k |

Every arm completed all 10 questions after the resume, so the "completed by all three" comparison covers all 10 questions and equals the end-to-end row.

**Per question (B0 / B1 / M1):**

| Question | Points | Question | Points |
|---|---|---|---|
| G01 | 3 / 2.5 / 2.5 | G06 | 2 / 3 / **4** |
| G02 | 4 / 4 / 4 | G07 | 3 / 3 / 2.5 |
| G03 | **0** / 4.5 / 2.5 | G08 | 4.5 / 5 / 4.5 |
| G04 | 3 / 3.5 / **0.5** | G09 | 2.5 / 3 / 3.5 |
| G05 | 0.5 / 3.5 / 4 | G10 | 1 / 1 / **0** |

## Where the points were lost

Each lost point gets exactly one cause. Execution failures cost no points after the resume; their cost shows only in the first-pass row and in latency.

| Points lost to | B0 | B1 | M1 |
|---|---|---|---|
| Retrieval: anchor not in the evidence | 13.0 | 8.0 | 4.0 |
| Retrieval: incomplete table pair (G07.2, G07.3) | 1.0 | 1.0 | 1.0 |
| Synthesis: anchor in the evidence but not stated | 6.5 | 2.0 | 1.5 |
| Synthesis: over-reaching draft claim correctly held by verification | – | – | 4.5 |
| Output contract: status disagreed with the claims, so the whole answer abstained (G10) | – | – | 2.0 |
| Verification: correct, fully quoted claim held (false rejection) | – | – | 3.0 |
| **Total lost** | **20.5** | **11.0** | **16.0** |

- **Retrieval:** the 6k skip-fit budget cut retrieval losses from 14 to 9 points (B0 to B1). M1's research rounds cut them to 5.
- **B0 synthesis:** B0 also published only limitations on G03 and G05, even though the key anchors were in its packet.
- **M1 false rejections (3 claims):** v2 still holds these, and the frozen check holds them too:
  - G03, SCR attack success: wrongly flagged for negation and subject mismatch.
  - G04, Pandora 64.3%/34.8%: the "respectively" pair was mapped wrongly.
  - G07, 61.33% and sub-4-second: the "4" in "sub-4-second" was not read as a number.
- **M1 over-reaching drafts (4 claims, held correctly):** each claim bundled correct figures with numbers its quotes did not contain (G03 Table 7, G04 ×2, G08). The verifier was right to hold them, but the correct parts were lost with them.
- **What v2 changed on M1:** v2 released one claim that the frozen check would have held (G03, attack-generation iterations 313.37/92.25 → 20.37). I checked it against the source and it is correct.

## Safety gates (final, after the blind re-score and the user's ruling)

| Gate | B0 | B1 | M1 |
|---|---|---|---|
| Quotes exact in the cited passage (programmatic) | 48/48 | 63/63 | 41/41 |
| Fabricated or factually incorrect published claims | 0 | 0 | 0 |
| Citation-grounding failures (correct but not covered by the attached quote; counted against the gate) | 0 | 1 (G03 F2) | 1 (G03 F1) |
| **Safety gate** | **Pass** | **Fail** | **Fail** |
| Fabrication on G09.3, G09.4, G10.4 | none | none | none |
| Unsupported recommendations in interpretations | 0 | 0 | 0 |
| v2-released claims correct | n/a | n/a | 1/1 |

Two items are flagged for the human reviewer:

1. **G05 interpretation (B1 and M1):** "consider a supervised pilot of non-diagnostic conversations" is close to a readiness claim. It does, however, state that diagnostic readiness is not established.
2. **Contradictory notes:** some leads and verification notes say a point is missing while a published limitation states it (B0 G08, B1 G01, M1 G01). None of these are factual claims, but they would confuse a reader.

## Frozen acceptance criteria on automated reviewer’s original scores (superseded; kept for transparency)

The final verdict uses automated reviewer’s blind scores and the safety ruling; see "Final verdict" at the top. On automated reviewer’s original scores:

**B1 vs B0: not qualified.**

| Criterion | Successful-attempt latency | Total latency |
|---|---|---|
| Points ≥ B0 + 3.5 | Pass (+9.5) | Pass |
| Fully answered ≥ B0 | Pass (2 vs 1) | Pass |
| Median ≤ 1.5 × B0 | Pass (1.35×) | **Fail** (3.2×) |
| p90 ≤ 120 s | **Fail** (175.9 s) | **Fail** (381.1 s) |
| Request tokens ≤ 3 × B0 | Pass (2.76×) | Pass |

B\* = B0.

**M1 vs B\* = B0, on automated reviewer’s original scores only:** it passed using successful-attempt latency and failed using total latency. This is superseded: under the blind scores it fails on points and on full answers, and it also fails the safety gate.

| Criterion | Successful-attempt latency | Total latency |
|---|---|---|
| Points ≥ B0 + 4.4 | Pass (28.0 vs a threshold of 27.9) | Pass |
| More fully answered than B0 | Pass (2 vs 1) | Pass |
| Median ≤ 120 s | Pass (71.9 s) | **Fail** (156.2 s) |
| p90 ≤ 300 s | Pass (104.2 s) | **Fail** (423.1 s) |
| ≤ 1 execution error after one resume | Pass (0) | Pass |

- **Which measure is official:** the frozen criteria (rules.json) specify the runner-recorded time, which is the successful attempt. On that basis M1 qualifies. The total-latency column is reported for the architecture decision; it does not change the frozen verdict.
- **Margin:** M1 clears the points threshold by 0.1. A single half-point change in the blind re-score reverses the result.

## Blind re-score (prepared, not yet run; 0 model calls)

- **`BLIND-PACKET.md`:** for each question, the three answers labelled A/B/C in a per-question random order.
  - It contains only scoreable published content: claims, cited limitations and labelled interpretations, each with its exact quotes. Every arm's answers are rendered in the same format.
  - Leads, verification notes, held or rejected drafts, packet sizes and timings are excluded, because they identify the engine and are not scored.
  - The required points and point-specific rules are included; anchor passages are in `REVIEW-PACKET.md`.
  - **Known tell:** M1's G10 answer is empty because it abstained, which an informed reader could recognise.
- **`blind-score-sheet.json`:** the form to fill in, with a score per point per label plus lists of misleading claims and unsupported recommendations.
- **`scoring/blind-key.json`:** the label mapping and the packet's sha256. **Do not give this file to the scorer.**
- **`scoring/compare_blind.py <filled sheet>`:** unblinds the sheet and lists every disagreement with automated reviewer’s scores, for the human to decide. It was self-tested by filling the sheet with automated reviewer’s own scores: it reproduced 23.5 / 33.0 / 28.0 with 0 disagreements.

## Blind re-score outcome (automated reviewer, 2026-11-24)

**Records:** both scoring records are kept unchanged: `scoring/scores.json` (automated reviewer) and `blind-score-sheet.json` (automated reviewer, blind). The unblinded comparison is `python -I scoring/compare_blind.py`; the totals are in `scoring/blind-results.json`.

**Scores out of 44:**

| | B0 | B1 | M1 | M1 − B0 (needs ≥ 4.4) | Fully answered (B0 / B1 / M1) |
|---|---|---|---|---|---|
| automated reviewer | 23.5 (53.4%) | 33.0 (75.0%) | 28.0 (63.6%) | 4.5 | 1 / 2 / 2 |
| **automated reviewer (blind)** | **24.0 (54.5%)** | **32.0 (72.7%)** | **26.5 (60.2%)** | **2.5** | **1 / 2 / 1** |
| Reconciled (automated reviewer’s view after review) | 23.0 (52.3%) | 32.0 (72.7%) | 27.0 (61.4%) | 4.0 | 1 / 2 / 1 |

**Disagreements: 11 point scores.**

| Disagreement | Accepted | Why |
|---|---|---|
| G01.2 (B1, M1) | automated reviewer | Function roles were stated |
| G06.1 (all arms) | automated reviewer | Median omitted |
| G06.2 (B1, M1) | automated reviewer | Cutoff and standard deviations omitted |
| G07.4 (M1) | automated reviewer | SME exclusion not stated in the claim text |
| G05.5 (B1) | automated reviewer | The improvement itself not stated |
| G03.1 (B0) | automated reviewer keeps 0 | The SCR mechanism appears only inside the quote; the limitation text just says the passages "describe SCR" |
| G09.2 (M1) | automated reviewer keeps 0.5 | It gives an accurate STARD Recall@10/MRR@10 result, just not the anchored Recall@14 figures |

**Safety review of the two G03 claims:**

| Claim | automated reviewer | What the source shows | Assessment |
|---|---|---|---|
| G03-C F1 (M1) | Flagged as unsupported | The statement about transfer across model sizes without regenerating examples is in a cited passage. c0027 says the framework improves defence "across different model sizes without the need for re-generation of adversarial examples". It is not in the attached quote. | Factually correct; a gap in the quote, not a misleading fact |
| G03-B F2 (B1) | Not flagged | The 3-shot and 4-shot figures (59.4/59.5 GB, 78.0/81.4 s) are correct to Table 7, but come from table rows `_2` and `_3`. Those rows were in B1's evidence but not cited; the claim cites only row `_1` (2-shot). | The same kind of defect |

**Verdicts:**

- **Safety:** with these two claims treated as citation gaps rather than misleading claims, every arm still passes every safety gate. If the human counts this defect as "unsupported", both B1 and M1 fail the safety gate.
- **B1:** not qualified. It fails the p90 latency requirement under every scoring view, despite leading completeness at 72.7–75.0%.
- **M1:** **not qualified under the blind scores**:
  - its lead over B0 is 2.5 points against the required 4.4;
  - it fully answers 1 question, no more than B0's 1.

  It is also not qualified under the reconciled view (4.0 points; 1 vs 1). Only automated reviewer’s original, non-blind scores gave a pass, by 0.1 point.
- **Final:** neither improved engine meets its frozen acceptance criteria; Baseline (B0) remains the default.
- **User ruling (2026-11-24):** both G03 gaps count as citation-grounding failures under the safety gate, so B1 and M1 both fail it. automated reviewer’s blind scores are the primary reported scores. The evaluation is closed.

**Needs human judgment (only the items that could change a verdict):**

1. **Citation gaps.** Should a claim that is correct but not fully covered by its quote count as "unsupported"? This affects G03-C F1 and G03-B F2. A "yes" fails the safety gate for both B1 and M1.
2. **The M1 margin points:** G03.1 (B0) and G09.2 (M1). M1 qualifies only if the human sides with automated reviewer’s original scores on nearly every point that touches the M1/B0 gap (G01.2, G03.1, G06.1, G06.2, G07.4, G09.2). Even then, the total-latency view fails it.

The B1-only disagreements do not affect any verdict: B1 fails on latency, and B\* is B0 regardless.
