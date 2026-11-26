# Handoff to Laptop Claude: optimized S2-R2 research candidate and Gemini evaluation

**Date:** 2026-11-26.

**From:** the research session. RAG optimization is **closed**.

**To:** Laptop Claude, who confirms the deployed Gemini configuration, prepares an isolated evaluation environment, and runs the final evaluation after the project lead approves.

## 1. Branches

| Branch | Commit | Role |
|---|---|---|
| `checkpoint/s2-engine-b1` | (Codex) | Frozen S2 checkpoint, the stable delivery engine |
| `exp/s2-r2-fusion` | `1d0e0ae` | **Validated** S2-R2 reference: passed the sealed unseen evaluation (Codex provider) |
| **`exp/s2-r2-opt`** | **head of branch** | **Final research candidate:** the same behaviour as `1d0e0ae`, with the duplicate original search removed |
| `deploy/azure-vm` | — | Live Azure application. **Not modified by research.** |

## 2. What the candidate is

**Engine:** `experiments/retrieval-v3/s2_r2_opt.py`, `S2R2OptResearch(retrieval_strategy='r2')`.

**Routing:**

| Question | Route |
|---|---|
| Names two or more papers present in the top-120 | **B1** (balanced per-paper window) |
| Otherwise, two or more question components | **Component-rank fusion** of the 30-candidate window |
| A single ask | S2's own window |

**Unchanged from frozen S2:**
- the evidence budget (6,000 passage tokens plus 800 C2, at most 40 passages);
- synthesis and review prompts;
- citation checks and publication gates;
- **2 LLM calls** per question.

**Results (Codex `gpt-6.1-sol` low; unseen-r2, 8 questions, 36 points):**

| | Frozen S2 | R2 |
|---|---|---|
| Completeness | 25.0 (69.4%) | **29.5 (81.9%)** |
| Safety flags | 0 | 0 |
| Median latency | 105.2 s | 118.5 s |
| p90 latency | 153.4 s | 166.4 s |
| Input tokens | — | 0.99× S2 |

All six frozen criteria passed: `unseen-r2/RESULTS.md`.

**Optimization:** byte-identical evidence on 69 of 69 questions; retrieval median 25.0 → **15.3 s**; CPU −37%. See `R2-OPT-REPORT.md`.

**Known limits:**
- **Provider:** results so far are Codex only.
- **Unseen questions, seen papers:** the unseen questions are about seen papers.
- **85% target:** not reached yet.
- **Remaining losses are retrieval-side:** see `R2-RETRIEVAL-BOTTLENECK.md`. Coverage tuning is stopped.
- **Deferred:** reviewer completion (`GENERATION-DIAGNOSIS.md`) is not implemented.

## 3. Files on `exp/s2-r2-opt`

**Code** (`experiments/retrieval-v3/` unless noted):
- **Engine:** `s2_r2_opt.py`, `s2_r2.py`, `s2_paper_balance.py`, `paper_balance.py`, `s3_evidence.py`, `components.py`, `s3_env.py`.
- **Production adapter pattern:** `s2_adapter.py`.
- **Frozen V2:** `experiments/consolidated-v2/` (engine, evidence, synthesis, review, publication, env, accounting, adapter).
- **Shared:**
  - `experiments/verification-repair/`;
  - `experiments/evidence-budget/`;
  - `experiments/agentic/statistical_reports.py`;
  - `experiments/agentic-handoff/` (`codex_paired.py`, `codex_baseline.py`);
  - `experiments/measure/` (`common.py`, `fresh-diagnostic-v1/prepare.py`);
  - `src/experimental/` (B2 retrieval);
  - `src/generation.py` (the Gemini adapter, `create_generate`).

**Evaluation infrastructure to reuse:**
- `unseen-r2/run_unseen.py`: automated, counterbalanced, resumable two-arm runner with per-arm persistent ledgers (cap 20 each, 40 combined), one resume pass after a 300 s backoff, progress log, seals.
- `unseen-r2/score_unseen.py`: metrics, programmatic audit (exact quotes, number recall, uncited absence claims), blind A/B packet, frozen-criteria evaluation.
- `unseen-r2/build_unseen.py`: question and key builder that checks every anchor and fact against the index. It is the template for the new final set.
- `fresh-v4/build_validation_bundle.py` and `fresh-v4/html/`: rebuild the validation index (section 4).

**Protocol and reports:**
- `GEMINI-EVAL-PROTOCOL.md`, corrected:
  - the compatibility criterion is ≥ 7/8 per arm;
  - the 4 smoke-test calls are inside the 32 expected and the 40 cap.
- `R2-OPT-REPORT.md`, `unseen-r2/RESULTS.md`, `R2-IMPLEMENTATION-REPORT.md`, `R2-RETRIEVAL-BOTTLENECK.md`, `GENERATION-DIAGNOSIS.md`.

## 4. Required assets not stored as large binaries in git

| Asset | How to obtain | Verify |
|---|---|---|
| demo-100 corpus bundle | Already on Azure and the laptop (`parents.jsonl` sha256 `78d8efd7…`) | `identity()['indexed_records_sha256']` |
| fresh-v4 validation bundle (52 MB) | Rebuild: `python -X utf8 experiments/retrieval-v3/fresh-v4/build_validation_bundle.py`. It uses demo-100 plus the 10 committed HTML files in `fresh-v4/html/` and writes a new folder under `data/processed/validation-bundles/` | `fresh-v4/validation-bundle.sha256`: `parents.jsonl` must equal `0039ce20…`. `vectors.npy` may differ in the last bits on other hardware; the runners pin `parents.jsonl` only |
| Encoder and reranker | `all-MiniLM-L6-v2`, `cross-encoder/ms-marco-MiniLM-L6-v2` (paths in `experiments/measure/common.py`) | Loaded by `open_ranked` |
| Python environment | 3.14 with `jsonschema`, `numpy`, `sentence-transformers`, `transformers`, `torch`, `google-genai` (Gemini). The bundle rebuild also needs `pandas`, `bs4` and `langchain_text_splitters` | — |

Change any machine-specific paths in `experiments/measure/common.py` (`BUNDLE`, `ENCODER`, `RERANKER`).

## 5. Verification commands (0 model calls)

Run from `experiments/retrieval-v3`:

```powershell
python -X utf8 -m unittest test_s2_r2_opt test_s2_r2 test_s2_paper_balance test_s3
```

```powershell
python -I seal_s3.py
```

```powershell
python -I run_b1_diagnostic.py --check
```

Run from `experiments/consolidated-v2`:

```powershell
python -X utf8 -m unittest test_v2 test_consolidated test_runner
```

**Expected results:**
- **retrieval-v3:** 64 tests OK.
- **Seals:** all verified.
- **Caveat:** the identity test against cached rankings needs `cache/` and the validation bundle. If the cache is absent, regenerate it with `rank_cache.py` and `fresh_coverage.py rank`, or skip that test and run `verify_r2_opt.py` after rebuilding the bundle.

## 6. Gemini evaluation: what Laptop Claude does

**1. Confirm the deployed configuration.**
- On `deploy/azure-vm`, `HANDOVER.md` says `gemini-3.1-flash-lite`, but `.env.example` and the README say `gemini-2.5-flash`.
- Read the live value from the Azure VM's configuration **read-only**, without printing secrets.
- Also confirm temperature 0, schema output and the 60 s adapter timeout.

**2. Isolated environment.**
- Use a separate Google project and API key **for evaluation only**, never Azure's production key.
- Set a budget alert (proposed USD 10) and quotas on that project.
- Expose the key as an environment variable, `GEMINI_EVAL_API_KEY`. The runner must never print or log it.

**3. New sealed final benchmark (kept separate from development).**
- Write 8 new questions (36 points) with `build_unseen.py` as the template: 3 named two-paper, 3 unnamed multi-part, 2 controls.
- **Use facts that no existing key point uses.** Check against `fresh-v4/references.json` and `unseen-r2/references.json`.
- Run one independent Codex CLI key review (`codex exec`, confined to a folder holding only the key, rules and passages), apply the findings, then seal.
- Do **not** reuse fresh-v3, fresh-v4 or unseen-r2 questions. They are development data now.

**4. Gemini runner: reuse `run_unseen.py`**, with these changes only:
- **Provider:** replace `create_codex_generate(...)` with `src.generation.create_generate(config)`, configured for Gemini with the confirmed model, temperature 0 and the key from `GEMINI_EVAL_API_KEY`.
- **Arm R2:** use `S2R2OptResearch(retrieval_strategy='r2', ...)`.
- **Token accounting:** record actual input and output tokens from the Gemini response usage metadata into the ledger. Codex receipts are not available for Gemini.
- **Token caps:** stop before input would exceed 1.2 M or output 150 k in total.
- **Smoke test:** S2 U1 and S2 U2 first, then continue automatically only if both returned valid structured output without an unrecovered timeout. These 4 calls count toward the 32 and 40.
- **Freeze** the runner and the engine code (as in `code-freeze.json`) before the first call.

**5. Approval gate.** Present to the project lead:
- the readiness check (seals, key present by name only, memory, caps);
- the confirmed model;
- the budget.

**Run only after explicit approval.** Then score with `score_unseen.py` (blind packet, a fresh Codex CLI scorer, programmatic audit, criteria) and report against the frozen criteria in `GEMINI-EVAL-PROTOCOL.md`.

## 7. Integration into Azure (only after the Gemini evaluation passes)

**Pattern:** follow `INTEGRATION-HANDOFF.md`:
- a server-side switch, for example `RESEARCH_ENGINE=baseline|s2` and `S2_RETRIEVAL=s2|r2`;
- construct `S2R2OptResearch` through the adapter pattern in `s2_adapter.py`.

**Defaults:**
- **Keep frozen S2 as the default** until R2 passes on Gemini.
- R2 adds no new dependencies or index changes, but about +8 s of CPU retrieval per question (median, optimized).

**Rollback:** `S2_RETRIEVAL=s2` gives frozen S2, so no redeploy of the index is needed.

## 8. Rules carried forward

- No modification of `deploy/azure-vm` from research branches.
- No further RAG tuning.
- No live calls without the project lead's approval.
- Report every failure, retry and call.
