# Blinded review

Use the execution directory's `blinded` folder. `review.json` contains the
final answer text, citations, limitations and outcome for each opaque label.
`synthesis-evidence.json` contains its corresponding actual passage packet.
`scoring-worksheets.json` contains the frozen reference points and source
locators, with exact required chunk presence prefilled. A missing exact chunk
can still have a sufficient alternative passage. A matching quote alone does
not establish semantic support.

Record reviews in a separate file. Keep the generated worksheet and frozen
reference files as read-only inputs. Mark each point correct, partial,
incorrect, omitted or inconclusive. Record citation entailment, alternate
evidence, unsupported statements, justified and false refusals, and complete
success under the locked rule. Record the reviewer identity and whether the
review was human or model-assisted. Do not grant credit based on unreviewed
drafts, automated verifier verdicts, or shadow decisions.

Nine references require a second human review. Treat them as provisional
until that review is completed. If a reference is disputed, record the
disputed point, both interpretations and exact source evidence, and mark the
case inconclusive. Do not revise the locked reference or omit the case from
the scheduled denominator.

Keep the restricted runtime artifacts and arm mapping closed during answer
review. The review package masks explicit arm labels, stage traces, order,
latency and usage. Wording or format may still hint at which path produced
an answer. Lock the applicable reviews before revealing the arm mapping or
applying the product decision thresholds.
