# Frozen business translation evaluation

This is an evaluation-only package for implementation 82702dc. It does not modify
or invoke research generation, indexing, S2/R2, Azure or the Gemini research campaign.
No live API calls have been made. Run `python business-evaluation/v1/run.py` for
offline preflight only; the default path never initializes a provider.

## Inputs and verification

Twelve packets are fixed in frozen/packets. Five follow the KPMG examples; seven
questions are newly authored and held out from translation generation and tuning.
The latter use known papers and are not an unseen-paper or independent-author
benchmark. This distinction must remain in every report. Their wording has not
been run through either translator. No expected business responses are hardcoded.

Evidence comes from six original local PDFs, not tests/fixtures. Seven relevant
pages were inspected as rendered pages; exact excerpts were independently checked
using PyMuPDF and pypdf. Source verification records hashes, PDF page locators and
primary-source excerpts. Semantic checks were performed by the preparing assistant
against the papers, not by an independent human. Local PDF identity has not been
revalidated against a publisher over the network. Peer-review status is not implied.
The source-page contact sheet is supporting inspection evidence, not a substitute
for the original PDF. No table is inferred from incomplete text extraction.

The comparative architecture evidence was located in a saved accepted research
capture and regrounded in its original PDF. The five reference papers were available
as original PDFs; manual source-checked accepted packets were prepared rather than
rerunning research. These are explicitly labeled manually accepted research inputs,
not model-generated research outputs. The empty case means no accepted evidence
was supplied, not that the literature has no relevant results.

Both arms receive the SAME projected accepted summary, quote-bounded passages,
question, industry, workflow and decision. shared_input_sha256 checks this identity.
Baseline is the existing baseline-v1.txt translator, compact=False; candidate is
the full downstream v1.1 stage, including its safeguards and failure isolation.
This evaluates the two deployed translation approaches, not just prompt wording.
The model/provider/configuration is the same for both and fixed before generation.
No research, context extraction, regulatory or reviewer-model calls are allowed.

## Freeze and provider requirements

frozen/manifest.json hashes questions, packets, rubric, blank scoring sheet, source
receipts, scripts and provider-config template. It also pins implementation and
prompt file bytes. Any change fails preflight. The exact run config is copied into
the private run directory before dispatch. Selecting a provider later does not
change the frozen research/question/rubric inputs; it creates a separately hashed
run config. Do not change it after seeing any output.

Fill a COPY of provider-config.example.json with a supported account-accessible
OpenAI or Gemini model and a clearly identified, separately authorized project.
Use BUSINESS_EVAL_API_KEY only. No .env loading, ambient-key fallback or endpoint
redirection is allowed. The runner rejects equality with common research credential
variables; project separation still requires an operator confirmation because key
strings alone cannot prove billing-project ownership. Do not copy campaign secrets
or use its free-tier quota. SDK attempts are one and temperature is zero. The shared
adapter does not expose successful token usage, so do not invent token/cost figures.
Both generation arms use the same response transport and provider defaults.

Only AFTER explicit approval for live calls:

    python business-evaluation/v1/run.py --execute --config <approved-config.json> --run-dir business-evaluation/runs/initial-pair --approved-manifest-sha256 <manifest-file-sha256>

The runner makes a persistent, exclusive campaign lock before initializing a
provider; it cannot start another initial run automatically, even in another
directory. Each attempted call gets an exclusive durable reservation BEFORE
network dispatch. SDK errors, invalid JSON and ambiguous attempts consume budget.
There is no automatic retry, repair, resume, replacement case or critic call.
If interrupted, inspect private artifacts before any decision to do further work.

Expected budget: 11 evidence-bearing cases x 2 arms = 22 translation calls.
The empty-evidence case produces two documented skips with zero calls. Absolute
ceiling: 24 attempted calls; the two unused slots are NOT retry authorization.
The one-shot schedule contains 24 case/arm outcomes, including the two skips.

## Blind review and scoring

run_dir/blind contains neutral Q01-Q12 case books and A/B outputs in the same
BusinessInsight schema. It omits prompt names, models, policy/screening metadata,
reference split and arm identity. Case order is randomized; first-run arm order
is balanced six/six. Only the operator receives private/blind-key.json, raw model
responses, candidate audit and timing/accounting. Do not share private/ with reviewers.
Anonymization cannot conceal stylistic differences; reviewers must not infer labels.

Give each reviewer a separate copy of frozen/review-sheet.csv and rubric.json;
assign actual reviewer IDs instead of placeholders. Two people independently review
every outcome. The sheet includes both people for convenient collection; do not
expose the other's scores. No fabricated human names or assistant ratings count.
Case books supply the question, accepted findings and original evidence citations.
The empty-evidence pair gets NA usefulness ratings and a separate abstention judgment.
A failed eligible output remains in availability denominators, not scored as an
invented response. If only one arm responds, do not fabricate a paired difference.

Usefulness is the mean of business relevance, action specificity and proportionality.
Fidelity and material limitations are scored separately. Explicit 0/1/2 defect
ratings capture generic advice, workflow parroting, semantic repetition and pilot
overreliance. A pilot is not intrinsically wrong: judge whether it is the right next
action. Source-supported conditional cross-industry interpretation is legitimate.
Critical unsupported financial, compliance, readiness or scientific claims are
separate vetoes, not averaged away by clear prose. Record exact output/evidence spans.

Report all 12 cases and 24 outcomes, with the 5/7 splits separately. Acceptance
criteria are frozen in rubric.json. A >1-point dimension difference or critical/
abstention disagreement requires adjudication; retain originals and resolver notes.
The comparison is descriptive at this size and cannot establish generalization,
production readiness or KPMG approval. Stop after the single paired comparison;
implementation changes require a separate decision after independent review.

## Current genuine dependencies

Assets are source-checked and frozen. Live execution remains blocked until there
is explicit API approval, a confirmed independent provider/project/model config,
and two actual reviewers with an adjudication owner. Independent human verification
of scientific support is still required for human acceptance claims. No scores,
live outputs, reviewer identities or provider availability have been invented.

## Score collection

`python business-evaluation/v1/score.py --run-dir <run> --reviews <reviewer1.csv> <reviewer2.csv> --output <new-report.json>` validates complete independent coverage and rating ranges, reports splits and disagreements, and refuses to infer approval. Give each reviewer only their own rows. The operator performs the frozen acceptance checks after adjudication; original reviews are never overwritten. Counts of material defects are review-record counts, not unique-case rates; inspect case-level agreements for the acceptance gate.
