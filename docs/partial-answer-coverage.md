# Gap-first partial answers — evidence-led v2

The extractor declares question answerability: `full`, `partial` or `none`.
This is a model judgment about the requested subject/comparator, not merely the
presence of true facts. Partial coverage requires an explicit gap. No direct
facts or `none` skips synthesis and returns evidence insufficiency.

Synthesis may cite only direct fact IDs. Context facts remain in the auditable
ledger but cannot be promoted into claims. At most four focused claims preserve
needed scope and adverse findings. Partial summaries prepend the extracted gaps
to limitations, retain source-supported study caveats rather than duplicating
those gaps as synthesis paraphrases, and add `answer_scope="partial"` and `answer_lead` containing the
first extracted gap. Full summaries have scope `full` and no lead; abstention has
scope `unavailable`. These fields are additive; status/citation/approval contracts
and the existing dense/BYOK defaults are unchanged. Extraction/validation failures
still retain an error and do not pretend to be successful abstentions.

Business generation receives that complete summary and is restricted to at most
three conditional implications. It must foreground partial coverage and avoid
detailed adjacent-study commentary as a substitute for the requested decision.

This is not a deterministic semantic-entailment or relevance oracle. Incorrect
model declarations can still misclassify background as direct. Source-check the
actual claims, coverage gap and abstention. In particular, one comparison must
not replace a different requested comparator, framing consistency is not
mechanistic interpretability, and unlearning attacks are not confidentiality
measurements or useful task adaptation. Prompt hashes/version v2 identify new
runs; older v1 ledgers are historical artifacts, not silently migrated outputs.

## Bounded quote correction

Evidence-led v3 permits one correction only after a schema-valid extraction
fails the unchanged displayed-source quote validator. The rejected structured
output and generic validation error are provided as untrusted feedback alongside
the original visible evidence. The complete replacement must pass the same schema
and quote validator before synthesis. No capitalization, math, citation, punctuation
or hidden-tail mismatch is repaired locally. A second rejection still emits no
findings; provider, parsing/schema and synthesis failures are not retried.

Successful results record `extraction_validation_attempts` (1 or 2); provenance
records the policy and implementation hash. The configured generation adapter's
receipts retain both model calls. This can add one extraction call per request.
Correction is not proof of semantic entailment: setup-only evidence is contextual,
and limited-data efficacy requires a quoted data-scale result. Review real claims
separately; a correct abstention is not successful retrieval of missing evidence.

## Conditional due-diligence boundary

For a business question asking what to check, quote-supported technical validation
workflows, studied scope and expressly stated limits can supply a **partial**
technical basis even when a paper does not literally list vendor questions.
Extraction/synthesis retain factual findings only. Business translation supplies
separately labeled conditional checks and transfer assumptions. The coverage gap
must state that the evidence does not establish vendor compliance or validation
of the deployed system; interpretability is not a behavioral guarantee.

This does not make arbitrary background direct, supply a missing comparator or
efficacy result, or fill proprietary-training privacy gaps. Validators and the
unapproved-review state remain unchanged. `tests/test_conditional_due_diligence.py`
checks the rendered prompt contract and strict pipeline shape with scripted replies;
it is not a model-quality test. A separate bounded q10 capture is needed to assess
whether the model actually applies this boundary faithfully.
