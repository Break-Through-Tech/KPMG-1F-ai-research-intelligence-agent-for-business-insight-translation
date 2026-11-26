# KPMG research engine: engineering handoff (2026-11-23)

## Production default: Baseline/B2, unchanged

`src.experimental.demo.create_research`, exactly as the app runs it today:

- B2 retrieval, table comparisons **off**, top-k 8.
- One synthesis call with exact-quote citation validation.
- The answer-quality review (`quality_check=True`).
- 2 model calls per question.

| Evidence | Score | Unsupported findings | Abstentions | Median time per question |
|---|---|---|---|---|
| Held-out (H01–H10) | 22.0 of 27 | 0 | 0 | about 33 s |
| Development (F01–F10) | 20.0 of 22 | 0 | 0 | — |

Nothing in this workspace changes Baseline or B2 source. `src` is byte-identical to the automated reviewer worktree.

## Decided against (keep the code, do not integrate)

| Option | Reason |
|---|---|
| Handoff Multi-Agent | No benefit over current Multi-Agent. Development stopped |
| Current Multi-Agent as default | +1 development point, entirely from extra searches; about 1.6× calls and a 271 s worst case |
| Current Multi-Agent as optional Deep Research mode | business-multiagent-v1: 20.5 / 41 vs Baseline 27.0 (needed ≥ 32), 3 full answers (needed > 3). Better retrieval (29 vs 22 anchored points) but 15 source-supported claims held by the deterministic number check. Not tuned (pre-registered). See `experiments/business-multiagent-v1/RESULTS.md` |
| Question decomposition for Baseline | 0 point gain on held-out; +17% tokens, +10 s median |
| Table comparisons for Baseline | Changed no evidence on F01–F10 |
| Scope review (interpretation scope fields) | Gemini mislabelled scope; superseded by the interpretation policy |

## Experimental, opt-in only (none wired into the app)

All under `D:\KPMG-source-grounded\experiments\`:

- **`baseline-completion/completion.py`: abandoned** under the frozen rule (completion-eval-v1, 2026-11-24). It is safe (0 unsupported claims, nothing removed) but recovered 0 of 41 points. It fired only on two false-positive gaps, whose facts were already in the review's published limitations, and missed all 4 genuine draft omissions. Keep it for reference only.
- `agentic/quote_grounding.py`, `agentic/interpretation_policy.py` and `agentic/statistical_reports.py`: Multi-Agent safeguards. They were useful for Gemini and are only relevant if Multi-Agent is revived.
- `baseline-decomposition/`: deterministic question decomposition. Not integrated.
- `verification-repair/` (2026-11-24, offline, development data): diagnosis of Multi-Agent's 21 held business claims. Results: 11 wrong rejections from ten number-check parsing defects; 6 defensible holds; 4 grounded recommendations withheld by design. Proposed fix: `numeric_checks_v2` (veto kept), plus a labelled-interpretation gate. Replay released 10 claims, newly held 0, and released nothing on earlier runs; the F01 misattribution stays held. Not integrated. Needs fresh-question validation. See `FINDINGS.md`.

## Operating notes

- **Live evaluation tooling.** Run `agentic-handoff/codex_baseline.py` and `codex_paired.py` with the venv `D:\KPMG-venvs\stage-a-py314`. They use the ChatGPT automated reviewer login, never API keys. They have persistent call caps, resume runs, and refuse to start below 6 GB of free system commit.
- **Machine.** Automated browser sessions held 15–19 GB of commit and caused the only memory failure. Close them before live runs.
- **Codex CLI.** About 8% of Multi-Agent calls timed out at 300 s, all on the CLI side. Resume recovered every one.

## Final research result (completion-eval-v1: 15 consultant-framed questions, 41 points)

| Measure | Baseline/B2 |
|---|---|
| Required points | 27.0 / 41 |
| Unsupported or misleading published claims | 0 |
| Quotes exact in their cited passages | 158 / 158 |
| Abstentions | 1, evidence-limited |
| Median time per question | 48 s, 2 calls |

Inferred business implications are labelled as interpretations. Remaining losses are mostly retrieval-limited, with a few draft omissions. Full write-up: `experiments/completion-eval-v1/RESULTS.md`.

## Before shipping

1. Independent human check of the answer keys (held-out, completion-eval) and of a sample of published answers.
2. Research experimentation is closed. Next is app integration and stakeholder-demo readiness on the unchanged Baseline/B2 default.
3. No app, merge or deployment changes have been made from this workspace. Integration is a separate, approved step.
