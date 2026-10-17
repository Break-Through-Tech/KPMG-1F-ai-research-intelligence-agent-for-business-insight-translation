# Shared research draft contracts — v1

`src.research_contracts` owns the JSON-compatible `TypedDict` declarations and
runtime validation. Importing it uses only the Python standard library. These
are local data checks, not JSON generation schemas, source verification, semantic
evaluation, human approval, or a change to retrieval/generation defaults.

## Fields

| Object | Required fields and rules |
| --- | --- |
| `ResearchRequest` | Nonempty `query`; optional positive integer `top_k` (default 5; bool is invalid); optional nonempty `industry`, `jurisdiction`. Query/context are never stripped. |
| `EvidencePassage` | Unique nonempty `chunk_id`, nonempty `text`, `title`, explicit `source`, `arxiv_id`, `pdf_url`, `source_url`, `page_number`. Source rules below distinguish real paper locations from synthetic fixtures. |
| `ResearchSummary` | `status` = `ok` or `insufficient_evidence`; nonempty `query`; `claims` = list of `{text, chunk_ids}`; `limitations` = list of strings. `ok` requires at least one claim; insufficient evidence requires none. |
| `BusinessInsight` | Same status rules; nonempty `industry`; `implications` = list of `{text, chunk_ids, suggested_action, assumptions}`; `risks`, `limitations` = lists of strings. Actions are nonempty text; assumptions are a list of strings, distinct from research findings. |
| `ResearchResult` | `schema_version="1.0"`, `request`, `evidence`, `summary`, `human_review`, `approved`; optional `business_insight`, `provenance`, `regulatory_checkpoint`, review fingerprints and other additive metadata. |

Each claim/implication needs nonempty text and a nonempty list of **unique known
evidence IDs**. IDs refer to this result's evidence, not another run or the separate
regulatory namespace. The summary query must exactly match the request; the business
industry must exactly match explicit request context. A business `ok` result cannot
follow an insufficient summary. Empty evidence is valid but cannot support claims.

`validate_result` checks **fresh drafts**: `human_review={status:"pending",
reviewer:null, notes:null}` and `approved=false`. It never approves anything.
Reviewed packets are deliberately outside this validator's scope; use the existing
`src.research_review.require_current_review` and explicit human decision path
described in [Research review](research-review.md). The optional regulatory bundle
remains advisory and is validated by its own module, not this paper contract.

## Source locations and compatibility

- **PDF:** nonempty paper ID; absolute HTTP(S) `pdf_url` identifying the document
  without a fragment; positive, non-boolean integer `page_number`; `source_url`
  identifying that same PDF. A `#page=N` fragment, when present, must agree with
  the page. Legacy unanchored document URLs remain valid with the explicit page
  field; validation does not rewrite them or silently manufacture a location.
- **HTML:** nonempty paper ID; absolute HTTP(S) `pdf_url` and `source_url`;
  `page_number` must explicitly be null. Optional `html_url` must exactly equal
  `source_url`, including its heading anchor. Base URLs remain valid when the
  extractor supplied no anchor; section text does not invent an anchor.
- **Synthetic:** preserves the existing explicit `source="synthetic"` adapter
  fixtures. `arxiv_id`, `pdf_url`, `source_url`, and `page_number` must all be
  present and null; no non-null `html_url`. These are invented examples, never
  real-paper evidence or real retrieval-quality measurements.
- Optional `distance` is a finite number or null; absence remains compatible with
  adapters that omit it. It is never converted to confidence. Optional `section`
  and `subsection` are strings. Additional JSON metadata is retained unchanged.
- URLs must not contain whitespace, credentials, or non-HTTP(S) schemes. Validation
  does **not** fetch a URL, establish that a page exists, or prove cited text occurs
  there. All contract data must serialize as finite JSON.

## Public validators and callables

```python
validate_request(request) -> dict  # defensive copy; fills top_k=5
validate_evidence(passages) -> set[str]  # validated IDs; no mutation
validate_output(output, field, ids) -> None  # claims or implications
validate_summary(summary, ids, *, query=None) -> None
validate_business_insight(business, ids, *, industry=None) -> None
validate_result(result) -> None  # fresh pending drafts only

retrieve(query, top_k) -> list[dict]
summarize(query, passages, *, generate) -> dict
translate(summary, passages, *, industry, generate) -> dict
run_research(request, *, retrieve, summarize_fn, translate_fn=None,
             review_fn=None, provenance=None) -> dict
```

Bind `generate` before injecting pipeline adapters: `summarize_fn(query, passages)`
and `translate_fn(summary, passages, *, industry)`. The injected `generate(prompt)`
returns JSON response text; some existing providers also support an optional
response-schema keyword. `review_fn(draft)` receives a defensive copy and returns
a separate advisory `regulatory_checkpoint`, never approval.

`run_research` uses the shared checks before generation and before returning a
fresh draft, then seals its existing content fingerprint. The historical
`research_pipeline._validate_output` import remains an alias for compatibility
with the existing translator. No callable signatures, result fields, default
models, prompt defaults, dependency/config files, or retrieval code change.

## Versioning and offline fixtures

The wire version stays **1.0**. Preserve unknown JSON fields; do not normalize,
strip, or discard additive citation metadata. New required fields, changed
meanings, or callable changes require explicit coordination in #76 and a version
decision, not silently editing consumers. This formalizes the existing draft's
source requirements and tightens rejection of inconsistent locations, duplicate
citations, contradictory statuses, nonfinite values, and invalid pending state.
It does not migrate historical reviewed packets or change their fingerprints.

Fixtures in [`tests/fixtures/research`](../tests/fixtures/research/README.md)
cover normal mixed HTML/PDF output, no evidence, insufficient support, and invalid
summary/business references and source locations. For example:

```python
import json
from pathlib import Path
from src.research_contracts import validate_result

result = json.loads(Path("tests/fixtures/research/normal-v1.json").read_text())
validate_result(result)  # leaves the complete pending draft unchanged
```

Run the isolated contract checks without even loading site packages:

```bash
python3.12 -S -m unittest tests.test_research_contracts -v
```

These checks need no provider key, embedding weights, Chroma index, downloads, or
network. They establish structure and failure behavior, not real model/corpus
quality or stakeholder acceptance.
