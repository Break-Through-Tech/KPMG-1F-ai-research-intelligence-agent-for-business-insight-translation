# Local research interface · fixture-only slice

Implements the local interface portion of #119. This is a flow for Jacqueline
and Latifa to review together, not evidence of Latifa's approval or stakeholder
acceptance. No hosting, authentication, real providers, or approval action.

## Run

From the repository root, with Python 3.10+ and a current browser:

```bash
python -m src.research_demo
# Open http://127.0.0.1:8765
# Use --port 8766 if that port is occupied; Ctrl-C stops the server.
```

Only Python's standard library is needed. Do not install the model dependencies,
set provider keys, build an index, or download weights to run this interface.
The server binds only to `127.0.0.1`; it is a development server, not a deployment.

## Walkthrough: normal path

1. Enter a research question. Keep **Full draft** selected and choose **Inspect
   example**. The interface labels the entered question **not executed**, and
   separately shows the original fixture question. Changing the input does not
   change or substantiate the example's answer.
2. Inspect research claims on the left and source passages on the right (stacked
   on mobile). Choose **Passage 1** under a claim to jump to that passage.
3. Inspect **Business implications**, the suggested action, assumptions, risks,
   and limitations. Assumptions are not presented as research findings.
4. Inspect the source links: HTML preserves `#results` with no PDF page; PDF
   preserves `#page=2`. These are example.com locator fixtures, not verified or
   necessarily resolving papers. Their URLs are not fetched by the demo. Distances
   are labeled **Not confidence**. No fabricated relevance scores appear.
5. **Human review** remains pending and **Not approved**. There is no approval
   button. Expand **Inspect demo JSON** to inspect the untouched v1 draft and
   additive metadata in its separate demo envelope.

## Walkthrough: partial and failure states

Select a state and choose **Inspect example** again. Prior results are cleared
while loading; failures do not leave an old draft on screen as a new result.

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

`src/research_demo.py:load_demo(request, scenario)` validates the submitted request
using `validate_request` and every returned draft using `validate_result`, from
[`src.research_contracts`](research-contracts.md). The wire version remains **1.0**.
The canonical files under `tests/fixtures/research/` are never rewritten.

`POST /api/demo` accepts `{query, scenario}` and returns an explicitly fixture-only
envelope `{mode, scenario, submitted_request, fixture_file, result, error}`.
`result`, when present, is a v1 fresh pending draft. The provider-error envelope is
not a `ResearchResult`. Invalid requests return HTTP 400; a simulated provider
failure returns HTTP 200 with the explicit demo error envelope, not a real outage.
Only allowlisted UI assets and demo scenarios are served. No live endpoint, pipeline
import, upload, persistent query store, or query logging exists.

The UI uses text nodes for all content and preserves source URLs exactly. Unknown
JSON fields stay visible in **Inspect demo JSON**, not silently dropped by the
adapter. A future live adapter must be a separate, explicit execution path and
coordinate interface/contract changes; do not swap a provider into this mock path.

## Verification

```bash
python -S -m unittest tests.test_research_demo tests.test_research_contracts -v
node --check ui/app.js  # optional syntax check when Node is installed
```

The seven demo tests cover fresh copies, exact fixture preservation, partial vs
empty vs abstention, pending-only validation, source locations, HTTP assets,
scenario allowlisting, and malformed requests. They run offline without site
packages. Browser checks exercise all five states, citation navigation, literal
query rendering, no automatic external requests, connection-failure recovery, and
responsive layout. These establish UI/contract behavior, not semantic research
quality, real-source correctness, human approval, or model/provider compatibility.
