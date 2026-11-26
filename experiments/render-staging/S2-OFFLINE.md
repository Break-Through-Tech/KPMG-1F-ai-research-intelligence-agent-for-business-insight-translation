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
  Browser E2E and a combined container run still require the approved
  hash-pinned UI staging candidate and a local Linux image runner with the
  pinned dependencies. The current stage.py intentionally requires the
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
UI checkout. Provide the UI checkout path or a read-only archive containing
ui-consult/design/merge-with-codex/{app.js,consult.css,index.html,mock-api.js,serve.py}
that matches the hash prefixes in stage.py, plus the tracked UI and shared
assets from that checkout. A replacement candidate needs explicit approval
and a new recorded hash. Keep the original staging integrity checks active.

Build the private staged context using the README commands. Run the image
with scripted synthesis and review and record startup and research peaks
from the Linux cgroup memory.peak counter. Run the browser suite locally
with an installed Chromium and Playwright using the command in smoke.cjs.
Use a fresh fake-provider state directory for each engine. Run Baseline
first, then Standard S2 with RESEARCH_ENGINE=s2 and S2_PAPER_BALANCE=0.
