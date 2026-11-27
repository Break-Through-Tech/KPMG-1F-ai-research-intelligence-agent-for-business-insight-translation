# fresh-v3 final validation: results

**Status (2026-11-25):**

- **Done:** runs, verification, mechanics and the programmatic audit.
- **Pending:** independent blind scoring (fresh Codex session), the Claude audit pass, and human adjudication.
- **Qualification:** not yet decided. The point and safety criteria depend on the blind scores.

No research-provider calls, engine changes or new experiments were made while preparing this.

## 1. Integrity

| Check | Result |
|---|---|
| fresh-v3 seal (questions, key, rules, all four arms' code; 45 files) | verified |
| v1 code seal (frozen S1 engine) | verified |
| Persistent ledgers | B0 15, S1 16, S2 16, D2 24; **71 of 90** combined (expected 72). Every arm is within its cap (20/20/20/30) |
| Failed calls | 1 (B0 J05, 300 s timeout; resumed successfully) |
| Execution records | `status.json`, per-question `result.json`/`attempts.json` and ledgers agree. Wall times match the operator's figures (S2 806.3 s, D2 929.8 s) |

**B0 final status:** 7/8 complete, with 1 execution error.

- **J06** failed both times, the first run and the permitted resume. Both synthesis calls returned successfully, from an identical prompt. Both replies (status `insufficient_evidence`) failed the Baseline summary contract, so no answer was accepted.
- **Scoring:** J06 is an empty answer for B0 and scores 0 on its 4 points. This is not a safety failure.
- **Effect on the comparison:** it lowers B0's ceiling to 34/38, which makes S2's "≥ B0 + 10 pp" easier.

## 2. Mechanics

Latency is the total per question, including failed attempts; p90 is the nearest rank (with n = 8, the maximum). Tokens are taken from the receipts.

| Arm | Complete | First pass | Median s | p90 s | Input tokens | Output tokens |
|---|---|---|---|---|---|---|
| B0 | 7/8 | 6/8 | 68.9 | 365.8 | 256,666 | 16,740 |
| S1 | 8/8 | 8/8 | 107.0 | 119.7 | 505,844 | 36,315 |
| S2 | 8/8 | 8/8 | 94.8 | 145.8 | 335,683 | 34,236 |
| D2 | 8/8 | 8/8 | 108.3 | 152.4 | 453,573 | 35,462 |

**Notes:**

- **S2 tokens:** 0.664 × S1, a 33.6% reduction.
- **Per question, actual:** S2 about 42k and D2 about 57k, both below the pre-run estimates (50–58k and 75–85k).
- **Identical prompts:** D2's synthesis prompt is byte-identical to S2's on J01 and J02. Those are the cases where the Deep planner's searches added no new evidence.

## 3. Programmatic safety pass (`fresh3-audit.json`)

| Arm | Published items | Quotes | Inexact quotes | Number-recall flags |
|---|---|---|---|---|
| B0 | 42 | 104 | 0 | 3 |
| S1 | 128 | 196 | 0 | 0 |
| S2 | 120 | 187 | 0 | 0 |
| D2 | 119 | 176 | 0 | 0 |

**B0's three flags** go to adjudication. All three look benign: a dataset name "NIST (2020)", a "1" in a limitation, and "two uses" in an interpretation.

**Limit of this pass:** it checks quote exactness and number recall only, so it cannot see semantic citation-grounding failures. Those are left to the blind scorer and the Claude audit.

## 4. Frozen criteria: status

| Criterion | S2 | D2 |
|---|---|---|
| Execution | **pass** (8/8, 8/8 first pass) | **pass** (0 errors) |
| Latency | **pass** (median 94.8 ≤ 120; p90 145.8 ≤ 180) | **pass** (median 108.3 ≤ 189.6; p90 152.4 ≤ 300) |
| Tokens | **pass** (0.664 ≤ 0.80) | n/a |
| Exact quotes | **pass** (programmatic) | **pass** |
| Numerical correctness | pending (programmatic recall clean) | pending |
| Citation grounding / misleading | pending (blind + Claude audit + adjudication) | pending |
| Completeness ≥ 80%, full ≥ 4/8, ≥ B0 + 10 pp, ≥ S1 | pending (blind scores) | pending (≥ 80%; ≥ S2 + 10 pp; full ≥ S2) |

**So far:** every mechanical criterion passes for both arms. Qualification now depends only on scoring and safety.

## 5. Remaining steps

1. **Blind scoring.** The scorer folder `D:\KPMG-blind-v3\` is outside the repo, so the scorer cannot reach the key, the engines, the results or the label map. It contains:
   - `SCORER-BRIEF.md`;
   - `BLIND-PACKET-v3.md` (sha256 `fd82e138…b689`, matching `fresh3-blind-key.json`);
   - `blind-sheet-v3.json`;
   - `ADJUDICATION-RULES.md`, a verbatim copy of the frozen `fresh-v3/AMBIGUITIES.md`.

   Open a fresh Codex session **in that folder** and give it: "Read SCORER-BRIEF.md and follow it." Keep `fresh3-blind-key.json` away from it.
2. **Claude audit** (frozen pass 3): **done**, before any Codex scores existed. See `CLAUDE-AUDIT-v3.md` (sha256 `cc1bd6ab…887c`, 2026-11-25 13:24).
   - **S2 and D2:** 0 citation-grounding failures, 0 misleading claims, 0 numerical errors.
   - **S1:** 1 plausible minor citation-grounding failure.
   - **B0:** 2 citation-grounding failures and 1 plausible misleading claim.
3. **Human adjudication** of every item flagged by any pass, recorded in `fresh3-adjudication.json` (per arm: `citation_grounding_failures`, `misleading_or_fabricated`, `quote_errors`, `numerical_errors`).
4. **Criteria evaluation:** `python -X utf8 fresh3_scoring.py criteria D:\KPMG-blind-v3\blind-sheet-v3.scored.json` writes `fresh3-results.json` with the S2 and D2 verdicts.
