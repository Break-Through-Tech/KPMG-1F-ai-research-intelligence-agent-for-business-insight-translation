# Deployment readiness: native Python on Render (single origin)

**Date:** 2026-11-26. **Branch:** `deploy/render-native` (local only, not pushed).
**Status:** ready for a synthetic-fixture hosting check on Render. Not ready for real research
hosting until the corpus is cleared and the authorized asset download exists.
Nothing has been deployed, no Render service was created, and no provider was called.

## 1. Baseline commits reviewed

| Ref | Commit |
|---|---|
| `integration/team-onboarding` (base of this branch) | `5e5722ac8b7fb9b17de4753728c465a1627863f9` |
| `integration/s2-offline` | `5bae206b28e20a3926b6dcc44e88ddec6480c36f` |
| `checkpoint/s2-engine-b1` (frozen engine) | `7bf2d3671dbef8e0733da90cee434107f919cb0f` |
| `main` | `8274afedeba8e516a7854ea41433140cfcb9e932` |

Documents reviewed: `experiments/render-staging/{README.md,S2-OFFLINE.md,server.py,stage.py,engine_runtime.py,dev_server.py,smoke_server.py,render.yaml,Dockerfile}`,
`onboarding/{README.md,PUBLISHING.md,setup.py,assets.json,fixture-assets.json,requirements-py311.lock.txt}`,
`experiments/retrieval-v3/{INTEGRATION-HANDOFF.md,FINAL-REPORT-fresh-v4.md,B1-DIAGNOSTIC-RESULTS.md}`.

## 2. Architecture

One Render **web service, native Python 3.11.9**, serving the approved UI and the API from one
HTTPS origin, exactly as `server.py` was designed (same-origin `/api/*`, Basic auth, Host/Origin
checks). No Docker image, registry, Vercel or second service.

```
Render build:  bash deploy/render/build.sh
                 pip: torch==2.15.0+cpu (CPU index) + onboarding/requirements-py311.lock.txt, pip check
                 python onboarding/setup.py --runtime native --prepare-only [--fixture]
                   -> verifies UI allowlist + hashes, models (HF pinned revisions, size+SHA-256),
                      index + table audit, then experiments/render-staging/stage.py
                   -> verified snapshot under experiments/render-staging/image-context-onboarding/<rev>-*-ready
Render start:  python -B deploy/render/start.py
                 real:    runs the staged, unchanged experiments/render-staging/server.py
                 fixture: same build_handler, auth, quotas, saved work and disk; scripted responses
Disk:          /var/data  -> briefs.sqlite3, provider-usage.sqlite3, s2-checkpoints/
```

### Files added (all under `deploy/render/`; nothing else changed)

| File | Purpose |
|---|---|
| `build.sh` | Render build command. Mode guard, Python 3.11.9 guard, pinned install, optional asset-fetch hook, real-mode presence check (fails before any arXiv reconstruction), Git-commit fallback, then the existing `setup.py` staging. |
| `start.py` | Render start command. Runs the staged context only. Real mode hands off to the unchanged `server.py`. Fixture mode reuses `build_handler(..., synthetic_fixture=True)` with the developer scripted responses and the same origin, password and disk rules as `server.main()`. |
| `render.yaml` | Optional Blueprint template mirroring §4. Not applied. |
| `test_hosted_fixture.py` | Offline end-to-end check of the start path (security gates, UI, cited research, saved work, review, restart). |
| `DEPLOYMENT-READINESS.md` | This report. |

### What is reused unchanged

Frozen S2 engine and its seals; `engine_runtime.py` (engine switch, B1 flag, signed S2 session
cookie); `server.py` (Basic auth, exact Host and same-origin write checks, cross-site rejection,
`/healthz`, research lock, 16-thread bound, Gemini quota ledger, business/regulatory refusal);
`stage.py` (allowlisted snapshot, UI staging hooks, per-file hashes); `setup.py` (pinned model
download and verification, approved frontend allowlist); the Python 3.11 lock; the approved UI
in `onboarding/frontend`; `BriefStore` SQLite saved work and reviews; the audited table endpoint.

### Deliberate limits kept

Baseline is the default (`RESEARCH_ENGINE=baseline`). S2 is opt-in (`RESEARCH_ENGINE=s2`). B1 stays
off (`S2_PAPER_BALANCE=0`; `1` without S2 refuses to start). Business and regulatory analysis stay
refused. One shared reviewer password and one shared library (pilot only, not client use).

## 3. Verification (local, Windows, Python 3.11.9, scripted providers only)

Environment: fresh venv with `torch 2.15.0+cpu`, `sentence-transformers 6.2.0`,
`transformers 5.21.0`; `pip check` clean.

| Check | Result |
|---|---|
| `KPMG_DEPLOY_MODE=fixture bash deploy/render/build.sh` | **pass**: models fetched at pinned revisions and verified; 150 allowlisted files staged (185,168,611 bytes); 23 s with a warm pip cache |
| `test_hosted_fixture.py --engine baseline` | **pass**, 21 checks |
| `test_hosted_fixture.py --engine s2` | **pass**, 22 checks (adds the signed S2 session cookie); `generation_method=consolidated-v2-standard` confirms S2 ran |
| Checks covered | public minimal `/healthz`; 401 without or with wrong password; 403 for wrong Host and cross-site fetch; approved UI served with `no-store`, mock API stripped, KaTeX served; `/api/config` live indexed; 403 for a write without the same Origin; business request refused; cited answer whose chunk ID is in the returned evidence; `human_review.status=pending`; unscripted question returns no claims; brief saved and reviewed against its exact version; both SQLite files in `KPMG_STATE_DIR`; brief and review survive a restart |
| Startup (fixture) | 7–15 s to ready |
| Peak memory (fixture, real interpreter) | Baseline 595 MiB working set / 674 MiB private; S2 598 / 676 MiB |
| Peak memory (real index, desktop record) | about 1.2 GB (`S2-OFFLINE.md`, Windows); Linux unmeasured |
| Fail-closed paths | missing mode; real build without cleared files (stops before arXiv reconstruction); real start without a staged context; HTTP origin on Render; short password; state not a mounted disk; `KPMG_GEMINI_SMOKE` in fixture; B1 without S2; unknown engine: **all refuse to start** |
| Git fallback (Linux shell, WSL, no Docker) | answers only `rev-parse HEAD` / `--short HEAD` from `RENDER_GIT_COMMIT`; any other git command fails; no `.git` and no `RENDER_GIT_COMMIT` refuses |
| Existing unit tests | `onboarding` 9 OK; `render-staging` `test_engine_runtime test_deploy` 10 OK |
| Frozen seals | `seal_s3.py` verified; `b1-freeze` verified; fresh-v3 `seal_v3.py` verified; no tracked file changed |

**The synthetic fixture verifies hosting only.** It has one artificial passage, a zero vector and
an empty table audit. It proves build, startup, authentication, same-origin protection, the
citation path, saved work and the persistent disk. It does not validate retrieval, answer quality,
charts on real tables, latency or memory with the real index.

Not verified locally: Linux runtime memory, Render's build environment, HTTPS behaviour behind
Render's proxy, Gemini. These are covered by the Render fixture deploy and the later approved
smoke test (§6).

## 4. Render dashboard settings

**New → Web Service → connect the GitHub repository** (after `deploy/render-native` is pushed).

| Setting | Value |
|---|---|
| Name | `kpmg-research-preview` |
| Language / runtime | **Python 3** (native) |
| Branch | `deploy/render-native` |
| Root directory | *(blank)* |
| Build command | `bash deploy/render/build.sh` |
| Start command | `python -B deploy/render/start.py` |
| Instance type | **Standard** (1 CPU, 2 GB) |
| Instances | 1 (no autoscaling; the SQLite disk is single-instance) |
| Health check path | `/healthz` |
| Auto-deploy | **Off** |
| Disk | name `kpmg-preview-state`, mount path `/var/data`, size 1 GB |

### Environment variables

| Name | Fixture check | Real prototype | Notes |
|---|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | `3.11.9` | `build.sh` refuses any other version |
| `KPMG_DEPLOY_MODE` | `fixture` | `real` | the same value is read by build and start |
| `KPMG_STATE_DIR` | `/var/data` | `/var/data` | must be the mounted disk |
| `KPMG_REVIEW_PASSWORD` | generated, ≥ 24 printable ASCII | same | Basic auth username is `reviewer`; secret |
| `RESEARCH_ENGINE` | `baseline` (then `s2`) | `baseline` until approval, then `s2` | |
| `S2_PAPER_BALANCE` | `0` | `0` | B1 stays off |
| `GOOGLE_API_KEY` | **unset** | secret | real mode only |
| `KPMG_GEMINI_DEDICATED_FREE` | **unset** | `true` | real mode only; confirms a dedicated free-tier project |
| `KPMG_ASSET_FETCH` | unset | path to the authorized fetch script | see §5 |
| *(fetch credential, name set by the fetch script)* | unset | secret | read-only; never logged |
| `KPMG_ORIGIN` | unset | only for a custom domain | otherwise `RENDER_EXTERNAL_URL` is used |
| `KPMG_GEMINI_SMOKE` | unset | `1` only during the approved smoke test | requires S2 |

Render supplies `RENDER=true`, `PORT`, `RENDER_EXTERNAL_URL` and `RENDER_GIT_COMMIT`.

### Cost

| Item | Price |
|---|---|
| Standard web service | $25/month, prorated by the second |
| 1 GB persistent disk | $0.25/month, prorated |
| **Continuous total** | **$25.25/month** |
| A 2-hour fixture check, then suspended | about $0.07 of compute; the disk is billed until the service is deleted |

Starter (512 MB) cannot run even the fixture (about 0.68 GB private memory measured). The free
plan cannot attach a disk, and `server.py` refuses to start without one on Render. If Linux
profiling of the real index exceeds about 1.8 GB, the next plan is Pro (2 CPU / 4 GB, $85/month).
Build minutes come from the workspace allowance; check it before the first build.

### Rollback

| Level | Action |
|---|---|
| 1 | `S2_PAPER_BALANCE=0` (already default) |
| 2 | `RESEARCH_ENGINE=baseline`, then restart |
| 3 | Render → service → **Events / Deploys → Rollback** to the previous deploy |
| 4 | **Suspend** the service: stops compute billing and access; disk data is kept |
| 5 | Delete the service only after exporting anything needed: this permanently deletes the disk |

The disk means each deploy has a short downtime (no zero-downtime deploys).

## 5. Asset download interface (for Desktop Codex; not implemented here)

`build.sh` (real mode) runs `python -B "$KPMG_ASSET_FETCH" --dest .kpmg-onboarding/assets` from
the repository root, after the pinned dependencies are installed. Then it requires every
`"source": "release"` file of `onboarding/assets.json` to be present, and `setup.py` re-verifies
size and SHA-256 of all files before staging. Proposed contract for the fetch script:

1. Non-interactive. No `gh` CLI, browser or prompt. The credential is read from a Render secret
   environment variable (a fine-grained, read-only token limited to the approved private asset
   repository), and the repository and tag are taken from `assets.json` or a variable.
2. Writes each release file to `<dest>/<path from assets.json>`, for example
   `demo-100/parents.jsonl`, verifying size and SHA-256 before an atomic rename.
3. Never prints the credential or download URLs containing it; exits non-zero on any failure.
4. Downloads only the cleared runtime files; nothing from fresh-v4 or evaluation outputs.

Open question for Codex: `assets.json` marks **three** files as release-sourced
(`demo-100/parents.jsonl`, `views.json`, `vectors.npy`); the desktop handoff referred to **four**
withheld index files. Confirm the exact set.

## 6. Existing Render service

No Render service ID, `onrender.com` URL or dashboard link appears in any branch of the
repository. `experiments/render-staging/README.md` states that no Render deployment was verified,
and its `render.yaml` describes an image-backed service that pulls a private GHCR image. I have no
Render account access and made no attempt to reach one. **If a service already exists**, check in
the dashboard whether it is image-backed. This plan needs a Git-backed Python service, so creating
a new service is the reliable path. Do not repurpose an image-backed service without confirming in
its settings that the runtime can be changed.

## 7. Remaining blockers

| # | Blocker | Owner |
|---|---|---|
| 1 | Push `deploy/render-native` so Render can see it (it is local only) | you |
| 2 | Approval to create the billable Standard service and disk | you |
| 3 | Data-owner clearance for the exact demo-100 corpus (redistribution basis for hosting) | project data owner |
| 4 | Non-interactive authorized asset download per §5 | Desktop Codex |
| 5 | Dedicated free-tier Gemini project and key, then the approved smoke test: 3 S2 questions, ≥ 61 s apart, hard cap 10 | you |
| 6 | Linux memory with the real index on Render (Standard headroom about 0.8 GB over the Windows record) | after 3–4 |

## 8. Shortest path to a working hosted prototype

1. Push `deploy/render-native`. *(you approve)*
2. Create the Render service with §4 in **fixture** mode, `RESEARCH_ENGINE=baseline`. Watch the
   build log, the "SYNTHETIC FIXTURE preview ready" line, `/healthz`, and the memory graph. Sign in,
   ask *What does the test fixture contain?*, save and review a brief, restart, reopen it. Repeat
   with `RESEARCH_ENGINE=s2`. Then suspend. *(you approve the cost)*
3. When clearance and the fetch script exist: set `KPMG_DEPLOY_MODE=real`, `KPMG_ASSET_FETCH`, the
   fetch credential, `GOOGLE_API_KEY` and `KPMG_GEMINI_DEDICATED_FREE=true`. Deploy with
   `RESEARCH_ENGINE=baseline` and check startup and memory without asking a question.
4. Run the approved Gemini smoke test on S2 (`KPMG_GEMINI_SMOKE=1`). Inspect citations, charts,
   saved work and stage timings.
5. With integration approval, switch the default to `RESEARCH_ENGINE=s2`, keeping B1 off.

## 9. Next action required from you

Approve pushing `deploy/render-native` to GitHub, then decide whether to create the Render
service in fixture mode (step 2, about $0.07 for a short check plus the disk while it exists).
In parallel, forward §5 to Desktop Codex and confirm the three-versus-four withheld-file question.
