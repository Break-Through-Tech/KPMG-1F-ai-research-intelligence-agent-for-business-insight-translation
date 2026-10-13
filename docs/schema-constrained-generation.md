# Schema-constrained research summaries

The built-in summarizer now binds a JSON Schema to each actual generation
request. It uses only the chunk IDs retained in the bounded prompt, not every
retrieved passage. Native provider constraints are requested **and** the returned
JSON is validated locally; an endpoint ignoring the schema cannot bypass that
local check.

## Provider paths

| Provider | Request when a schema is bound | Verification boundary |
|---|---|---|
| Gemini | `response_json_schema` plus JSON MIME type | Real SDK config exercised offline; no live cloud call |
| OpenAI / compatible | Chat Completions `response_format=json_schema`, named schema, `strict=true` | OpenAI request shape tested offline; real local Ollama exercised |
| Bedrock | Converse `outputConfig.textFormat` / `jsonSchema` | Real boto3 service model and Stubber validate request/response shapes; no live AWS call |

Model support is not implied by provider support. An unsupported schema/model,
refusal, incomplete response or SDK failure fails explicitly. There is **no**
retry with `json_object`, prompt-only downgrade or provider fallback.

The OpenAI request follows [official Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs).
An OpenAI-compatible endpoint must implement that format itself; compatibility
is not a promise of OpenAI's guarantees from a different server.

Dependencies require the SDK versions whose native configuration was checked:
`google-genai>=2.30.1`, `boto3>=1.43.113,<2`, and direct `jsonschema>=4.0`.
The exercised local versions are recorded with the PR evidence. Older SDKs must
be upgraded; these minimums are a verified baseline, not a claim about the first
release that introduced each vendor's feature.

## Contract and validation

All three fields are required: `status`, `claims`, and `limitations`. Extra
members are forbidden at the root and within claims. Status has two allowed
values; each claim has a string `text` and a nonempty array `chunk_ids`.
Citation strings must belong to the enum of **included** source IDs.

The constrained summary envelope bounds arrays to eight claims and eight
limitations, text strings to 600 characters, and citation arrays to the number
of included IDs. These are engineering output limits, not measured quality
targets; they apply to the built-in schema-bound path. The schema does not
replace the existing evidence-context budget or add a configurable token budget.

Before any request the schema is copied and checked. On return, duplicate JSON
members, nonfinite numbers, non-JSON content, missing/extra fields, wrong types
and out-of-enum citations are rejected locally. OpenAI refusals/non-stop finishes,
Gemini non-STOP finishes and Bedrock incomplete/nontext output are also rejected.
Sensitive response bodies and provider errors are not echoed.

The existing summarizer still checks nonblank claims, the relationship between
status and claim count, and citation IDs after parsing. A schema-valid response
is not necessarily a valid summary: `insufficient_evidence` with claims, or
`ok` with no claims, remains a failure. If no evidence fits the prompt budget,
generation is skipped instead of sending an invalid empty citation enum.

## Callable integration and provenance

```python
generate, settings = create_generate(config)
text = generate(prompt, response_schema=my_schema)
```

Factory callables advertise `supports_response_schema=True`. The built-in
summarizer recognizes that exact flag and supplies its per-context schema.
The debugging helper forwards the keyword rather than losing this capability.
Calling an unbound generator remains the existing JSON-object path; this allows
other output stages to bind their own contract instead of accidentally inheriting
the research-summary schema. Business output is **not** schema-bound by this PR.

Simple injected `generate(prompt)` fixtures/custom callables remain compatible,
but are labeled `injected_callable_unconstrained`; they are not claimed to use
native schema enforcement. Generation metadata describes available capability.
Each attempted summary additionally records the requested enforcement mode and
exact schema SHA-256, including its citation enum. That mode is a requested policy,
not proof of success when the summary contains an error.

Schema validation failures produce no claims and `malformed_response`; provider
or completion failures produce `generation_failed`. Existing CLI/capture/report
failure handling is retained, with nonzero exit status for errors. Normal valid
evidence abstention is not an execution error. All pipeline output remains
`approved=false`, pending actual human review.

## Real local evidence and the important remaining limit

The Ollama/Llama 3.2 1B local factory returned the requested simple status object
under native schema mode plus local validation. A bounded-schema summary of
the synthetic sentence "The library opens at 9 am." also returned correctly
shaped claims with the supplied ID.

**It nevertheless invented closing hours, weekday/weekend rules and other
details not present in that sentence.** Those claims can pass a shape/ID check
because they cite an existing ID. This is actual model output, not a canned
reply, and it demonstrates why schema enforcement does not establish semantic
support. No human score or factual-quality pass is claimed.

The initial unbounded-schema probes failed before yielding an accepted summary;
the bounded output envelope is part of the implemented contract. Runtime behavior
and full benchmark results are reported separately in the PR, with exact heads,
model digest, corpus and prompt/schema identities. Use the existing
[local E2E and benchmark commands](local-model-e2e.md); human source checks in
the evaluation protocol remain necessary.
