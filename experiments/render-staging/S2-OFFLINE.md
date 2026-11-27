# Offline S2 integration

The Render preview defaults to Baseline. Select the S2 demo candidate with
`RESEARCH_ENGINE=s2`. B1 remains off unless `S2_PAPER_BALANCE=1` is also set.
Unknown values fail startup. The preview continues to reject business and
regulatory requests. The reusable S2 constructor installs the existing
regulatory assessor for callers with those features enabled.

S2 takes the bundle and model directories from the verified image snapshot.
Its ranked and bounded retrieval use one loaded encoder and reranker pair.
Use the existing preview authentication, same-origin checks, generation quota,
research lock and SQLite brief store. An authenticated config response seeds
a signed browser cookie for S2 checkpoint identity. Serving requests without
an identity directly through the wrapper fails closed. The cookie uses
SameSite Strict, HttpOnly and Secure on HTTPS. Checkpoints live under the
private persistent state directory. Review approval continues through saved
work and remains separate from engine output. The shared preview library
continues to be shared and the cookie does not constitute a reviewer account.

## Offline checks

- From this folder, run `python -m unittest test_engine_runtime test_deploy`.
  The first module needs only the standard library. The second uses the
  application dependencies and fake providers.
- From retrieval-v3, run
  `python -m unittest test_s2_paper_balance.PaperResolution test_s2_paper_balance.Selection test_s2_paper_balance.EngineFlag`.
  The B1 classes shown here use synthetic fixtures. Run test_s3 separately with the historical suites. Some S3 cases use local
  replay data. Run the complete historical suites on the evaluation machine
  with the assets listed in CODEX-CHECKPOINT-REPORT.md.
- Windows Python 3.11.9 compiled the integration and engine modules and ran
  three portable wrapper tests. Python 3.14 ran six preview quota/schema
  tests and ten synthetic B1 regressions. With the pinned local assets, S2
  initialized in 34.73 seconds and reached a peak process working set of
  1,204,580,352 bytes. A fake synthesis timeout failed closed, retry in the
  original session succeeded, and a second session created its own marker.
  This measures the engine process on Windows. Linux startup, memory and
  proxy deadlines remain to be measured.
- The fetched UI checkpoint at 11ae22d passed JavaScript syntax checking.
  Its optional summary fields and indexed deadlines were reviewed in source.
  The separate local follow-up below records browser verification. A combined
  Linux container run still requires an approved local Linux runner. The current stage.py intentionally requires the
  separately approved design candidate. Preserve that integrity check.

## Proposed provider smoke test for a later approval

Use a local private staging context built with the documented stage.py
command, an approved dedicated Gemini project, and a new private state
directory. Verify the image and fake-provider browser run first. Configure
the existing environment secrets outside the command line. The following
commands are a proposed local preview procedure, with browser requests
authenticated through the existing Basic challenge.

```sh
export RESEARCH_ENGINE=s2 S2_PAPER_BALANCE=0 KPMG_GEMINI_SMOKE=1 PORT=8821
export KPMG_ORIGIN=http://127.0.0.1:8821
python -B experiments/render-staging/server.py
```

Open the preview at that origin and submit exactly three approved public-paper
questions, serially, using the same authenticated browser session. Retrieve
/api/config first so the session cookie exists before the first POST. The
equivalent client sequence for each question is a same-origin JSON POST to
/api/research with query, context_id from /api/config, and
interpret_context set to false. Allow at most two stages per question and
avoid automatic retries. Smoke mode enforces a lifetime cap of ten reservations
in gemini-smoke-attempts.sqlite3, including failed attempts. The existing
minute and day limits also apply. Reuse the same private state directory
and ledger for every restart or retry of this approved campaign. Never
delete or rotate the ledger mid-campaign. Inspect structured output,
grounding, pending review status, provider errors, token usage and individual
stage durations against the 60-second provider timeout. Stop on the first
quota, timeout or schema failure. These commands were not run with Gemini.

## Remaining Linux and browser verification

Use an authorized Linux AMD64 machine with Docker Engine or an equivalent
local Docker-compatible runner. It needs local access to the pinned demo-100
bundle, matching table audit, both pinned MiniLM snapshots, and the approved
UI checkout. Use the existing KPMG-ui-refresh worktree, whose candidate
ui-consult/design/merge-with-codex/{app.js,consult.css,index.html,mock-api.js,serve.py}
matches the hash prefixes in stage.py, with its surrounding UI assets. A replacement candidate needs explicit approval
and a new recorded hash. Keep the original staging integrity checks active.

Build the private staged context using the README commands. Run the image
with scripted synthesis and review and record startup and research peaks
from the Linux cgroup memory.peak counter. Run the browser suite locally
with an installed Chromium and Playwright using the command in smoke.cjs.
Use a fresh fake-provider state directory for each engine. Run Baseline
first, then Standard S2 with RESEARCH_ENGINE=s2 and S2_PAPER_BALANCE=0.

## Offline verification results

Windows Python 3.11.9 installed all pinned requirements and CPU Torch 2.15.0.
pip check found no broken dependencies. All 10 preview tests, 18 saved-work
tests, 13 review tests and 21 evidence-table tests passed. The table tests
require the pinned audit supplied from the local evaluation artifacts.
They refused 13 tables without adequate completeness or reconstruction evidence.

The real-index Python 3.11 S2 worker loaded in 38.15 seconds. Its peak working
set was 1,223,995,392 bytes at startup and after the scripted research run.
A scripted timeout recovered in the same session. A different session created
a separate checkpoint. This measurement is for the Windows worker process.

A separate loopback HTTP run started with pinned artifacts. The first S2
request returned a cited answer with approval pending. A second authenticated
client did not receive a result envelope. The diagnostic did not retain that
error payload, and full HTTP session, chart and review coverage remains open.
Repeat with distinct client cookies, paced requests and error-envelope capture
while keeping the configured rate limits. The independent saved-work and
table tests do not substitute for the browser test.

Smoke mode passed the persistent cap test with failed fake-provider calls,
concurrent attempts and restart. Linux build, memory and browser verification
are still required before requesting approval for the Gemini smoke test.

## Local asset and HTTP follow-up

The approved UI candidate is available in the existing KPMG-ui-refresh
worktree under ui-consult/design/merge-with-codex. All five staged candidate
hashes match. The local pinned bundle, matching table audit and both MiniLM
snapshots were verified and produced a 148-file private staging context.
Windows Chrome and bundled Playwright Core 1.57.0 successfully launch
headlessly. No separate browser or UI package is required.

The second HTTP client received status 200 with scenario execution-error,
result null and error code summary_failed. The first answer reserved
62,648 and 67,174 estimated input units. The second request added no
reservation. Its synthesis could not fit in the existing 160,000-unit
rolling minute window. With distinct cookie jars and the same question,
retrying the second client after the window expired returned a cited
answer. The ledger recorded four calls and the two session IDs produced
two separate checkpoint markers. The second client recorded and reopened
a review. The matching audited table endpoint returned 16 rows.

For the later approved Gemini smoke test, space each question at least
61 seconds after the preceding answer completes. Keep the existing rate
limits, hard ten-attempt cap and state ledger active.

No usable WSL2 distribution, Docker Desktop or Podman was found on this
host. Linux image build, startup and memory still need an approved
Docker-compatible Linux AMD64 runner.

Both Windows browser runs passed with the approved candidate and scripted
providers. They covered authentication, exact quote inspection, the full
16-row chart, keyboard cell selection, saved work, human review, and
reopening the saved review after a full server restart. Baseline startup
was 23.24 seconds and its request took 6.55 seconds. S2 startup was 40.23
seconds and its request took 6.37 seconds.
