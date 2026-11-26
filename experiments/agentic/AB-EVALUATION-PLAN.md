# Baseline RAG vs Multi-Agent: controlled live comparison (plan, not yet run)

No live model call has been made for this comparison. Nothing below is a result.

**Tooling (2026-11-19):**
- `ab_questions.json` pins the questions, the corpus and the required points.
- `ab_run.py` is the guarded live runner: preflight, then a run refused without explicit approval.
- `ab_eval.py` is the offline harness: replay, report and merge-review.
- `test_ab_dryrun.py` is the end-to-end dry run with a fake provider.

`HANDOFF.md` section E has the exact command sequence and stop conditions; it supersedes the procedure below where they differ.

## Fixed conditions (identical in both modes)

| Item | Value |
|---|---|
| Corpus | `D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100`, parents.jsonl SHA-256 `78d8efd7…72ff41aa` (the same bundle as the verified table audit) |
| Retrieval | B2 `document-table-balanced-facets-v1`, top_k 8, local MiniLM encoder and ms-marco cross-encoder |
| Provider | `capped_codex_ui` (automated reviewer `gpt-6.1-sol`, effort low, 300 s timeout, no retries, stop after a provider error), evidence compaction on |
| Table audit | `D:/KPMG-demo-corpus/table-endpoint-exp/table-audit-demo-100.json` |
| Request | No industry, no risk assessment. Baseline is sent with `interpret_context: false` so it does not spend a call guessing an industry. |
| Order | Baseline first, then Multi-Agent, per question. One run each (single runs, not repeated measurements). |

## Questions (retrieval checked with 0 model calls on 2026-11-18)

| # | Type | Question | What baseline retrieval returns (top 8) |
|---|---|---|---|
| Q1 | Straightforward | Do large language models show financial bias when making investment decisions, and how much can it be reduced? | 7 passages from *Are LLMs Rational Investors?* (2402.12713), plus 1 off-topic |
| Q2 | Multi-part comparison, two sources | Compare how Agent-SafetyBench and TravelPlanner evaluate LLM agents, and what safety or success rates does each report? | 6 Agent-SafetyBench passages and **no TravelPlanner passage**, although TravelPlanner (2402.01622) is in the index |
| Q3 | Hard: numbers and tables | By how much did the CU-DPO training method improve strategy-selection accuracy, and on how many base models? | 2602.00931: 2 text passages and 6 table rows from 2 tables |
| Q4 (optional) | Should abstain | What did recent studies find about using LLMs to forecast quarterly retail electricity demand in Southeast Asia? | General finance and time-series papers; nothing on the asked-for topic |

Q2 tests whether planned subquestions recover the missing source. Q3 tests numeric verification and table charts. Q4 tests refusal.

## Measures (scored by a person against the cited passages, blind to mode where practical)

| Measure | How it is scored |
|---|---|
| Evidence coverage | Distinct papers and question parts represented in the final evidence (Q2: is TravelPlanner present?) |
| Answer correctness | Each accepted claim marked correct / partly correct / wrong against its passages |
| Citation support | Share of accepted claims whose cited quote fully supports the claim |
| Refusal / abstention | Abstains when it should (Q4); does not abstain when the evidence answers (Q1–Q3) |
| Held claims (Multi-Agent only) | Claims withheld by the verifier: correctly or wrongly withheld |
| Latency | `timings_seconds.total` (baseline) and `provenance.agentic.seconds` |
| Model calls | Ledger lines added per question, plus `model_calls.by_agent` |

Do not claim Multi-Agent is better unless it wins on these measures for these questions, and say the sample is three or four single runs.

## Call budget

| Mode, no industry | Typical | Maximum |
|---|---|---|
| Baseline (`interpret_context: false`): synthesis + quality review | 2 | 2 |
| Multi-Agent: plan + research + verify, + one targeted retry (research + verify) | 3 | 5 |
| Per question, both modes | 5 | 7 |

| Plan | Maximum calls |
|---|---|
| Q2 + Q3 | 14 |
| Q1 + Q2 + Q3 | 21 |
| Q1–Q4 | 28 |

### Remaining authorization (reconciled 2026-11-18, provisional)

- Authorization: 40 automated reviewer calls for laptop development and demo work.
- Ledger: the one canonical `D:/KPMG-demo-corpus/table-endpoint-exp/automated reviewer-authorization-40.ledger.sqlite3`, created from the 20 calls in `automated reviewer-authorization-40.ledger.jsonl` (see `AUDIT-RESPONSE.md`). **20 remain.** No other ledger file is accepted, and the seed cannot be initialized again.
- The initial run is **two questions (Q2, Q3), research-only, at most 14 calls**. The profile refuses `industry`, `interpret_context` and `risk_assessment`, so Business Translation cannot run; send baseline requests with `interpret_context: false`.
- After the run, a person may close the allocation (`call_ledger.py close-experiment --ledger <canonical> --authorized 40 --experiment ab-agentic-1`). The calls the A/B did not use (at least 6) then stay available for a separately approved purpose.
- Start the live backend with `--profile ab-agentic-1 --call-ledger D:/KPMG-demo-corpus/table-endpoint-exp/automated reviewer-authorization-40.ledger.sqlite3 --authorized-calls 40 --experiment ab-agentic-1 --experiment-cap 14 --max-calls 14 --agentic`. First run the same command with `--budget-check-only` (read-only; loads nothing). The first profile launch locks the ledger to `ab-agentic-1`; after that, omitting or renaming the experiment is refused. The 14-call cap is recorded once and can never be raised. The JSONL file is only the seed and is not accepted as a ledger.
- Do not run live until automated reviewer clears the reliability blockers.

## Procedure

1. Restart the live backend with the flags above (`--check-only` first, which makes no model call).
2. Note the ledger line count.
3. For each question: POST `/api/research` (baseline), then POST `/api/agentic-research`, with the same body. Save both envelopes and note the ledger count after each.
4. Stop at the first provider error. The backend refuses further calls by design.
5. Score the saved envelopes with the measures above. Report raw counts per question.
