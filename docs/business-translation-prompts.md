# Business translation prompt strategy (#79)

Two immutable version-1 design candidates live in `prompts/business_translation/`:

| ID / version | File | Intended difference |
|---|---|---|
| `business-translation/baseline` / `1.0` | `baseline-v1.txt` | Direct, bounded advisory translation with evidence checks |
| `business-translation/counterevidence` / `1.0` | `counterevidence-v1.txt` | Counterevidence-first framing for conflicting or context-sensitive studies |

Baseline is the **proposed** default, not a performance winner. Neither was run
against a live model or scored by reviewers. The examples are synthetic design
expectations, not actual research findings, generated outputs, or measured quality.
Change the version/file for substantive revisions; record the selected ID/version
and template hash with future run artifacts.

## Translator handoff (#80)

The translator retains `translate(summary, passages, *, industry, generate)`.
Reject missing/blank industry before rendering. Use Python `string.Template`
with `industry`, `summary_json`, and `evidence_json` substitutions, where the two
JSON values are produced by `json.dumps`, not ad-hoc string concatenation. Ordinary
JSON braces intentionally remain literal. Substituted data is not re-templated.

`generate` takes the resulting prompt and returns response text. The translator
must parse JSON and validate status, exact industry, required fields/types,
nonempty implication citations against supplied chunk IDs, and abstention shape.
Reject unknown IDs, malformed/provider-failed output, or unsupported fields; do
not silently strip citations or fill missing scores. Semantic support still needs
human source review. Keep the research and regulatory evidence namespaces distinct.
This pack contains **no runtime adapter or shared-config changes**; adoption remains
the small #80 handoff. Both prompts use the Week 6 BusinessInsight shape, with
suggested_action as a string and assumptions as an array of strings.

## Fixture checks and expected behavior

`fixtures.json` supplies three self-contained scenarios. Each EvidencePassage
uses the shared fields and explicitly labels synthetic sources/IDs. Example
responses are handwritten expectations, not recorded model results.

```sh
python prompts/business_translation/validate_fixtures.py
```

The check validates template substitution, fixture/expected-output structure,
industry preservation, known cited IDs, and empty implications on abstention.
It does not test provider obedience or certify source support.

| Scenario | Expected qualitative behavior | Negative control for human comparison |
|---|---|---|
| Bounded benefit | Describe the simulated setting, cite the finding, propose an industry-specific pilot; retain transfer limits | Guaranteed savings, deployment recommendation, or uncited numerical benefit |
| Weak evidence | Abstain with empty implications and describe unavailable business evidence | Elaborate a plausible industry benefit from an unsupported summary |
| Conflicting findings | Cite both studies, preserve disagreement and conditions, recommend a controlled pilot | Select only the favorable study or average incompatible measurements |

## Rubric mapping and future comparison

Use the existing [evaluation framework](../notebooks/docs/evaluation_framework.md),
without replacing its targets (Precision@5 >=0.7, scored rubric average >=4).
Prompt design is not a retrieval measurement.

| Existing dimension | Prompt choice / review question |
|---|---|
| Accuracy | Verify implications in original passages, not only summary; does counterevidence survive? |
| Clarity | Plain language and separate findings/actions/assumptions; can an advisor explain the limitation? |
| Completeness | Retain weak/conflicting evidence, study limits and missing transfer conditions; no false completeness from abstention |
| Actionability | Specific, proposed validation step rather than generic commentary or unsupported rollout |
| KPMG relevance | Explicit industry and concrete advisory decision; relevance is not endorsement |
| Citation quality | Exact supporting chunk IDs, both sides of conflicts, original-source check; a valid ID is insufficient |

For a future comparison, freeze fixtures, model/config, and generation settings;
run each template on the same inputs; retain raw responses, failures/abstentions,
prompt ID/version/hash, and independent named human ratings. Score only available
reviewed outputs and disclose denominators. Inspect qualitative failure types as
well as means; do not declare a winner or stakeholder approval before that run.
