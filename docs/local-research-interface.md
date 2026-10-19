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
   are under **Demo options**). Enter submits; Shift+Enter adds a newline. The conversation labels your
   question **not executed**, and keeps the original fixture question under **Details → Run details & demo JSON**.
   Changing the input does not change or substantiate the example's answer.
2. Hover or focus an inline **[1]** or **[2]** citation to preview that claim's
   **Cited quote**, paper title, and PDF page. Click the citation to open the
   original paper at the cited location in a new tab. On touch, tap previews the
   quote; **Open paper** inside the preview opens the source. Tab enters preview
   controls; Escape dismisses it. Quotes remain inspectable without leaving the answer.
   If an extractive/fixture item has no stored quote, the preview is honestly
   labeled **Source passage** instead.
   **More context** opens the optional **Source context** rail with the full
   passage, page browser, and source metadata, without repeating answer claims.
   On mobile this is a full-height dialog; closing it or pressing Escape returns
   focus to the citation. There is no persistent header Evidence control.
3. Inspect **Business implications** and the suggested action. Expand
   **Details → Assumptions, risks & limitations** for secondary detail; assumptions remain
   explicitly distinct from research findings. **Inspect evidence** inside that
   disclosure also makes uncited abstention passages accessible.
4. Inspect the source links: HTML preserves `#results` with no PDF page; PDF
   preserves `#page=2`. These are example.com locator fixtures, not verified or
   necessarily resolving papers. Their URLs are not fetched by the demo. Distances
   appear under **Source details** and are labeled **Not confidence**. No fabricated
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
intact. Restart the server and retry. The button becomes usable again after a
failure (requests time out after ten seconds).

## Adapter boundary

### Live single-paper synthesis

Run with an existing ChatGPT Codex login (no API-key fallback):

```sh
python -m src.research_demo --port 8768 \
  --paper 'data/<arxiv_id>_<title>.pdf' \
  --codex-model gpt-6.1-sol --codex-bin /absolute/path/to/codex
```

The page now executes **Ask paper** questions against the full bounded paper
context, not canned answers or the persistent vector index. Each question is
independent; prior conversation is not supplied. The selected model synthesizes
findings, explicitly labeled interpretations, and cited scope/limitations.
Every paragraph requires known evidence IDs and supporting quotes. The server
checks quote membership against the actual evidence text and rejects the whole answer
on invalid output. This is **not semantic entailment verification**; the UI says
so and lets readers inspect each quote alongside the claim and full PDF page.
All outputs remain pending and unapproved. The most recent accepted result is
kept in server memory for reloads, not written to the repository or a database.

The server stays on loopback, rejects cross-site live requests, serializes model
calls, and exposes no provider credentials. The configured Codex text-only adapter
disables tools/integrations and uses the existing subscription. Live requests may
take up to five minutes; failures preserve the question for retry. PDFs must have
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
