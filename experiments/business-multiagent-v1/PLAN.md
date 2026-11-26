# Current Multi-Agent on the business set (business-multiagent-v1): pre-registered plan, not run

**Purpose:** decide whether current Multi-Agent qualifies as an *optional Deep Research mode* beside the Baseline/B2 default. Baseline remains the default whatever the result.

## Frozen inputs (unchanged)

- **Questions and key:** `experiments/completion-eval-v1` C01–C15, 41 required points, the same anchors and `rules.json` scoring definitions (1 / 0.5 / 0, published vs inferred, added-claim audit definitions). The seal is verified before the run.
- **Baseline comparator:** the saved `automated reviewer-completion-v1-baseline` run, **reused, not regenerated** (27.0 / 41; 3 complete / 11 partial / 1 abstained; 0 unsupported; 29 calls; median 48 s, p90 58 s).
- **Model:** `gpt-6.1-sol`, low effort, 300 s timeout, ChatGPT login.
- **Index:** pinned B2 index `78d8efd7…`.

## Arm: current Multi-Agent (no handoff, no tuning)

- **Engine:** `OrchestratorAgent`, research-only, top-k 8, at most 5 calls per question: planner, synthesis, verification, and at most one targeted round with up to 3 planner sub-searches and 14 merged passages.
- **Route:** `preflight.open_route`, with table comparisons on, as in every earlier Multi-Agent run. This is a documented retrieval difference from Baseline (tables off). On F01–F10, table comparisons changed no evidence for Baseline.
- **Safeguards (all enabled):** quote grounding, the interpretation policy (accepted interpretations held), and the statistical-report correction.
- **Runner:** `experiments/agentic-handoff/codex_multiagent.py`. Output: `data/processed/automated reviewer-business-v1-multiagent`.

## Decision rule (fixed before execution)

Multi-Agent qualifies as an optional Deep Research mode only if **all** of these hold:

1. **Coverage:** at least **+5.0 required points** over Baseline, so at least **32.0 / 41**, by the same source review.
2. **Completeness:** **more fully answered questions** than Baseline (more than 3 of 15).
3. **Safety:** **no more unsupported or misleading published claims** than Baseline (Baseline: 0, so Multi-Agent must have 0).
4. **Latency:** median wall time per question **≤ 120 s** and p90 **≤ 300 s**.
5. **Reliability:** at most **1** question left with an execution error after one resume. Remaining errors score 0 points for Multi-Agent.

Otherwise, Multi-Agent is not offered, and Baseline/B2 remains the only engine.

**Reported regardless:**

- retrieval coverage of anchors, against Baseline's packets
- draft omissions and false rejections (claims held by checks or the verifier although source-supported)
- withheld interpretations
- citation exactness
- the quality of labelled business interpretations
- calls, tokens and latency
- **the C07 cross-paper comparison specifically**

## Budget

| | Value |
|---|---|
| Calls | about 3.2 per question (automated reviewer F01–F10 current arm: 32 calls for 10 questions), so **about 48 calls**. **Hard cap: 75** (5 per question), persistent in `calls.sqlite3` |
| Tokens | about 18k input per call, so **about 0.9–1.2M input** and about 15–25k output |
| Time | earlier median **about 44 s** per question, worst case 271 s, so **about 15–25 minutes** in total |
| Safeguards | resume without repetition; stops on login, quota, rate-limit, budget or memory errors; refuses below 6 GB free commit |

## Readiness (offline)

- `test_codex_multiagent.py` passes 5 tests:
  - 15 questions at 3 calls each with the cap at 75;
  - quote grounding recovers an elided quote, and the policy holds an interpretation;
  - the statistical fix is enabled;
  - resume does not repeat work;
  - a quota error stops the run;
  - MemoryError stops it, then resume continues and keeps the attempt.
- The full offline suite passes.
- `--check`: seal verified, login and model OK, Baseline results present. **Free commit is 5.3 GB (below 6), so close browsers before running.**
- `src`, `agents.py`, `numeric_checks.py` and `handoff.py` are unchanged.

## Limitations

- Single run, single model, 15 questions.
- The key is AI-assisted.
- The Multi-Agent route enables table comparisons (a pre-existing architecture difference).
- The comparison reuses a Baseline run from the same day rather than interleaving runs.
