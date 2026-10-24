# Answer navigation and announcements (#138)

This increment extends the existing research desk. It does not certify WCAG
conformance, source support, model quality, or human approval.

## Behavior

- The conversation is a named region. Each turn is named by its numbered
  question heading; its answer article is named by a numbered answer heading.
  Saved replay and newly requested turns use the same structure.
- Research findings and interpretations have separate level-three headings.
  Business implications are explicitly conditional interpretations. Limitations
  and review status remain in the existing disclosures; the draft's unapproved
  status is also visible beside its answer heading.
- One atomic, polite `status` region announces loading and a concise outcome.
  Answer prose is not a live region. Partial, abstention, no-evidence, simulated
  provider error, transport failure, and paper-change recovery remain distinct.
- Results do not automatically focus or scroll to their answer. The submit
  button remains focused and uses guarded `aria-disabled` while a request runs.
  An explicit **Jump to latest answer** action focuses and scrolls to the latest
  completed answer (including a failed outcome). It works with Enter and Space.
- Citation inspection/open-link names and citation focus lifecycle belong to
  #137. This patch deliberately leaves those functions unchanged.

## Reproduce automated checks

Use Python 3.12 (the CI version) and an isolated local server port:

```sh
python3.12 -m src.research_demo --port 8838
```

In another terminal, with Playwright available in the Node environment:

```sh
RESEARCH_DEMO_URL=http://127.0.0.1:8838 node tests/ui/answer_accessibility.cjs
python3.12 -m unittest tests.test_research_demo tests.test_research_chat tests.test_research_contracts -q
```

The Python tests require `jsonschema` from `requirements.txt`. The standalone
browser check requires `playwright` and its Chromium browser; these are QA-only,
not new application dependencies. An existing external install can be selected
with `NODE_PATH`. Set `QA_SCREENSHOT_DIR` to an existing local directory to also
capture desktop (1280×900) and mobile (390×844) screenshots and exercise mobile
jump/overflow checks. Keep generated screenshots outside the checkout.

The browser check uses actual local fixture endpoints for five outcomes, delays
responses while focus remains on an older heading, checks one loading and one
completion DOM mutation per request, and verifies Enter/Space navigation.
Saved replay and live-mode submission/paper-change recovery are intercepted
synthetic envelopes, **not a model or indexed integration run**. An aborted
request and a synthetic HTTP 409 deliberately produce browser resource errors;
other console warnings/errors and uncaught script errors fail the check.

## Manual VoiceOver walkthrough — acceptance gate still outstanding

**No VoiceOver walkthrough or recording has been performed for this increment.**
Chromium accessibility roles, DOM mutations, and programmatic focus do not prove
spoken announcement timing, absence of duplicate speech, or rotor usability.
The observed automation host is macOS 26.6.2 (25G83), Chromium 156.0.8078.4;
these are not VoiceOver-tested browser/OS combinations.

Before marking #138 complete, record a walkthrough with the actual macOS,
VoiceOver, and browser versions, recording location, date, and tested modes:

1. With VoiceOver enabled in Safari, navigate the initial fixture desk using
   headings/landmarks and ordinary Tab/Shift+Tab. State whether Quick Nav and
   browser keyboard-navigation settings are enabled.
2. Submit a full fixture from both the question field and button. Listen for a
   concise loading/outcome announcement, not the whole answer. Confirm focus
   stays where the user left it. Repeat while reading an older answer.
3. Navigate Question/Answer headings in the rotor. Read findings,
   interpretations, business caveats, limitations disclosures, and review status.
4. Activate Jump to latest answer using Enter and Space. Confirm the numbered
   answer heading is spoken and subsequent navigation continues sensibly.
5. Repeat for partial, abstention, no evidence, simulated provider error, and
   a stopped-server failure. Record actual speech and any duplication or loss.
6. After integrating #137, inspect a cited quote and source/page context, open
   the original link intentionally, dismiss, and return to the initiating
   citation. Check desktop nonmodal and small-screen modal behavior.
7. Repeat saved-result and real single-paper modes when available, then the
   indexed mode from #130. Record which modes actually ran; leave unavailable
   modes untested. Coordinate integrated acceptance with #120 and #145.

Safari/VoiceOver, zoom, actual speech, and real indexed/live-provider acceptance
must remain explicitly unverified until these tests are performed.
