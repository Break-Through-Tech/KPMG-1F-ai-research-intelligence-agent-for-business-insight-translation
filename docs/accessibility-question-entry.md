# Question entry and recovery (#140)

This increment extends the existing composer; it does not add conversational
memory, indexed execution, or a research-quality claim. Parent: #136.

## Controls

- **Enter key** selects **Inserts newline** (default) or **Sends question**.
  The selection persists in this browser/origin's local storage. If storage is
  unavailable, a visible notice explains that the preference is tab-only.
- **Ctrl+Enter** or **Command+Enter** sends in either setting.
  **Shift+Enter** always inserts a newline. The visible hint is also associated
  with the question's accessible description. Sending still requires a valid,
  nonempty question, and is blocked while another request is active.
- Composition events, `isComposing`, legacy key code 229, repeated keys, and an
  IME commit-Enter guard prevent keyboard shortcuts from submitting composition.
  Dictation/beforeinput events do not trigger submission. Newline is the safe
  default for voice entry. Actual OS dictation and native IME acceptance remain
  manual gates; synthetic browser events are regression evidence, not that audit.
- Suggestions appear after a returned draft. They **fill the composer only**,
  focus it, and select the term placeholder where applicable. Edit before sending.
  Fixture suggestions include the original question or an explicit term slot;
  their text does not promise contextual execution. Only the existing live
  single-paper mode, with a bound paper identity and accepted recent turns, uses
  “previous answer” suggestions. Saved-result replay remains read-only.
- Busy/loading and failure status is visible and exposed by the existing polite
  status region. A failed turn retains its original question and adds **Retry
  original question**. This deliberately restores that turn's exact question and
  scenario, focuses the composer, and sends once. Editing while a request is busy
  is allowed; completion does not erase a different draft typed meanwhile.
- Configuration/saved-result check failures disable sending, do not silently
  switch to fixture execution, and offer **Retry loading question entry** without
  reloading the page or discarding the draft. Successful retry focuses entry.

## Mode boundaries and integration handoff

The `/api/demo` and `/api/research` payload contracts and server are unchanged.
Existing bounded successful-turn history and `paper_changed` recovery remain in
place. Retry after a paper change uses the server's new identity and cleared
history, not stale conversational context. Outputs, source provenance, partial
and abstention states, and pending/unapproved review status are unchanged.

#130's indexed adapter is not present on this change's base (`ffb3027`). It must
wire its own explicit mode label/endpoint and use self-contained suggestions for
independent queries. Do not infer contextual capability from the chat-like layout,
from a saved answer, or from this composer. Indexed live integration is outstanding,
not delivered by the mocked live-paper browser tests here. #145 owns the combined
manual accessibility audit after sibling PR integration.

## Reproduce focused verification

Use Python 3.10+ (verified with 3.12), Node.js, Playwright, and installed Chrome.
No model, index, provider credentials, or paid service is used by these checks.

```sh
# Terminal 1: use an unused issue-specific port
python3.12 -m src.research_demo --port 8840

# Terminal 2, from repository root
python3.12 -m unittest tests.test_research_demo tests.test_research_contracts -q
# Optional existing single-paper regressions require jsonschema:
uv run --python python3.12 --with jsonschema python -m unittest \
  tests.test_research_demo tests.test_research_contracts tests.test_research_chat -q
node --check ui/app.js

# Use an existing Playwright installation, or an isolated temporary installation:
npm install --prefix /tmp/kpmg140-browser playwright
NODE_PATH=/tmp/kpmg140-browser/node_modules \
RESEARCH_UI_URL=http://127.0.0.1:8840 node --test tests/ui_question_entry.cjs
```

The script defaults to installed Chrome (`PLAYWRIGHT_CHANNEL` can override the
channel). It does not start/stop another session's server. Browser tests intercept
live-paper responses with synthetic fixtures; they do not call a model. The
provider-error example is explicitly simulated. A transport-abort check intentionally
causes a browser network diagnostic; runtime JavaScript errors are checked separately.

## Evidence and remaining gates (2026-10-23)

- 41 existing Python adapter/contract/single-paper tests passed (with jsonschema
  supplied in an isolated uv environment). Syntax and whitespace checks passed.
- 12 Chrome browser regressions passed: newline/send preferences and persistence,
  both alternate send shortcuts, composition/legacy/commit-Enter event guards,
  fill-only editable suggestions, HTTP/network/simulated-provider failures,
  retry focus/original payload, duplicate request blocking, draft retention while
  busy, storage denial, configuration retries, paper-identity recovery,
  read-only replay, and 320px keyboard retry reachability/no horizontal overflow.
- Visual inspection: 1440×1000 desktop and 375×900 mobile fixture success and
  failure states. Mobile document width equals viewport width. No JavaScript
  runtime errors or console warnings/errors on the successful fixture walkthrough;
  no framework error overlay. Screenshots are local QA artifacts, not evidence of
  screen-reader announcements, native dictation, source truth, or semantic quality.
- Pending: manual VoiceOver, real OS dictation, native Japanese/Chinese IME across
  Safari/Chrome, browser zoom, integrated sibling changes, #130 real-index flow,
  and stakeholder/semantic acceptance. No WCAG conformance claim, merge, or deployment.
