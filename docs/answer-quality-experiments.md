# Answer-quality experiments

These opt-in routes address source-selection and synthesis errors without
changing the existing dense/BYOK defaults or weakening output validation.
Synthetic review is the working quality evaluation. It is recorded as AI review,
never attributed to a human reviewer or stakeholder.

## What changes

- `src.hybrid_retrieval.HybridRetriever`: BM25 + dense candidates (25 each),
  reciprocal-rank fusion, an optional local cross-encoder, and lexical candidate expansion for interpretability, SAEs, limited-data terminology and multi-agent
  coordination risks. Final selection follows the cross-encoder (or RRF),
  without keyword-based overrides. No benchmark
  IDs, known answer IDs, or fixed per-paper caps are used.
- `src.evidence_led.summarize`: extraction first, then synthesis from an exact-
  quotation ledger. Unknown citations, fabricated quotations, quotations from
  text hidden by truncation, and unsupported study-limitations without evidence
  locators fail closed. v2 additionally classifies full/partial/unavailable query
  coverage, leads partial answers with the extracted gap, and permits only direct
  facts in at most four summary claims. Source membership does **not** prove semantic entailment.
- `src.evidence_led.translate`: the existing strict business contract, with a
  scoped comparison/check and a decision metric instead of an unsupported
  deployment prescription. Partial evidence may support conditional advice.
- `src.codex_generation.create_codex_generate`: an explicit local experiment
  adapter using an existing ChatGPT Codex login. No API-key provider fallback.
  It allowlists runtime/auth-location environment variables, uses an empty
  temporary working directory, read-only ephemeral execution, and ignores user
  config. Shell/exec, code mode, integrations, browsing, computer use,
  multi-agent, hooks, image access and memory features are disabled before
  evidence is supplied. Unexpected tool-using output is also rejected. The CLI still needs network access to the model service.

## Run locally using a Codex subscription

Use Python 3.12 and installed project requirements. Supply the actual installed
CLI path and an account-accessible model; model availability is not inferred
from its name. This route uses subscription limits and is not a deployed API
replacement. It belongs on the account owner's trusted local machine, not in
public CI or on shared runners. Never copy authentication files into this repo.

```sh
python main.py --query 'How are sparse autoencoders used to interpret model behavior?' \
  --mode business --industry 'professional services' \
  --generation-route codex --codex-model gpt-6.1-sol \
  --codex-bin /absolute/path/to/codex \
  --evidence-led --retrieval-mode hybrid \
  --reranker-model cross-encoder/ms-marco-MiniLM-L6-v2
```

The reranker is local and may download its weights on first use. Retrieval
signals, including cross-encoder scores, are never confidence probabilities.
The benchmark experiment verifies the persistent index against the frozen
corpus before using hybrid retrieval. The regular CLI records corpus identity
as unverified rather than asserting that same stronger reconciliation proof.

## Controlled comparisons

`evaluation.compare_answer_variants` compares explicitly named Codex models on
identical frozen evidence and the unchanged baseline summary prompt.

`evaluation.run_answer_improvements` supports:

- `model-only`: new generator, original dense evidence/prompts.
- `evidence-led-frozen`: new evidence-led generation, original dense evidence.
- `evidence-led`: new generator, hybrid retrieval and evidence-led generation.

All modes require the integrated frozen baseline and its retrieval-only export.
The latter recovers the retrieved passages for a failed integrated case without
silently pretending that case was successfully generated in the original run.
Input run hashes, corpus hashes, code/prompt hashes and per-invocation usage/
latency receipts identify each experiment. Output directories refuse overwrite.
`run.json` checkpoints accumulate during execution; only a completed run is a
finished comparison. Original baseline artifacts are never edited.

Model-only isolates the generator change. Comparing it with evidence-led-frozen
isolates the extraction/synthesis change. Comparing frozen vs hybrid evidence-led
isolates retrieval. A combined treatment alone cannot identify which component
caused a gain. Assess exact source support, question responsiveness, omissions,
scope and abstentions; counting valid JSON or nonempty answers is insufficient.

## Evaluation-led specialization and acceptance criteria

Fine-tuning is successful only when it improves the targeted failure categories
on held-out source families, without materially degrading factual support,
qualifier retention, abstention behavior, or operating efficiency.

This is an experiment protocol, not a report of completed training or a change
to model defaults. The existing runners above do not by themselves implement a
local tuned-model comparison. Establish contract-aware adapters and retained
evaluation artifacts before claiming that comparison is complete. Four-task
smoke runs establish neither generalization nor plain-language quality.

### 1. Diagnose baseline failures before choosing a treatment

Retain each baseline input, supplied passages, raw response, validation outcome
and review. Label the failing stage and one or more observable failure categories:

| Category | Evidence to inspect | Candidate intervention |
| --- | --- | --- |
| Missing or irrelevant evidence | Corpus availability and retrieved passages versus the question | Corpus/retrieval repair; not automatically training |
| Missed supplied evidence | A relevant supplied passage omitted from extraction or the answer | Extraction/prompt changes; tuning if the pattern persists |
| Unsupported claim or definition | Claim versus its cited passage, not just quote membership | Grounding/prompt/contract changes; reviewed training examples |
| Lost qualifier or distorted meaning | Negation, uncertainty, numerical bounds, conditions and disagreement | Targeted extraction/synthesis or presentation examples |
| Wrong coverage or abstention | Supported, partially supported and unavailable aspects of the question | Coverage calibration and targeted examples; neither blanket answering nor blanket abstention |
| Malformed output or contract violation | Raw output versus the task schema and failure contract | Adapter/schema/prompt repair; tuning for persistent model errors |
| Unreadable presentation | Meaning-preserving output versus the intended reader's needs | Presentation-specific examples and separate readability review |

Distinguish model errors from provider failures, timeouts and harness defects;
retain all of them in the operational report. Select training targets only after
checking whether retrieval, prompting or deterministic validation addresses the
observed problem. Do not train a generator to compensate for absent sources by
inventing evidence.

### 2. Freeze a versioned evaluation set

Before model/prompt/adapter selection, version the case manifest, source and
passage hashes, input/result identities, task schemas, rubric and split policy.
Record provenance and whether each case is real-source or synthetic. Use three
disjoint source-family splits: training, development and untouched final test.
Keep related versions, near-duplicates, overlapping passages and technical/plain
pairs in the same split. Source families, not individual chunks or paraphrased
questions, are the leakage boundary.

Use development cases for error analysis and all selection decisions. Lock the
candidate, inference configuration, thresholds and final-test manifest before
opening final-test results. If final-test findings drive another revision, that
set becomes development evidence; obtain a new untouched test set before making
a fresh generalization claim. Do not claim unseen-family performance for probes
over a training corpus.

Maintain a coverage table with case counts for extraction, QA, synthesis and
plain-language presentation, crossed where applicable with supported, partial
and unanswerable evidence, conflicting/qualified sources, numerical claims and
technical difficulty. Inspect sparse cells explicitly. Synthetic cases can fill
contract/edge-case gaps but must be scored separately; they do not establish
performance on real research. Set sample sizes before the comparison and report
uncertainty rather than treating a small smoke set as decisive.

Training targets require review against supplied sources. Generated drafts are
not automatically correct labels. Record reviewer type, rubric version,
corrections and unresolved disagreements; AI review must never be relabeled as
human review. Keep test cases and their answers out of training and selection.

### 3. Compare on identical evidence with two layers of scoring

Compare untuned 9B, tuned 9B and untuned 27B with identical frozen task inputs
and evidence. For presentation, freeze the validated original result too; do not
regenerate a different summary for each model. Keep task-level results separate
so presentation gains cannot conceal extraction or synthesis regressions. Use
the controlled comparisons above to distinguish retrieval, prompt and generator
effects; label any combined treatment as such.

- **Deterministic checks:** schema, allowed citation IDs, literal quote membership,
  ordered claim/citation mapping and applicable identity/invariant checks. Retain
  malformed outputs as failures; do not quietly repair or drop them.
- **Semantic/readability review:** assess claim-to-source entailment, question
  responsiveness, omissions, qualifier/number retention, correct coverage and
  abstention, and presentation readability. Score readability separately from
  meaning preservation. A valid quote can still fail to support its claim.

Use explicit rubric anchors and reviewed examples. Calibrate AI judges against
reviewed cases and retain judge identity/settings and disagreements. Blind model
identity and randomize output order where feasible; obtain second review on
adverse, ambiguous and sampled passing cases. Report AI-only results as AI review
with uncertainty, not independent human acceptance. Judge valid outcomes, not
exact agreement with one reference wording or tool path.

### 4. Measure repeated-run reliability and operating cost

Predeclare a repeat count and run every model/case at intended inference settings
under the same retry, timeout and output-budget policy. Record exact model/base
and adapter identities, quantization, chat template, code/prompt/schema hashes,
decoding settings/seeds when supported, hardware/runtime, memory, latency and
usage for every attempt. Retain raw outputs and failures; checkpointed or partial
runs remain incomplete comparisons.

Report per-task/category and overall case counts, attempt success rates, and the
fraction of cases passing **every** scheduled repeat. Pair comparisons by case
and report uncertainty clustered by source family; repeated outputs are not new
independent research cases. Do not infer reliability by raising an aggregate
success rate to a power: that assumes independent runs with fixed success
probability, while failures can be correlated. Best-of-N success is not normal
single-attempt reliability unless that selection policy is actually used and
its costs are included.

Report latency distributions, peak memory and total operating cost per successful
task, counting failed attempts and retries in the numerator. State what counts as
success, the cost units/assumptions and the fixed workload; a zero-success run has
no finite cost-per-success estimate. For local inference, report measured time
and resource use even when no monetary estimate is available. Report training
and data-review costs separately, with an explicit workload assumption if making
an amortized savings claim.

### 5. Predeclare the selection gate

Before viewing final-test results, record the target categories, primary metric,
minimum worthwhile gain, per-category regression tolerances, reliability floor,
latency/memory/cost budgets, sample/repeat counts and uncertainty method. Define
numerical values and the rule for inconclusive results; unspecified thresholds
do not constitute a passed gate. Semantic failures remain visible even if an
aggregate score improves.

Select tuned 9B only when the held-out comparison meets those criteria against
untuned 9B, with no material regressions in factual support, qualifier retention,
coverage/abstention or other tasks. Use untuned 27B as the explicit quality/cost
alternative, not an assumed winner or an obligatory quality ceiling. Retain a
decision record for all three models, including adverse cases, uncertainties and
why any quality/efficiency tradeoff is acceptable. If evidence is inconclusive,
retain the current configuration; do not turn lack of proof into success.

The sequence is **failure analysis → frozen evaluation set → untuned baselines →
reviewed training examples → tuned comparison → recorded selection decision**.
A selected model still needs explicit integration, contract regressions and
source-backed review; passing this gate does not authorize training, compute
spend, deployment, publication or a silent default change. The presentation
contract and its additional invariants live in
[the fine-tuning handoff](plain-language-view.md#fine-tuned-model-runbook-handoff).

### Current extraction pilot: LLM-only evaluation

For the local extraction pilot, Jacqueline explicitly selected **LLM judges only**
on October 28, 2026. Neither Jacqueline nor teammates are required to hand-label,
judge, calibrate, or approve experiment answers. Use deterministic checks, blinded
LLM rubric judgments, order-swapped comparisons and further LLM review of
disagreements. Unresolved cases remain inconclusive rather than becoming a human
review queue. Record the absence of human-labeled calibration as a property of
the method, not an outstanding task for the team.

The executable pilot, frozen protocol, result record and reproduction commands
are in [the extraction experiment](../experiments/qwen-extraction/README.md).
Its small development set and three-step training smoke do not establish a
tuned-model quality gain or authorize changing application defaults. Existing
application review/approval fields are not changed by experiment judging.

## Quality safeguards and remaining limits

Quote membership is deterministic; semantic support remains an AI-review task.
Generic rerankers may favor adjacent topics; lexical expansion is not proof of
relevance. Keep results that underperform. Do not suppress malformed responses,
convert missing stages to scores, treat abstention as inherently good or bad,
or move a study's limitations to another paper. New questions over the same
corpus are useful probes, not proof of generalization to unseen research.

These experimental modules leave the existing approval fields unchanged. No
approval or external publication is inferred from synthetically scored outputs.
