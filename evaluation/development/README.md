# Development evaluation inputs

`questions.json` contains the existing 15 first-review-approved development
question texts, categories and required-point counts. Original text is preserved.
It does not include expected answers, point wording, evidence quotes, answer keys,
reviewer notes, generated answers or scored results. Private keys and adjudication
records remain local. No other question split is bundled or loaded by this tool.

Validate the shared specification without retrieval or generation:

```sh
python -m evaluation.development
```

The quality rubric awards 1 for a met requirement, 0.5 for partial coverage and 0
for a missing requirement. A reviewer needs the original approved private rubric
to assign credits: the software does not infer credits from answer text or from
an automated full-coverage label. Sharing the approved answer keys is a separate
decision; they are not published here.

To aggregate an explicitly supplied local review list:

```sh
python -m evaluation.development --reviews data/processed/local-review/point-credits.json
```

Each object has `id`, `point_credits`, `abstention`, `notes`,
`human_confirmed: false`, and `confirmation_status: pending`. Credits must match
the question's required-point count and use only 0/0.5/1. For answerable cases set
`abstention` to `not_applicable`. For zero-point controls use an empty credit list
and `correct`, `incorrect` or `not_checked`. Abstention outcomes stay separate from
answer-point coverage. Partial review sets are labeled incomplete, not silently
reported as a full benchmark. Unknown or duplicate IDs are rejected.

This utility only aggregates provisional assessments and cannot mark them human
confirmed. Independent review uses the existing review/adjudication workflow.
`citation_membership` checks locator resolution and exact quote presence, not
semantic entailment or truth.

For reproducible comparisons retain local question IDs, rubric version, corpus
and embedding hashes, retrieval implementation, model/prompt settings, source
records, call counts and timings. Report pipeline-only and startup-inclusive
latency separately. Do not train or tune on unseen evaluation questions. Do not
mix negative controls into numerical required-point denominators.

No scoring keys or raw outputs are needed to validate this public specification.
Reproducing historical answer scores requires separately authorized private
artifacts and review records; this repository update does not publish them.
