# Issue #106: reproducible retrieval acceptance

The opt-in implementation landed in #109. Landing code does not establish
semantic relevance. This follow-up compares the unchanged hybrid cross-encoder
baseline with source-checked intent ranking over **all ten original questions
plus four new controls**, using the same frozen corpus and top-five budget.
Neither route changes default application behavior.

## Capture once, preserve adverse results

```sh
python -m evaluation.compare_intent_retrieval \
  --reference /path/to/frozen-integrated/run.json \
  --output /path/to/new-private-comparison \
  --codex-bin /path/to/codex --model gpt-6-luna
```

Requires the existing validated Parquet/metadata, reconciled Chroma index,
cached embedding/cross-encoder weights and existing ChatGPT subscription login.
The reference's artifact hash, input hashes and indexed text/citation digest
must match before generation. No API-key route, download, index rebuild,
default change or source-slot override is introduced.

`run.json` retains every question, both selections, implementation/model/weight/
prompt/corpus provenance, and explicit errors. `traces.json` retains every
candidate, assessment, prompt, response schema and returned raw model response;
`receipts.json` retains provider call status and hashes. Keep these files private
by default: they contain source text and experimental outputs, not product code.
Checkpoint after each paired case, including rejections, and continue later
cases. Output directories refuse overwrite. The existing single quote-correction
policy remains unchanged; failed cases have no fallback and no individual rerun.

## Predeclared source review

Do not infer acceptance from a zero process exit, nonempty selection, a known
source ID, ordinal score or quote membership. Inspect actual displayed source
text against the whole question, including selected **and missed** candidates.

For q02 and `intent_coordination`, check whether results/limitations concerning
cooperating-agent outcomes are selected rather than setup alone. For q03 and
`intent_low_data`, check whether useful task adaptation/data-scaling comparisons
are retrieved, not just unlearning/relearning attacks. For q10 and
`intent_mechanistic`, distinguish internal mechanism/causal evidence from
behavioral consistency and business wording. For `intent_tool_security`, verify
that actual untrusted-skill/tool threats survive instead of being displaced by
coordination material. These are review criteria, never ranking overrides.

Review all ten original questions for regressions as well as these controls;
record irrelevant selections and available-but-missed evidence. A study-bound
partial answer is useful but not broad answerability. Corpus gaps remain gaps.
Record reviewer identity/type and the exact run ID. Synthetic source review
is not human or stakeholder approval. Retrieval acceptance alone is not
generated-answer, deployment, universal relevance or human acceptance.

Close #106 only after the uniform run and source inspection support its bounded
criteria; if a ranking rejects or a required intent fails, retain it and keep the
issue open. A later separately declared experiment must not replace rows in this
comparison. No closing keyword is justified by the harness tests alone.
