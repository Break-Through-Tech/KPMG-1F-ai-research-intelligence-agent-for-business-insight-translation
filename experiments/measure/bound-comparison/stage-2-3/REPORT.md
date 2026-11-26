# Stage 2 shadow check and Stage 3 offline trial

**The isolated trial passed. Keep live answers on the current path.** Structured records worked when the proposed values, scope and exact links could be checked against trusted source records. This study supplied those proposals as fixtures. The existing generator still needs to demonstrate that it can produce those records reliably.

## Stage 2 — Shadow

The observer reads the sealed answer and its delivered evidence. It returns the original answer and separate observations. Archived prose keeps the Stage 1 linking path. A proposed structured record carries explicit roles, values, units, metric, conditions and exact chunk spans or cell IDs. The checker validates these against the trusted finding and rejects or refers incomplete, contradictory or ambiguous proposals.

| Cohort | Outcome |
| --- | --- |
| 11 archived Baseline answers | All 11 preserved exactly. Two archived numeric claims linked via the existing Stage 1 path. Eight went to review. No trial previews were shown. |
| 8 authored structured controls across four papers | All four valid records linked. All four wrong-metric records were rejected. All underlying answers were preserved. |

The gate reopened for the fixture trial when both checks passed. The archived answers have no structured records. Their 2/10 linkage rate remains the observed coverage for that archived prose.

## Stage 3 — Opt-in offline trial

The trial enables a separate preview generated from the validated source fields. It is marked pending human review and leaves the sealed research answer intact. Three comparisons came from two other versioned papers. The test suite checked exact source cell and header IDs against hash-matched archived HTML.

| Cohort | Outcome |
| --- | --- |
| 3 valid comparisons | 3 canonical previews with exact source-cell links. |
| 12 invalid or incomplete records | 6 rejected and 6 sent to review. No preview was produced for any of these. |
| All 15 cases | All ordinary answers preserved. |

The table trial covered reported metric ranges across three selected models, negative mean differences, and separately labeled lower and upper bounds. It did not infer an interval confidence level. Mutations included wrong metric, population, role order, unit and sign, decimal drift, an unknown cell, a mismatched claim, missing evidence, a wrong index and altered evidence text or table metadata. [Agent-SafetyBench v2 Table 6](https://arxiv.org/html/2412.14470v2#S4.T6) · [Assessing the Performance of Human-Capable LLMs v1 source table](https://arxiv.org/html/2410.16285v1#A1.tab1)

The real Multi-Agent orchestrator and shared answer builder also ran with scripted planner, research and verification replies. A structured record attached in the experiment produced the separate preview. The shared answer validator and review fingerprint still passed. No provider was called, and no running demo changed.

## Remaining evidence before a live trial

- The new producer path is untested on generated records. The structured fixtures establish what the verifier does with those records. They provide no rate for how often a real agent can create good records or find trustworthy source bindings on new questions.
- A record hash checks which claim the sidecar accompanies. It does not establish that all of the original wording is supported. The preview uses canonical source fields and remains separate from the original answer. Whole-answer approval still requires the existing workflow.
- The 8 shadow controls and 15 trial fixtures are engineering examples and are flagged `reviewed=false`.
- The existing Multi-Agent integration suite had 31 passing tests and three environment errors involving disposable SQLite ledgers on Windows. All seven new tests passed, including the scripted Multi-Agent envelope test. No real authorization ledger was accessed.

## Reproduce

Use Python 3.11+ for the standalone replay. The application-envelope test uses the project's existing dependencies and was run with Python 3.14.

```powershell
python -I -B experiments/measure/bound-comparison/stage-2-3/run_trial.py
python -I -B experiments/measure/bound-comparison/stage-2-3/run_trial.py --output replay-new.json
py -3.14 -I -B experiments/measure/bound-comparison/stage-2-3/test_trial.py
```

[Raw shadow and trial records](results.json) contain the source index, pinned hashes, structured inputs, decisions and accepted previews. Writes were limited to this experiment directory. The pinned Q2/Q3 specification remains unchanged.
