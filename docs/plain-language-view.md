# Plain-language presentation adapter (#141)

## Boundaries and startup

`python3.13 -m src.research_demo --port 9141` starts the loopback fixture UI.
Choose **Demo options → Plain-language · supported definition fixture**, then
**View example**. Use the native **Technical / original** and **Plain language**
radio group (arrow keys switch); expand **Technical term definitions** with
Enter/Space. Citations retain the original source links, quote previews and
source-context inspection. Full draft remains the default fixture.

This is an optional summary-presentation layer, not another execution mode.
Fixture, saved-result and live single-paper modes remain distinct. Live and saved
results explicitly report unavailable plain-language generation; no provider is
called for simplification, no automatic fallback to fixture content occurs, and
no unavailable generation is relabeled as an abstention. Indexed integration
under #130 is outstanding.

## Additive envelope contract v1

The existing `ResearchResult` v1 is **unchanged**, including review/fingerprint,
provenance, evidence, limitations, business implications, assumptions and status.
The UI envelope gets a sibling `plain_language` property, validated by
`src.plain_language.plain_language_view(result, candidate)`:

- `status`: `available`, `unavailable`, or `failed`. Unavailable/failed returns a
  safe `reason` and the UI retains the complete original answer.
- Available requires `version: "1.0"`, `fixture: boolean`,
  `semantic_review: "pending"`, and `result_identity`: SHA-256 of the **entire**
  original validated result serialized as sorted, ASCII-escaped compact JSON
  (see `result_identity`). Any result change makes the presentation stale.
- `claims`: exactly one rewrite for each original summary claim, in original
  order. Each has `claim_index`, nonempty `text`, identical ordered `chunk_ids`,
  and `support: [{chunk_id, quote}]` with literal quotes from every cited passage.
  The UI preserves the original claim kind. Interpretations deliberately remain
  original; the view notice says so. Business actions are not rewritten.
- `definitions`: entries with `term`, and either `status: "supported"`, `text`,
  `chunk_ids`, and literal `support`, or `status: "unavailable"` and `reason`.
  Missing support must be unavailable, not model-memory explanation.
- Missing candidate means unavailable. A provider failure can be represented by
  `{"status":"failed"}`. Malformed, stale, or ungrounded candidates fail closed
  as a presentation failure; do not discard a valid original answer.

All prose is rendered as text (existing delimited-math renderer applies).
Quote membership and identity checks do **not** prove semantic entailment,
readability, equivalent meaning, or that uncertainty was retained. `available`
means structurally available, never approved. Definitions and rewritten claims
remain pending semantic review even when the base result has been inspected.

## Retained side-by-side source-backed development examples

These are **synthetic fixtures, not actual papers or provider outputs**. Source
identity is “Synthetic fixture, not a paper”; example.com locators are synthetic.
Original canonical `normal-v1.json` and `insufficient-v1.json` are untouched.
The added `plain-language-v1.json` explicitly extends the first synthetic source
with a definition sentence; it is a separate demonstration, not discovered
research evidence. Both views expose the exact original passages.

| State | Technical/original | Plain language | Retained source and boundary |
| --- | --- | --- | --- |
| Supported (`plain-language`) | Synthetic agents need task-specific evaluation. | Synthetic agents need to be tested for the specific task. | `synthetic-html-1`, HTML results, https://example.com/fixture#results; source contains the original sentence verbatim. “Need” is not strengthened into demonstrated effectiveness. |
| Supported (`plain-language`) | Synthetic evidence requires human checks. | People need to check synthetic evidence. | `synthetic-pdf-2`, PDF p.2, https://example.com/fixture.pdf#page=2; source contains the original sentence verbatim. No business outcome is claimed. |
| Definition (`plain-language`) | Task-specific evaluation means testing an agent on the particular task it is intended to perform. | Testing an agent on the particular task it is intended to perform. | Literal added definition in `synthetic-html-1`; no extra method or benefit is asserted. |
| Partial (`partial`) | Same two supported claims; no supported business recommendations. | Same two rewrites; still no supported business recommendations. | Original two source passages retained. Business limitation: “Demo partial state: evidence supports the summary, not a business recommendation.” Term definition unavailable because this fixture does not define it. |
| Abstention (`insufficient`) | No supported research claims. | No supported research claims. | Both original passages remain inspectable, but no rewrite is fabricated. “Synthetic passages do not establish the requested business outcome.” Translation stays skipped. |
| Empty (`empty`) | No supported research claims; no evidence. | Same; no claims invented. | No retrieval is not a provider failure. |

Across both views: draft is not approved; synthetic-corpus limitations, conditional
business action, industry caveat, risks and transfer assumptions remain original
under **Details → Assumptions, risks & limitations**. Unavailable definitions are
explicit in the expandable term panel, including in the original view.

### Meaning/uncertainty review, separate from software tests

Author inspection of the synthetic pairs above: rewrites retain the original
obligations without claiming success; partial and abstention pairs add no claims;
the definition shortens an explicitly defining sentence. This is an author
comparison only, **not independent semantic approval**, held-out evaluation,
KPMG acceptance, or validation of live outputs. Reviewers must check every pair
against the original passage, qualifiers, coverage gaps and transfer assumptions.
Semantic review remains pending in the adapter and UI.

## Coordination handoff

- **#123:** use `plain_language_view` only after producing the validated original;
  submit exact claims/quotes and explicit unavailable definitions. Preserve
  modality, negation and disagreement. No generation route is added here.
- **#124:** review the original result and presentation separately. The sibling
  envelope is not part of the original approval fingerprint; **do not interpret
  original approval as approval of the rewrite**. Bind any future presentation
  review to `result_identity` plus the candidate content. This UI cannot approve.
- **#130:** add a validated candidate to the UI envelope only after configured
  provider execution; retain unavailable/failed states. Never call `fixture_view`
  for live or replay results. Current server deliberately marks these unavailable.
- **#145:** integrate these checks with the sibling accessibility changes; no
  manual VoiceOver, Safari, browser-zoom, WCAG conformance or stakeholder acceptance
  is claimed by #141.

## Verification (2026-10-23)

- 45 focused tests pass using existing `/tmp/kpmg138-qa-venv/bin/python`:
  `-m unittest tests.test_plain_language tests.test_research_demo tests.test_research_contracts tests.test_research_chat`.
  Initial default Python 3.9 was incompatible with existing contracts; standalone
  Python 3.13 lacked jsonschema. One initial existing oversized-body HTTP test
  raced a connection reset; the full repeat passed. No dependency files changed.
- `node --check ui/app.js` and `git diff --check` pass.
- Browser plugin not available; Playwright CLI named session `kpmg141` used at
  `http://127.0.0.1:9141/`. Page identity/content checked; no framework overlay or
  relevant console errors. Six fixture states exercised; native radio arrow-key
  switch, definition keyboard expansion, unchanged citation URLs, unchanged
  original source inspection, pending status, limitations and assumptions checked.
- Desktop 1280×900 and mobile 390×844 screenshots inspected. Mobile page width
  does not overflow. Scrolling is required for longer content, as in existing UI.
- Intercepted fixture replay tested unavailable/failed presentation states:
  original answer and pending review stay present. This is **not provider proof**.
- Local QA scripts `/tmp/kpmg141-qa.js`, `/tmp/kpmg141-fallback-qa.js`; screenshots
  `/tmp/kpmg141-desktop.png`, `/tmp/kpmg141-mobile.png`. These temporary artifacts
  are not committed; the reproducible manual flow and fixture pairs are above.
