# Deployment readiness: native Python on Render (single origin)

**Date:** 2026-11-26. **Branch:** `deploy/render-native`, based on `integration/team-onboarding`
at `5bfa2d6cd9da7b0ea41d6e89e142b718a8ddcd63`.
**Status:** ready for a synthetic-fixture hosting check, and for real mode once the three index
files are on the persistent disk (or at an approved HTTPS location). Nothing has been deployed, no
Render service was created, and no provider was called.

## 1. Commits reviewed

| Ref | Commit |
|---|---|
| `integration/team-onboarding` (base) | `5bfa2d6cd9da7b0ea41d6e89e142b718a8ddcd63` |
| `integration/s2-offline` | `5bae206b28e20a3926b6dcc44e88ddec6480c36f` |
| `checkpoint/s2-engine-b1` (frozen engine) | `7bf2d3671dbef8e0733da90cee434107f919cb0f` |
| `main` | `8274afedeba8e516a7854ea41433140cfcb9e932` |

## 2. How it works

One Render **web service, native Python 3.11.9**, serving the approved UI and the API from one
HTTPS origin, as `experiments/render-staging/server.py` was designed (same-origin `/api/*`,
Basic auth, Host and Origin checks).

| Mode | Build (`bash deploy/render/build.sh`) | Start (`python -B deploy/render/start.py`) |
|---|---|---|
| `fixture` | pinned install; `setup.py --prepare-only --fixture` stages the synthetic index | same handler, auth, quotas, saved work and disk; scripted responses; no provider |
| `real`, disk | pinned install; public models and checked-in metadata fetched and verified | copies the three files from `$KPMG_STATE_DIR/assets/demo-100/` (or `KPMG_ASSET_DIR`), `setup.py --prepare-only` verifies size and SHA-256 and stages, then the unchanged `server.py` runs |
| `real`, download | pinned install; `onboarding/fetch_demo100.py` (`KPMG_ARTIFACT_BASE_URL`, optional `KPMG_ARTIFACT_TOKEN`); `setup.py --prepare-only` stages | the unchanged `server.py` runs on the staged snapshot |

State on the disk at `/var/data`: `briefs.sqlite3`, `provider-usage.sqlite3`, `s2-checkpoints/`, and
in disk mode `assets/demo-100/{parents.jsonl,views.json,vectors.npy}`.

### The three index files

| File | Bytes | SHA-256 |
|---|---|---|
| `parents.jsonl` | 21,731,899 | `78d8efd7c9df075be09ffa5f3a9c7ca79c54efa2d7caf75c8f0329ea72ff41aa` |
| `views.json` | 10,373,981 | `c6c1563ee6888887d354ec6a27e61de4b931f534f9142fbab2e94a30ad5ec5d3` |
| `vectors.npy` | 16,942,208 | `50468962cff785b71c4de72f9e7436b656bcf30d8df801b2681473873d23bd14` |
| **Total** | **49,048,088** | |

### Files in `deploy/render/` (nothing else in the repository changed)

| File | Purpose |
|---|---|
| `build.sh` | Render build command: mode and Python 3.11.9 guards, pinned install, Git-commit fallback, then one of the three build paths above |
| `start.py` | Render start command: runs only a verified staged context; disk-mode staging at startup; hosted fixture mode |
| `render.yaml` | Optional Blueprint mirroring §4; not applied |
| `test_hosted_fixture.py` | Offline end-to-end hosting test |
| `DEPLOYMENT-READINESS.md` | This report |

Reused unchanged: frozen S2 engine and seals, `engine_runtime.py`, `server.py`, `stage.py`,
`onboarding/setup.py`, `onboarding/fetch_demo100.py`, the Python 3.11 lock, the approved UI, the
SQLite brief store and the audited table endpoint. Baseline is the default, S2 is opt-in and B1 is
off; business and regulatory analysis stay refused.

## 3. Verification (local, Windows, Python 3.11.9, scripted providers only)

| Check | Result |
|---|---|
| Fixture build | **pass**: 150 allowlisted files staged and verified (185,168,611 bytes) |
| `test_hosted_fixture.py --engine baseline` | **pass**, 21 checks |
| `test_hosted_fixture.py --engine s2` | **pass**, 22 checks; S2 confirmed by `generation_method=consolidated-v2-standard` |
| Checks covered | public `/healthz`; 401 without or with wrong password; 403 for wrong Host, cross-site fetch and a write without the same Origin; approved UI with mock API removed; KaTeX; cited answer pointing at retrieved evidence; review pending; no claims for an unscripted question; brief saved and reviewed; SQLite in `KPMG_STATE_DIR`; brief and review survive restart |
| Real build, disk mode | **pass**: models and metadata verified, nothing staged, exit 0 |
| Real build, unreachable or non-HTTPS artifact URL | **refuses** with the downloader's message |
| Real start, disk files absent | **refuses**, naming the three files and the path |
| Real start, wrong bytes on disk | **refuses** (`setup.py` checksum mismatch); the copied cache is removed and no context is staged |
| Other fail-closed paths | missing mode; HTTP origin on Render; short password; state not a mounted disk; smoke flag in fixture; B1 without S2; unknown engine |
| Git fallback (Linux shell) | answers only `rev-parse HEAD` / `--short HEAD` from `RENDER_GIT_COMMIT`; refuses otherwise |
| Onboarding tests | 15 OK (includes the downloader tests) |
| Staging tests | `test_engine_runtime test_deploy` 10 OK |
| Frozen seals | `seal_s3.py`, `b1-freeze`, fresh-v3 `seal_v3.py`: **verified** |
| Peak memory, fixture | about 600 MiB working set / 675 MiB private (Baseline and S2) |
| Peak memory, real index | about 1.2 GB on Windows (desktop record); Linux to be read from Render's metrics |

**Not run here:** a successful real-index start (the three files are not on this machine) and a
successful download (no approved storage URL yet). The fixture verifies hosting only; it is not
research validation.

## 4. Render settings

| Setting | Value |
|---|---|
| Service type | Web Service, Language **Python 3** |
| Repository / branch | this repository / `deploy/render-native` |
| Root directory | blank |
| Build command | `bash deploy/render/build.sh` |
| Start command | `python -B deploy/render/start.py` |
| Instance type | **Standard** (1 CPU, 2 GB), 1 instance |
| Health check path | `/healthz` |
| Auto-deploy | Off |
| Disk | `kpmg-preview-state`, mount `/var/data`, 1 GB |

| Variable | Fixture | Real (disk) | Real (download) |
|---|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | `3.11.9` | `3.11.9` |
| `KPMG_DEPLOY_MODE` | `fixture` | `real` | `real` |
| `KPMG_STATE_DIR` | `/var/data` | `/var/data` | `/var/data` |
| `KPMG_REVIEW_PASSWORD` | ≥ 24 printable ASCII, secret | same | same |
| `RESEARCH_ENGINE` | `baseline` | `baseline` until approval | same |
| `S2_PAPER_BALANCE` | `0` | `0` | `0` |
| `GOOGLE_API_KEY` | unset | secret | secret |
| `KPMG_GEMINI_DEDICATED_FREE` | unset | `true` | `true` |
| `KPMG_ARTIFACT_BASE_URL` | unset | **unset** | approved HTTPS directory |
| `KPMG_ARTIFACT_TOKEN` | unset | unset | optional secret |
| `KPMG_ASSET_DIR` | unset | optional (default `/var/data/assets`) | unset |

Cost: Standard $25/month plus 1 GB disk $0.25/month, prorated by the second ($25.25/month if left
running). Rollback: `RESEARCH_ENGINE=baseline`; Render **Rollback** to a previous deploy;
**Suspend** to stop compute billing while keeping the disk. Deleting the service deletes the disk.

## 5. Existing Render service

No Render service ID or URL appears in any branch, and the older `experiments/render-staging/render.yaml`
describes an image-backed service. A new Git-backed Python service is the path used here.

## 6. Remaining blockers

1. Your approval to create the billable service.
2. Data-owner clearance before uploading the three files.
3. A dedicated free-tier Gemini key, then the approved smoke test (3 S2 questions, ≥ 61 s apart, cap 10).
