# KPMG Baseline demo release-readiness assessment

Decision: ready for a facilitator-led recorded walkthrough. A teammate-run live demo has a clear path but needs one end-to-end smoke test on a second machine before handoff. Keep Multi-Agent off the demo's critical path.

## What works

- The fixture Research Desk starts without a model or API key. It exercises the research response and evidence surface, and can replay a retained pending result. Label fixture and replay sessions as such.
- The B2 launcher exposes a local indexed research route and uses the existing response contract. It accepts an explicit provider factory, an optional local briefs database, and an optional arXiv fallback. The local demo-100 artifacts exist. A standalone local encoder and reranker load succeeded during preflight after an earlier Windows paging-file error.
- The consultant UI couples to a loopback backend through its same-origin allowlisted proxy. In the inspected isolated UI, no-backend requests return an explicit error, and mock UI states require the explicit mock mode. The existing handoff documents recorded citation/table inspection and saved-brief review.
- Model-free verification in this checkout: 60 tests and 35 subtests passed for Research Desk, indexed research, B2 retrieval, and BYOK configuration. This check did not submit live application research or independently verify Chrome behavior.

## What blocks self-service

| Blocker | Minimum action and acceptance check |
|---|---|
| Demo launch depends on desktop-only paths and separate server commands | Publish one reviewed quickstart or local launcher with configurable paths. Bundle manifest, model snapshots and any table audit must pin exact artifacts. Use demo-100 for the review. Run the preflight on a second machine and check that the fixture path still works without the bundle. |
| Historical live consultant integration uses a personal provider. Current BYOK path exists, but the consultant handoff identifies its live UI integration as untested. | Launch the existing Baseline/B2 backend with the explicit approved provider factory. Verify one known-answer query end to end. Treat any Gemini schema rejection as a blocker to the live path, since the experimental simplified schema does not change Baseline. Use recorded mode if the live check fails. Keep risk/regulatory off for the initial smoke test. |
| Complete tables depend on a matching endpoint and audit. Basic passages and source links are a separate verified path. | For the simplest demo, use source-linked citations plus the Evidence Inspector. Show reconstructed charts only if the table endpoint and matching audit are present. Verify one valid source table and one unavailable case; the latter should fall back to source evidence. |
| Initial memory use depends on the machine, and services are local-only | Start one backend before the demo, use an isolated writable brief database, verify available ports and memory, and check the exact URL. Leadership can join a facilitated screen share. A remote deployment or shared database is outside this release. |
| Browser and approval workflows need a rehearsed run | From the actual consultant UI, verify real mode, query submit, source passage and URL, saving/reopening a brief, and human review. Also exercise timeout/partial and unknown-billing behavior with a fixture. Confirm that the UI clearly labels recorded and unapproved results. Do not connect a live provider during rehearsal unless explicitly approved. |

## UI integration boundary

automated reviewer owns the isolated consultant UI and proxy. The backend hands off the existing loopback endpoint, configuration/result and library contracts, a disposable brief store, and mode identification. Keep the two checkpoints separate. Pair one known-answer browser smoke run with automated reviewer’s pinned checkout before a release tag or leadership session.

Baseline/B2 remains the demo default. Keep the paired comparison results separate from product readiness. A favorable experimental result cannot substitute for a live browser smoke test, and a failed experiment does not invalidate the recorded Baseline demo.

## Minimal handoff sequence for the remaining days

1. Rehearse the zero-provider Research Desk via `python -m src.research_demo --no-library --port 8765` on a free loopback port. For the consultant layout, use the existing recorded backend and proxy instructions in automated reviewer’s handoff. Label the session as recorded where applicable.
2. Give teammates the versioned demo-100 bundle manifest and local model paths. Run `python -m src.experimental.demo --bundle <bundle> --encoder <encoder> --reranker <reranker> --check-only` before loading credentials.
3. Use the same launcher without `--check-only`, with `--generator-factory src.generation:create_generate`, a free port, a disposable `--library` path and an explicitly approved provider configuration. Leave automatic arXiv fallback and risk assessment out of the first live smoke test. Point automated reviewer’s proxy at that loopback URL. If a fresh answer cannot be verified, use the recorded path for the leadership session.
4. File one smoke record with commit identity, browser mode, source link, save/reopen and review outcomes, measured cold startup and answer times, and the result of the failure-state rehearsal. Ship the recorded route even if live access remains environment-dependent.

The isolated automated reviewer proxy suite passed eight model-free tests against temporary loopback servers. The fake server emitted a connection-aborted message during its late-write timeout test, but all assertions passed. No automated reviewer checkout files were edited.
