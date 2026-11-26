# Proposed live validation: Consolidated Standard vs Deep (NOT run)

**Status:** prepared offline. **No live model calls have been made.** Running this requires approval of this proposal, plus independent review and human sign-off of the fresh-v2 answer key.

**What it does not show:** this comparison does not establish qualification against the Original Baseline. The Original Baseline remains the production default unless separate promotion requirements are met.

## Design

- **Questions:** 8 fresh consultant-oriented questions (`fresh-v2/questions.json`), 36 required points, source-anchored key (`fresh-v2/references.json`, `answer-key.md`).
  - Papers: the 8 corpus papers used in no earlier set (`fresh-v2/OVERLAP.md`).
  - Types:

    | Type | Questions |
    |---|---|
    | Single-paper | H01, H02 |
    | Cross-paper | H03, H04, H07 |
    | Numerical/table | H02, H05 |
    | Partially unanswerable | H06, H08 |

- **Arms:** both arms run the same sealed code. One run per question per arm, with one resume of a failed question.

  | Arm | Pipeline | Calls per question |
  |---|---|---|
  | Standard (S) | protected 6k packet, then synthesis, review and publication | 2 |
  | Deep (D) | planner, then protected packet plus at most 3 planned searches (8k / 38k estimated tokens), then the *same* synthesis, review and publication | 3 |

- **Model:** gpt-6.1-sol, low effort, 300 s timeout, ChatGPT automated reviewer login. Never API keys.

## What the comparison measures: planning and the larger budget together

**Standard versus Deep measures the combined benefit of planning and Deep's larger evidence budget, not planning alone.**

- **Two things change together:** Deep gets up to 3 planned searches *and* an 8k-token budget (38k estimated request tokens), against Standard's 6k.
- **Why they can't be separated:** no arm uses the larger budget without a plan, or a plan within 6k. Separating them would need a third arm, which is out of scope under the 50-call cap. This is recorded in `fresh-v2/rules.json` (`what_the_comparison_measures`).

**What is held equal:**

- **Same protected packet:** both arms start from it. The Deep packet is the Standard packet plus appended passages, and a code assertion fails if any protected passage is displaced.
- **Same downstream functions:** synthesis, review and publication are identical.

**Descriptive aids** (they do not separate planning from budget):

- **Per-point attribution:** whether a point that Deep gained over Standard was anchored only in a supplementary passage (`evidence_management.supplementary_ids`).
- **Noise estimate:** questions where the planner proposed no extra search, or fell back, give the two arms identical evidence. Their score differences estimate run-to-run model variance.
- **Inconclusive results:** with 8 questions, a difference within that variance is reported as inconclusive.
- **Paired reporting:** scores, latency and usage per question for both arms side by side.

## Measures (`fresh-v2/rules.json`)

| Measure | How it is measured |
|---|---|
| Completeness | Required points scored 1 / 0.5 / 0; fully answered questions |
| Citation entailment | Exact-quote membership (programmatic), plus blind judgment that the attached quotes entail each published item |
| Numerical correctness | Each published number checked for value, unit, subject, metric and condition |
| Business interpretation quality | Each labelled interpretation scored 0–2 |
| Safety gate | 0 misleading claims, 0 citation-grounding failures, 0 unsupported recommendations, no fabrication on H06.4 or H08.4 |
| First-pass success, execution errors, planner fallbacks, contract repairs | From each question's `attempts.json`, `result.json` and `status.json` |
| Latency | Total including failed attempts and the resume; successful-attempt time reported separately; median and p90 |
| Usage | Calls (ledger); estimated request tokens (guard); actual provider tokens (receipts), reported separately |

**Decision rule** (frozen in rules.json before any run): Deep becomes the optional deep mode only if all of these hold:

- it scores at least Standard + 3.6 points;
- it fully answers at least as many questions;
- both arms pass the safety gate;
- its median total latency is no more than 2× Standard's, and its p90 is no more than 300 s;
- it has at most 1 execution error after the resume.

Otherwise Standard alone is kept.

## Call budget and expected usage

| Arm | Cap (retries included) | Expected calls |
|---|---|---|
| Standard | 20 | 16 |
| Deep | 30 | 24 |
| **Total** | **50 (hard, persistent ledgers, checked before each arm starts)** | **40** |

**Estimated input tokens** (guard estimate, ceil(UTF-8 bytes / 3), which over-states; `offline-check.json`):

| Arm | Per question | Total |
|---|---|---|
| Standard | synthesis 28–39k + review about 32–45k ≈ 60–85k | about 0.6M |
| Deep | planner about 1k + synthesis up to about 44k + review up to about 50k ≈ 80–95k | about 0.7M |
| **Total** | | **about 1.3–1.4M** |

Actual provider usage is recorded from the receipts. Expected wall time is about 15–25 minutes per arm if no timeouts occur.

## Commands (run by you, in order, from the VS Code terminal; close browsers first)

Run from `D:\KPMG-source-grounded\experiments\consolidated`:

```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_consolidated.py --check standard
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_consolidated.py --run standard
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_consolidated.py --run deep
```

- **Outputs:** `data/processed/consolidated-v1-standard/` and `.../consolidated-v1-deep/`. Each question folder holds `stages/` (checkpoints with raw replies), `attempts.json`, `calls.json` (estimated vs actual usage) and `result.json`.
- **Resuming:** rerunning a command resumes the run. Each question gets at most two attempts.
- **Seal:** `fresh-v2/seal.json` pins the question set and every engine file. Any change after sealing makes `--check` and `--run` refuse.

## Before running

1. Independent review of the 36-point key (`fresh-v2/answer-key.md`), then human sign-off. Any key change means rebuilding with `python -I fresh-v2/build_set.py` and resealing.
2. Approve this proposal and the 50-call cap.
