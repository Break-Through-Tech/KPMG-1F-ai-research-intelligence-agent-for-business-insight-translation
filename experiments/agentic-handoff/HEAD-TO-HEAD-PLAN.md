# Baseline/B2 vs current Multi-Agent: head-to-head (pre-registered 2026-11-23, not run)

## Step 1 done (offline): statistical-report fix

**Defect.** `numeric_checks.py` attaches a negation within 40 characters *before* a number to that number. In the F09 claim "…was not significant, F(3,26)=0.341, p=.796", "not" was close enough to the test statistic. In the source, "no" was further away. So 3, 26 and 0.341 read as negated on one side only, and the check reported `negation_mismatch`. A test statistic is never itself negated; the negation applies to significance.

**Fix:** opt-in `experiments/agentic/statistical_reports.py`. `numeric_checks.py` stays frozen and byte-identical.

1. Numbers inside test reports (F(df)=…, t(df)=…, chi2, p=/</>) are exempt from number-level negation. Their values must still match.
2. A new **significance_mismatch** check fires when a claim and a cited source report the same test statistic with opposite significance. The frozen check missed this case.

**Tests and verification:**

- `test_statistical_reports.py`, 8 tests: the saved F09 claim passes; a null result restated as significant is caught; a significant result restated as null is caught; a changed statistic is still caught as absent; ordinary negated numbers, including a number in the same sentence as a test report, still hit `negation_mismatch`; disabling the fix restores frozen behaviour.
- The existing agentic, adversarial, audit, publication-gate, handoff, grounding and policy suites (198 tests) pass with the fix enabled.
- **Saved-run recheck, no model calls:** all 20 automated reviewer runs were replayed with and without the fix. Only F09 changes, in both arms: the null result is now published and coverage becomes `full`, so F09.1 is recovered. The other 18 runs are identical.

Corrected automated reviewer Multi-Agent (current arm) score: 8 questions complete, 2 partial (F04.2 draft omission, F08.1 retrieval-limited). Required points: 20 fully published and 2 half-published, out of 22. Unsupported findings: 0.

## Step 2: design

| | Baseline/B2 (deployed) | Baseline/B2 (tables) | Current Multi-Agent |
|---|---|---|---|
| Construction | `src.experimental.demo.create_research`, unchanged | same | `OrchestratorAgent` (research-only) + quote grounding + interpretation policy + statistical fix |
| Retrieval | B2, table comparisons **off**, one search, top-k 8 | B2, table comparisons **on**, one search, top-k 8 | B2, table comparisons on, original question + up to 3 planner searches, at most 14 passages; optional second round |
| Calls per question | 2 (synthesis + answer-quality review) | 2 | 3 (plan, synthesis, verification); 5 with a second round |
| Draft rejection | All-or-nothing on any bad quote (production behaviour) | same | Per-claim grounding, then verifier + number checks |
| Interpretations | Published if drafted | same | Withheld by policy |
| Model | `gpt-6.1-sol`, low, 300 s timeout, ChatGPT login | same | same (already run: `automated reviewer-paired-v1-full`, current arm) |

- **Fairness.** Same questions, frozen references, model, index and scoring rules. "Tables" isolates architecture from the table-comparison retrieval setting. "Deployed" is what the app runs today.
- **Re-use instead of re-running Multi-Agent.** The Multi-Agent arm reuses the saved current-arm runs, and F09 is re-scored offline with the fix on the saved draft. Those runs are real `gpt-6.1-sol` outputs from 2026-11-23. Re-running Multi-Agent would add about 35 calls for little information. The difference in run date is a documented limitation.
- **Differences to report:** evidence actually delivered to the writer (packet IDs vs anchors), calls, tokens, latency.

**Measures**, per question, with the frozen `rules.json` definitions:

- required-point correctness (source review), and complete / partial / abstention
- unsupported published claims
- misleading interpretations
- retrieval-limited vs draft-omission vs safeguard-rejection points
- calls, input/output tokens, wall time (median, p90)
- execution errors kept separate

Automated screens (anchor cited, numbers present) are reported separately from source review.

**Decision rule (declared before running).** Prefer current Multi-Agent as the default only if both hold against Baseline (deployed):

- it publishes **more required points** in total;
- it publishes **no more** unsupported or misleading claims.

Prefer Baseline if it ties or wins on points with no more unsupported claims, because it costs fewer calls and less latency. Anything else is inconclusive and goes to the held-out set.

## Step 3: budget and readiness

**Runs:**

| Variant | Calls expected | Cap | Output |
|---|---|---|---|
| deployed | 20 | 30 | `automated reviewer-baseline-v1-deployed` |
| tables | 20 | 30 | `automated reviewer-baseline-v1-tables` |

Expected total: 40 calls, about 0.7–0.9M input tokens, and about 10–20 minutes. Keep the computer awake.

**Readiness, all offline:**

- `--check deployed` and `--check tables` both pass: ChatGPT login, `gpt-6.1-sol` listed, CLI isolation flags present, seal and comparator verified.
- `test_codex_baseline.py` passes 4 tests: ten questions at two calls each with evidence recorded, resume of only the failed question, stop on a quota error, and directories separate from the Multi-Agent and Gemini runs.
- The full offline suite passes.

**Commands, once approved:**

    cd D:\KPMG-source-grounded\experiments\agentic-handoff
    D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I codex_baseline.py --run deployed
    D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I codex_baseline.py --run tables

## Held-out evaluation (proposed, for the final decision)

F01–F10 have been used throughout development, so they are not independent. Proposal:

- **Questions:** 10 new ones from corpus papers *not* used in F01–F10, mirroring the categories: 3 table, 2 multi-paper, 2 methodology, 3 limitations.
- **References:** written and sealed (hash recorded) before any generation. A person signs off on the expected points, and nobody tunes code after seeing outputs.
- **Arms:** Baseline (deployed) and current Multi-Agent only.
- **Budget:** about 20 + 35 calls, cap 90.
- **Decision rule:** the rule above, applied once.
