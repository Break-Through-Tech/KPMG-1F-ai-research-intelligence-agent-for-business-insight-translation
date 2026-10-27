# Local research interface · expanded paper preview

Implements the local interface portion of #119. This is a flow for Jacqueline
and Latifa to review together, not evidence of Latifa's approval or stakeholder
acceptance. The default fixture mode stays offline; optional live single-paper
synthesis uses an existing ChatGPT Codex login. No hosting, authentication
service, or approval action.

## Run

From the repository root, with Python 3.10+ and a current browser:

```bash
python -m src.research_demo
# Open http://127.0.0.1:8765
# Use --port 8766 if that port is occupied; Ctrl-C stops the server.
```

The default fixture mode needs only Python's standard library. It requires no
provider keys, model dependencies, index, or downloaded weights. Optional live
and saved-result modes are described separately below.
The server binds only to `127.0.0.1`; it is a development server, not a deployment.

## Walkthrough: normal path

1. Use the bottom composer. Choose **View example** (the default is **Full draft**; other states
   are under **Demo options**). Enter inserts a newline by default; choose **Enter key → Sends question** to change it.
   Ctrl+Enter or Command+Enter sends; Shift+Enter always adds a newline. The conversation labels your
   question **not executed**, and keeps the original fixture question under **Details → Run details & demo JSON**.
   Changing the input does not change or substantiate the example's answer.
2. Hover an inline **[1]** or **[2]** citation for a preview, or Tab to its
   **Inspect citation** button and press Enter/Space. Activation inspects; it does
   not navigate. Focus moves to **Close cited quote**. Tab proceeds through the
   separate **Open original paper** link and **Inspect source context** button.
   The original-paper link opens the cited location in a new tab. On touch,
   tapping the citation also inspects; opening the paper remains a separate action.
   If an extractive/fixture item has no stored quote, the preview is honestly
   labeled **Source passage** instead of **Cited quote**.
   **Inspect source context** opens the optional **Source context** rail with
   the full passage, page browser, source metadata, and originating claim/quote association. On mobile (800 CSS px
   or narrower) this is a modal full-height dialog. On desktop it is nonmodal.
   Close or Escape returns focus to the initiating citation. There is no
   persistent header Evidence control.
3. Inspect **Business implications** and the suggested action. Expand
   **Details → Assumptions, risks & limitations** for secondary detail; assumptions remain
   explicitly distinct from research findings. **Inspect evidence** inside that
   disclosure also makes uncited abstention passages accessible.
4. Inspect the source links: HTML preserves `#results` with no PDF page; PDF
   preserves `#page=2`. These are example.com locator fixtures, not verified or
   necessarily resolving papers. Their URLs are not fetched by the demo. Distances
   appear beside the passage and are labeled **Not confidence**. No fabricated
   relevance scores appear.
5. **Human review** remains pending and **Not approved**. There is no approval
   button. Expand **Details → Run details & demo JSON** to inspect the untouched v1 draft and
   additive metadata in its separate demo envelope. Additional questions append
   separate fixed-example turns, not live answers. Earlier citations reopen their
   own example's evidence. History is in-memory only and clears on reload.

## Walkthrough: partial and failure states

Enter another question, select a state under **Demo options**, and choose **View example** again.
Each request has a separate loading/result turn. The rail clears while loading;
failures show an explicit failed turn rather than relabeling an earlier draft.
Previously loaded turns remain available as labeled history, never as the new result.

| State | Visible outcome | Fixture / derivation |
| --- | --- | --- |
| Full draft | Summary and conditional business implications | `normal-v1.json`, unchanged |
| Partial · summary only | Supported summary; no business recommendation | A fresh normal copy with business status `insufficient_evidence`, empty implications/risks, explicit demo limitation; validated again |
| Abstention · insufficient support | Two passages, no supported claims or implications | `insufficient-v1.json`, unchanged |
| No evidence | Zero passages; generation skipped | `empty-v1.json`, unchanged |
| Provider error (simulated) | No draft; explicitly simulated provider failure | UI transport envelope with error and `result=null`; no provider is called |

For a local connection failure, stop the Python server and submit again. The
inline status explains that the local example could not load; the question stays
intact. Restart the server and choose **Retry original question**. The button becomes usable again after a
failure (requests time out after ten seconds).

See [Question entry and recovery](accessibility-question-entry.md) for persistent
keyboard preferences, editable fill-only suggestions, retry behavior, and scoped QA.

## Adapter boundary

### Live single-paper synthesis

Run with an existing ChatGPT Codex login (no API-key fallback):

```sh
python -m src.research_demo --port 8768 \
  --paper 'data/<arxiv_id>_<title>.pdf' \
  --codex-model gpt-6.1-sol --codex-bin /absolute/path/to/codex
```

The page now executes **Ask paper** questions against the full bounded paper
context, not canned answers or the persistent vector index. The browser sends recent
successful question/answer pairs to `/api/research`; the server validates and passes
that history to the synthesis prompt so follow-ups can refer to earlier discussion.
History is untrusted context, **not evidence**: every new claim still requires
supporting quotes from the loaded paper. The selected model synthesizes
findings, explicitly labeled interpretations, and cited scope/limitations.
Every paragraph requires known evidence IDs and supporting quotes. The server
checks quote membership against the actual evidence text and rejects the whole answer
on invalid output. This is **not semantic entailment verification**; the UI says
so and lets readers inspect each quote alongside the claim and full PDF page.
All outputs remain pending and unapproved. The most recent accepted result is
kept in server memory for reloads, not written to the repository or a database.

History is scoped to the browser page, limited to the most recent six complete
successful turns and 24,000 characters; each retained assistant answer is capped at
6,000 complete Unicode characters (never split surrogate pairs). Invalid Unicode
history is rejected before generation. Oldest pairs are dropped first, and the UI discloses that older
context may be dropped. Failed requests and fixtures are never added. Reloading
seeds context from the displayed saved synthesis answer only when its paper-context
identity matches the active paper, not the full earlier conversation. Mismatched or
unknown saved identities seed no history. The identity hashes the complete bounded
evidence (text and source metadata), not just a filename. History-bearing HTTP
requests must also carry that identity, preventing a stale tab from forwarding
context after the server switches papers. A distinct paper-change response clears
obsolete browser history and updates the active identity while retaining the typed
question; the UI explicitly asks the user to select **Ask paper** again for the
current paper. No model call occurs on that rejected request. No localStorage, cookies, persistent chat sessions, or cross-paper
memory are added. The live endpoint accepts at most 192 KiB (fixture stays 16 KiB),
rejects malformed/oversized history before generation, and keeps the 2,000-character
question limit. Roles are restricted to alternating user/assistant pairs; no system
or tool messages are accepted. Prompt instructions are a guardrail, not proof that
model outputs are semantically correct or immune to injection.

The server stays on loopback, checks loopback Host/Origin before all reads and writes, rejects cross-site requests, serializes model
calls, and exposes no provider credentials. The configured Codex text-only adapter
disables tools/integrations and uses the existing subscription. Live requests may
take up to five minutes; failures preserve the question for retry. PDF fallback requires the Poppler `pdftotext` executable on PATH
(macOS: `brew install poppler`; Debian/Ubuntu: `apt install poppler-utils`).
A missing executable produces an actionable startup error. PDFs must have
extractable text and fit the 30 MB / 40-page / 120k-character preview limits.
This local experimental route is not a production deployment or a full RAG index.

### Paper math

For version-pinned arXiv PDFs, the live preview first requests the matching
`https://arxiv.org/html/<id>v<version>` (15-second timeout, 5 MB maximum).
LaTeXML math `alttext` / TeX annotations are preserved as delimited LaTeX,
including display equations. Evidence links point to HTML sections, with null
PDF page numbers; PDF page locators are never invented for HTML evidence.
HTML source URL and byte hash are recorded in provenance. This live adapter is
separate from the persistent ingestion/index pipeline; no existing index is rebuilt.

If HTML is missing, invalid, too large, unavailable, or lacks a version-pinned
ID, the preview uses the original PDF text and records `html_fallback` in source
provenance. `--pdf-only` disables the lookup. The live math path requires
`beautifulsoup4` (already listed in requirements); fixture mode remains stdlib-only.
This preview does not download or compile TeX archives or guess missing PDF
formulas. The separate persistent-ingestion `--with-tex` fallback merged in #127
is not invoked by this adapter; its source pipeline remains independent.

The UI locally bundles KaTeX 0.16.22 (MIT, license under `ui/vendor/katex`).
Answer paragraphs, source quotes, limitations, and source context render explicit
`\(...\)`, `\[...\]`, and `$$...$$` math, with accessible MathML. Single dollar
signs remain literal currency. Invalid / unsupported math retains its original
LaTeX. Long display equations scroll within their container on narrow screens.
Prose remains text, `trust=false` disables TeX-generated links/HTML, and expansion
and sizing are bounded. CSP permits generated style attributes, not inline scripts.
Raw result JSON retains the exact stored TeX and source quote text. Existing saved
PDF results are not silently rewritten; submit a new question to use HTML evidence.

### Inspect a separately executed real-data result

`python -m src.research_demo --port 8768 --result /absolute/path/result.json`
opens a read-only replay of a validated pending v1 result. Its passages and
original-paper links use the same citation rail. The screen explicitly labels
it a saved real-paper result, hides the composer and synthetic controls, and
does not execute new questions. `/api/saved-result` returns that result (or null
in fixture mode); `/api/demo` remains synthetic and unchanged. Only use this
option for actual paper evidence, with honest execution provenance and limitations.
Replay labels use recorded provenance; unknown methods are not called extractive.
An extractive run is not evidence of LLM generation or persistent-index retrieval.
The loopback server is still local-only and does not publish the supplied file.

`src/research_demo.py:load_demo(request, scenario)` validates the submitted request
using `validate_request` and every returned draft using `validate_result`, from
[`src.research_contracts`](research-contracts.md). The wire version remains **1.0**.
The canonical files under `tests/fixtures/research/` are never rewritten.

`POST /api/demo` accepts `{query, scenario}` and returns an explicitly fixture-only
envelope `{mode, scenario, submitted_request, fixture_file, result, error}`.
`result`, when present, is a v1 fresh pending draft. The provider-error envelope is
not a `ResearchResult`. Invalid requests return HTTP 400; a simulated provider
failure returns HTTP 200 with the explicit demo error envelope, not a real outage.
Only allowlisted UI assets and demo scenarios are served. The separate
`POST /api/research` route is disabled unless `--paper` is explicitly supplied;
fixture mode never imports the live pipeline. No upload, persistent query store,
or query logging exists.

The UI uses text nodes for prose and KaTeX only for delimited math; source URLs
are preserved exactly. Unknown
JSON fields stay visible in **Inspect demo JSON**, not silently dropped by the
adapter. The live adapter uses its own explicit execution path; no provider is
swapped into the mock endpoint.

## Verification

```bash
python -S -m unittest tests.test_research_demo tests.test_research_contracts -v
node --check ui/app.js  # optional syntax check when Node is installed
```

The demo tests cover fresh copies, exact fixture preservation, partial vs
empty vs abstention, pending-only validation, source locations, HTTP assets,
scenario allowlisting, and malformed requests. They run offline without site
packages. Browser checks exercise all five states, citation navigation, literal
query rendering, no automatic external requests, connection-failure recovery, and
responsive layout. These establish UI/contract behavior, not semantic research
quality, real-source correctness, human approval, or model/provider compatibility.

## Structured source reader (#142)

**Inspect source context** retains the exact originating claim and its stored supporting
quotes, even while browsing other passages. A passage not quoted for that claim
is explicitly labeled. **Return to answer** closes the source panel and returns
to its originating control through the existing panel focus hook (#137).
Paper title, source identity, explicit version when supplied, section, PDF page,
passage ID and original-source link accompany the passage; missing values are
labeled. Retrieval distance remains **not confidence**. Pending review/approval
and source/quote checks are unchanged.

Fresh single-paper arXiv HTML extraction now retains an optional `reader` v1
semantic tree **before** the existing canonical text/TeX conversion. It carries
`provenance=source-html` and the raw HTML SHA-256, with source headings, lists,
MathML, table header IDs/scopes/spans and supplied figure text. IDs are remapped
per rendered view; no table headers or figure descriptions are inferred.
Captions and image descriptions are distinctly labeled as source-supplied. A
caption is **not** presented as a complete figure description. Native MathML
is preserved where supplied, not replaced with generated descriptions.
Fraction `linethickness` retains validated source values, including barless
binomials. Unsupported thickness values reject the whole passage's structured
view with an extraction limitation, preserving canonical text/TeX as fallback.
Other unsupported MathML attributes (for example enclosure notation or explicit
fence delimiters) also reject the whole structured passage instead of silently
changing source notation. Table spans retain valid native values, including
`rowspan="0"` for the remaining row group; unsupported spans fail closed.
Column groups and columns retain bounded span attributes, preserving the
structure associated with source `scope="colgroup"` headers.

Both retention and rendering are allowlisted and bounded. No source scripts,
images, URLs, styles, event handlers or arbitrary HTML are inserted. MathML
uses its native namespace; tables remain real tables inside keyboard-focusable
horizontal scroll regions. Reader headings are normalized below the source
section heading (levels 5–6; deeper source nesting is flattened at level 6).
The browser falls back to text when a retained tree is unsupported/over-budget.
The separately available **Citation-check text** remains the canonical quote
membership basis, not the reader tree; reader metadata is excluded from the
single-paper generation prompt. Quote membership does not establish entailment,
source fidelity, or human approval.

### Extraction and integration boundaries

- Existing saved results, PDF-text fallback, TeX/indexed ingestion and evidence
  without `reader` remain readable as retained text/explicit TeX, with a visible
  structure/figure-description limitation. This patch does not retrofit their
  ingestion or recover lost tables, headings, math or image descriptions.
- Table relationships are retained only as supplied. Missing headers/scopes and
  unsupported markup are reported; there is no inferred semantic repair.
- Source images are not fetched. Source captions/alt text may themselves be
  incomplete. HTML has no fabricated PDF page mapping.
- Reader-specific styling inherits the existing reading surface; #139 owns
  persistent typography/reflow preferences. #137 owns general keyboard/panel
  behavior. Their final combined changes still need integration testing.
- #130's indexed multi-paper integration remains separate. No corpus/model run
  or stakeholder approval is implied by this fixture-backed change.

### Reproduce focused verification

Use the repository's Python 3.12 test environment with BeautifulSoup/jsonschema/
pytest and an existing Playwright installation (no new browser dependency is
required by the application):

```bash
python -m pytest tests/test_paper_reader.py tests/test_paper_html.py \
  tests/test_research_demo.py tests/test_research_chat.py tests/test_research_contracts.py
python -m tests.source_reader_fixture > /tmp/source-reader-fixture.json
python -m src.research_demo --port 9142
# In a second terminal, from the same checkout:
RESEARCH_URL=http://127.0.0.1:9142 node tests/source_reader_browser.cjs
# Optional: PLAYWRIGHT_MODULE=/absolute/path/to/playwright
# Optional: READER_FIXTURE_JSON=/tmp/source-reader-fixture.json SCREENSHOT_DIR=/tmp
```

The browser regression intercepts **only** `/api/demo` with the explicitly
synthetic structured fixture; the normal page, scripts, styles and config are
served by the real loopback application. It checks 1280/640/320px viewports,
claim/quote retention, passage switching, missing metadata, return focus,
MathML, table header ID associations, inert rendering, long passage retention,
console errors, and document/panel overflow. This proves a deterministic fixture
flow, not a live paper or provider result.

Manual acceptance still required: VoiceOver/Safari math and table navigation,
native browser 200%/400% zoom, integrated #137/#139 preferences/focus behavior,
and source-fidelity review on representative real papers. CSS 200% zoom
emulation and DOM/keyboard checks are supplementary, **not** those manual gates
or a WCAG conformance claim. #145 owns the combined manual audit.

## Keyboard-only citation walkthrough (#137)

Run the fixture server above; no provider or live paper is needed. Use a current
browser supporting native `dialog` and Popover APIs. This procedure is reproducible
manual QA, not a claim that assistive-technology acceptance has been performed.

1. Tab to **Skip to research question**, press Enter, then Ctrl+Enter in the composer
   to load the default full draft. Fixture, not-executed, and not-approved labels
   must remain visible.
2. Shift+Tab from the composer through **Details** to the last inline citation
   (or Tab forward from the top). Press Enter or Space on **Inspect citation**.
   The quote preview opens and focus moves to **Close cited quote**. It must not
   open another browser tab. Hover is an additional route, never required.
3. Tab through **Open original paper** → **Inspect source context**. Shift+Tab
   reverses that order. Shift+Tab from Close returns to the citation and dismisses
   the preview. Tab beyond the last preview action dismisses and continues to the
   next control after the citation. Escape or Close returns to the citation.
4. Activate **Open original paper** with Enter to open its original HTML fragment
   or PDF `#page=N` URL in a new tab. Link activation follows native link behavior
   (Enter, not Space). Fixture example.com URLs are locator examples, not verified
   or necessarily resolving papers.
5. Activate **Inspect source context**. Focus lands on **Source context**; Tab
   reaches Close, source choices in document order, original-source link, and
   **Source details**. Enter/Space select a source choice without moving focus.
   In synthesized answers, expand **Browse paper pages** to reach source choices.
6. Above 800 CSS px, Tab can leave the panel for the rest of the page. At 800px
   or narrower, Tab/Shift+Tab wrap within the modal; the background is inert.
   Resize while the panel is open in both directions: preserve the current
   panel control; when narrowing with focus outside, move it into the panel.
   Close/Escape restores the citation, including after a viewport change.
7. Submit another fixture question while the desktop panel is open. Its content
   clears during loading and updates to the new turn without removing focus
   from a surviving panel heading/control. Historical citations still reopen
   their own turn. If an initiating element is removed by rerendering, dismissal
   falls back to the question, or the conversation when the form is hidden.
8. Select **Abstention** or **No evidence** under Demo options, submit, and expand
   **Details → Assumptions, risks & limitations → Inspect evidence**. Escape must
   return to this initiating button even when there are no source choices.

### Focused browser regressions

`tests/ui_keyboard.cjs` runs an isolated ephemeral-port Python fixture server and
Chromium. It requires Python 3.10+ and Playwright (optional QA tooling, not a
production dependency). For example, install into an external QA directory:

```bash
npm install --prefix /tmp/kpmg-ui-qa playwright@1.64.1
NODE_PATH=/tmp/kpmg-ui-qa/node_modules PYTHON=python3.12 node --test tests/ui_keyboard.cjs
```

If Chromium is not already installed, use that Playwright installation's browser
installer. Set `UI_QA_ARTIFACTS=/tmp/kpmg-137-qa` to save desktop, mobile and narrow
preview screenshots outside the repository. The test itself picks a free loopback
port and stops its server/browser when done. Default `PYTHON` is `python3`; choose
an executable >=3.10 explicitly if macOS's system Python is older.

Citation inspect and source-context actions include the source title and PDF page
(or section / explicit no-page fallback) in their accessible names. Original-source
links also announce that they open a new tab.

Coverage includes contextual accessible names, activation without navigation, separate original-source URL
navigation (intercepted fixture, not live source verification), forward/reverse
preview exit, Escape/Close restoration, native source-choice activation, mobile
Tab containment, desktop nonmodality, open-panel breakpoint changes, removed
initiators/result replacement, historical turns, abstention/empty evidence, and
320px preview target/focus bounds. Runtime and console errors fail the checks.
Fixture browser checks do not prove live/model support, semantic entailment,
source certification, WCAG conformance, VoiceOver behavior, manual zoom acceptance,
Safari/Firefox behavior, or stakeholder acceptance. #138 owns broader screen-reader
structure, #142 owns structured evidence rendering, and #145 owns the integrated
manual accessibility audit; integrate and rerun these interaction checks together.

## Persistent-index research (#130)

Use **an existing compatible Chroma index** and a locally cached
`all-MiniLM-L6-v2` encoder. This command never downloads/rebuilds a corpus or
promotes experimental retrieval. The adapter calls the existing dense
`src.retrieval.search`; no hybrid/reranking defaults change.

```sh
python -m src.research_demo --index /absolute/path/to/data/chroma_db \
  --collection arxiv_papers --top-k 5 --codex-model YOUR_CONFIGURED_MODEL \
  --codex-bin /absolute/path/to/compatible/codex
# Alternatively, explicitly select the existing environment-configured provider:
python -m src.research_demo --index /absolute/path/to/data/chroma_db --configured-provider
```

Open the printed loopback address. Use the single question box and **Research**.
Include business context in the question when requesting conditional implications,
for example: “What are the business implications of these findings for banking?”
The indexed UI sends `interpret_context: true`; the backend uses the configured
generator to extract an explicitly supplied context before retrieval. The extractor
accepts only a verbatim substring up to 300 characters, or an empty context for
research-only questions. Malformed/invented context fails before research; retries
retain the question. This adds one provider call per new UI research question.
Clarification resumes retain the original context without reinterpreting the answer.
Legacy API callers may still supply `industry` directly; no extraction occurs unless
requested. Extraction is a prompted intent classifier, not a certified semantic gate:
substring validation cannot prove that the model understood business intent.

Enter-key preferences are under **Research options**; the question uses a caret
and outer composer focus border rather than an inner rectangular outline.
Buttons and links retain their keyboard focus indicators. Each indexed query
is **independent**: previous answers are neither intent context nor evidence.
Fixture mode, saved-result replay, and `--paper` remain separate, mutually exclusive
startup modes. No silent fallback occurs. Configured providers retain their usual
billing; this feature does not provision a service or change credentials.

The view distinguishes research-only summary, complete draft, translation
abstention/partial, insufficient support, empty retrieval, and execution errors.
A translation failure retains the supported summary and an explicit failed-stage
message; it is not relabeled evidence absence. Inspect citations, exact supporting
summary quotes, source pages/sections, transfer assumptions, risks and limitations.
Business implications use the existing chunk-ID contract, **not exact-quote or
semantic entailment certification**. All outputs remain pending/unapproved.
The result JSON in Run details includes the complete result and review fingerprint,
compatible with the existing `src.research_review` packet workflow. HTML/Markdown
exports remain available. Indexed results are not placed in a global replay slot.

### Run identity and reproducibility

Run details retain code revision, startup arguments, explicit provider/model,
collection name/count/model metadata, retrieval settings, stage statuses, and a
SHA-256 of the **actual indexed IDs/text/source metadata**. This is not a hash of
`chunks.parquet`, source certification, or a digest of embedding bytes. Keep the
index immutable while serving; stop/restart the host after index/embedding/config
changes. Record snapshot/corpus version externally when needed. Record identity
is rechecked before/after research; changed source records reject stale context.
There is no transaction/revision lock against concurrent index writers.

### Verification and handoff (2026-10-24)

- Focused adapter/HTTP tests cover multi-paper citations, industry translation,
  summary-only, empty evidence, abstention, false-premise/out-of-corpus fixtures,
  provider/retrieval/quote failures, translation failure, and stale context.
- Browser checks use injected **synthetic development adapters**, not held-out
  evaluation or evidence of model answer quality. Keep those claims separate.
- A real existing index was opened without reindexing: 877 passages,
  `arxiv_papers`, indexed-record digest
  `41c71d4bbbdc5aa40a75d03f43691439a36be11ee256dd32ff48969faf3be260`.
  Query `How should AI agents be evaluated?`, top-k 5 returned versioned papers
  `2608.00339v1`, `2605.00276v1`, `2604.00319v1`, `2604.00324v1` with PDF-page
  locators. This proves retrieval wiring, **not supported cross-paper synthesis**.
- The earlier Codex 0.144.2 compatibility blocker is resolved by explicitly
  selecting a compatible installed CLI, without modifying user config or auth.
  On 2026-10-24, Codex 0.163.0-alpha.11.2 with existing ChatGPT subscription
  login and explicit `gpt-6.1-sol` passed isolated structured JSON generation.
  A real loopback HTTP run over the existing 877-record index then passed:
  multi-paper summary plus professional-services business translation (`full`),
  out-of-corpus propulsion abstention (`insufficient`), and a vague question
  followed by clarification/resume to a cited summary (`summary-only`).
  These are development walkthroughs, not held-out semantic evaluation,
  source certification, stakeholder acceptance, or deployment. Results remain
  pending/unapproved; exact-quote membership is not entailment certification.
- Handoff to #120: visible flow/citation usability; #121: independently labeled
  source-backed answers; #122: retrieved chunk/rank/locator diagnostics; #123:
  summary/business/transfer audit; #124: pending result/review fingerprint. Those
  assignments are not closed by this integration. Use a new predeclared held-out
  set; the injected test cases are development-only.

### Select a compatible subscription CLI

Pass `--codex-bin /absolute/path/to/codex`, or set `RESEARCH_CODEX_BIN` to that
same executable. Explicit `--codex-bin` wins, then the environment setting,
then `codex` on PATH. There is no silent alternate-binary/provider fallback.
The adapter checks `exec --help` for required isolation/output options before
checking existing ChatGPT login. An incompatible CLI fails before research
prompts are sent. Actual generation still uses strict config, an empty scratch
working directory, read-only sandbox, disabled execution/integration features,
ephemeral sessions, schema validation and tool-event rejection.
Help preflight checks advertised options, not every runtime capability; generation
continues to fail closed if the selected model or flags are rejected.

Confirm the selected executable with `codex --version`, `codex exec --help`,
and `codex login status`. Do not remove isolation flags, copy credentials,
change global configuration, or switch to API-key billing to make an old CLI work.
Official references: [CLI options](https://learn.chatgpt.com/docs/developer-commands#codex-exec)
and [subscription authentication](https://learn.chatgpt.com/docs/auth).
