# Blind engineering review

Score each anonymous response against its case packet and the supplied rubric.
Use a separate copy of scores.csv. Record your AI reviewer ID on every row.
Review only this archive. Work independently from the other reviewer and disclose
any exposure to the historical outputs, prior scores, or arm identities.
Record the exact output text and evidence chunk ID for material concerns and
avoid inferring the system from writing style.

Apply five 1–5 dimensions, the four 0/1/2 defect ratings, the critical-claim
flag and the abstention judgment as defined in the original rubric. Eligible
evidence-bearing abstentions receive scores for the response actually delivered.
The empty control and failed or unattempted responses use NA for all five
dimensions. Record absent defects as 0. Appropriate abstention is yes or no for
insufficient_evidence or skipped_no_accepted_evidence. Use not_applicable otherwise.
A pilot is appropriate when it resolves an actual uncertainty and gives a decision
criterion. Judge missing advice and true repetition independently.

Record four additional observations using yes, no, or not_applicable.

- application_condition asks whether needed organizational facts remain open
  conditions or evidence requests. Use not_applicable when no unknown condition
  affects the proposed action. An invented workflow premise is no.
- decision_action asks whether the delivered action answers the stated decision
  and names a concrete comparison, evidence request, change, or reason to defer.
- research_scope asks whether findings retain the material metric definition,
  comparator, experimental setting, and counterevidence.
- evidence_gap asks whether the answer identifies the most important missing
  information that affects the decision and scopes the limitation accurately.

Use not_applicable for observations on the empty control, failures and deferred
calls. For eligible abstentions, score the observations that the output can
support. An avoidable abstention with no actionable next step is decision_action=no.
A cautious caveat can receive research_scope=yes or evidence_gap=yes when justified.
The observations inform engineering interpretation. The frozen scoring dimensions,
defect flags and thresholds determine quality results.

The operator preserves both original AI assessments, resolves dimensional gaps
greater than one point and every categorical disagreement using the evidence,
and seals the adjudicated scores before opening system identities. The original
human acceptance protocol still requires people. This run reports AI-assisted
engineering results.
