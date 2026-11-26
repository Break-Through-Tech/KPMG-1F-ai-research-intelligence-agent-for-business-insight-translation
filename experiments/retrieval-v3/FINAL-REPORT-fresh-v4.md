# Final engine evaluation (fresh-v4) and demonstration recommendation

**Date:** 2026-11-25.

**Inputs:**
- Frozen S3 and frozen S2.
- 10 fresh November-2026 papers, with 10 questions and 50 points.
- An independently reviewed key, signed off by the project lead.
- 41 of the 50 allowed calls.
- Blind scores from a fresh Codex session (scorer "GPT-6"). The packet and sheet hashes are unchanged.
- The programmatic audit.
- Claude's verification of every flagged item. A full independent Claude audit pass was **not** run, to conserve usage. The programmatic audit found 0 issues in both arms.

## Result: S3 does not qualify

| Criterion (frozen) | S3 | Result |
|---|---|---|
| Completeness ≥ 80% | 74.0% (37/50) | fail |
| S3 ≥ S2 + 2 points | 37 vs 37 | fail |
| Safety | 1 citation-grounding failure (proposed) | fail |
| Execution 10/10, ≥ 9 first pass | 10/10, 9 first pass | pass |
| Median ≤ 120 s / p90 ≤ 180 s | 158.0 s / 5,238 s (the K08 provider stall) | fail |
| Input tokens ≤ 1.15 × S2 | 1.157× | fail |

## Head to head (same questions, blind)

| | S3 | S2 |
|---|---|---|
| Points / 50 | 37.0 (74%) | 37.0 (74%) |
| Fully answered (reported only) | 3 | 1 |
| Safety flags (proposed adjudication) | 1 grounding | 0 |
| Median / p90 latency | 158 s / 5,238 s | 93 s / 141 s |
| First pass | 9/10 | 10/10 |
| Input tokens | 489,561 | 423,024 |

**Where the points went:**
- **S3 better:** K04, K08 and K09.
- **S2 better:** K03, K05, K06 and K10.
- **Tied:** K01, K02 and K07.
- **Both weak:** the two cross-paper questions, K05 (S3 1.5, S2 2.0) and K07 (1.5 each). This matches the offline retrieval finding.

## Safety flags (proposed; the project lead's adjudication is final)

- **S3 K03 F2.** It says "natural-language analysis policy", but its own quotes say only "mutable analysis policy". This is a qualifier the quotes do not state, so it is a **citation-grounding failure** under the strict rule. The statement itself is correct per the paper.
- **S2 K05 L0.** "Transfer to bank customer conversations is untested in the supplied evidence." This is scoped to the supplied evidence and describes the benchmark scope accurately. Proposed: **not misleading**, consistent with the fresh-v3 rulings on scoped evidence-limit statements.
- **S2 K09 L0.** "They do not establish accuracy for the client's customer-support assistant." This is a correct evidence limit backed by the quoted scope, not a claim about what the paper contains. Proposed: **not misleading**.

## Recommendation for the supervised KPMG demonstration: S2 (consolidated-v2 Standard)

**Why S2:**
- **Completeness:** equal to S3 on fresh material.
- **Safety:** 0 safety failures here and on fresh-v3.
- **Speed and cost:** about 40% faster (93 s median), 14% fewer tokens.
- **Reliability:** 10/10 first-pass execution here and 8/8 on fresh-v3.
- **Simplicity:** S3's extra searches and component checklist added cost and latency without a net score gain.

**Limitations to disclose:**

| Limitation | Evidence |
|---|---|
| Measured completeness is about 66–74% of required points | fresh-v3 65.8%, fresh-v4 74.0%. It is below the 80% target, and answers often omit some requested details |
| Cross-paper questions are weak | about 30–40% of their points |
| Questions are answered from the retrieved evidence only | "Not established" statements describe that evidence, not whole papers |
| Scoring is AI-assisted | blind Codex scorer plus AI checks; no human expert scoring |
| Latency is measured on the Codex subscription provider only | the production-provider smoke test (6 calls, cap 10) is still outstanding |

**Operating mode:** supervised, with a human reviewing each answer before use. This was always the plan (`approved: false` by default).

## Status

- **Engine development:** stopped, per the decision rule.
- **Next:** production testing and integration of S2, starting with the provider smoke test once the production provider is named.
- **Nothing** has been committed, merged or deployed.
- **Saved artifacts:**
  - `fresh4-results.json`
  - `fresh4-adjudication.json` (proposed)
  - `fresh4-audit.json`
  - `D:\KPMG-blind-v4\blind-sheet-v4.scored.json`
