# Deterministic quote insertion (opt-in)

This treatment makes the model select evidence rather than reproduce quotations.
It does not establish that selected evidence entails a finding, that all necessary
qualifiers survived synthesis, or that a model is better than another model.

## Run

With an existing index and configured generation route:

```sh
python main.py --query "How are AI agents evaluated?" \
  --evidence-led --evidence-span-selection
```

The same flag works with `--mode business --industry banking` or an explicitly
configured `--generation-route codex --codex-model MODEL`. It requires summary or
business mode and `--evidence-led`; it is not available in the synthetic demo.
The Python entrypoint is `src.evidence_led.summarize(..., quote_selection=True)`.
Existing calls, provider routes, literal-quote correction policy and defaults are
unchanged. No new credentials or model calls are introduced.

## Contract

1. Use the existing passage normalization and context packing first. Never expose
   omitted passages or hidden source tails. Remove the packer's synthetic
   truncation marker before constructing the menu.
2. Build the versioned `displayed-source-spans-v1` menu from those displayed
   source prefixes. Split at sentence/paragraph boundaries. Long units use
   contiguous windows of at most 1,000 Unicode characters with 120-character
   overlap; short units include preceding source context when possible.
   Spans with fewer than 15 normalized characters are not selectable. This is a
   deterministic heuristic, not a linguistic sentence parser: abbreviations and
   long clauses can be split. Selection granularity can limit usable evidence.
3. Generate only `{span_id, finding, relevance}` for each fact, plus the existing
   answerability and coverage gaps. Validate IDs against a JSON-schema allowlist
   locally, even when native constrained output is unavailable. Unknown or altered
   IDs, generated quotes/offsets, malformed JSON and provider errors fail closed;
   no retry, fuzzy matching, aliasing or text correction occurs in this treatment.
4. Resolve the ID locally. Verify source SHA-256 and bounds; insert the exact
   original slice and its actual chunk ID. Keep `source_span` provenance in each
   hydrated fact: policy, ID, chunk ID, start/end and source-text hash. Offsets
   are Python Unicode character offsets into the normalized displayed source
   prefix (after existing outer-whitespace stripping), **not** PDF positions,
   bytes or offsets in the raw ingestion artifact. End is exclusive.
5. Apply the existing quotation membership validator and synthesis support gates.
   Context cannot become a claim, partial answers still require a gap, study
   limitations still require support, and results remain unapproved drafts.

The extraction prompt contains only the selectable menu, not hidden full chunks.
Menu JSON/IDs add prompt overhead on top of the existing source-text packing
budget; that budget is not a total rendered prompt/token cap. The model does not
supply hashes or offsets. SHA-256 detects source drift during hydration; it does
not authenticate a paper or certify its claims.

Provenance distinguishes `evidence-led-spans-v1` from `evidence-led-v3`, including
its prompt and span implementation hashes. The new prompt is excluded from the
legacy adapter's prompt hashes so baseline provenance remains comparable.
The returned ledger retains the existing `quote`, `chunk_id`, `finding` and
`relevance` fields, with additive `source_span` metadata.

## Verification and evaluation boundary

`tests/test_source_spans.py` covers Unicode fidelity, source hashes, bounds,
unknown IDs, forbidden generated fields, truncation, fake source delimiters,
long-unit coverage, citation mapping, partial/context gates and CLI routing.
These scripted providers test contracts, not semantic model quality.

Before claiming improvement, run each model on the same retained evidence with
separate output directories and blinded support/qualifier review. Do not repair
or relabel old failed outputs. Existing three-case baseline results are not
measurements of this treatment. No training, default switch, UI change or
production deployment is part of this change.
