# Developer handoff: KPMG Multi-Agent Research Intelligence (2026-11-19)

This file is self-contained. It describes what exists, how to run and test it, how the controlled A/B
evaluation will be run, and what is still open. **Nothing here has been committed.** No live model call was made
while building or testing anything described below.

Status in one line: the system is built and model-free tested, including an end-to-end dry run against the real
backend with a fake provider. **The live A/B is NOT approved.** Independent verdict: **NEEDS CHANGES**. See the verification checkpoint below.

---

## Independent verification checkpoint

**NEEDS CHANGES.** Verified branch and HEAD match section B. The index contained no staged changes. Before the documentation rename, Git listed 14 modified tracked files and 30 untracked files. The rename and reference updates are documentation-only.

- **Blocking numeric gap:** the reported range 35–46% to 68–78% is retained. Reversing it to 68–78% to 35–46%, reshuffling the endpoints, or collapsing it to 35% to 78% also produces a grounded result and is retained with a permissive verifier. The probe uses the pinned CU-DPO abstract's exact result sentence. Extend the existing comparison check to treat each range as one interval with ordered endpoints and compare pre/post role and metric. Add valid and invalid tests on the pinned source before requesting live approval.
- **Experiment identity gate:** runner preflight and post-response validation accept a missing index fingerprint. Both were reproduced with fixture responses. Require the pinned index hash in configuration and for successful research responses. Preserve typed error handling and clean abstentions with provenance. Add a fixture that refuses before the first POST if configuration lacks the fingerprint.
- **Other numeric limitations:** the two stated Audit #5 cases passed end to end. A valid age-condition paraphrase (participants under age 18 vs. minors under age 18) was still held. The cross-subject contrast with an unnamed baseline was flagged uncertain, and one ambiguous trailing condition was classified as grounded. Keep these visible as general grounding limitations.
- **Verified model-free:** agentic 33/33, integration 34/34, adversarial 44/44, audits #2–#5 16/16, 9/9, 9/9 and 2/2 with 32 subtests. Ledger 16/16, A/B profile 19/19, harness 11/11, and real-index fake-provider dry run 4/4. Fixture-backed chart-first 13/13 and evidence tables 21/21. Baseline non-HTTP 125 passed with 214 subtests. Proxy 10/10 with the existing external fixture supplied in memory (9/10 without it). Baseline HTTP rerun: 26 passed and one WinError 10053 subtest failure. The untouched baseline export reproduced the same socket error (25 passed, two failure entries). The prior 37/37 browser count is historical; browser was not rerun. On this host, disposable ledger hard-link and loopback tests needed normal Windows permissions.
- **Ledger:** read-only profile preflight passed. Integrity ok; 40 authorized, 20 used (19 completed, one failed), 20 left, zero unresolved reservations, no lock or allocations. File digest stayed the same. Do not start the live backend against the authorization ledger until approved.
- **Demo:** use explicit mock mode for the agent trace and recorded replay for real CU-DPO evidence. Approve or revise only on an isolated brief database. The demo-100 audit digest matched the pinned index. Chart availability depends on an audited eligible source table.
- **Reuse direction:** keep B2 and current agents. After the initial comparison, prioritize frozen retrieval-input replay (GPT Researcher and AutoGenBench), question-part evidence tracking (STORM), separate claim-support and numeric scoring (DeepResearch Bench), relevance-aware retry gating (AutoGen), and token-aware lossless evidence packing. Implement the patterns independently in the experimental layer. Avoid framework dependencies, external search and extra provider calls for these proposals.

---

## A. Project overview

**What it does.** A local research assistant over a fixed corpus of arXiv papers. A user asks a research question;
the system retrieves passages, writes an answer whose every claim is tied to exact quotes from cited passages, can
show audit-verified tables as charts, and saves the answer as a brief that a person reviews and approves. Optional
business translation turns findings into conditional implications for an industry.

**Two research modes behind the same dashboard (`ui-consult`):**

| | Baseline RAG (default, stable) | Multi-Agent (experimental, opt-in) |
|---|---|---|
| Endpoint | `POST /api/research` (shared pipeline `src/indexed_research.py`) | `POST /api/agentic-research` (`experiments/agentic/route.py`) |
| Flow | Fixed: retrieve (B2) → synthesize (1 call) → quality review (1 call) → optional business → optional risk | An orchestrator plans and delegates. See below. |
| Checks | Exact quote and citation-ID validation; model quality review | Same quote validation, plus code checks on numbers, settings and conditions, plus an independent verifier agent |
| Calls per research-only question | at most 2 | at most 5 (6 with business) |

**Multi-Agent roles (`experiments/agentic/agents.py`):**
- **OrchestratorAgent:** one planning call returns a structured plan (subquestions, whether to delegate business and charts). It routes and decides one optional targeted retry. It picks the best round by verified coverage. It assembles the result under step and call limits (`MAX_CALLS=6`, `MIN_CALLS=3`, `MAX_STEPS=10`).
- **ResearchAgent:** runs B2 retrieval for the question and each subquestion (no model), merges up to 14 passages, then calls the shared `synthesize` (1 call). On a retry it keeps citations of *verified* claims, reserves 4 slots for new passages, and skips the call when nothing new reaches the context.
- **VerificationAgent:** code checks (quote membership, plus `numeric_checks.ground_claim`) and its own prompt (1 call): supported, partially supported, unsupported or contradicted, with issue types. A claim is kept only if both pass. Coverage is recomputed from the kept claims.
- **BusinessInsightAgent:** the shared `translate` on verified claims only (1 call), then `screen_business`: unsupported numbers, settings, premises and advice are withheld. The rest is shown as **unverified** proposals, assumptions and caveats.
- **Chart tool:** model-free `chart_preview` (audit-verified complete tables only), bound to the answer's index.

**Numeric grounding (`numeric_checks.py`):**
- Each number in a claim is matched to **one** source mention. Value, sign, unit (with conversions), subject, metric, population group, negation, setting (benchmark vs deployment) and conditions must hold for that mention.
- Scope: a number's own clause, plus clearly shared context.
  - A number-free lead-in applies to every number in the sentence.
  - A trailing clause applies only when the sentence has a single number; with several numbers its scope is ambiguous, which gives *uncertain*.
  - An elliptical clause inherits the earlier subject only.
- Result states:
  - **contradicted:** held.
  - **uncertain:** kept only if the verifier supports it, and flagged for a person.
  - **grounded** or **no_numbers:** passes this check.

**Review.** Every result is `human_review.status = pending`, `approved = false`. Briefs are versioned snapshots (`src/brief_store.py`); a review binds to a snapshot fingerprint. The agentic trace is stored in `result.provenance.agentic`, so it is part of the reviewed snapshot.

---

## B. Exact repository state

| Item | Value |
|---|---|
| Worktree | `C:\Users\ngkho\.automated reviewer\worktrees\research-evidence-integration\KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation` |
| Branch | `khoi/research-evidence-integration` (also on origin at the same commit) |
| HEAD | `9994eed920d0afd9ee5f36769077a05137763d6e` ("docs: record evidence integration design and QA reproduction") |
| Committed | Everything up to HEAD: consultant UI (`ui-consult/`), table endpoint and audit tooling (`experiments/table-endpoint/`) |
| Uncommitted | Everything below. **Preserve it.** Do not reset or stash without the owner's approval. |
| Unchanged | `src/`, `tests/`, `ui/`, provider defaults, the shared backend, other worktrees |

**Modified, tracked (14 files):**
- `experiments/table-endpoint/capped_codex_ui.py`: SQLite ledger, experiment cap
- `experiments/table-endpoint/live_backend.py`: `--agentic`, `--profile`, `--budget-check-only`, research-only gate, shared research lock
- `experiments/table-endpoint/recorded_backend.py`: chart-first routes
- `ui-consult/`: `app.js` (mode selector, trace panel, labels), `chart-svg.js`, `consult.css`, `evidence.js`, `index.html`, `mock-api.js`, `serve.py` (proxies `/api/agentic-research`), `tests/evidence.test.js`, `tests/test_serve.py`, and the two design docs

**Untracked (new):**
- `experiments/agentic/`:
  - Agents and contracts: `agents.py`, `contracts.py`, `envelope.py`, `route.py`, `numeric_checks.py`
  - A/B tooling: `ab_questions.json`, `ab_eval.py`, `ab_run.py`, `fake_provider.py` (test only)
  - Tests: `test_agentic.py`, `test_integration.py`, `test_adversarial.py`, `test_audit2.py` … `test_audit5.py`, `test_ab_harness.py`, `test_ab_dryrun.py`
  - Docs: `README.md`, `AUDIT-RESPONSE.md`, `AB-EVALUATION-PLAN.md`, this file
- `experiments/table-endpoint/`:
  - Ledger and profile: `call_ledger.py`, `ab_profile.py`
  - Chart-first and progress: `chart_preview.py`, `evidence_compaction.py`, `progress.py`
  - Tests: `test_call_ledger.py`, `test_ab_profile.py`, `test_chart_first.py`

**Runtime (this laptop):**
- **Python 3.14.2** (`py -3.14`): jsonschema 4.26, numpy 2.4, sentence-transformers 6.1. Runs the agentic code, ledger, backend and harness.
- **Python 3.11.9** (`python`): runs `ui-consult/serve.py` and its tests.
- **User site-packages:** the backend and the dry run need them for the retrieval models, so they run with `py -3.14 -B`, **without `-I`**.
- **No commit noise:** use `-B` everywhere so no `__pycache__` lands in the worktree.

**Data, models and fixtures (outside the repo):**

| What | Path |
|---|---|
| Baseline source export (served `src/`) | `D:/KPMG-demo-corpus/main-727b0b3` |
| Pinned 100-paper bundle | `D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100` (parents.jsonl SHA-256 `78d8efd7c9df075be09ffa5f3a9c7ca79c54efa2d7caf75c8f0329ea72ff41aa`) |
| Table audit | `D:/KPMG-demo-corpus/table-endpoint-exp/table-audit-demo-100.json` (423 verified, 13 refused) |
| Encoder | `%USERPROFILE%/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |
| Reranker | `C:/Users/ngkho/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/data/processed/model-cache/models--cross-encoder--ms-marco-MiniLM-L6-v2/snapshots/233902d25c440f23af6f7d6e94d2946bac0bee0a` |
| Authorization ledger (**real; read only**) | `D:/KPMG-demo-corpus/table-endpoint-exp/automated reviewer-authorization-40.ledger.sqlite3` (+ seed `automated reviewer-authorization-40.ledger.jsonl`, notes `automated reviewer-authorization-40.README.md`) |
| Recorded browser fixtures (for `test_serve`, browser suite) | `C:/Users/ngkho/KPMG-ui-redesign/ui-consult/tests/fixtures/*.json` (4 files) |
| Codex CLI binary used by the provider wrapper | `C:\Users\ngkho\AppData\Local\OpenAI\automated reviewer\bin\f71a721e0e6193a9\automated reviewer.exe` (model `gpt-6.1-sol`, effort low, 300 s timeout; `capped_codex_ui.py`) |

---

## C. System integration

**Live backend** (`experiments/table-endpoint/live_backend.py`):
- **What it is:** the shared B2 research backend, plus an isolated table endpoint, chart-first routes, progress reporting, and the opt-in agentic route.
- **Key flags:**

  | Flag | Purpose |
  |---|---|
  | `--export --bundle --encoder --reranker --library --table-audit --port` | Data, models, brief library and port |
  | `--max-calls N` | Per-process cap; default 0, so generation is refused |
  | `--agentic` | Serves `/api/agentic-research` |
  | `--call-ledger --authorized-calls` | The SQLite cumulative authorization |
  | `--experiment --experiment-cap` | The experiment allocation inside it |
  | `--profile ab-agentic-1` | Approved A/B profile: canonical ledger, exact flags, research-only |
  | `--budget-check-only` | Read-only validation; loads nothing and exits |
  | `--check-only` | Index and model identity check; no generation |

- **Routes:**
  - `GET /api/config`: `live`, `context_id`, `index`, `call_budget`, `agentic_mode`
  - `POST /api/research`: baseline
  - `POST /api/agentic-research`: multi-agent
  - `POST /api/chart-preview`, `GET /api/evidence-table`, `GET /api/progress`
  - `/api/briefs`, `/api/briefs/<id>`, `/api/briefs/<id>/reviews`
- **Request handling:**
  - Only one research request runs at a time across both modes (409 otherwise).
  - The agentic route validates `library_revision` before any call, exactly like the baseline, and saves every answer as a brief, or as the next version when revising.
  - Under the profile, `industry`, `interpret_context: true` and `risk_assessment` are refused (400 `research_only`) before any call.

**UI and proxy:**
- `ui-consult/serve.py <port> --backend http://127.0.0.1:<backend port>` serves the page and proxies an allowlist of routes. The agentic route is POST-only, with a 1,900 s timeout.
- The page shows a Baseline RAG / Multi-Agent selector only when `/api/config` reports `agentic_mode`. Each agentic answer gets a "How this answer was produced" trace panel.
- Mock UI states, no backend: open the page with `?mock=1`.

**Contracts:**
- The agentic answer goes through the shared `src.research_pipeline.run_research` (`envelope.py`), so it is the same `indexed` envelope as a baseline answer (validated, fingerprinted, pending review).
- Agentic provenance holds: plan, decisions, trace (task/reply/decision entries), rounds, selected round, evidence IDs, index SHA-256, held claims, claims needing a number check, business screening, charts, model calls by agent, and seconds.

**Call budget:**
- **Per process:** `capped_codex_ui.py` enforces the per-process cap, never retries, and stops after any provider error.
- **Cumulative:** `call_ledger.py` (SQLite, `BEGIN IMMEDIATE`, `synchronous=FULL`) reserves each call atomically across processes before it reaches the provider, then marks it completed or failed. A crash leaves it `unresolved`, still counted.
- **Fail closed:** a missing or corrupt ledger, a changed authorization, a reset (rows below the high-water mark), or an unknown state refuses every call.
- **Experiment allocation:** an experiment cap is recorded once and never raised. Registering it locks the ledger to that experiment. `close-experiment` ends it for good and unlocks the remaining calls.
- **One authoritative ledger:** `ab_profile.py` pins the canonical path, seed SHA-256 and `created_at`.
  - `init` refuses the approved seed.
  - `ab-agentic-1` is refused anywhere else.
  - Only listed experiment names are allowed on the approved ledger (currently only `ab-agentic-1`).
- **Trust boundary:** copying the file and editing the profile code bypasses all of this. No local mechanism can prevent that; every supported path fails closed.

---

## D. Tests and verification

Run from the worktree root. All are model-free. The reproduction matrix below includes prior runs. The independent rerun is summarized above.

| Command | Latest |
|---|---|
| `py -3.14 -I -B experiments/agentic/test_agentic.py` | 33/33 |
| `py -3.14 -I -B experiments/agentic/test_integration.py` | 34/34 |
| `py -3.14 -I -B experiments/agentic/test_adversarial.py` | 44/44 |
| `py -3.14 -I -B experiments/agentic/test_audit2.py` | 16/16 |
| `py -3.14 -I -B experiments/agentic/test_audit3.py` | 9/9 |
| `py -3.14 -I -B experiments/agentic/test_audit4.py` | 9/9 |
| `py -3.14 -I -B experiments/agentic/test_audit5.py` | 2/2 (16 paired cases each) |
| `py -3.14 -I -B experiments/agentic/test_ab_harness.py` | 11/11 (harness and runner against a fake backend) |
| `py -3.14 -B experiments/agentic/test_ab_dryrun.py` | 4/4, about 75 s (**real backend, real index and models, fake provider, disposable stand-in ledger**) |
| `py -3.14 -I -B experiments/table-endpoint/test_call_ledger.py` | 16/16 (cross-process races, crashes, corruption, reset) |
| `py -3.14 -I -B experiments/table-endpoint/test_ab_profile.py` | 19/19 (launcher profile, canonical ledger, lookalike names, init race) |
| `py -3.14 -I -B experiments/table-endpoint/test_chart_first.py` | 13/13 **with fixtures** (otherwise 10/13) |
| `py -3.14 -I -B experiments/table-endpoint/test_evidence_tables.py` | 21/21 **with fixtures** (423 verified) |
| `python -I -B ui-consult/tests/test_serve.py` | 10/10 **with fixtures** (otherwise 9/10) |
| Baseline `py -3.14 -B -m pytest -q -p no:cacheprovider tests/test_answer_quality.py tests/test_brief_store.py tests/test_business_translation.py tests/test_experimental_b2_integration.py tests/test_experimental_b2_retrieval.py tests/test_indexed_research.py tests/test_research_chat.py tests/test_research_contracts.py tests/test_research_pipeline.py` | 125 passed |
| Baseline HTTP files `tests/test_research_demo.py tests/test_brief_library_http.py` | Intermittent: 1–5 failures per run (see below) |
| Browser suite: serve with `--serve-tests` and open `/tests/evidence.test.html` | 37/37 when last run; files unchanged since |

**Fixture-dependent suites.**
- Run them in a disposable copy of the worktree.
- Put `table-audit-demo-100.json` next to `experiments/table-endpoint/test_*.py`.
- Put the 4 recorded fixtures under `ui-consult/tests/fixtures/`.
- Never commit the fixtures.

**Windows socket flake.**
- **Symptom:** in `tests/test_research_demo.py` (DemoHttpTests), tests fail with `ConnectionAbortedError: [WinError 10053]` inside `socket.recv_into`. The `AssertionError` lines that follow are consequences.
- **Not a regression:** the untouched baseline export `D:/KPMG-demo-corpus/main-727b0b3` fails the same way (2–5 per run). `src/` and `tests/` are unchanged.
- **How to tell it apart:** a real regression fails without `WinError 10053`, or also fails in the non-HTTP baseline files.

**Unsupported or incomplete:**
- Multi-Agent does not support the risk and compliance assessment or the clarification flow.
- Under the A/B profile, the dashboard's Baseline questions are refused, because the UI sends `interpret_context: true`. The A/B is driven by `ab_run.py`, not the UI.

---

## E. Live A/B evaluation (NOT approved yet)

**Questions** (`experiments/agentic/ab_questions.json`; required points quote chunks of the pinned corpus):
- **Q2:** "Compare how Agent-SafetyBench and TravelPlanner evaluate LLM agents, and what safety or success rates does each report?"
  - Points P1–P4: Agent-SafetyBench design; its result of 16 agents, none above 60%; TravelPlanner design with 1,225 intents; its result, GPT-4 at 0.6%.
- **Q3:** "By how much did the CU-DPO training method improve strategy-selection accuracy, and on how many base models?"
  - Points: from 35–46% to 68–78%; seven base models. Optional: +6.6 points downstream.

**Fixed conditions:**
- **Corpus:** demo-100 (SHA-256 above), retrieval `document-table-balanced-facets-v1`, top_k 8.
- **Provider:** automated reviewer `gpt-6.1-sol`, effort low, 300 s timeout, evidence compaction on.
- **Requests:** research-only in both modes, the same question text, one request at a time, order Q2 B, Q2 A, Q3 B, Q3 A.

**Budget:**
- **Overall:** the 40-call authorization; the ledger shows **20 used** (19 completed, 1 failed), 20 remaining, **no experiment lock**, no caps.
- **A/B allocation:** at most **14** calls. Baseline uses ≤2 per question and Multi-Agent ≤5, so 2+5+2+5 = 14. Every server pre-check passes in this order (the baseline pre-check needs ≥4 remaining; Multi-Agent needs ≥3).

**Commands (set once):**

```text
set EXPORT=D:/KPMG-demo-corpus/main-727b0b3
set BUNDLE=%EXPORT%/data/processed/demo-bundles/demo-100
set ENC=%USERPROFILE%/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41
set RR=C:/Users/ngkho/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation/data/processed/model-cache/models--cross-encoder--ms-marco-MiniLM-L6-v2/snapshots/233902d25c440f23af6f7d6e94d2946bac0bee0a
set LEDGER=D:/KPMG-demo-corpus/table-endpoint-exp/automated reviewer-authorization-40.ledger.sqlite3
set FLAGS=--export %EXPORT% --bundle %BUNDLE% --encoder %ENC% --reranker %RR% --table-audit D:/KPMG-demo-corpus/table-endpoint-exp/table-audit-demo-100.json --port 8787 --max-calls 14 --agentic --profile ab-agentic-1 --call-ledger %LEDGER% --authorized-calls 40 --experiment ab-agentic-1 --experiment-cap 14
```

1. **Read-only budget preflight** (loads nothing, writes nothing; must print used 20, remaining 20, `locked_experiment` null, no caps):
   `py -3.14 -I -B experiments/table-endpoint/live_backend.py %FLAGS% --library <NEW ab-briefs.sqlite3> --call-log <NEW ab-calls.jsonl> --budget-check-only`
2. **Only after explicit owner approval**, start the backend (this **locks the real ledger to `ab-agentic-1`**):
   `py -3.14 -B experiments/table-endpoint/live_backend.py %FLAGS% --library <same> --call-log <same>`
3. **Runner preflight** against the running backend (0 calls):
   `py -3.14 -I -B experiments/agentic/ab_run.py preflight --backend http://127.0.0.1:8787`
4. **Run** (≤14 calls; refused without the exact phrase):
   `py -3.14 -I -B experiments/agentic/ab_run.py run --backend http://127.0.0.1:8787 --run-dir <NEW dir> --approve "ab-agentic-1 14 calls"`
5. **Report** (no calls):
   `py -3.14 -I -B experiments/agentic/ab_eval.py report --run-dir <run dir> --out <NEW dir> --blind`
6. **Human review:** a person fills `review-sheet.json` (all fields start `pending`), reading the cited passages. Then:
   `py -3.14 -I -B experiments/agentic/ab_eval.py merge-review --report <report dir> --review <filled.json> --out <NEW dir>`

**What the runner records per request** (one file each, written before the next request, never overwritten):
- question, mode, request body, full response, HTTP status
- wall latency and timestamps
- `/api/config` snapshots before and after
- **actual calls** (the ledger experiment delta), and the provider and index from config

**Stop conditions** (the runner writes `STOPPED.json`, exits non-zero, and never retries):
- a non-200 response or an execution error (provider or budget)
- a step using more calls than its maximum (2 or 5), or a negative delta
- the orchestrator's reported calls differing from the ledger
- generation stopped
- a wrong experiment, cap, authorization or index
- a cited ID outside the evidence, a quote absent from its passage, or an answer index other than the pinned one
- business output present

A clean abstention is a result, not a stop. After a stop, do not restart to retry; report to the owner.

**Compare fairly:**
- Use the blind review sheet (answers labelled A and B; the key is kept in `blinding-key.json`).
- Automatic metrics (status, index match, citation validity, required-point evidence and citation coverage, anchors, latency, actual calls, held claims) are **proxies**.
- Correctness, entailment, misleading comparisons and false abstention come only from the human review.
- Report raw counts per question. The sample is two questions with one run each.

**Close the allocation afterwards** (a person decides; the total is not reset, and the unused calls, at least 6, return to the pool):
`py -3.14 -I -B experiments/table-endpoint/call_ledger.py close-experiment --ledger %LEDGER% --authorized 40 --experiment ab-agentic-1`

Read-only status at any time: `py -3.14 -I -B experiments/table-endpoint/call_ledger.py status --ledger %LEDGER%`

---

## F. Known limitations

- **Meaning:** code checks are surface checks. Meaning still depends on the verifier model and a person. Word lists (metrics, settings, population groups, negation, premise joints) are finite; anything outside them is *uncertain*, not judged.
- **False holds:** a correct claim can be held, for example a rephrased qualifier, an unlisted unit or an unusual subject. Ambiguous scopes give *uncertain* and a human flag. This understates the Multi-Agent arm, by design.
- **Uneven checks:** the baseline runs the quality review but not the numeric grounding (except with the arXiv fallback). Multi-Agent runs stricter checks, which is a known asymmetry in the A/B.
- **Business:** recommendations are never model-verified; unsupported ones are withheld. Business translation is off in the A/B.
- **Coarse metrics:** required-point evidence coverage is chunk-level (an abstract chunk can cover several points). Anchors are lexical. Neither is correctness.
- **Ledger:**
  - The local trust boundary (section C).
  - An `unresolved` reservation after a crash needs a person.
  - Hard links (NTFS or POSIX) are required to initialize a ledger.
- **Sample size:** the A/B is tiny. The results will be indicative only.
- **Open audit items:** structured numeric ranges and fail-closed runner identity checks. See the verification checkpoint above.

---

## G. Next engineering steps

1. **After owner approval, address the verification checkpoint findings and rerun the Audit #5 checks.** Read `AUDIT-RESPONSE.md` (audit #5 section), `numeric_checks.py` (`_breaks`, `_scope`, `_qualifiers`, `_clause_subject`, `_judge`), and `ab_profile.unapproved_experiment` with its uses in `call_ledger.py` and `live_backend.py`. Run `test_audit5.py` and `test_ab_profile.py`.
2. **Review the A/B harness:** `ab_questions.json` (each required point quotes its chunks), `ab_eval.py`, `ab_run.py`, `fake_provider.py`, `test_ab_harness.py` and `test_ab_dryrun.py`. Run both tests.
3. **Verify readiness, read only:** step 1 of section E, plus `call_ledger.py status`. Expect 20/40, no lock.
4. **Get explicit approval** from the owner before steps 2–4 of section E (they spend real calls and lock the ledger).
5. **Run the comparison** only when cleared. Stop on any stop condition; never retry automatically.
6. **Analyze:** generate the report, have a person fill the blind review sheet, merge it, and summarize per question.
7. **Prepare the checkpoint:** an isolated, user-approved commit. Exclude fixtures, audits, ledgers, logs, `__pycache__` and run outputs. Keep `src/` untouched.
