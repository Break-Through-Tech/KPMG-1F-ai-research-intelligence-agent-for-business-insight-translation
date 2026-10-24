# Selected-result HTML and Markdown export

Issue #143 under #136. This extends the existing research desk, not its review
workflow. No PDF generation, hosting, sharing permission, or approval changes.

## Use

1. Load an answer in the local research interface.
2. In that answer, activate **Export this result as HTML** or **Markdown**.
   Each answer has its own labeled export region; older answers remain exportable.
3. Check browser downloads. The local status reports a download **request**, not
   proof that the browser saved the file. A failure leaves the answer in place.
4. Open the HTML file locally. Follow its citation links to retained evidence and
   its meaningful original-source links to source locations when available.

The export contains the selected result's actual request question, generated
claims/interpretations and business recommendations, assumptions, limitations,
risks, exact supporting quotes when supplied, source identities/locators, recorded
generation provenance, and pending/unapproved status. It excludes conversation
history, other answers, unrelated source-panel state, and uncited passages for
supported results. Abstentions retain their retrieved context explicitly labeled
as insufficient, or state that no evidence exists. Fixture questions are clearly
identified as fixed examples rather than the user's unexecuted input.

## Fidelity and review boundaries

- Claim-specific supporting quotes are checked against their associated passage
  and citation IDs using the synthesis contract's whitespace-normalized membership
  check. Original quote and passage text are preserved. Missing citations or invalid quotes
  stop export. This is **not** a test of semantic entailment or source truth.
- Text is never interpreted as source HTML. URLs are restricted to HTTP(S).
- HTML is self-contained: language, main landmark, meaningful heading hierarchy,
  citation anchors, readable reflow, and native MathML for supported formulas.
  Exact original quote notation is retained alongside rendered source math.
- Markdown escapes source markup and preserves literal notation. Reader support
  for anchor HTML, MathML, and structured tables varies; it is not an equivalent
  accessible math/table reading surface to standalone HTML.
- Only retained structure can be exported. #142 owns extraction and its sanitized
  `structuredSource(passage.reader)` renderer. The exporter uses it when present,
  preserving source table cells/headers and MathML without rebuilding structure.
  On standalone main before #142, retained structure is explicitly labeled
  unavailable and citation-check text remains available. **Integration gate:**
  after #142 lands, verify its renderer loads before export and exercise genuine
  source table/header and MathML navigation in exported artifacts.
- The pending draft contract remains unchanged. No review decision is recorded,
  no approval is copied, and no regulatory source IDs are folded into paper
  evidence. This is a reading artifact, **not a sealed review-packet replacement**.
  #124 continues to own review decisions, stale fingerprint validation, and the
  regulatory review handoff. Export does not certify a fingerprint or reviewer.

## Reproducible verification

Use Python 3.12 with the repository requirements installed:

```sh
python -m unittest tests.test_research_demo tests.test_research_contracts tests.test_research_review -q
python -m src.research_demo --port 8843
```

With Playwright and its Chromium installed in your local tooling (no repository
dependency change), in another terminal:

```sh
EXPORT_ARTIFACT_DIR=/tmp/kpmg143-export-qa node scripts/check_answer_exports.cjs
```

If Playwright is outside the default module path, set `NODE_PATH` to that tooling's
`node_modules`. `EXPORT_TEST_URL` can select another loopback test server.

The browser check covers keyboard-initiated downloads from an older selected
answer, retained focus and feedback, full/partial/insufficient/empty states,
pending status, source locators, citation anchors, exact-quote validation, exclusion
of other history/evidence, inert source markup, rejected unsafe links, standalone
MathML with literal quote notation, failure recovery, page errors, and narrow
reflow. Optional artifacts include HTML/Markdown for all four states and desktop/
narrow screenshots. These are **synthetic fixture** checks, not real model or
human acceptance evidence.

### Remaining manual/integration acceptance

- [ ] Screen-reader inspection of standalone supported, partial and abstaining
  HTML: navigate headings, read review state/limitations, follow citation/source
  links and return, inspect math pronunciation and table relationships.
- [ ] #142 integrated structured source tables, headings, figure descriptions,
  extraction gaps and MathML survive export; original citation-check text remains.
- [ ] Manual browser zoom, Safari/VoiceOver and live/saved real-paper workflow.
- [ ] #124 reviewer walkthrough confirms the reading artifact is not mistaken
  for review approval, a sealed packet, or independent source verification.

Automated DOM/browser checks do not establish WCAG conformance, manual VoiceOver
acceptance, semantic support, source certification, or stakeholder acceptance.

## Local verification receipt (2026-10-23)

- Full repository pytest: **376 passed, 1 skipped, 365 subtests passed** using
  the existing dependency-equipped Python 3.12 tooling environment.
- Focused demo/contracts/review unittest run: **41 passed**.
- Chromium: keyboard HTML/Markdown downloads, four fixture states, invalid
  citation/quote failure, selection/history isolation, safe rendering, MathML,
  local citation jumps and 360px app/320px artifact reflow passed.
- Screenshots and exported artifacts were inspected under
  `/tmp/kpmg143-export-qa` (local, not committed, hosted, or publicly shared).
- No manual screen-reader, Safari, browser-zoom or live model acceptance claimed.

### Local review follow-up (2026-10-23)

- Repeated full Python suite: **376 passed, 1 skipped, 365 subtests passed**.
- Fixed a reproduced omission: source extraction limitations now survive HTML
  and Markdown export even when the optional structured reader is unavailable
  or declines the structure. The browser regression failed before and passed
  after the fix; the existing selection/download checks still pass.
- Supplemental browser contract check with #142's reader at `aa2ff04` preserved
  one semantic table, its header associations, one MathML formula, two figure
  containers, canonical passage text, exact support quote and extraction gaps.
  This explicitly injected-reader fixture check does **not** establish merged
  script ordering, final dependency integration, or screen-reader acceptance.
- The second actual local ClawSweeper review identified export rejection of
  whitespace-normalized quotes already accepted by synthesis. Reproduced that
  failure, aligned membership normalization with Python (including Unicode
  whitespace), and retained original quote/passage text in HTML and Markdown.
  The new browser regression failed before and passed after the correction.
