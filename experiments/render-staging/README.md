# Render preview

## What runs

One Render Web Service runs the existing Python Baseline/B2 pipeline and the Claude consultant UI on one HTTPS origin. The service uses one warm encoder/reranker pair and accepts one research request at a time. The existing brief store uses SQLite on /var/data. The pilot shares one library across the invited reviewers and records the reviewer names they enter. It does not provide individual user accounts or tenant separation. Use public-paper test questions and avoid client-sensitive material.

The UI snapshot has the same research, citation, table, Library, and review views. The staging copy removes mock mode and hides business and regulatory settings. Baseline quality review stays enabled. The endpoint wrapper rejects requests for business and regulatory calls and does not route Multi-Agent or arXiv discovery. The latter can be assessed separately after the live Baseline smoke test.

Team 1J uses the useful deployment pattern of a single FastAPI/Uvicorn app, static web assets, same-origin API calls, server-side environment credentials, local saved-work files, and paired prebuilt corpus/index artifacts. We kept 1F's Python handler and SQLite implementation because they already supply the contracts and review integrity needed here. Team 1J's current source identifies a local launch procedure. No Render deployment was verified.

## Build from approved inputs

1. Use Python 3.11 and point stage.py at the freshest approved Claude checkout, the existing B2 demo-100 bundle, its matching extractor audit, and the exact two local MiniLM model snapshots. Stage into a new folder under this experiment directory. The snapshot records every copied file hash plus each checkout HEAD. Original tracked and uncommitted UI files are read-only inputs.
2. Only the staged directory is the Docker build context. It contains source code, static UI, the pinned existing index, verified table audit and safetensors. It excludes environment files, existing databases, logs, source PDFs, benchmarks, Multi-Agent and model results. Do not send the wider repository or any unapproved corpus to a registry.
3. On an approved Linux AMD64 builder, run the Docker build and perform a local container smoke test. Docker and an active Linux subsystem were unavailable on the Windows test machine. The pinned Linux CPU Torch wheel is available. The Linux image build and Linux runtime memory remain to be validated.

    python -B stage.py --output <new-image-context> --ui <refresh-checkout> --bundle <demo-100-dir> --audit <matching-audit-file> --encoder <encoder-snapshot> --reranker <reranker-snapshot>
    docker build --platform linux/amd64 -t kpmg-research-review <new-image-context>

The existing demo-100 parents SHA-256 is 78d8efd7c9df075be09ffa5f3a9c7ca79c54efa2d7caf75c8f0329ea72ff41aa. The pinned model snapshots used were all-MiniLM-L6-v2 at 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 and ms-marco-MiniLM-L6-v2 at 233902d25c440f23af6f7d6e94d2946bac0bee0a.

## Local verification

The browser test runs the packaged Python server with the actual B2 index, model weights, evidence endpoint, and new SQLite database. It supplies scripted provider responses from a separately reviewed CU-DPO recording. It does not call Gemini. The fixture, test credentials, and test state are outside the image context.

    python -B test_deploy.py
    node smoke.cjs <python> <image-context> <new-empty-state-dir> <playwright-module> <chrome-executable>

The browser smoke passed on the staged image context. Startup took 24.3 seconds and the real retrieval plus scripted generation took 5.78 seconds. It verified signed-out blocking, source links, complete Table 2, keyboard navigation from a chart to a source cell, and a saved brief and review across restart. Six offline unit tests passed.

The resource measurement used the 100-paper bundle on Windows with one compute thread. B2 plus table startup took 29.5 seconds and peaked at 936 MiB. Three eight-passage retrievals took 5.6, 9.5 and 11.0 seconds, peaking at 1,044 MiB. The index is 49 MB and the two staged model directories total 183 MB, decimal. The image context is 234 MB before Python system packages and wheels. No 1,000-paper or parallel load result is implied.

For a live local smoke test, use a new private state directory, the protected loopback origin and the existing Gemini credential through the approved secure loader. Confirm current Free tier status and quota for the selected project first. The first known-answer smoke question is “By how much did the CU-DPO training method improve strategy-selection accuracy, and on how many base models?” It should cite the versioned paper and report 35–46% to 68–78% across seven base models. Do not treat the fixture result as confirmation of a live Gemini answer.

## Deploy only after approval

- Approve the 100-paper asset snapshot for private hosting and select an existing private registry and approved Render workspace. Push the tested image there by digest. No Git push is required for the image-backed service. Only use a registry credential with read access to the approved image.
- Render Dashboard → New → Web Service → Existing Image. Select the pinned private image digest. Use 1 CPU / 2 GB, single instance. Attach 1 GB at /var/data, set health path /healthz, and disable automatic deploys. The render.yaml template records these settings, but a manual image service does not require applying a Blueprint.
- Set KPMG_STATE_DIR to /var/data. Set GOOGLE_API_KEY and a unique KPMG_REVIEW_PASSWORD as Render secrets. The app's Basic username is reviewer. Set KPMG_GEMINI_DEDICATED_FREE=true only after confirming the project's current free limits and exclusive use. Keep the public app password separate from the Gemini key. Render supplies PORT and RENDER_EXTERNAL_URL for the default hostname. Custom domains need a matching canonical KPMG_ORIGIN.
- Verify unauthenticated access returns 401 for the homepage, assets and app APIs. /healthz returns only readiness. Run the CU-DPO question once with a configured free-tier provider, inspect the evidence/chart, reopen the saved brief, record a test review, and confirm persistence across a restart. Check Linux memory before sharing the URL. Keep protected access narrow and rotate the shared preview password when access changes.

The server sets a 60-second SDK timeout per Gemini generation and uses one attempted call per stage. With context/business/risk/arXiv disabled, normal research uses synthesis plus quality review. The browser inherits its longer indexed request deadline. The API's meaningful user-facing wait depends on retrieval and provider time, so measure it on Render. The local limiter reserves attempts and a conservative request-size token estimate before dispatch, with ceilings of 6 RPM, 160,000 estimated input TPM and 60 attempts over 24 hours. Failed calls count and quota history uses the separate preview SQLite disk. This is app-local enforcement and depends on an exclusive free-tier project. An external project's usage is not observable from this counter.

Render lists $25/month for 1 CPU / 2 GB and $0.25/GB-month for disk. The minimum credible candidate for this workload is $25.25/month at continuous uptime, excluding workspace charges or overages. The 512 MB tiers do not fit measured memory and Free lacks a persistent disk. The 2 CPU / 4 GB fallback is $85.25/month with the same 1 GB disk, and should only be considered if Linux profiling shows the 2 GB instance is insufficient.

References: [Team 1J source at inspected revision](https://github.com/Break-Through-Tech/KPMG-1J-ai-research-intelligence-agent-for-business-insight-translation/tree/c67d9b28771c94c4c942c0d21affa73049fbfb55/src/app), [Render Web Services](https://render.com/docs/web-services), [Prebuilt images](https://render.com/docs/deploying-an-image), [Render pricing](https://render.com/pricing), [Persistent disks](https://render.com/docs/disks).


## November 22 frontend handoff

The Render builder now selects the checksum-verified merge-with-codex candidate. It keeps the experimental label and capability gate. The Render wrapper deliberately does not advertise or route Multi-Agent. The export in this snapshot distinguishes the unmodified draft from the decision on its exact saved version and fingerprint. The shared exporter and review database are untouched.

The review preview starts with a fresh SQLite database. Seed only from a separately approved sanitized copy if reviewers need existing briefs. Reviewer names are self-reported under shared preview access. Production review requires authenticated reviewer identities and roles. Hosted Host/Origin behavior and persistence still require a test on the actual service before release.
