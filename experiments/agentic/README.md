# Experimental agentic research mode

> Start with `HANDOFF.md`, which covers state, commands, tests, the A/B procedure and next actions. Audit history is in `AUDIT-RESPONSE.md`.

Status: isolated prototype, model-free tests only. The stable pipeline (`src/indexed_research.py`,
`POST /api/research`) is unchanged and remains the default. Every result is pending human review.

## Agents

| Agent | Decides / does | Model calls | Reuses |
|---|---|---|---|
| Orchestrator | Plans: question type, up to 3 searches, whether to delegate business insight and charts. Then decides on one targeted retry, skips optional work when the call budget is short, and assembles the answer. | 1 (plan) | — |
| Research agent | Runs B2 retrieval for each planned search, merges evidence round-robin (max 14 passages), drafts cited claims. | 1 | `src.research_chat.synthesize` (exact-quote and source-ID validation) |
| Verification agent | Deterministic re-checks per claim (quote membership, reported numbers), then its own independent prompt: verdict, issue types, coverage, and an optional request for one more search. A claim is kept only if both pass. | 1 | `attach_validated_citations`, `validate_reported_numbers` |
| Business insight agent | Runs only with a user-selected industry, or one the question names verbatim. Receives verified claims and only the passages they cite. | 1 | `src.business_translation.translate` (compact) |
| Chart tool | Model-free audit-verified tables for the retrieved table rows. | 0 | `table-endpoint/chart_preview.preview` |

Worst case: 6 calls (plan, research, verify, retry research, retry verify, business). The run is
refused before any call when fewer than 3 approved calls remain. The cumulative cap, 300 s timeout and
stop-after-provider-error rule of `capped_codex_ui.py` still apply underneath.

Messages: each delegation is a `task` (`task_id`, `to`, `kind`, payload) answered by one `reply`
(status, compact output with IDs, seconds, model calls, deterministic checks). Routing choices are
`decision` entries with a reason. The full list is returned as `trace`.

## Failure behaviour

- An invalid plan falls back to the baseline route (`plan.source = "fallback"`).
- An invented quote or unknown source ID rejects the draft: abstention, or the earlier verified answer after a failed retry.
- Malformed verifier output holds every claim (fail closed).
- A provider failure ends the run as `execution_error` with a coarse cause, and no unverified draft is returned.
- A business or chart failure leaves the verified research answer intact.

## Why no framework

The flow is a fixed set of agents, a single bounded retry and explicit budgets. Plain Python keeps every
call auditable, testable with in-process fakes, and inside the existing provider wrapper. LangGraph or
CrewAI would add dependencies and their own retry and tool semantics without a capability this needs yet.

## Run

```text
py -3.14 -I -B experiments/agentic/test_agentic.py
py -3.14 -I -B experiments/table-endpoint/live_backend.py ... --max-calls <approved> --agentic
POST http://127.0.0.1:<port>/api/agentic-research  {"query": "...", "industry": "optional"}
```

## Dashboard integration

- `ui-consult` Settings shows a "Research mode" selector (Baseline RAG / Multi-Agent) only when `/api/config` reports `agentic_mode`. Baseline is the default and posts to `/api/research`; Multi-Agent posts the same body to `/api/agentic-research`.
- `envelope.py` sends the verified answer through the shared `run_research` contract. The response is the same `indexed` envelope as a baseline answer, so saved briefs, citations, evidence inspection and reviews are unchanged. The trace lives in `result.provenance.agentic` and is covered by the review fingerprint.
- The brief shows a "How this answer was produced" section: each delegation, its reply, every routing decision with its reason, and a claim-by-claim table of the deterministic checks against the verifier's judgment.
- Without a loaded table audit, the chart tool reports "chart evidence is unavailable" and the text answer is unaffected.
- `--call-ledger <file.sqlite3>` with `--authorized-calls` (and optionally `--experiment`/`--experiment-cap`) enforces the cumulative authorization atomically across processes and restarts (`table-endpoint/call_ledger.py`).
- Numbers in claims are grounded in code (`numeric_checks.py`): contradicted claims are held; uncertain ones need the verifier and are flagged for a person. Business output is grounded field by field and shown as unverified recommendations.
- Agentic answers are saved to the brief library like baseline answers, including revisions (`library_revision`).

See `AB-EVALUATION-PLAN.md` for the controlled live comparison.

## Not done yet

- No live run, and no comparison with the baseline. Do not claim agentic mode is better until it is evaluated on the same independent questions (evidence coverage, correctness, citation support, abstention, latency and calls).
- Risk and compliance assessment and the clarification flow are baseline-only. Multi-Agent refuses `risk_assessment` and is hidden on clarification backends.
- Multi-Agent always runs the reported-number check; the baseline runs it only with the arXiv fallback. This is a known difference between the two arms of the comparison.
- Decomposition is planned by the model and is not yet scored against the V2/V3 syntactic splitter.
- The verifier is still a model. Its judgment is recorded separately from the deterministic checks, and neither replaces human review.
- A rejected draft returns no evidence list, so the reviewer sees the trace IDs only.
