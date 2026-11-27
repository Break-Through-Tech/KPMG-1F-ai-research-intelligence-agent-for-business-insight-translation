# Integration handoff: S2 (default) and B1 (experimental opt-in)

**Audience:** Codex and the application team.

**Date:** 2026-11-25.

**Status:**
- The engine optimization phase is **closed**.
- The shared application has **not** been modified.
- Nothing in this handoff has been committed by Claude; commits and pushes are Codex's.

## 1. What is being integrated

| Engine | Role | Behaviour |
|---|---|---|
| **S2: consolidated-v2 Standard** | **stable default and fallback** | One retrieval packet, 2 model calls: synthesis, then review. Deterministic publication gates. |
| **B1: S2 + paper-balanced selector** | **experimental, opt-in** (`paper_balance=True`) | Identical to S2 except evidence selection, and only when a question names two or more papers whose titles appear in the top-120 candidates. In that case the 30-candidate window is shared round-robin across those papers. No extra searches. |
| Original Baseline (B0) | existing production path | Unchanged. It remains available and is the rollback of last resort. |
| S3, D2, S1, Adaptive | **not integrated** | Evaluated; did not qualify. Kept for the record only. |

**S2's evidence path:**
- B2 ranking;
- protected 6,000-token skip-fit packet over the top-30;
- C2 conclusion allowance of 800 tokens;
- whole table groups, or an incomplete-table note.

## 2. Files

**Engine (frozen; hashes in `experiments/retrieval-v3/b1-freeze.json` and `s3-freeze.json`):**
- `experiments/consolidated-v2/`: `engine.py`, `evidence.py`, `synthesis.py`, `review.py`, `publication.py`, `env.py`, `accounting.py`, and `adapter.py` (the S2 production adapter).
- `experiments/verification-repair/`: `numeric_checks_v2.py`, `interpretation_gate.py`, `verification_v2.py`.
- `experiments/evidence-budget/`: `evidence_budget.py`, `request_guard.py`.
- `experiments/agentic/statistical_reports.py`.
- `experiments/agentic-handoff/`: `codex_paired.py`, `codex_baseline.py`. These are only needed for the evaluation runners and the Codex provider.

**B1 (new, isolated):**
- `experiments/retrieval-v3/paper_balance.py`: the resolution and allocation rule.
- `experiments/retrieval-v3/s2_paper_balance.py`: `S2Research(paper_balance=...)`.
- `experiments/retrieval-v3/s2_adapter.py`: `create_s2_research(..., paper_balance=False)`, the production adapter for S2 and B1.
- `experiments/retrieval-v3/components.py` (`named_terms`) and `s3_env.py` (import setup).

**Shared `src/` files the engine depends on. These carry UNCOMMITTED modifications in the `D:\KPMG-source-grounded` worktree, and the frozen evaluations ran against those versions.** Codex must commit them together with the engine, or confirm they match the branch it pushes:
- `src/experimental/b2.py`
- `src/experimental/balanced_retriever.py`
- `src/experimental/evidence_coverage.py`
- `src/codex_generation.py`
- `src/generation.py`

The sealed hashes in `s3-freeze.json` identify the exact evaluated versions.

## 3. Dependencies

**Python:** 3.14, as in `D:\KPMG-venvs\stage-a-py314`. The engine needs `jsonschema`, `numpy`, `sentence-transformers`, `transformers` and `torch` (CPU).

**Models (local, no network at run time):**
- `all-MiniLM-L6-v2`, the encoder;
- `cross-encoder/ms-marco-MiniLM-L6-v2`, the reranker.

The paths are in `experiments/measure/common.py`.

**Index:** the demo-100 B2 bundle, parents sha256 `78d8efd7…`. The adapter's checkpoint fingerprint includes the index identity.

**Ingestion only, not needed at run time:** `pandas`, `bs4` and `langchain_text_splitters`.

**Memory:** about 1.5 GB per process for retrieval. The evaluation runners refused to start below 6 GB free.

## 4. Configuration

| Setting | Default | Meaning |
|---|---|---|
| engine | Original Baseline (current) | Switch to `create_s2_research(...)` to enable S2 |
| `paper_balance` | **False** | True enables B1. Leave it off in production until the unseen-question validation in §8 passes |
| evidence budget | 6,000 passage tokens, plus 800 for C2, at most 40 passages | Frozen. Do not change |
| model calls | 2 per question | Synthesis, then review |
| checkpoint root | per deployment | Per-request resumable stages, keyed by session, query, variant, index and context |

## 5. Provider requirements

**Evaluated provider:** all evaluations used the Codex subscription provider (`gpt-6.1-sol`, low reasoning effort, ChatGPT login, 300 s timeout).

**Production adapters are not validated yet:** the Gemini, OpenAI, OpenAI-compatible and Bedrock adapters use the application's 60 s timeout. Before go-live, run the planned **provider smoke test**:
- S2 on 3 questions, 6 calls, hard cap 10;
- it checks structured output and schema validation, malformed-output handling, output length, the 60 s timeout and actual token usage.

**Measured cost per question (S2, Codex):**

| Measure | Value |
|---|---|
| Median latency | 93 s |
| p90 latency | 141 s |
| Input tokens | about 42k (both calls) |

**Measured cost per question (B1, on named two-paper questions):**
- input tokens about the same;
- output tokens 1.5–2.1× higher;
- 20–70 s slower.

## 6. API contract

**Seam:** `src.indexed_research.IndexedResearch.execute(payload, session_id=...)` is unchanged.

**What the adapter replaces:**
- `retrieve` becomes the engine's evidence phase;
- `summary` becomes the engine's answer phase.

Business translation, the regulatory checkpoint, `validate_result`, fingerprints and the UI contract all remain the existing code.

**Additional fields in the summary (additive):**
- `answer_scope`, `answer_lead` and `answer_lead_check`;
- `held_claims` and `dropped_limitations`;
- `evidence_notes`;
- `generation_method`: `consolidated-v2-standard` or `consolidated-v2-standard+paper-balance`;
- `paper_balance`: `{enabled, requested_papers, applied}`;
- `quality_review`.

**Unchanged:** every published claim keeps exact quotes and chunk IDs, validated against the evidence. `human_review.status` stays `pending` and `approved: false`, because the demonstration is supervised.

## 7. How to integrate without breaking current functionality

1. **Commit the files in §2, with no app edits.** Keep the Original Baseline as the live default.
2. **Add a server-side engine switch.** Use an environment variable or configuration value, for example `RESEARCH_ENGINE=baseline|s2` and `S2_PAPER_BALANCE=0|1`. At startup, build `create_s2_research(retrieval=open_ranked(...), generate=<provider>, metadata=..., checkpoint_root=..., paper_balance=bool)` only when it is selected. Otherwise use the current Baseline construction unchanged.
3. **Treat the additive fields as optional in the UI.** Render `answer_lead`, `held_claims` and `evidence_notes` only if present.
4. **Run the provider smoke test (§5)** on the chosen provider.
5. **Run the regression suites (§9)** in CI on every change.
6. **Flip the default to S2 in staging.** Check end-to-end reliability: timeouts, retries and resume, memory, concurrency and checkpoint isolation. Then go to production with the Baseline switch kept available.
7. **Keep B1 off** until §8 passes, then expose it as an opt-in "multi-paper" option.

## 8. Integration validation, including unseen multi-paper questions

- **Smoke and reliability:** the provider smoke test, 10 or more end-to-end requests through the UI on S2, a forced timeout and resume, and two concurrent sessions, checking checkpoint isolation.
- **Unseen multi-paper questions (B1 generalization):**
  - **Questions:** 3–5 new questions that each name two papers by title, written against the production corpus. None may be J03, K05 or K07.
  - **Runs:** each with `paper_balance` off and on, about 6–10 calls per question pair.
  - **Measures:** answer completeness (blind A/B), citation safety (programmatic audit plus blind flags), latency and input and output tokens.
  - **Proposed bar for enabling B1 as an opt-in:** higher total points with zero new safety flags. Latency is reported as a product decision.
- **Single-paper regression:** 3 single-paper questions with `paper_balance` on. The evidence must be byte-identical to S2; the offline check already verifies this.

## 9. Regression tests (0 model calls)

Run from each folder with `D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -X utf8 -m unittest <module>`.

| Folder | Module | Tests | Covers |
|---|---|---|---|
| `experiments/consolidated-v2` | `test_v2`, `test_consolidated`, `test_runner` | about 134 | S2 engine, gates, serialization, runner |
| `experiments/retrieval-v3` | `test_s2_paper_balance` | 11 | B1 resolution (ambiguous or overlapping titles, model names, missing papers), single-paper identity, budget, tables, flag-off equivalence, exact offline reproduction |
| `experiments/retrieval-v3` | `test_s3` | 40 | Shared safety fixtures (absence guard, replay identity), retained for the record |

Integrity checks: `python -I seal_s3.py` and `python -I run_b1_diagnostic.py --check`.

## 10. Evaluation results (summary)

| Evaluation | Result |
|---|---|
| fresh-v3 (8 questions, 38 points) | S2 65.8%, 0 safety failures, median 94.8 s; B0 46.1% |
| fresh-v4 (10 new papers, 50 points) | S2 74.0%, 0 safety failures (adjudication proposed), median 92.9 s; S3 74.0%, not qualified |
| B1 offline (6 sets, 236 points) | evidence coverage 178 to 184, 0 displaced, no false triggers |
| B1 live diagnostic (J03, K05, K07; development cases) | 6.0 to 10.5 of 15 points, 0 safety flags; **failed frozen criteria** (1 lost half-point; latency 1.21x) |
| Retrospective fresh-v4 with B1 on K05 and K07 | 41/50 = 82%. **Not independent validation** |

**Reports:**
- `experiments/consolidated-v2/FRESH-V3-FINAL-REPORT.md`
- `experiments/retrieval-v3/FINAL-REPORT-fresh-v4.md`
- `PAPER-BALANCE-REPORT.md`
- `B1-DIAGNOSTIC-RESULTS.md`

**Known limitations of S2, to disclose in the demonstration:**
- completeness of about 66–74% of required points;
- weak cross-paper answers unless papers are named and B1 is on;
- "not established" statements describe the retrieved evidence only;
- scoring was AI-assisted;
- latency measured on the Codex provider only;
- human review required.

## 11. Rollback

| Level | Action | Effect |
|---|---|---|
| 1 | `S2_PAPER_BALANCE=0` | Exactly frozen S2. No restart of other components needed |
| 2 | `RESEARCH_ENGINE=baseline` | The current Original Baseline path, unchanged by this integration |
| 3 | Revert the integration commit | Engine files are additive and isolated under `experiments/`, so reverting the switch removes all S2 wiring |

**Checkpoints:** keyed by variant and index, so switching never reuses stale stages.

## 12. For Codex (commit and push)

**Commit to the integration branch as additive files:**
- `experiments/consolidated-v2/` and `experiments/retrieval-v3/`, excluding `cache/` and the large `fresh-v4/html` and `fresh-v4/discovery` data, or putting them in LFS. Large data stays out of git.
- The dependency folders listed in §2.

**Commit or verify the modified `src/` files** listed in §2, so the pushed branch matches the evaluated versions. Verify with `python -I seal_s3.py`.

**Do not commit:**
- `D:\KPMG-blind-*` (scorer folders);
- `data/processed/` run outputs;
- secrets or login state.

**Claude made no commits, pushes or branch changes.**
