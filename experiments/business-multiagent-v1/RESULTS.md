# Current Multi-Agent on the business set (business-multiagent-v1): results

**Decision: NOT QUALIFIED.** Multi-Agent is not offered as an optional Deep Research mode. Baseline/B2 remains the only engine.

**Scoring status:** AI-assisted, not independently verified by a human. The frozen completion-eval-v1 key, anchors and `rules.json` were used unchanged. Baseline numbers are from the saved `automated reviewer-completion-v1-baseline` run, which was not regenerated.

## Decision rule (pre-registered in PLAN.md)

| Criterion | Required | Multi-Agent | Met |
|---|---|---|---|
| Coverage | ≥ 32.0 / 41 (Baseline 27.0 + 5) | **20.5 / 41** (−6.5) | No |
| Completeness | > 3 fully answered | **3** (C01, C09, C13) | No |
| Safety | 0 unsupported or misleading published claims | **0** found | Yes |
| Latency | median ≤ 120 s, p90 ≤ 300 s | median **67.7 s**, p90 **107.9 s** (max 326.7 s) | Yes |
| Reliability | ≤ 1 execution error after one resume | **1** (C02, CLI timeout; not resumed) | Yes |

A C02 resume cannot change the outcome: even 4/4 on C02 would give 24.5 / 41.

## Per question (required points)

| Q | Max | Baseline | Multi-Agent | What happened in Multi-Agent |
|---|---|---|---|---|
| C01 | 3 | 3 | 3 | Full. Interpretation held by policy |
| C02 | 4 | 2.5 | 0 | Execution error (Codex CLI timeout after 2 calls). All anchors were in the packet |
| C03 | 3 | 2 | 1.5 | One supported claim held by the number check (subject_mismatch) |
| C04 | 2 | 2 | 1.5 | Verifier held a supported claim |
| C05 | 3 | 2.5 | 1 | **All 3 numeric claims held** → insufficient_evidence; credit only from limitations |
| C06 | 3 | 2 | 0 | **All 3 numeric claims held** → insufficient_evidence |
| C07 | 3 | 0.5 | **1.5** | Retrieval now found KG²RAG (c0021). Both mechanisms published; both gain figures held |
| C08 | 3 | 1.5 | 2 | Extra retrieval gained a point |
| C09 | 2 | 1.5 | 2 | Full |
| C10 | 2 | 1.5 | 1.5 | — |
| C11 | 3 | 1 | 0.5 | 3 claims held by the number check, 1 by the verifier |
| C12 | 2 | 1.5 | 1.5 | — |
| C13 | 2 | 2 | 2 | Full |
| C14 | 4 | 2 | 1 | Latency and F1 claims held |
| C15 | 2 | 1.5 | 1.5 | Interpretation held by verifier |
| **Total** | **41** | **27.0** | **20.5** | Better on C07, C08, C09 (+2.5); worse on C02–C06, C11, C14 (−9.0) |

## Diagnosis: better retrieval, lost at verification

- **Retrieval coverage:** required points with an anchor in the synthesis evidence were **29 / 41** for Multi-Agent and **22 / 41** for Baseline. The planner's sub-searches retrieved more of the right evidence (C02, C07, C10 among others).
- **False rejections dominate the losses.** 21 drafted claims were held:
  - **15 by the deterministic number check** (`numbers_and_qualifiers`) on C03, C05, C06, C07, C09, C11 and C14. Every one of these quotes is exact in its cited passage. In 12 of the 15, every number in the claim appears in its quote; the hold came from heuristic subject, metric, condition or denominator mismatches. These are **false rejections**. The other 3 (`numbers_absent`) cite a model version ("3.5") or a report year not present in the quote. Those holds are defensible.
  - **5 by the verifier** (C04, C08, C11, C15).
  - **1 by the interpretation policy** (C01), as designed.
- **Draft omissions** were not the limiting factor. Where points were lost, the claim was usually drafted and then held.
- **Net effect:** Multi-Agent finds more of the evidence than Baseline, then withholds much of it. The number check was tuned on F01–F10 short claims. It over-fires on the multi-figure comparative claims that these consultant questions require. The plan forbade tuning, so this was not changed.

## C07 (cross-paper comparison, KG²RAG vs MultiRAG)

- **Baseline:** 0.5. It abstained because no KG²RAG passage was retrieved.
- **Multi-Agent:** 1.5. A sub-search retrieved c0021, so both mechanisms were published with exact citations. This is the clearest case where Multi-Agent's retrieval helps.
- **Lost:** both headline gains ("≥ 8% over baselines in fullwiki" for KG²RAG and "> 10% over SOTA on sparse data" for MultiRAG) were held by the number check (metric/subject mismatch and missing_condition), although both were source-supported.
- **Lesson:** Multi-Agent's retrieval does solve the comparison problem, but the current verification layer throws away the quantitative half of the answer.

## Safety and citations

- Published quotes (claims and limitation support): **105 / 105 exact** (whitespace-normalised substring of the cited `parents.jsonl` passage).
- Unsupported or misleading published claims: **0** found (AI-assisted audit).
- Business interpretations: most were held (C01 by policy; C04, C11, C15 by the verifier). Answers therefore read more like terse findings than Baseline's labelled, bounded recommendations. For a consulting audience this is a **regression in business usefulness**, not just in points.

## Cost

| | Baseline | Multi-Agent |
|---|---|---|
| Calls | 29 | 46 (45 ok, 1 timeout); 3.1 per question |
| Tokens | — | 808,583 input / 24,780 output |
| Median / p90 per question | 48 s / 58 s | 67.7 s / 107.9 s (max 326.7 s) |

## Limitations

- Single run, single model (gpt-6.1-sol, low effort), 15 questions.
- The key and the scoring are AI-assisted.
- Multi-Agent ran with table comparisons on (pre-existing architecture difference).
- Half-point scores involve judgement; no plausible re-scoring closes a 11.5-point gap to the threshold.

## What would change the picture (not done; would need a new pre-registered evaluation)

Relaxing the deterministic number check to "all claimed numbers appear in an exact quote" would, on this run, have released 12 supported claims. That is a tuning change made after seeing results, so it is recorded only as a hypothesis.
