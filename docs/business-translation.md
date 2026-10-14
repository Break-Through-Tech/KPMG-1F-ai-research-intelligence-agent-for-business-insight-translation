# Business translation runtime (#80)

`src.business_translation.translate(summary, passages, *, industry, generate)`
implements the shared BusinessInsight contract without importing a provider,
retriever, or model. `generate(prompt)` is injected and must return JSON text.
No shared workflow, prompt-library, dependency, or configuration files change.

## Selected prompt and provenance

The adapter adopts #79's proposed default, `business-translation/baseline`, version
`1.1`, from `prompts/business_translation/baseline-v1.txt`. This is a design choice,
not a measured winner over the counterevidence candidate. JSON-serialized summary
and complete passages are substituted with `string.Template`; input dollar signs
are not re-templated. Inputs and original source metadata remain unchanged.
`prompt_provenance()` returns the selected ID/version and actual template SHA-256
for capture owners to record alongside their generation settings. The existing
CLI records the adapter name but does **not** automatically add that template hash;
it still identifies an external adapter's prompt version as unspecified.

## Validation and limits

- Require explicit nonblank industry; preserve it exactly in the result.
- Empty evidence or an insufficient summary returns empty implications and an
  explicit limitation without calling generation.
- Reject malformed input, duplicate evidence IDs, unknown/duplicate citations,
  malformed JSON, duplicate JSON keys, nonfinite JSON constants, missing/extra
  output fields, and invalid actions, assumptions, risks, or limitations.
- Provider abstention requires empty implications and explicit gaps. Provider
  exceptions become sanitized `PipelineError` messages, never raw payloads.
- The baseline instructs the generator to retain conflicting findings and both
  citations, distinguish findings/actions/assumptions, and avoid unsupported ROI,
  confidence, compliance, endorsement, or approval. These semantic properties
  cannot be established by schema validation; human source review remains needed.
- No approval/confidence fields are accepted. The existing workflow retains
  pending human review and `approved=false`. #81 owns explicit human review.

## Run through the existing CLI

After building the local corpus/index and configuring a generation key:

```sh
python main.py --query "Should we pilot an AI triage assistant?" \
  --mode business --industry Insurance \
  --translation-adapter src.business_translation:translate
```

This defaults to the grounded `src.summarization:summarize` adapter already on
main; `--summary-adapter` overrides that default. It can make billed provider
calls; it was **not** used for this PR's offline
verification. No actual corpus/model business translation or quality claim is made.

## Inspectable offline fixture outputs

Run from the repository root with standard-library Python only:

```sh
python -m unittest tests.test_business_translation -v
python prompts/business_translation/validate_fixtures.py
python - <<'PY'
import json
from src.business_translation import PROMPT_PATH, prompt_provenance, translate
fixtures = json.loads((PROMPT_PATH.parent / 'fixtures.json').read_text())
for fixture in fixtures:
    result = translate(fixture['summary'], fixture['evidence'],
        industry=fixture['industry'],
        generate=lambda prompt: json.dumps(fixture['expected']))
    print(json.dumps({'fixture': fixture['id'], 'execution': 'canned_fixture',
                      'prompt': prompt_provenance(), 'result': result}, indent=2))
PY
```

The three existing synthetic scenarios exercise bounded benefit, weak evidence,
and conflicting findings. For the two supported summaries the injected generator
returns the **handwritten expected response**, not actual model output. Weak
evidence skips that callable and emits the adapter's own abstention. For example,
the weak-evidence result is:

```json
{
  "status": "insufficient_evidence",
  "industry": "Retail",
  "implications": [],
  "risks": [],
  "limitations": [
    "No evaluated retail outcome.",
    "No supported summary available; translation skipped."
  ]
}
```

Offline checks verify contracts, transport, and failure handling—not provider
obedience, citation support, useful advice, human scores, or stakeholder approval.
Semantic quality evaluation remains in #65; #78 retains real integration acceptance.
