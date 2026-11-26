# Consolidated live validation: Standard vs Deep (8 fresh questions, 36 points)

**Status: preliminary, and the scoring is AI-assisted.**

- **Scoring:** automated reviewer scored the answers without being blind to which arm produced them. Under `rules.json` a blind independent re-score is required (`BLIND-PACKET.md` and `blind-score-sheet.json`). Disagreements are adjudicated by the human using `AMBIGUITIES.md`.
- **Frozen setup:** the key was human-approved; engines, key and rules stayed frozen; the 50-call cap was kept.
- **Scope:** this comparison does **not** test qualification against the Original Baseline, which remains the production default.
- **Records:** `scoring/scores.json` (per point, with causes), `scoring/mechanics.json`, `scoring/results.json`, `scoring/answers/Hxx.md`.

## Execution

| | Standard | Deep |
|---|---|---|
| Model calls (cap) | 16 (20) | 24 (30) |
| Failed calls / timeouts / resumes | 0 / 0 / 0 | 0 / 0 / 0 |
| First-pass success | 8/8 | 8/8 |
| Planner fallbacks / failed supplementary searches | n/a | 0 / 0 |
| Median / p90 total latency (no failed attempts occurred) | 119.0 / 139.7 s | 140.0 / 143.2 s |
| Estimated request tokens (guard) | 0.51M | 0.62M |
| Actual provider input / output tokens (receipts) | 0.62M / 39k | 0.80M / 44k |

- **Combined calls:** 40 of 50.
- **Token estimate:** actual input exceeded the guard estimate by 21–30%. The estimate excludes the Codex CLI's own system prompt, so it is not an upper bound on provider usage.

## Scores

| | Standard | Deep |
|---|---|---|
| **Completeness (points / 36)** | **26.5 (73.6%)** | **27.5 (76.4%)** |
| Fully answered questions | 0 | 1 (H01) |
| Published items; exact quotes | 129; 100% | 135; 100% |
| Numbers present in their own attached quotes | 100% | 100% |
| Misleading / fabricated claims | 0 | 0 |
| Citation-grounding failures (AI-assisted reading) | 0 | 0 |
| Interpretations published (mean rubric score, 0–2) | 5 (2.0) | 6 (2.0) |
| Fabrication on H06.4 (time/cost) and H08.4 (Yoruba) | none | none |

**Per question (Standard / Deep):**

| Question | Points | Question | Points |
|---|---|---|---|
| H01 | 4.5 / 5 | H05 | 3.5 / 3.5 |
| H02 | 3 / 3.5 | H06 | 3.5 / 2.5 |
| H03 | 2.5 / 2.5 | H07 | 3 / 3 |
| H04 | 4 / 4 | H08 | 2.5 / 3.5 |

## Where points were lost

| Points lost to | Standard | Deep |
|---|---|---|
| Retrieval (anchor not in the evidence) | 5.5 | 4.0 |
| Synthesis (point in the evidence but not stated, or only partly) | 3.0 | 4.5 |
| Review judged a correct claim "not relevant" | 1.0 | – |

- **Deep's net +1.0:**
  - **Supplementary evidence: +1.5.** H03.2 (all six HarmNet figures, +0.5) and H08.3 (CLINIC's conclusion, +1), both anchored only in planner-retrieved passages.
  - **Run-to-run variation: −0.5 net.** H01.1 +0.5, H02.4 +0.5, H03.4 −0.5, H06.2 −0.5, H06.3 −0.5, with the anchors available to both arms.
  - With 8 questions, the difference is within the observed variation.
- **Safeguards working as designed:**
  - Standard's review withheld a drafted claim that conflated JMedEthicBench's 50,000+ benchmark conversations with its 2,345-sample evaluation, the exact error the reviewed key flags.
  - Atomic claims kept every model figure separately attributed.
  - The incomplete-table notes appeared where tables were partial.
- **Residual costs observed:**
  - In both arms, a correct "GPT-5 sustained 8.0–9.0" claim was withheld by an unresolved number-checker subject flag (its GPT-5-mini twin published). It was not a required point.
  - Standard's review rejected three correct RAG-variant figures as "not relevant" (−0.5 on H02.4).
  - Questions with large tables produced up to 13 incomplete-table notes.

## Frozen decision rule (Deep as the optional deep mode)

| Criterion | Result |
|---|---|
| Points ≥ Standard + 3.6 | **Fail** (+1.0) |
| More fully answered questions | Pass (1 vs 0) |
| Both arms pass the safety gate | Pass (AI-assisted; the blind re-score must confirm) |
| Median total latency ≤ 2× Standard | Pass (1.18×) |
| p90 ≤ 300 s | Pass (143 s) |
| ≤ 1 execution error after the resume | Pass (0) |

**Verdict: Deep is not preferred. Standard alone is retained** as the consolidated research mode.

- **What this measures:** planning and the larger evidence budget together, not planning alone (`fresh-v2/rules.json`).
- **What it does not change:** the production default, which remains the Original Baseline.

## Limitations

- **Small sample:** 8 questions and an AI-drafted key (reviewed once by ChatGPT, approved by the human).
- **Correlated questions:** three papers each serve two questions.
- **Scoring:** not yet blind.
- **One run per arm:** run-to-run variation alone moved scores by ±0.5 on five points.
