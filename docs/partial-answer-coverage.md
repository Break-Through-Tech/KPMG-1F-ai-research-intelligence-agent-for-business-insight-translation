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
