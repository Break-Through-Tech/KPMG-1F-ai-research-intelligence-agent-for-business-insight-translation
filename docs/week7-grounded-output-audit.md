# Week 7 audit: grounded outputs and review

Prepared 2026-10-25 under PR #112 (Week 7, "Grounded outputs and review", paired with Teegawende).

**Status: DRAFT.** Labels were made with AI assistance and have not yet been verified by a second human reviewer. See the review checklist at the end. Nothing here claims KPMG or stakeholder acceptance.

## 1. Summary

- I compared generated summaries and business translations on the **alesha-baseline-v1** questions with the full text of the passages they cite: 10 questions, **36 claims**.
- Overall: 22 supported, 1 supported but off-topic, 11 partial, 2 unsupported.
- **No valid abstentions occurred.** Every query returned `ok`.
- Most errors are small distortions, not fabrications: dropped hedges, scope shifts, causal glue the source doesn't state, and related-work asides promoted to findings.
- The business stage mostly inherits summary-stage problems, then adds invented specifics, mandates, and a legal-compliance risk the prompt forbids.
- Retrieval is a real bottleneck. For alesha-v1-q03 the corpus holds the paper's multi-turn results, but the top 5 passages did not include them.
- **One prompt refinement (`qpm_v1`) was tested on development evidence (`benchmark_cases.json`) and not adopted.** It failed its pre-registered abstention criterion, with mixed results elsewhere (section 7). Next experiments are in section 8.

## 2. What was audited, and how

### Artifacts (under `data/processed/evaluation-runs/`, git-ignored)

| Artifact | What it is | Generated or fixture |
|---|---|---|
| `alesha_retrieval_run1/run.json` | Retrieval-only capture on `baseline_alesha_v1.json`, via `src.evaluation_retrieval`. Run ID `0885356d533a9ccc2a163d1fc03aa4c15e8ca8e095f7331d9e120915721c8b7b`. Not corpus-validation-gated. | Real retrieval. |
| `audit_groq_alesha_all.json` | Summaries for all 10 alesha questions plus business output for q08, q09, q10. | **Generated** |
| `prompts/business_translation/fixtures.json` | Three handwritten scenarios with canned expected responses. | **Fixture-only.** Not used in any count here. |

Artifacts for the development-evidence experiment are listed in section 7.

### Generation setup

- `summarize()` (prompt `research-summary-v1`) and `translate()` (prompt `business-translation/baseline` v1.1) were used unchanged. Prompt hashes are recorded in each output file's `prompts` field.
- They were called through an ad hoc harness (`audit_run.py`, **not in the repo**) against Groq: `openai/gpt-oss-120b`, temperature 0, JSON mode, industry "Insurance", calls paced to stay under a tokens-per-minute limit.
- This is **not the team's official generation run** and may differ from it in model and settings. Temperature 0 does not guarantee identical output on rerun.
- A first attempt on an earlier set hit HTTP 429 rate limits. Those `generation_failed` entries are not abstentions.

### Case selection

All ten alesha questions were run. No cases were selected after viewing retrieval.

### Dev and held-out designation

- No dev/held-out split is documented in the repo (`benchmark_cases.json` has no split field).
- The author treats `alesha-baseline-v1` as the final benchmark (per a teammate) and designated `benchmark_cases.json` as development evidence. **Confirmation from the team is pending in the issue thread.**
- No prompt was tuned on alesha. The author did inspect alesha outputs while auditing, so any alesha run after a prompt change would be confirmation, not a blind test.

### Labeling method

- Each claim was compared with the full text of every chunk it cites.
- **Supported:** the cited text states it. **Partial:** supported in part, or the claim is broader or stronger than the text. **Unsupported:** the cited text does not say it, or says the opposite.
- Support is judged against the passages the model was shown, not the full paper. Where a claim is true to the paper but wasn't supported by the shown chunks, it is noted.
- No truncated or omitted chunks appear in any alesha case (checked from output metadata), and all cited passages are far below the 2,500-character cap.

## 3. Results (alesha-baseline-v1)

| Claims | Supported | Supported, off-topic | Partial | Unsupported |
|---|---|---|---|---|
| 36 | 22 | 1 | 11 | 2 |

### The issue's four categories

- **Unsupported claims:** 2 (q04 claim 5, q10 claim 5), plus the 11 partials below.
- **Exact-quote failures:** none. Three short quoted phrases appear (q02, q04, q08), and all match their sources apart from case or hyphenation. The schema has no quote field, so this category can't be tested systematically.
- **Missing coverage:**
  - q01: the paper's scale figures and its point that small gaps among top models are evaluator uncertainty.
  - q03: the multi-turn results (retrieval cause, see below).
  - q05: how utilities are scored (LLM judge) and the data-fraction result.
  - q06: the workflow-based multi-agent baseline (23.6%) did worse than the single-agent baseline (30.4%), which the answer never says.
  - q09: the quantified blackmail rates.
  - q10: the paper's central finding that its scanners rarely agree.
- **Valid abstention:** none observed. alesha q10 is the closest candidate for a more cautious answer. Section 7 covers development cases where abstention was expected and did not occur.

### Named cases

**alesha-v1-q03** (multi-turn unlearning): 1 supported, 1 partial.
- Claim 1 is true to the paper but was not supported by what the model saw. The cited `c0002` only poses the dialogue-conditioned question, and `c0003` covers self-correction only.
- The paper's findings sit in `c0004`, `c0018`, and `c0024`, none of which were retrieved.
- The claim also generalizes to "unlearning" although RMU stayed robust (`c0018`).

**alesha-v1-q10** (vendor safety evidence): 1 supported, 3 partial, 1 unsupported. The five claims draw on sources about agent oversight, skill registries, scheming monitors, and an alignment thesis. None addresses evaluating a vendor's safety claim directly.

### Claims not cleanly supported

| Claim | Label | Why |
|---|---|---|
| q01 c5 | Partial (minor) | `c0007` says prior work names tool discovery a primary failure mode. "Earlier benchmarks missed" is closer to `c0008`, which was not cited. |
| q02 c3 | Partial | "Because reasoning may be unfaithful": the source raises unfaithfulness as a caveat on interpreting results, not as why instructions fail. |
| q03 c1 | Partial | See named cases above. |
| q04 c3 | Partial | Neuron labeling is a related-work mention. "A direct way to interpret what each neuron represents" is added. |
| q04 c5 | Unsupported | Source: mask learning is a special case of using gradient information. The claim calls it a "broader approach" and presents it as an interpretability approach. |
| q07 c1 | Partial | A limitations sentence (taxonomy and rules are heuristic and LLM-assisted) became "safety evaluation can involve..." with the caveat dropped. |
| q07 c4 | Supported, off-topic | Faithful, but it describes a network fault-detection pipeline, not safety or reliability evaluation of agents. |
| q08 c1 | Partial | A descriptive survey sentence became "companies should assess...". |
| q08 c2 | Partial | "Should involve oversight" became "should require", and was extended to tool and MCP access, which `c0009` doesn't mention. |
| q09 c4 | Partial | "Risk increases as autonomy grows" is stated as a graded finding. The sources show harm at sufficient autonomy, not a dose-response. |
| q10 c1 | Partial | Adds "independent" and turns a statement about deploying agents into a vendor-evidence requirement. |
| q10 c2 | Partial | The source concerns trust in agent skill registries. The claim applies it to vendor AI systems generally. |
| q10 c4 | Partial | The paper's central finding is that its three scanners rarely agree. The claim prefers "consistent signals across methods" and adds examples not in the chunk. |
| q10 c5 | Unsupported | `c0131` lists these mitigations as unexplored research options. Nothing says documenting them indicates vendor commitment. |

### Business stage (q08, q09, q10)

- **Weak summaries pass through.** `translate()` only abstains when the summary does. In q09, implication 3 repeats summary claim 4 (partial) almost word for word.
- **Invented specifics inside cited implications.**
  - q08 action: signed tool manifests, version pinning, network segmentation.
  - q09 actions: immutable audit logs, human-in-the-loop review.
  - q10 actions: external auditors, "at least two" scanners.
  - None appear in the cited text.
- **Forbidden risk.** q08 lists "regulatory non-compliance", which the prompt says not to invent.
- **Findings and recommendations are mixed in `text`.** Most q08 and q10 `text` fields are imperatives, although the prompt reserves recommendations for `suggested_action`. Several actions are mandates ("require", "demand", "adopt a regime"), not scoped validation steps.
- **Assumptions that misstate evidence.** q10 implication 5 says mitigations were "demonstrated in research", but the source calls them unexplored. Implication 3 assumes monitors "detect the majority" of unsafe behavior, a threshold no source gives.
- **Strengths.** Limitations are honest and specific in every case. q09 implication 4 (cite simulation-only evidence, recommend scoped pilots on synthetic or anonymized data) is a good model of what the prompt asks for.
- **Design contributor.** Business-type questions go through the same summary prompt first, so the summary stage receives "What should a company...?" and answers with recommendations.

### Limitations that misdescribe the evidence

- q01 says the passages lack quantitative breakdowns, but they give 1,000 tasks, 36 servers, 220 tools, and a top-three span of 78.2-82.2%.
- q05 says the passages lack empirical details, but `c0004` (LLM-judge scoring of utilities, 3,150 and 2,680 pairs) and `c0022` (data-fraction result) were retrieved.
- q04 calls the pruning evidence "primarily anecdotal". The source says progress is limited.

## 4. Stage-specific checks

**Summary stage**

1. Each claim's specific words and numbers appear in the cited chunk, not just its topic.
2. Subject, setting, and hedges carry over (single vs multi-agent, pretraining vs fine-tuning, "experimental conditions").
3. Numbers and directions are exact (counts, increase vs decrease).
4. Findings only. No "should" or "a business should ask".
5. If no passage addresses the question itself, and not just an adjacent topic, the right output is `insufficient_evidence`.
6. Limitations describe the evidence accurately and never deny content the passages contain.
7. A related-work aside is not a finding. "Prior work does X" stays attributed to prior work.

**Business stage**

1. `text` uses no verb stronger than the source ("should" or "could" never becomes "require" or "mandate").
2. Any transfer step the source doesn't make sits in `assumptions`, not `text`.
3. `suggested_action` is a scoped validation step (pilot, test, ask for evidence), not a mandate or deployment.
4. No controls, actions, or risks beyond the cited evidence unless marked as the writer's inference. No legal-compliance claims.
5. Limitations and risks are consistent with `text`, and assumptions neither restate nor contradict the evidence.
6. Abstain when the summary's claims are only adjacent to the business question.

## 5. Findings to report, by owner

**Retrieval and ingestion**

- alesha q03: the corpus holds the RQ2 and RQ3 results for `2603.00823v2` (`c0004`, `c0016`, `c0018`-`c0020`, `c0022`-`c0024`). The top 5 returned only the section opener `c0015` (no results), two intro/RQ1 chunks, and two off-topic chunks from other papers. Hypothesis, untested: long chunks may exceed the 256-token embedding limit the repo's own validation notes mention.
- alesha q07 and q10: scattered evidence. q07 returned five unrelated methods, and no q10 passage addresses vendor safety claims directly.
- Development cases show the same pattern on benchmark q03 and q09 (section 7).

**Summarization prompt and adapter**

- Scope and hedge drift (q03 c1, q09 c4).
- Related-work asides promoted to findings (q04 c3 and c5, q10 c2).
- Recommendations inside the findings stage for business questions (q08, q10).
- Spurious causal glue (q02 c3).
- Limitations that misdescribe the evidence (q01, q04, q05).
- Missing coverage (section 3).
- Answers instead of abstaining on adjacent evidence: strongest on development cases (section 7).

**Business translation**

- Weak summaries pass through, invented specifics, mandates, a forbidden compliance risk, and assumptions that misstate evidence (details in section 3).

**Schema and process**

- `risks` and `limitations` carry no citations, so they can't be checked per source (one q10 risk happens to trace to `c0132`).
- No quote field, so quote fidelity can't be audited systematically.
- Neither adapter checks claim-level support. Only ID validity is enforced, as documented.
- No dev/held-out split is documented. A commit message mentions "frozen development cases" (`a24ebff`) but no case-level designation was found.
- Two question sets share the IDs q01-q10. The docs say they are distinct, but `capture_validated_retrieval.py` hardcodes `benchmark_cases.json` while `src.evaluation_retrieval` uses the alesha file.
- A retrieval-only capture marks every summary `insufficient_evidence` as a placeholder. Anyone counting abstentions from `review.csv` will miscount.

## 6. Examples for the review-packet walkthrough (Teegawende)

All are **generated** (Groq, `openai/gpt-oss-120b`) from `alesha_retrieval_run1` (`0885356d533a...`). None is fixture-only. Source URL is `arxiv.org/html/<paper>#<fragment>`.

| Label | Case | What the output said, versus the source | Chunk and URL |
|---|---|---|---|
| Supported | q06 c1 | Orchestrated multi-agent 77.4% vs 30.4% single-agent vs 23.6% workflow baseline | `2605.00276v1_c0004`, #S1 |
| Supported | q01 c4 | Three validity threats MCP-Atlas targets | `2602.00933v3_c0008`, #S3 |
| Partial | q03 c1 | Dialogue-conditioned recovery is true in the paper but the shown chunk only poses it as a question | shown: `2603.00823v2_c0002`, `c0003`, #S1; missed: `c0004`, `c0018` |
| Partial | q09 c4 | "Risk increases as autonomy grows" stated as a graded finding | `2604.00324v1_c0002`, #Ch1 |
| Rejected | q10 c5 | Documenting mitigations "indicates vendor commitment"; source calls them unexplored options | `2604.00324v1_c0131`, #Ch6.S6 |
| Rejected | q04 c5 | Special case became a "broader approach" | `2604.00324v1_c0034`, #Ch3.S5 |
| Business, flawed | q08 action | Invented controls (manifests, version pinning, segmentation) | `2606.01494v1_c0008`, #S3.SS2 |
| Business, good | q09 implication 4 | Simulation-only evidence leads to scoped pilots on synthetic data | `2604.00324v1_c0104`, `c0100`, #Ch6.S1 |

Suggested standard for the walkthrough: judge support against the passages the model was shown, and add a separate note when a claim is true to the full paper (q03 c1).

## 7. Refined prompt attempt: `qpm_v1` (tested on development evidence, not adopted)

### Setup

- **Development evidence:** `benchmark_cases.json` (10 questions), through the frozen retrieval run `retrieval_run1/run.json` (run ID `14eeb816ea09708ab7b7dc4cb166a1104f3c1e933e3ae93386783e5c235d7f18`). Designation is the author's, confirmation pending.
- **Alesha was not used** for this experiment.
- **Two arms on identical evidence, interleaved case by case:** `baseline` is `research-summary-v1` unchanged, and `qpm_v1` replaces only rule 6 of that prompt. The business prompt and both adapters were unchanged.
- **Same model and harness** as section 2 (`openai/gpt-oss-120b`, temperature 0, 30-second pacing), through an ad hoc A/B harness (`audit_ab.py`, not in the repo). Prompt hashes are recorded for both arms.
- **Artifacts (generated):** `ab_summary_dev.json`, and the candidate prompt under `prompt_candidates/qpm_v1/research_summary.txt`.

### The change

Rule 6 became a question-to-passage match rule:

- 6a: A passage counts only if it directly addresses the specific subject of the question. A passage about a neighboring topic, or one that mentions the question's keywords in passing, does not count.
- 6b: If no passage counts, return `insufficient_evidence` with no claims, and say in limitations what the passages are about and what is missing.
- 6c: If the passages cover only part of the question, write claims only for that part and say which part is not covered.
- 6d: Describe each passage's setting in its own terms. Do not use the question's wording (who or what was studied, simulation vs deployment) unless the passage does.

No dev-case examples appear in the prompt text. Motivating failures on development cases: q03 and q09 answered despite no matching evidence, and q02 carried the question's "multi-agent" wording into claims about single-agent experiments.

### Pre-registered criteria (written before the run) and outcome

| Criterion | Outcome |
|---|---|
| 1. Candidate returns `insufficient_evidence` on q03 and q09 (verified retrieval misses) | **FAIL.** Both still returned `ok` with claims. |
| 2. Candidate still returns `ok` on q05 and q07 (on-target evidence) | **PASS** |
| 3. On the other six cases, no more unsupported claims than baseline (hand-labeled) | Counts equal (3 vs 3), but they moved: see below. |
| 4. If criterion 1 fails, the refinement is not justified | **Applies.** Not adopted. |

### Before and after, by case

Counts are supported / partial / unsupported. Draft hand labels.

| Case | Baseline | `qpm_v1` | What changed |
|---|---|---|---|
| q01 | 5 / 2 / 0 (7 claims) | 2 / 0 / 0 | Seven claims became two. `qpm_v1` states the passage has no evidence on efficiency, which the baseline never said. Baseline claim 6 imported "efficiency" from the question. Better. |
| q02 | 0 / 2 / 2 | 1 / 2 / 0 | "Thousands of malicious skills", "zero-day" (source: one-day), and a claim wrongly cited to `c0104` are gone. "Multi-agent" persists, and espionage is still not in the cited chunk. Better, but 6d did not hold. |
| q03 | 0 / 2 / 0 | 0 / 1 / 2 | New invented "even when the amount of training data is limited", an inverted sample-efficiency claim, and a limitation naming LoRA, adapters, and prompt-tuning that no passage mentions. Worse. |
| q04 | 1 / 0 / 0 | 1 / 0 / 0 | Same. The evidence is a one-sentence mention (`c0006`), and both arms say so in limitations. |
| q05 | 3 / 1 / 0 | 4 / 1 / 0 | Baseline attached the win-rate metric to the greedy-baseline comparison (`c0021`). `qpm_v1` keeps a weaker version. Slightly better. |
| q06 | 1 / 0 / 1 | 1 / 1 / 1 | Both invent a "self-supervised" framing and advantages. `qpm_v1` adds an off-topic self-correction claim from an unlearning chunk (`2603.00823v2_c0007`). Slightly worse. |
| q07 | 1 / 1 / 0 | 0 / 1 / 0 | `qpm_v1` merged into one claim saying multi-agent wins "only" when orchestrated. The source says superiority is not guaranteed by default. Slightly worse. |
| q08 | 0 / 2 / 0 | 0 / 2 / 0 | Same claim quality, more candid limitations. Visible business output in both arms still has regulatory risks and invented controls. |
| q09 | 0 / 4 / 0 | 3 / 1 / 0 | Largest gain: dropped the invented "proprietary data" attachments in three claims. Claim 3 still swaps the subject to "proprietary fine-tuning data". Still did not abstain. |
| q10 | 3 / 1 / 0 | 2 / 0 / 0 | Baseline limitations were empty. `qpm_v1` says the sources are research framing, not procurement guidance. Claims remain recommendations, and business mandates are unchanged. |
| **Total** | **14 / 15 / 3 (32 claims)** | **14 / 9 / 3 (26 claims)** | Same supported count, fewer partials, same unsupported count. |

### Before and after examples

| Case | Before (baseline) | After (`qpm_v1`) | Source |
|---|---|---|---|
| q01 | Claim 6: step-level reward modeling "for enhancing reasoning efficiency" | Absent. Limitation says the passage gives no evidence on efficiency. | `2602.00931v2_c0023`, #S5: lists step-level reward modeling among DPO-for-reasoning approaches and never mentions efficiency |
| q09 | Claim 2: harmful behaviors "introduced by proprietary data" are hard to remove | Claim 1: fine-tuning can leave persistent harmful behaviors that are hard to remove (supported) | `2604.00324v1_c0064`, #Ch4.S5: nothing about proprietary data |
| q02 | Claim 3: "thousands of malicious skills" | Absent | `2606.01494v1_c0005`, #S2.SS3: 2,857 skills audited, 341 malicious, later 824 |
| q03 | Two partial claims | Claim 2 says targeted LAT reduces the sample efficiency required for re-learning, making it useful with few examples (inverted, and not a limited-data technique) | `2604.00324v1_c0064`, #Ch4.S5: LAT can reduce the sample efficiency of re-learning |
| q06 | Two claims | Adds a self-correction and unlearning claim to a supervised vs self-supervised question | `2603.00823v2_c0007`, #S2: concerns the safety of unlearning, not reasoning tradeoffs |
| q02 | Claim 1: email-oversight agents (correct scope) | Claim 1: "multi-agent LLM systems" while its own limitation says simulated email-oversight agents (6d did not hold) | `2604.00324v1_c0002`, #Ch1 |

### Retained failures (present in `qpm_v1`)

- No abstention on q03 and q09. 6a was applied leniently.
- q03: invented "limited data" claim, inverted sample-efficiency claim, outside-knowledge limitation.
- q06: invented "self-supervised" framing and advantages, plus an off-topic claim.
- q02: "multi-agent" scope, espionage not in the cited chunk, prompt injection conflated with malicious skills.
- q09 claim 3: subject swap to "proprietary fine-tuning data". q05 claim 5: no numbers in `c0021`. q07: "only".
- Business stage (prompt unchanged): mandates, invented controls, regulatory risks, assumptions that misstate evidence.

### Interpretation

- The candidate improved limitations (6c, partial coverage) and, in q09, removed some subject transfers. It did not make the model abstain (6a) or hold scope (6d), and it regressed on q03, q06, and q07.
- Per the pre-registered rule, **the refinement is not justified and was not adopted.** `prompts/research_summary.txt` is unchanged.

### Caveats

- One paired run. An earlier baseline run on the same evidence (`audit_groq_all.json`) differed from this baseline in several claims, so single-run comparisons are weak evidence.
- Two repeat runs on q03, q09, q02, and q06 exist (`ab_repeat_1.json`, `ab_repeat_2.json`) but were not analyzed.
- Business outputs were viewed only in truncated form (first 1,500 characters), so business labels cover the visible portion.
- Labels are drafts made with AI assistance. The development designation is pending team confirmation.

## 8. Next experiments

**A. Relevance gate (pipeline change).** Before summarizing, make one cheap yes/no model call per passage ("does this passage directly address the question's subject?"). Drop failing passages, and if none remain, return `insufficient_evidence` without calling the summarizer. This moves abstention out of the generating call, where it was applied inconsistently.
- Develop on `benchmark_cases.json` first and keep the pre-registered criteria style: abstain on verified misses, still answer on-target cases.
- Add new dev queries written independently of both benchmark files: roughly 4 answerable, 3 adjacent-only, 2 scope traps, and 1 recommendation-style business question. Capture them with `python -m src.evaluation_retrieval --cases <dev_cases.json> --output <new dir>`.
- Two reviewers label claims independently.
- Freeze the design, then run alesha once as a confirmation, reported as non-blind.

**A2. 6c-only prompt variant.** Test only the partial-coverage rule (6c), since that is where `qpm_v1` helped (more candid limitations), without 6a and 6d.

**B. Stage boundary.** For business-type cases, pass a neutral research form of the question to the summary stage and keep advice for the business stage. This needs a pipeline change in `src.research_pipeline`.

**C. Adapter check (no prompt change).** Flag claims whose key terms or numbers don't appear in the cited chunk, for human review. This would flag, for example, an espionage claim cited to a chunk without that word. It would not catch inverted or conflated claims, which need a person.

## 9. What this audit does not claim

- No KPMG or stakeholder acceptance, and no human review yet.
- No tuning on alesha and no change to benchmark expectations.
- The development designation of `benchmark_cases.json` is the author's and pending confirmation.
- One model, one run per case. These are patterns, not rates.
- Tests and CI validate structure, not semantic quality.
- The outputs came from an ad hoc Groq harness, not the team's official generation configuration.

## 10. Open questions for the team

1. Confirm in the issue thread that `baseline_alesha_v1.json` is the official benchmark, that `benchmark_cases.json` is development evidence, and that the issue's "q03/q10" means the alesha IDs.
2. Which support standard should the review packet use: shown passages or full paper?
3. Who owns the alesha q03 retrieval miss?
4. Should the ad hoc harnesses (`audit_run.py`, `audit_ab.py`) be attached to the PR for reproducibility?

## Review status

- [ ] Unsupported and rejected claims verified against source by the author
- [ ] A sample independently labeled by Teegawende
- [ ] Dev/held-out designation confirmed
- [ ] Harnesses and run artifacts attached or linked

## Appendix: commands used

```sh
python -m tests.validate_html_sample --report-dir data/processed/html-validation
python -m evaluation.capture_validated_retrieval \
  --validation data/processed/html-validation/html-ingestion-validation.json \
  --output data/processed/evaluation-runs/retrieval_run1 --mode retrieval
python -m src.evaluation_retrieval --output data/processed/evaluation-runs/alesha_retrieval_run1
# generation: ad hoc harnesses, not in repo
python audit_run.py --run data/processed/evaluation-runs/alesha_retrieval_run1/run.json \
  --query-ids alesha-v1-q01 ... alesha-v1-q10 --industry "Insurance" --min-interval 30 \
  --output data/processed/evaluation-runs/audit_groq_alesha_all.json
python audit_ab.py --run data/processed/evaluation-runs/retrieval_run1/run.json \
  --candidate-dir data/processed/evaluation-runs/prompt_candidates/qpm_v1 \
  --output data/processed/evaluation-runs/ab_summary_dev.json
```
