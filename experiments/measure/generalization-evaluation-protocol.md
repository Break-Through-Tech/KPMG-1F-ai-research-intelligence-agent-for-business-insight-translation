# KPMG paired research evaluation protocol

Status: proposed. Evaluation questions and reference answers have not been selected. The evaluation has no live authorization under this protocol.

## Freeze before question selection

Use the recorded workspace snapshot as the starting candidate. Before selection, produce a write-once run manifest with exact dependency versions, the proposed harness digest, runtime source digests including untracked files, model weight and CLI digests, adapter settings, and corpus hashes. Run model-free isolation and budget tests. Stop on a mismatch. Freeze a second manifest with the approved candidate questions and reference files before either arm runs. Keep these files in a separate evaluation directory. Neither reference data nor scoring notes enter planner, synthesis or verifier prompts.

The corpus is the pinned demo-100 bundle under `D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100`. Parent, view and vector digests matched the on-disk manifest during protocol preparation. There are 100 versioned papers, 7,667 parent records and 11,030 search views. Use the existing local encoder and reranker snapshots. Source-cache presence is preliminary until each selected passage, cell and qualifier is verified.

## Question sampling and references

| Primary stratum | Count | Required source structure |
| --- | ---: | --- |
| Single-paper factual | 4 | One directly supported result or method |
| Numerical table comparison | 4 | Auditable row and column labels, units, conditions, and exact cell IDs |
| Multi-paper comparison | 4 | Material evidence from each of at least two papers |
| Methodology or limitations | 3 | Specific design constraint, scope condition, or stated limitation |
| Apparently conflicting evidence | 2 | Two findings with traceable scope and a reference explaining real disagreement or why the results are compatible |
| Evidence-based refusal | 3 | Related indexed evidence plus a demonstrably unmet requirement, such as an untested population, outcome, or condition |

Build a source-first candidate registry without running retrieval or seeing either arm's answers. Draw on versioned originals and the frozen parent inventory. Deduplicate by underlying claim, topic and comparison. Exclude any question used for troubleshooting, a demo, or development measurement and any close paraphrase. Exclude the four named debug topics and their core source papers from the new registry. Keep an exclusion log based on known open artifacts. Sealed questions and answers remain unopened. If exact disjointness from sealed paper sets is required, a custodian can apply a metadata-only paper-ID exclusion separately and return eligible IDs. Without that clearance, describe the set as new against the known open development material only.

Predeclare the seed `kpmg-demo100-generalization-v1`. Give each candidate a stable identifier built from its stratum, sorted versioned paper IDs and original source locators. Sort within each stratum by SHA-256 of the seed plus the stable ID. Sample in a fixed stratum order from the table, cycling one place per stratum so larger strata do not dominate the paper exclusions. For the primary set use each paper at most once, including both constituents of comparisons. If too few independently valid candidates survive, pause and document the shortage before changing a quota or reuse rule. Keep the original pool, ranking, exclusion reasons and next eligible reserves for audit. Use reserves only before results exist. Never replace a question because either arm has trouble answering it.

For each selected question preserve a minimal independently sourced answer, atomic required points, acceptable variants, versioned source links and hashes, exact quotes or table cell IDs, and compatible indexed chunk IDs. Independently recalculate numeric results and check units, scope, denominators and conditions. Record original-source span and indexed evidence as distinct fields. In refusal cases a reasonable source and corpus audit must establish the specific missing condition. The reference should describe the insufficiency of this corpus, avoiding claims about the whole literature.

A second reviewer should check all conflict and refusal cases, ambiguous table headers, derived values and disputed qualifiers before the set locks. If no independent human reviewer is available, record source-check and reviewer status separately, leave that status pending, and treat disputed labels as inconclusive. Machine-assisted references and judgments are never reported as human-verified.

## Primary paired comparison

| Setting | A · Baseline/B2 | B · Improved Multi-Agent |
| --- | --- | --- |
| Retrieval | Original B2 single-query route | Planner-directed searches and opt-in table-pair retrieval |
| Evidence | Top eight per search and at most eight distinct synthesis passages | Same cap and normal evidence merge |
| Publication | Existing Baseline synthesis and quality review | Existing research, model verification and corrected ordinary publication gate |
| Additional signals | Standard review details | Source-bound numerical shadow, recorded separately |
| Maximum invocations per question | 2, synthesis and conditional review | 3, planning, synthesis and conditional verification |

Use the same ChatGPT subscription provider, `gpt-6.1-sol`, low reasoning effort, 300-second CLI invocation timeout, and the adapter's implicit sampling defaults. Pin and record the compatible CLI version. Both arms use the same encoder and reranker. Keep context interpretation, industry translation, risk, charts, web and arXiv fallback outside this research-only evaluation. The primary comparison uses one synthesis round per arm, with no extra retrieval round after synthesis. Record that this leaves Multi-Agent's optional recovery round unevaluated. Its initial focused searches remain enabled. The extra planner and different review prompts are intentional architecture differences. The two systems may retrieve different passages or prompt lengths under the same passage cap.

Use a stable seeded ordering for the 20 questions and exactly ten A-first and ten B-first pairs. Run each pair sequentially. Save every search, candidate and delivered passage ID available at runtime, stage receipt, effective evidence cap, prompt byte count, provider usage, error category, wall time, draft, verdict and final answer. Retain stage-level timings and record cold model startup separately. Preserve output even when a run abstains or fails.

## Budget and stop rules

40 question-arm runs are scheduled. The proposal is a separate cap of 100 application-level CLI invocations, with two slots for each A run and three for each B run. Correct refusals and other draftless runs can skip verification. The three refusal cases alone would bring planned consumption to 94 if both arms abstain before review every time. The existing runtime has no strict HTTP-attempt guarantee because the CLI can retry internally. It also has no strict token ceiling. These distinctions are part of the approval.

For planning, the earlier six-run receipts averaged 17.7k input tokens per synthesis, 11.0k per plan and 18.2k per verification. Assuming 18–25k for a Baseline quality review, the 94–100 stage workload suggests roughly 1.5–1.8 million input tokens. Budget for roughly 20k–60k output tokens as a planning estimate. Report actual input, cached input, output and missing usage separately. The earlier questions were selected diagnostics, so they provide a sizing estimate only.

Before live execution, use a separate write-once run directory and reserve each authorized stage before calling the CLI. Count failures as attempts. Test duplicate, over-budget, out-of-order and restart refusal model-free. Do not use the existing authorization ledger. There is one run per question-arm, with zero application retries and zero selective reruns. Keep ordinary isolated failures as outcomes and move to the next planned cell. Stop on changed hashes, missing evidence identity, exhausted authorization, failed isolation, or a systemic login, rate-limit or provider outage. Report every scheduled cell and distinguish failed from never attempted. Do not claim a complete paired result if the study stops early.

## Blinded review and product decision

Generate random answer labels and strip arm labels, trace, usage, timing and ordering metadata from the review copy. Keep final text, citations, exact supporting excerpts and versioned originals. Save the mapping separately and reveal it only after the scores lock. Reviewers may still recognize writing style. Use two independent scores where feasible, record disagreements and adjudicate against the original. Keep human adjudication, model assistance and deterministic checks separate.

1. Score evidence retrieval by required-point coverage at search and at synthesis. Log sufficient alternative sources separately.
2. Score each final required point as correct, partial, incorrect or omitted. Check range order, sign, units, denominator, model identity and conditions.
3. Check citation version and locator, quote membership, and semantic support as separate measures.
4. Count unsupported published claims per answer and report complete answers separately from correct partial answers.
5. On answerable questions, score false refusals and correct claims withheld. On refusal cases, reward clear source-bounded abstention. Draft and shadow observations diagnose the failure stage only.
6. Retain all provider failures and absent answers in the operational denominator. Also show paired content results for cells with interpretable outputs.
7. Report stage and end-to-end median and p90 latency, invocation and token totals, and cost in extra calls per additional successful answer when defined.

Primary success means all mandatory points published correctly with supporting citations and zero unsupported claims, or a justified refusal on a refusal case. Report pair wins, losses and ties, separate refusal results, all denominators, and question-level paired differences. Any uncertainty interval is descriptive for 20 selected questions. Proposed threshold for considering Multi-Agent as default: at least three net additional primary successes out of 20, with zero excess unsupported-answer cases, evidence of gains across more than one question type, and an acceptable measured latency and call tradeoff agreed before unblinding. Otherwise favor Baseline as default with optional deep research if the gains are concentrated, or keep manual selection if results are mixed. Do not use the evaluation set for tuning, do not change samples or code after observing outputs, and place future fixes on a separate validation set.
