# combined-v1 preliminary live validation: ready, NOT run

**Status:** everything is built, sealed and checked offline. **No live model calls have been made.** No shared-app changes, merges or deployment. This evaluation is **preliminary**: 10 questions, and the evidence budget was chosen offline on these same questions.

## 1. Fresh questions (fresh-business-v1, sealed in `seal.json`)

| ID | Type | Paper(s) | Question (abridged) |
|---|---|---|---|
| G01 | single-paper | AI Governance through Markets | Which market mechanisms govern AI risk, how they connect AI and financial risk, and the authors' limits |
| G02 | single-paper | EU/U.S./UK/China AI risk frameworks | How the four regimes differ and the trade-off of each |
| G03 | cross-paper | Safety Context Retrieval vs adversarial tuning | Approach, effectiveness, normal-task cost |
| G04 | cross-paper | Pandora (RAG poisoning) vs 10-shot benign fine-tuning | Customisation routes as attack surfaces, success, detectability |
| G05 | cross-paper | Polaris vs AI Hospital | How each evaluated conversational medical LLMs, and what that implies about readiness |
| G06 | numerical/table | White House voluntary commitments | Overall and company scores, weakest and strongest commitments |
| G07 | numerical/table | FinStat2SQL | Accuracy and speed vs proprietary and untuned models, limits (includes two table-row pairs) |
| G08 | numerical/table | Fail-closed alignment | Why alignment fails open, attack success, compliance, quality, compute, models tested |
| G09 | partially unanswerable | LegalMALR | Method, results, **English/EU performance** (not studied), **per-query cost** (not reported) |
| G10 | partially unanswerable | Emergent lying in LLM agents | Lying rates and effects, **deployed commercial agents' lying rate** (not studied) |

- **Answer key:** `answer-key.md` / `references.json`.
  - 44 required points: 43 anchored, 1 with no evidence (G09.4).
  - G09.3 and G10.4 require stating the cited limitation instead of inventing a result.
  - Every anchor ID was checked to exist, and its passage was checked to contain the key facts (`build_set.py`).
  - The 13 papers appear in no prior question, reference, label, case or fixture file (`OVERLAP.md`).
- **Scoring rules:** `rules.json`, frozen.
- **Key status:** AI-assisted. **automated reviewer review and human sign-off are still required.** Any key change must be resealed before running.

## 2. Offline evidence-budget comparison (0 model calls; `offline-coverage.json`)

Baseline route (table comparisons off). Anchored points are out of 43 (G09.4 has no anchor). Request tokens are the bounded estimate of the full synthesis request.

| Budget | Anchored points / 43 | Fully anchored questions | Mean passages | Max passage tokens | p90 request tokens | Split table pairs |
|---|---|---|---|---|---|---|
| Top-8 (current) | 23 | 1 | 8.0 | 2,489 | 11,696 | G07.2 |
| Top-16 | 27 | 1 | 16.0 | 4,995 | 21,407 | G07.2 |
| **6k skip-fit** | **29** | 1 | 22.7 | 5,991 | 28,522 | G07.2, G07.3 |
| 8k prefix (reference only) | 32 | 2 | 28.6 | 7,981 | 36,911 | G07.2, G07.3 |

- **Multi-Agent route (table comparisons on):** identical first packets on this set.
- **Window check:** for every question, the top-30 window's first 20 equal the public `retrieve(q, 20)`.

**Selection (rule in `SELECTION-RULE.md`, frozen before this run): 6k skip-fit.**

- It scores +2 over top-16, exactly the threshold.
- It is within the request caps.
- It splits no table pair that top-16 keeps whole.
- **Notes:**
  - The whole +2 comes from one question (G09.1 and G09.3).
  - Skip-fit includes one of the two G07.3 table rows. A partial table is a known skip-fit risk; scoring will show whether it misleads.
  - **Correction, recorded in the JSON:** my first computation wrongly treated that G07.3 partial row as disqualifying and selected top-16. The written rule only disqualifies splitting a pair that top-16 keeps whole, and top-16 contains neither G07.3 row. I fixed the code to match the text and recomputed from the saved packets.

## 3. Selected configuration (three arms; engines otherwise unchanged)

| Arm | Command variant | Evidence | Verification |
|---|---|---|---|
| **B0** Original Baseline | `codex_baseline.py --run fresh-top8` | top-8 | answer-quality review (as in production) |
| **B1** Improved Baseline | `codex_baseline.py --run fresh-skipfit6k` | 6k skip-fit, window 30 | same |
| **M1** Improved Multi-Agent | `codex_multiagent.py --run --fresh skipfit6k v2` | 6k skip-fit for the first-round original-question search; sub-searches top-8; merged ≤ 8,000 passage tokens / 40 passages | `numeric_checks_v2` + statistical rule + quote grounding + interpretation gate |

**Request guard** (`evidence-budget/request_guard.py`), on every call in every arm:

- It records **evidence tokens** (serialized passages) separately from **request tokens** (whole prompt + schema). The figures are saved per call in each `result.json` under `requests`.
- It refuses any request with evidence over 40,000 estimated tokens, or request + 8,000 output reserve over 64,000. The refusal happens **before** a call is reserved, so nothing is sent or counted.
- The estimator is ceil(UTF-8 bytes / 3), a conservative bound; no tokenizer package is available offline. The Codex CLI's own system prompt is outside this count.

**Safeguards unchanged:**

- exact-quote citation validation;
- number grounding of values, units, attribution, conditions, qualifiers and direction;
- statistical-report rule;
- verifier veto;
- interpretations never published as findings.

## 4. Call budget: hard cap 100, retries included

| Arm | Cap | Expected |
|---|---|---|
| B0 | 22 (2 per question + 2 spare) | 20 |
| B1 | 23 (was 22; one spare moved from M1 after the first pass, user-approved) | 20 |
| M1 | 55 (was 56) | about 33 (3.3 per question; range 30–50) |
| **Total** | **100** | **about 73** |

- **Enforcement:**
  - each arm has its own persistent ledger (`calls.sqlite3`);
  - every `--run` checks all combined-v1 ledgers and refuses if the arm's remaining allowance could push the total past 100.
- **Resume:** resuming a failed question is allowed within its arm's cap.
- **Stops:** login, quota, rate-limit, budget and memory errors stop the run. It refuses to start below 6 GB of free system commit (8.0 GB free now).

**Estimated usage (bounded estimate, which over-states):**

| Arm | Per question | Total | Wall time |
|---|---|---|---|
| B0 | about 25k tokens | about 0.25M | about 8 min |
| B1 | about 58k tokens | about 0.6M | about 10 min |
| M1 | about 80–150k tokens (planner, synthesis, verifier, possibly one targeted round) | about 1.0–1.5M | about 15–20 min |
| **Total** | | **about 2–2.4M estimated input tokens** | |

## 5. Acceptance criteria (frozen before execution; P = 44)

**Safety gates** (any failure rejects that arm as a candidate):

- 0 unsupported or misleading published claims;
- 100% of quotes exact in their cited passages;
- every claim that `numeric_checks_v2` accepts and the frozen check would have held is correct on attribution, conditions and qualifiers;
- 0 unsupported recommendations among labelled interpretations;
- no fabricated answer for G09.3, G09.4 or G10.4.

**Improved Baseline (B1 vs B0):**

1. Points ≥ B0 + 3.5 (8% of P).
2. Fully answered questions ≥ B0.
3. Median ≤ 1.5 × B0 and p90 ≤ 120 s.
4. Estimated request tokens per question ≤ 3 × B0. Offline the ratio measures 2.4×; this replaces the earlier ≤ 2× draft, which skip-fit would fail by construction. The change is declared here before any run.

**Improved Multi-Agent (M1) as an optional Deep Research mode:**

1. Points ≥ B\* + 4.4 (10% of P), where B\* is B1 if it qualified, else B0.
2. More fully answered questions than B\*.
3. Median ≤ 120 s and p90 ≤ 300 s.
4. At most 1 execution error after one resume.

Baseline remains the default regardless. **Reported in any case:**

- anchored-evidence coverage of the actual packets;
- draft omissions;
- false rejections;
- labelled-interpretation quality;
- calls, tokens and latency per arm.

**Separating retrieval from verification** (0 extra calls):

- **Retrieval effect (Baseline):** B1 − B0.
- **Verification effect:** replaying M1's saved verifier verdicts under the frozen number check and interpretation policy shows which claims the repairs released or held (`verification-repair/replay.py`).
- **Not measured:** with 100 calls there is no live frozen-Multi-Agent arm. Multi-Agent's retrieval-only effect on fresh questions is therefore not measured live; this is a stated limitation.

## 6. Execution commands (run by you, in order, from the VS Code terminal; close browsers first)

```
cd D:\KPMG-source-grounded\experiments\agentic-handoff
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I codex_baseline.py --run fresh-top8
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I codex_baseline.py --run fresh-skipfit6k
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I codex_multiagent.py --run --fresh skipfit6k v2
```

- Each command prints its readiness check and the combined-cap status before running.
- Outputs go to `data/processed/combined-v1-baseline-top8`, `combined-v1-baseline-skipfit6k` and `combined-v1-multiagent-skipfit6k-v2`.
- Rerunning the same command resumes without repeating finished questions.

## 7. Offline readiness evidence

- **`--check` passed for all three arms:** seal verified, ChatGPT login OK, model listed, 8.0 GB free, combined cap 0/100.
- **Tests:**

  | Suite | Tests |
  |---|---|
  | `test_combined` | 12 (incl. request guard, guard refusal spends no budget, combined cap across arms) |
  | Frozen agentic suites | 206 |
  | `test_numeric_v2` | 21 |
  | `test_interpretation_gate` | 9 |
  | Runner suites | 6 + 5 + 8 + 5 + 5 |

- **Real B2:** top-8 / top-16 / 6k skip-fit reproduced automated reviewer’s development numbers (22 / 31 / 34 of 41).
