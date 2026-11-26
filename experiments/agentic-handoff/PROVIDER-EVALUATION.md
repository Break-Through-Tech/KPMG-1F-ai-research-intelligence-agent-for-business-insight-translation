# automated reviewer-backed paired evaluation (separate from all Gemini runs)

Runner: `codex_paired.py`. Generation uses the existing `src/codex_generation.py` adapter:

- **Auth:** the saved ChatGPT login only. The adapter refuses API-key auth and never reads auth files.
- **Isolation:** each call runs in an empty temporary directory with `--sandbox read-only`, web search off, approvals off, user config ignored, and shell, exec, apps, plugins, multi-agent, browser and computer use disabled. Tool-using replies are refused.
- **Structured output:** `--output-schema`, then local validation against the same schema. The agents validate again against their full schemas.

## Pipeline

Unchanged from the Gemini runs:

- frozen questions
- B2 route
- one shared plan per question, with matched initial evidence (`gemini_paired.replay_pair`)
- both arms (current and handoff)
- quote grounding and the interpretation policy in both arms, with scope review off
- exact-quote checks, number checks, the verifier and the publication gate

## Configuration

- Model: `gpt-6.1-sol`, effort `low`, 300 s timeout.
- CLI: the binary pinned by the seal (0.167).
- `gpt-6.1-sol` is listed in the CLI model cache, refreshed 2026-11-23.

## Labels

| Label | Questions | Call cap | Output directory |
|---|---|---|---|
| `pilot` | F01, F03 | 18 | `data/processed/automated reviewer-paired-v1-pilot` |
| `full` | F01–F10 | 90 | `data/processed/automated reviewer-paired-v1-full` |

## Operation

- **One command per label.** Re-running the same command resumes.
- **Persistent call budget.** `calls.sqlite3` reserves a row before every call and records its status, diagnostic, time and token usage.
- **No repeated work.** A question that finished is never rerun. An unfinished attempt folder is kept as `F0x.attempt-N`.
- **Failures.** A failure on one question is recorded in `status.json` and the run continues. Budget exhaustion, login or authentication errors, quota or rate limits, a missing model, forbidden tool output, and evidence-integrity failures stop the run.
- **Report.** `report.json` (the scenario report) is written at the end.

## Comparability

automated reviewer results are a new baseline. Never compare them in one table with Gemini results: the model changes both the drafts and the verifier's verdicts.

Within a automated reviewer run, current-vs-handoff comparisons remain valid. The pre-registered criteria in `STAGE-B-PLAN.md` apply. F01 and F03 are scored again under automated reviewer rather than borrowed from Gemini.

## Offline status (2026-11-23)

- `test_codex_paired.py`: 8 tests pass, using a scripted adapter with the real `replay_pair`, orchestrators, grounding and policy. They cover:
  - completion
  - no repeated work on rerun
  - continuing past a failure, then resuming only that question while keeping the failed attempt
  - stopping on quota, rate-limit and authentication errors
  - a persistent cap across restarts
  - per-call receipts
  - isolation flags
  - directories separate from Gemini's
- Full offline suite: OK.
- `--check pilot`: seal, comparator, CLI flags, ChatGPT login and model listing all pass.
- No live automated reviewer call has been made.
