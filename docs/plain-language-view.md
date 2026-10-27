# Plain-language presentation adapter (#141)

## Boundaries and startup

`python3.13 -m src.research_demo --port 9141` starts the loopback fixture UI.
Choose **Demo options → Plain-language · supported definition fixture**, then
**View example**. Use the native **Technical / original** and **Plain language**
radio group (arrow keys switch); expand **Technical term definitions** with
Enter/Space. Citations retain the original source links, quote previews and
source-context inspection. Full draft remains the default fixture.

## Configured generation — 2026-10-27

This remains an optional summary-presentation layer, not a new research mode.
Add `--plain-language` to explicitly opt into an additional generation request
using the **same selected generator** as live indexed/single-paper research:

```sh
python -m src.research_demo --index /path/to/existing-index --codex-model YOUR_CONFIGURED_MODEL --plain-language
python -m src.research_demo --paper /path/to/versioned_paper.pdf --codex-model YOUR_CONFIGURED_MODEL --plain-language
python -m src.research_demo --result /path/to/pending-result.json --codex-model YOUR_CONFIGURED_MODEL --plain-language
```

For saved replay, select the existing subscription model/binary explicitly;
no new research query, API-key fallback, or fixture substitution occurs.
For indexed mode `--configured-provider` also reuses the configured generator.
Without the flag, real modes remain explicitly unavailable for simplification.
The original validated ResearchResult is never modified. Malformed/oversized,
unquoted, citation-changing or failed generation produces a presentation failure
with the entire original retained. Interpretation text must remain unchanged;
UI renders only finding rewrites. Abstention/empty results skip the provider and
retain no claims/definitions. Business assumptions, risks and coverage limitations
remain original and inspectable in both views. Available means structurally
validated, not independently verified or approved.

The generation prompt asks for preserved negation, uncertainty, disagreement and
numerical bounds and only source-supported definitions. Literal quote checks
cannot establish meaning preservation; semantic review stays pending. Provider,
model, prompt version and prompt/response hashes are recorded separately in the
presentation, not in the original result fingerprint. No automatic retry/fallback.

Retain an inspectable side-by-side development packet without altering input:

```sh
python -m scripts.plain_language_examples --result /path/to/pending-result.json --codex-model YOUR_CONFIGURED_MODEL --out /tmp/presentation-example.json
```

This executes the selected subscription provider. Retain source identity/locators
and exact quotes, and inspect supported, partial and abstention examples against
the cited text separately from browser tests. The command never grants semantic
approval or treats a development case as held-out evaluation. Existing synthetic
examples below remain labeled synthetic.

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
  modality, negation and disagreement. Configured generation now uses `generate_view` after original validation.
- **#124:** review the original result and presentation separately. The sibling
  envelope is not part of the original approval fingerprint; **do not interpret
  original approval as approval of the rewrite**. Bind any future presentation
  review to `result_identity` plus the candidate content. This UI cannot approve.
- **#130:** add a validated candidate to the UI envelope only after configured
  provider execution; retain unavailable/failed states. Never call `fixture_view`
  for live or replay results. The opt-in route above supplies a validated pending presentation; disabled configuration remains unavailable.
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

### Offline replay of a retained presentation

To inspect an already-generated candidate without another provider call, save its
`plain_language` object and run `--result original.json --presentation candidate.json`.
The candidate is revalidated against the full result identity and literal quotes;
stale/malformed candidates show a failed presentation while retaining the original.
`--presentation` cannot be combined with live modes or `--plain-language`.

## Fine-tuned model runbook handoff

Include this presentation task in the local Qwen specialization runbook, not
only the UI rollout. Keep extraction/QA/synthesis and plain-language generation
separately identifiable in training and evaluation. Existing four-task smoke runs
are not evidence for the new presentation task.

- Prepare reviewed technical/plain pairs from training source families only;
  keep both views in the same split. Inputs are fixed, validated original results
  plus exact supplied passages. Generated drafts are not automatically targets.
- The generator returns **only `claims` and `definitions`** matching `generate_view`'s
  response schema. The adapter supplies result identity, pending-review state,
  fixture flag and provenance; do not train a model to invent approval or hashes.
- Preserve ordered claim/citation mapping, exact support quotes, uncertainty,
  negation, numerical bounds, conditions, disagreements and coverage gaps. Keep
  interpretations/business actions/assumptions original. Define terms only from
  explicit support; otherwise mark unavailable. No invented claims on abstention.
- Compare untuned 9B, tuned 9B and untuned 27B on **identical original results and
  evidence**, not separately regenerated summaries. Record exact model/adapter,
  quantization/chat template, prompt/schema, settings, memory, latency and errors.
- Review meaning/qualifier retention and readability separately, using supported,
  partial, qualified/conflicting and unanswerable cases. Count malformed/failed
  presentations and retain adverse cases. Keep final-test source families held out
  throughout data/prompt/adapter selection; obtain second/blinded review where
  feasible. A schema/quote pass or simpler prose is not evidence of preserved meaning.
- Integrate a selected tuned model only through an explicitly configured generator
  that supports this schema and failure contract; run presentation/server/browser
  regressions and source-backed examples before changing a model default. Never
  silently substitute a hosted provider, retrain, download or start paid compute.

The separate local experiment's runbook/plan now include this task. Its current
queues/runners still need reviewed fifth-task examples and a contract-aware
comparison adapter; this PR does not claim to have trained or evaluated a tuned
model or modify the experiment's existing datasets and recorded runs.
