# Message for Codex: checkpoint the S2 and B1 engine, then review integration compatibility

**Paste everything below the line into Codex,** working in `D:\KPMG-source-grounded`.

---

You are taking over the checkpoint and integration review of the evaluated research engine. Read `experiments/retrieval-v3/INTEGRATION-HANDOFF.md` first. It is the full handoff: files, dependencies, configuration, provider requirements, API contract, tests, results and rollback.

## Decisions (project lead)

- **S2** (consolidated-v2 Standard) is the selected demo engine.
- **B1** (`paper_balance=True`) is experimental and opt-in.
- **The Original Baseline stays the application default** until integration testing passes.

## Hard rules

- Do **not** merge into `main`. Do **not** overwrite or change existing application functionality: backend, frontend or Render deployment.
- Do **not** deploy. Do **not** make paid provider or live model calls.
- Do **not** modify the frozen engine files. If any hash below does not match, stop and report it; do not "fix" the file.

## Step 1: verify the frozen engine (0 calls)

From `experiments/retrieval-v3`:

```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I seal_s3.py
```

```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_b1_diagnostic.py --check
```

Both must report verified. `--check` also checks the Codex login, which is not a model call.

**The five shared dependency files are uncommitted in this worktree.** The evaluated versions have these sha256 hashes:

| File | sha256 (evaluated) | Sealed in |
|---|---|---|
| `src/experimental/b2.py` | `476518d6a2424c229d2afd78cef5b281e85dbc766eee9ada5f4963bb35aa9fc3` | `s3-freeze.json` |
| `src/experimental/balanced_retriever.py` | `267ff7113339a262c15669ae09d4058f4e6d869918650b12636963cb43d66307` | `s3-freeze.json` |
| `src/experimental/evidence_coverage.py` | `f177c97a502727ccd4b57cd3ea5d20637c5e789d2f346ef4b244ed7d0d8549ff` | `s3-freeze.json` |
| `src/codex_generation.py` | `93946a22a852001ea57d5340584772225921e5ce9ee4233bbb49c955a2a923e7` | `s3-freeze.json` and fresh-v3 `seal.json` |
| `src/generation.py` | `bb10b4ce7fc3c043243c06bf53e68ab98ee9fe688d75cbcdf9a08d083b43d38a` | working-tree version at evaluation time (**not sealed**) |

For `src/generation.py`:
- Confirm whether the S2 engine path imports it.
- If it does, commit this exact version.
- If it does not, leave it to its owner and say so in your report.

## Step 2: run the regression suites (0 calls)

| Folder | Command |
|---|---|
| `experiments/consolidated-v2` | `D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -X utf8 -m unittest test_v2 test_consolidated test_runner` |
| `experiments/retrieval-v3` | `D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -X utf8 -m unittest test_s2_paper_balance test_s3` |

Report the counts. All must pass.

## Step 3: commit and push to a checkpoint branch (not main)

**Branch:** create or update a checkpoint branch, for example `checkpoint/s2-engine-b1`, from the current branch `claude/source-grounded-quotes`. Push it to origin. **No merge into main.**

**Commit, as additive files:**
- `experiments/consolidated-v2/`: engine, adapter, tests, runners, reports, the `fresh-v3/` key, rules and seal.
- `experiments/retrieval-v3/`: the B1 files (`paper_balance.py`, `s2_paper_balance.py`, `s2_adapter.py`, `components.py`, `s3_env.py`), S3 files for the record, runners, seals (`s3-freeze.json`, `b1-freeze.json`), tests, all reports (`INTEGRATION-HANDOFF.md`, `FINAL-REPORT-fresh-v4.md`, `PAPER-BALANCE-REPORT.md`, `B1-DIAGNOSTIC-*.md`, `READINESS-fresh-v4.md`, `SIGN-OFF-fresh-v4.md`) and the result JSONs (`fresh4-results.json`, `fresh4-audit.json`, `fresh4-adjudication.json`, `paper-balance.json`, `coverage*.json`, `offline-acceptance.json`).
- `experiments/retrieval-v3/fresh-v4/`: the question set, key, rules, `seal.json`, review record and report, `SELECTION-RULE.md`, `selection-log.json`, `sources.json`, `bundle-record.json` and the build scripts.
- The dependency folders used by the engine: `experiments/verification-repair/`, `experiments/evidence-budget/`, `experiments/agentic/statistical_reports.py`, `experiments/agentic-handoff/` (`codex_paired.py`, `codex_baseline.py`) and `experiments/measure/` (`common.py`, `fresh-diagnostic-v1/prepare.py`).
- The four sealed `src/` files above, plus `src/generation.py` if required.

**Do NOT commit:**
- `experiments/retrieval-v3/cache/` and `fresh-v4/html/`, `fresh-v4/discovery/` and `fresh-v4/passages/`: large or derived data;
- `data/processed/` run outputs and the validation bundle;
- the `D:\KPMG-blind-*` scorer folders;
- secrets or login state.

**Afterwards:** re-run Step 1 on the pushed branch's checkout to confirm the hashes still verify.

## Step 4: compatibility review (read-only, no code changes)

Review §6 and §7 of `INTEGRATION-HANDOFF.md` (API contract, integration steps) against the **latest backend, frontend and Render deployment work**. Report:

1. **Whether the seam still exists unchanged.** That is, `src.indexed_research.IndexedResearch.execute`, with `retrieve` and `summary` injection.
2. **Additive summary fields.** Whether the frontend tolerates or ignores them: `answer_scope`, `answer_lead`, `held_claims`, `evidence_notes`, `paper_balance`, `generation_method`, `quality_review`.
3. **Configuration.** How to add `RESEARCH_ENGINE` and `S2_PAPER_BALANCE` without changing the Baseline default.
4. **Render constraints:**
   - memory, since retrieval needs about 1.5 GB per process plus the local models;
   - local model files and the demo-100 index on disk;
   - cold start;
   - request timeouts: S2 takes about 93 s median and 141 s p90 on Codex, and production adapters time out at 60 s per call.
5. **Provider wiring.** Which production provider the deployment uses. Note that the 6-call smoke test (cap 10) needs the project lead's approval before any paid call.
6. **Anything else** that would break existing functionality, with file and line references.

## Deliverable

Write a short report to `experiments/retrieval-v3/CODEX-CHECKPOINT-REPORT.md` covering:
- hash verification;
- test counts;
- branch name and commit SHA;
- files committed and excluded;
- the `src/generation.py` decision;
- the compatibility findings, ranked by severity;
- proposed integration changes, awaiting approval.

Then stop and wait for the project lead.
