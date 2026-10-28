# Research desk: liveness and UI improvements

**Implementation handoff for Alesha · 2026-10-28**  
**Status:** proposed design, not implemented or accepted.  
**Source baseline:** `ae8df58d0b7627d107be4b44611aa277facca0cb` (current `main` at inspection).

## 1. Problem and intended outcome

A reader should immediately understand whether a question will run a model,
whether their submitted request is still being handled, and what they can do
when it fails. Today the distinction between the live research workflow and
prepared examples is easy to miss. Long requests show a single loading message,
which cannot distinguish useful work from a lost connection.

Design for a quiet research desk: one question composer, one primary action,
one compact run-status block. Keep evidence inspection and the existing reading
preferences; do not turn the page into an infrastructure dashboard.

Success means users can answer these questions without opening developer tools:

1. Is this live research, a prepared example, or a saved answer?
2. Did the server accept my question?
3. What stage has the server actually reported, and when was it last heard from?
4. Is it waiting for me, still processing, complete, or unable to continue?
5. Can I recover without losing my question or accidentally starting another run?

## 2. Current behavior and implementation anchors

These observations are source-based, not a browser usability acceptance report.

| Area | Current behavior | Source |
| --- | --- | --- |
| Mode detection | `/api/config` reports live/indexed/clarification capabilities; the UI adjusts labels after initialization | `src/research_demo.py`, `ui/app.js` |
| Request transport | One `POST /api/research` waits for the complete response | `ui/app.js`, `DemoHandler.do_POST` |
| Busy state | `setQuestionBusy()` guards submissions; answer turn and feedback show a general loading message | `ui/app.js` |
| Long wait | Indexed request timeout is 1,560,000 ms, plus 300,000 ms when plain-language generation is enabled; this is a browser ceiling, not a promised duration | `ui/app.js` |
| Concurrency | Threaded HTTP server, with a nonblocking research lock and HTTP 409 while another synthesis holds it | `src/research_demo.py` |
| Model adapter | Selected Codex CLI runs synchronously via `subprocess.run`; startup checks are not continuous model-health probes | `src/codex_generation.py` |
| Pipeline | Explicit context interpretation, clarification, retrieval, synthesis, business translation, validation and optional plain-language work can take different paths | `src/indexed_research.py`, `src/indexed_clarification.py`, `src/research_pipeline.py`, `src/plain_language.py` |
| Reading and evidence | Citation preview/source rail, saved briefs, themes, text size, spacing, plain-language view and read-aloud already exist | `ui/index.html`, supporting UI scripts |

The inspected rehearsal used a local index and cloud-backed `gpt-6.1-sol` via an
existing ChatGPT login. This is a configuration example, not a value to hardcode.
Local app hosting does **not** mean local model inference. No new model call is
required merely to load the page or check status.

## 3. Information hierarchy and proposed layout

```text
1F / Research desk                         Saved briefs   Preferences
Live research · Local index · Cloud model

[Question and prior answers; citations stay attached to their claims]

Researching your question                         Elapsed 01:24
Writing supported findings
Server checked in 2 seconds ago

Research question
[What would you like to research?                          ]
                                               [Research]
Your question runs research automatically. Answers remain drafts.
```

The running block belongs to its answer turn, not a global toast. Keep it visible
near the current composer without forcing scroll away from earlier evidence.
An elapsed timer measures time since submission, never percent complete or ETA.
When the stage has not been reported, say **“Waiting for a server update”**, not
“Writing findings.” No timer-driven fake stage progression.

### Mode labels and entry

| Mode | Persistent visible label | Primary action | Supporting explanation |
| --- | --- | --- | --- |
| Indexed live | Live research · Local index | Research | Submitting searches indexed sources and runs the configured model automatically. |
| Single paper live | Live research · Loaded paper | Ask paper | Answers use the loaded paper, not a corpus-wide search. |
| Fixture | Prepared example · No model run | View example | Your typed question is not executed. |
| Saved result | Saved answer · No model run | Open saved brief, where available | Opening an answer does not run research. |
| Configuration unknown | Checking research availability | Disabled until resolved | Do not show a live/ready claim before configuration succeeds. |

Expose model location as “Cloud model,” “Local model,” or “Model location not
reported,” derived from explicit provider metadata. Put the configured model
name and run identifier in **Run details**, not the main heading. “Configured”
must not be relabeled “Model online”: a saved login or startup check cannot prove
the next request will succeed. Hide fixture controls in live modes.

### Other UI improvements

- Keep a single question field. Use a visible **Research question** label;
  placeholder text is an example, not the only label.
- Preserve the single-prompt business-context flow. Use explicitly supplied
  context; if necessary, ask one focused clarification. Do not invent an industry
  or add mandatory audience/industry fields to every query.
- Consolidate reading/research preferences under one predictable disclosure,
  retaining all existing settings and keyboard shortcut guidance.
- Separate **Research findings**, **Business implications**, and **Assumptions
  and limitations**. Do not give generated interpretation the styling of source
  evidence. Keep “Draft · Human review pending” attached to each result.
- Keep citation inspection in context and preserve the source rail's existing
  focus-return behavior. Hide secondary diagnostics under Run details.
- Show “Answer ready; plain-language version still preparing” if a validated
  technical result is available before the optional rewrite finishes. A rewrite
  failure must not erase the validated original or imply meaning-review approval.
- During work, retain the submitted question and allow drafting the next one;
  prevent a second submission. Preserve existing retry snapshots rather than
  retrying whatever happens to be in the composer now.

## 4. Liveness: distinguish three different signals

1. **Browser waiting:** elapsed time and local activity. Proves only that the
   page is still waiting.
2. **Server reachable:** a recent status response. Proves the server can answer
   status requests, not that a model is generating tokens.
3. **Observed run progress:** a stage change emitted by the executing backend.
   Proves that boundary was reached, not semantic correctness or future success.

Do not expose “Model thinking” or a green “Model alive” dot based on a heartbeat.
While a synchronous provider call is pending, show **“Waiting for model response”**
and separately show server freshness. No token stream or chain-of-thought display
is needed. Publish only validated final content, never unvalidated partial claims.

### Run states and copy

| State | Visible message | Behavior |
| --- | --- | --- |
| Submitting | Sending your question… | No accepted-run claim until receipt. |
| Accepted | Question received | Assign run identity; prevent duplicate execution. |
| Context/clarification | Checking your question | Only when emitted by that adapter. |
| Needs input | One detail needed | Show existing clarification controls; waiting is not a failure. |
| Retrieval | Searching indexed sources | Use “Reading the loaded paper” on the paper path where appropriate. |
| Generation | Waiting for model response | Optional sublabel identifies findings, implications or rewrite. |
| Validation | Checking response format and supporting quotes | Not “Verifying truth”; quote membership is not entailment. |
| Ready | Draft answer ready | Preserve human-review-pending status. |
| Partial | Findings ready; business implications unavailable | Retain valid findings and explain the missing section. |
| Abstention/empty | Not enough supported evidence to answer | Successful terminal outcome; no fake failed-model badge. |
| Busy rejection | Another request is running | Do not imply this question is queued. |
| Failed | Research could not finish | Specific safe cause and recovery action; retain question. |
| Status stale | No recent server update | Overlay on last known state, not a terminal failure. |
| Unknown run | This run is no longer available | Explain restart/expiry; do not automatically rerun. |

Stages may repeat or be skipped. Emit before/after actual operations, including
pre-retrieval model calls, and identify each generation purpose. Never force a
linear “search → model → validate” narrative onto clarification or rewrite paths.

## 5. Delivery plan and backend contract

### Slice A: useful without backend progress

Ship explicit mode labels, corrected welcome copy, visible pending status,
elapsed time, preserved input, and specific recovery copy. Label all pending work
**“Request in progress; stage updates unavailable.”** This slice must not claim
server heartbeats or observed model progress. Keep the existing POST contract.

### Slice B: accepted runs with polling (recommended)

Use a small bounded run registry and background worker, not an additional model
or a framework migration. Polling is simpler than streaming for this local
threaded server; it supports reload recovery without rendering partial output.
Keep the existing synchronous endpoint compatible until its callers migrate.

Proposed additive routes (not existing APIs):

- `POST /api/research/runs`: existing validated request fields plus a client
  submission key. Validate origin, size, context and ownership before accepting.
  Reserve the existing research slot atomically, then return HTTP 202 and a
  server-generated opaque `run_id`. A busy rejection returns 409, not “queued.”
- `GET /api/research/runs/{run_id}`: authorized status snapshot. Poll every two
  seconds while visible, back off to ten seconds while hidden, and stop on
  terminal state. Status reads must not acquire the research execution lock.
- Return terminal results using the existing result envelope and validation
  rules. Keep the run registry lock short; never hold it around generation or
  database work. Worker cleanup releases the research slot in `finally`.

Example minimal status payload:

```json
{
  "run_id": "opaque-server-generated-id",
  "state": "running",
  "stage": "generation",
  "purpose": "research_findings",
  "sequence": 4,
  "elapsed_ms": 84000,
  "stage_elapsed_ms": 62000,
  "server_time": "2026-10-28T20:00:00Z"
}
```

Use monotonic clocks for durations and a monotonically increasing sequence per
run. Browser freshness is measured since the last successful poll, independently
of stage age. Ignore late responses for another run or a lower sequence. A status
snapshot updates liveness even when the stage sequence has not changed.

Keep orchestration status outside research result schemas and fingerprints.
Propagate a bounded status callback through adapters, including optional rewrite
work; do not let a status-rendering failure change research approval semantics.
Use allowlisted stage/error codes, not raw exceptions, prompts, subprocess output,
credentials, filesystem paths or research text in status metadata.

### Ownership, retries and lifecycle

- Bind run reads and submission keys to the initiating browser session and
  active context. For modes without the existing conversation session, add an
  opaque owner capability; a guessed ID or loopback access alone is insufficient.
  Apply existing Host/Origin protections to every new route.
- Within a session, the same submission key and same request return the same run;
  key reuse with changed content is rejected. Reserve keys atomically with the
  execution slot. A lost POST response can then be retried without another model
  call. Keys must not be treated as permanent research history.
- Store only the active run locator/capability in session-scoped browser storage,
  never credentials. On reload, reattach to the owned run; do not resubmit.
  If storage is unavailable, work normally but disclose that reload recovery is
  unavailable. Never attach an old run to a new clarification or revision target.
- Starting values: mark freshness stale after 15 seconds without a successful
  poll; retry status checks with bounded backoff. This is **connection unknown**,
  not **model failed**. Do not start research automatically on reconnection.
- Cap retained run records at 100 and expire terminal records after 30 minutes.
  Never evict active work to make room; reject new work if capacity is exhausted.
  Remove completed in-memory payloads on expiry; saved-brief retention remains
  governed by its existing separate policy. Restart loses in-memory run state.
- Keep existing provider timeouts; define an overall run deadline covering all
  enabled stages before enabling the new route. On deadline, prevent any late
  completion from overwriting terminal state and clean up worker/subprocess work.
  Do not assume the current browser timeout cancels backend computation.
- **No Stop button in the first release.** Closing a tab or aborting fetch does
  not prove the CLI stopped. Real cancellation needs separate subprocess control,
  cleanup and race tests. A future “Stop waiting” must explicitly disclose that
  research may continue; it must not immediately offer a duplicate run.

## 6. Accessibility and responsive behavior

- Reuse semantic controls and existing CSS tokens; do not introduce React or a
  new design system for a vanilla HTML/CSS/JS improvement.
- Announce accepted requests, real stage transitions, clarification, completion
  and errors through a polite status region. Do not announce every heartbeat or
  elapsed second. Keep a stable focus target; no automatic jump on each update.
- Keep actionable failure/clarification text outside an `aria-busy` subtree so
  it can be announced. Preserve existing answer-ready and jump-to-latest behavior.
- Text and icon accompany color. No flashing or indefinite pulsing; respect
  reduced motion. A static activity symbol plus changing elapsed time is enough.
- Wrap status labels at narrow widths; use tabular timer digits and reserve
  status space to avoid layout jumps. Verify 320 CSS px and real 200% browser
  zoom without obscuring composer, source controls or focus indicators.
- Retain all themes, high-contrast variants, text sizing, spacing, read-aloud
  controls and keyboard submission preferences. Use accessible contrast and
  comfortable pointer targets; do not rely on hover for explanations.

## 7. Implementation sequence and acceptance checks

| Increment | Primary files | Acceptance evidence |
| --- | --- | --- |
| A: truthful UI | `ui/index.html`, `ui/app.js`, `ui/styles.css` | Correct fixture/live/saved/unknown copy; elapsed timer; no invented progress; existing entry/citation behavior preserved. |
| B: run lifecycle | `src/research_demo.py`, new bounded run-registry module | Atomic slot/key reservation, owner isolation, safe polling, expiry/restart behavior, lock release on all exits, old endpoint compatibility. |
| C: real stages | Research/clarification/pipeline/provider and presentation adapters | Events match actual execution, including skipped/repeated stages, no-evidence path and optional rewrite failure. |
| D: recovery and QA | UI plus existing HTTP/browser test suites | Reattach, late-response isolation, stale connection, no duplicate model calls, accessible transitions and responsive checks. |

Use deterministic synthetic adapters for transport/state tests; separately run a
small live walkthrough for genuine provider wiring. Record exact revision,
configuration and observed outcomes. Required scenarios:

1. Live supported answer: exactly one accepted execution; observed stages;
   validated draft with usable citations and pending human review.
2. Fixture and saved answer: no model invocation, unmistakable labels.
3. Clarification: input required is visible and announced; resume runs only after
   reply, with existing conversation/context checks preserved.
4. Empty evidence and abstention: accurate terminal outcome; stages skipped when
   work is not performed; no unsupported claims displayed.
5. Provider/validation failure and partial translation/rewrite failure: specific
   recoverable message; preserve only sections accepted by existing contracts.
6. Slow provider with healthy polling, then failed polling: clearly distinguish
   waiting for model response from lost server contact; never fabricate progress.
7. Double click, lost acceptance response, reload and another tab: idempotency,
   ownership and busy behavior prevent duplicate runs or cross-session disclosure.
8. Server restart, retention expiry, deadline and late result: explicit unknown/
   terminal state; no automatic rerun and no stale answer inserted as current.
9. Keyboard-only, reduced motion, high contrast, 320 px and native 200% zoom;
   manual screen-reader check for stage/error announcements without timer spam.

Automated checks do not establish screen-reader usability, semantic entailment,
stakeholder acceptance or production readiness. Record those as separate manual
or unresolved gates. This handoff neither implements the UI nor records Alesha's
approval, and it does not change source, review or publication status.

## 8. Related repository guidance

- [Local research interface](local-research-interface.md)
- [Question entry and recovery](accessibility-question-entry.md)
- [Answer navigation](accessibility-answer-navigation.md)
- [Query clarification](query-clarification.md)
- [Plain-language view](plain-language-view.md)
- [Saved briefs](saved-briefs.md)
- [Research contracts](research-contracts.md)
