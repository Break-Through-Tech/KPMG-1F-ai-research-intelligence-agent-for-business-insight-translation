# KPMG desktop offline reliability measurement

## Decision

Fix numerical range verification first. On the exact pinned CU-DPO abstract, the current checker grounded three wrong claims: reversing the pre/post ranges, regrouping their endpoints, and collapsing them into two point values. All three reached the final answer with a permissive fake verifier. The same replay retained the correct range. This localizes the error to verification with the correct source already in context.

The smallest next engineering experiment is a **disposable, range-only verification adapter**. Represent each reported interval by its two endpoints, unit, pre/post role, metric and source locator. Run it against the four frozen CU-DPO cases and matched scalar/unit controls. The pass condition is rejecting all three wrong variants while retaining the correct version and preserving supported controls. Keep the frozen runtime and rubric untouched during that experiment. This study does not clear the live comparison. The existing missing-index-fingerprint blocker remains outside this measurement.

## Environment and reproduction

- Worktree: `C:/Users/ngkho/.automated reviewer/worktrees/research-evidence-integration/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation`
- Branch: `khoi/research-evidence-integration`. HEAD: `9994eed920d0afd9ee5f36769077a05137763d6e`. Before study: 14 modified tracked paths, 30 untracked paths, nothing staged. Work outside `experiments/measure/` was preserved.
- Windows 11 build 26300, Python 3.14.2, CPU with four Torch threads for retrieval. NumPy 2.4.4, Torch 2.14.1, sentence-transformers 6.1.0, Beautiful Soup 4.15.0 and jsonschema 4.26.0.
- Corpus: `D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100`. 100 versioned papers, 7,667 indexed parent records, 11,030 search views, `token224_parent`. Parent SHA-256 `78d8efd7c9df075be09ffa5f3a9c7ca79c54efa2d7caf75c8f0329ea72ff41aa`. Parent, view and vector hashes matched the manifest. The parent hash also matched the pinned A/B specification and table audit.
- Retrieval loads the same frozen export as the desktop backend. The B2 shortlist and balanced-retriever source hashes also match the corresponding files in the development worktree. Existing local MiniLM-L6-v2 encoder and ms-marco MiniLM-L6-v2 cross-encoder snapshots were loaded with network discovery disabled. Exact paths and weights are in [environment.json](run-02/environment.json).
- Authorization ledger read-only integrity: `ok`. 19 completed, one failed, 20 of 40 used, zero unresolved, no experiment cap or lock. SHA-256 before and after: `ac497432a376b039e1a67a5c8430c96c61b56bdf49f513b2e994c07c91c12986`. No live backend or generation provider was loaded. The explicit fake-verifier checks use in-process canned replies.

Run from the worktree root with the installed Python 3.14 runtime and its user packages. Use a new output name. The command runs the four matched retrieval arms, verification, source DOM checks, recorded response localization, fake-verifier replay, and output integrity checks.

```powershell
& 'C:/Users/ngkho/AppData/Local/Programs/Python/Python314/python.exe' -B experiments/measure/run.py reproduction-01
```

[run-02](run-02) is the final measured dataset. It was produced by the main study command followed by the source-check and summary commands, which are now wired into that entry point. [run-01](run-01) preserves the initial dry analysis and raw DOM output. Its initial literal MathML string differences should not be used for the final fidelity counts. Both retrieval runs produced identical counts and Q2 localization. Two ev05 rows swapped ranks 2 and 3 in all four arms without changing membership or counts at either budget. Exact position stability across processes was not established.

Tests actually executed: Q2 exact baseline top-14 parity with the deployed adapter; four-arm matched budgets and identity checks; 43 frozen verifier examples; 5 fake-verifier claim replays; 50 source-table DOM checks; 485 whole-row association checks; 11 retained envelope and compaction inspections; exact-question retrieval replays for Q3, the saved chart request, both MultiRAG vs. Fin-RATE requests, financial bias and the two legacy laptop questions; deterministic chart preview over ordinary retrieved rows and supplied known-correct rows. Existing model-free suites: Audit #2 16/16, #3 9/9, #4 9/9, #5 2/2 with 32 subtests, and `tests/test_research_chat.py` 13 passed with 16 subtests. No new live answer was scored.

## A. Matched retrieval ablation

**Selection.** Included pinned Q2 and two of 14 eligible-to-inspect development cases, ev05 (CU-DPO and binary DPO) and ev06 (MCP-Atlas). For each required point, an indexed passage had to have a same-version literal anchor or one of its source-checked excerpts. All 19 selected point/passage anchor checks matched hash-identified original HTML at whole-paper scope. Whole-paper scope confirms literal presence, so it does not certify source-level entailment. Ten of the 12 excluded development cases reference paper versions absent from demo-100. Two have no asserted facts. Development labels remain provisional. KIR-100 paper metadata showed **1/26 paper versions** in demo-100 (`2506.23273v2`), with complete paper overlap for **3/100 questions**. No KIR questions entered development, and no KIR answer texts or reserved evidence-eval answers were inspected.

B2 scored each query with the same corpus, models, thresholds and per-query ranking. The diagnostic adapter changed the shortlist constant in memory and exposed candidate and rank traces. For decomposition it retained the original query and added one query per recognized named paper, using only the user's text and title metadata. It merged the rankings in round-robin order with duplicate parent IDs removed, before applying the same 8 or 14 passage budget. Only Q2 triggered decomposition. This experimental adapter does not change the deployed retriever.

| Budget | Arm | Required papers | Compatible gold passages | Question parts | Off-target-paper passages |
|---:|---|---:|---:|---:|---:|
| 8 | A · 3, current | 3/4 | 5/12 | 6/10 | 2/24 |
| 8 | B · 6, current | 3/4 | 5/12 | 6/10 | 2/24 |
| 8 | C · 3, split | 4/4 | 4/12 | 8/10 | 3/24 |
| 8 | D · 6, split | 4/4 | 5/12 | 8/10 | 2/24 |
| 14 | A · 3, current | 3/4 | 5/12 | 6/10 | 2/42 |
| 14 | B · 6, current | 3/4 | 5/12 | 6/10 | 2/42 |
| 14 | C · 3, split | 4/4 | 6/12 | 8/10 | 4/42 |
| 14 | D · 6, split | 4/4 | 7/12 | 8/10 | 3/42 |

A part is counted once when at least one of its anchored passages is returned. Gold passage recall counts the distinct anchored IDs. Off-target paper is a relevance proxy, not a judgment on every unlabelled passage. The extra off-target Q2 hits talk about other agent safety systems and do not supply either named benchmark's setup or results. At eight, C added one such passage and traded away a redundant gold passage while filling both missing Q2 parts. At 14, C and D added two and one off-target passages respectively over A. Widening alone changed which incidental papers appeared but recovered no extra required points. All arms stayed at **1/3** parts for ev06, despite finding its paper. This is another instance of paper recall exceeding answer-evidence coverage.

See [eligibility](run-02/eligibility.json), [query-level ranks and IDs](run-02/retrieval.json) and [aggregate checks](run-02/study-summary.json).

## B. Deterministic verification

Every test cites a real passage in its original source or a controlled synthetic audit fixture. Expected outcomes in the established set were previously checked in engineering audits. They are not human-adjudicated gold labels. The new drafts carry `reviewed=false`. The rates below describe this deliberately selected case set only.

| Cohort | Check | Unsupported accepted | Supported rejected |
|---|---|---:|---:|
| Established, 33 cases | Quote membership | 14/14 | 0/19 |
| Established, 33 cases | Literal numeric membership | 14/14 | 2/19 |
| Established, 33 cases | Current agentic numeric checker | **3/14** | **1/19** |
| Unreviewed drafts, 10 cases | Quote membership | 8/8 | 0/2 |
| Unreviewed drafts, 10 cases | Literal numeric membership | 8/8 | 1/2 |
| Unreviewed drafts, 10 cases | Current agentic numeric checker | 3/8 | 0/2 |

Both agentic decision projections, grounding required and deterministic contradictions only, gave the same counts on these cohorts. The schema shape check admitted these well-formed claims. Neither schema nor quote membership measures semantic support. Literal membership wrongly rejected equivalent unit conversions and failed to distinguish established wrong signs, units, settings, negation, conditions and range comparisons. The current checker blocked 11 of those 14 established unsupported cases. Its remaining errors were the three CU-DPO range variants and one false hold for “participants under age 18” versus “minors under age 18.” Draft residuals concern a denominator, the wrong metric with a real figure, and a changed spelled-out model count. [Raw cases and categories](run-02/verification.json) · [Fake-verifier and original HTML checks](run-02/source-and-fake-replay.json)

## C. Table-header fidelity

The audit covers 436 tables. Historic endpoint verification accepted 423 and refused 13. This study sampled 50 by provenance, including both CU-DPO tables as targeted cases. It matched each original HTML source by content hash, reconstructed DOM row and column positions including spans, retained source IDs, and represented MathML once so visible math and its annotation were not double counted. All adjudication records remain `reviewed=false`.

| Provenance | Sample / available | Full structural agreement | Unverified interpretation | Cell text and column agreement |
|---|---:|---:|---:|---:|
| latexml_guessed | 24/246 | 23/24 | 1/24 | 1,186/1,186 |
| first_row_assumed | 23/187 | 0/23 | 23/23 | 1,387/1,387 |
| html_th_markup | 3/3 | 3/3 | 0/3 | 174/174 |

**2,747/2,747 indexed cell texts and columns and 485/485 row labels/row associations agreed structurally.** No unindexed numeric rows or cells were found by the locator-based checks in the sampled tables. This is not a corpus-wide ingestion audit. **121/252** indexed headers met the structured check, **124/252** matched first-row text but lack independent header-role markup, and **7/252** are numeric-containing paths that need review. For the latter, see `2505.15753v1#S5.T6`, where a path such as “Skeleton Key / Llama-3.1 / 52.0” includes a no-defense result. DOM agreement cannot tell whether a numeric header component should act as a label or a comparator. [Source IDs and annotations](run-02/tables-dom-normalized.json)

**CU-DPO source scope issue.** `2602.00931v2#S3.T2` (Table 2) has **80/80** matching cells and contains **eight** distinct Phase 1 strategy-selection before/after pairs. The extrema in the accuracy column are **0.35–0.46** and **0.68–0.78**. For example, `S3.T2.8.2.3` and `S3.T2.8.3.2` are the DeepSeek-Math baseline and tuned accuracy values. The abstract `2602.00931v2_c0000` explicitly reports the same ranges across **seven** models. `S4.T4.fig1` (Table 4a) has **84/84** agreeing cells and seven model pairs, but its metric is two-phase downstream reasoning Pass@1, not Phase 1 selection accuracy. Its delta column describes Phase 2 over Phase 1. Preserve both source scopes and surface the count discrepancy for adjudication. Do not silently infer which model the abstract excludes. The pinned Q3 rubric was left as-is.

## Current Desktop End-to-End Failure Localization

Reproduce using the command above. `retrieval.json` contains full paper and passage ranks. `historical-retrieval.json` holds exact-question reruns and deterministic chart previews. `saved-traces.json` preserves the original recorded questions, evidence IDs and answer summaries. These are prior desktop demo responses and controlled replays. No new live generation occurred.

| Case | Earliest confirmed stage and what was reproduced |
|---|---|
| **Q2 · Compare Agent-SafetyBench and TravelPlanner** | Both versioned abstracts (`2412.14470v2_c0000`, `2402.01622v4_c0000`) contain the anchors. The raw-query paper rank for TravelPlanner was **6**, outside the top-3 shortlist. Global candidates still contained TravelPlanner, first at hybrid rank **73**, beyond the first 60 passed to the reranker. No TravelPlanner passage was in the A reranker result. Widening to six admitted it, but its first fused rank was **102**, so the final eight or fourteen still omitted it. With a TravelPlanner-focused search the paper ranked **1**, the abstract entered context, and Q2 coverage rose **2/4 → 4/4**. Confirmed retrieval/ranking loss. No pinned live Q2 response is available to judge synthesis. |
| **Q3 · How much did CU-DPO improve strategy selection, and on how many models?** | `2602.00931v2_c0000` was rank **1** in the current replay. Both retained baseline versions, `e5a8c4c460134444ad0b3e7da476fa44` and `39b20c7e451a4d2b9c5579a6b3767d34`, correctly quote the abstract's ranges and seven-model count. The abstract/table count discrepancy is already in the source. Incorrect range acceptance was reproduced **only in the frozen-claim, permissive-verifier path**. No corresponding bad live result was found in these archives. |
| **Seven-model CU-DPO chart request** | Saved version `98a2b82213874820972ebb3adfb0f60a` had eight isolated rows from `S3.T2`, `S4.T4.fig1` and `A2.T11` and abstained. Current top eight reproduced those same rows and mixed metrics. The existing deterministic chart path expanded the retrieved candidates to complete tables with 14, 16 and 15 rows. It returned the seven-pair reasoning table first. Injecting the known Phase 1 table and naming Table 2 returned its 16 rows. This isolates partial evidence from reconstruction and shows chart availability does not settle metric selection. No live synthesis replay. |
| **MultiRAG vs. Fin-RATE** | Saved versions `a964786bd4fe48bbab643c0272f44421` and `08ca414c98754b068a44222c9d498c9f` abstained. The exact request reruns reproduced their evidence. The first delivered no Fin-RATE passage. The second delivered its coverage table row, not its conclusion. Relevant `2602.07294v4_c0026` is indexed but outside both top-20 results. Confirmed evidence delivery failure before synthesis. Whether the source was lost in shortlisting or passage ranking was not traced for these saved questions. |
| **Financial-bias mitigation** | Saved version `b2a9bd0559d04dad93327fb584f06352` received qualitative `2402.12713v2_c0026` but no `S7.T1` row. The complete Table 1 is indexed, including Direct and four intervention rows `2402.12713v2_table_65c56e3f976ef42f_1…5`. The exact current rerun still found none in top 20. This supports an evidence selection failure. The abstention does not show that the generator misunderstood the table. |
| **Willow distance-7 error rate** | Saved version `af4e65d7d7074dd98a1bdfd8f1617073` abstained. The title for the expected surface-code threshold paper and the known candidate base ID `2408.13687` are absent from the pinned paper inventory. The eight saved passages do not contain the requested result. This is a corpus coverage limitation for that source. The study cannot establish whether another source mentions the same result elsewhere. |
| **Earlier DeepMath Table 4 timeout** | The existing QA report records table rows reaching retrieval. The retained provider log independently records a **300.05 s** timeout on a **24,066-character** request. The saved log does not retain exact prompt bytes. Reconstructing the current compact evidence shape on 11 saved envelopes preserved every passed passage ID and text. That rules out whole-passage loss in this compaction replay, while the old timeout's cause and any current latency gain remain unresolved without provider calls. |
| **Correct claim wrongly rejected** | A known-equivalent under-18 qualifier was held even when the fake verifier accepted it. Earliest failure is the deterministic condition comparison. No comparable observed live false hold was located in the archived envelopes. |

### Laptop cross-check and chunk boundaries

- **Missing ingestion values.** The old 25-paper XGBoost case had a source-table ingestion gap. I opened the cached `2604.00319v1` HTML at `S5.T1` and confirmed XGBoost accuracy/precision/recall of **0.9644 / 0.9397 / 0.9929**. There are **zero parents for that paper** in demo-100, and neither exact laptop question retrieved it. The same old ingestion mechanism therefore cannot be reproduced for this paper on desktop. The present failure is corpus absence. The 50-table sample confirms that numerical table cells can be preserved in the new index.
- **Ranked too low or dropped.** Reproduced in desktop on Q2, MultiRAG/Fin-RATE, financial bias, and the mixed-table chart. The old rank-19 critique passage `2604.00319v1_c0019` cannot be compared directly because its source is absent from the pinned corpus.
- **Literal-only numeric acceptance.** Reproduced on **14/14** established unsupported cases when running the literal check itself. Desktop Multi-Agent prevented 11 of those 14 and retained the three wrong CU-DPO range claims with a permissive verifier.
- **Chunking.** The **11 indexed pinned Q2/Q3 source parents** each had at least one search view containing all literal anchors found in that parent. No checked anchor disappeared across view boundaries. Mixed metrics, low rank and absent papers explain observed gaps more directly. A separate chunking experiment would need a source-verified fact present in HTML but split or missing across the emitted views.

## Three measured bottlenecks

1. **Numerical comparisons can be wrong with complete evidence.** Three of 14 established unsupported claims passed the current checker, all variants of the pinned CU-DPO result. Prioritize this because retrieval has already succeeded and the wrong claim still reaches the answer.
2. **Required passages fail to reach context.** Q2 gained two parts with a focused search at the same budget. Historical cross-study and financial questions missed valid indexed passages. The causality is demonstrated for these queries. It is not yet a general gain estimate.
3. **Header interpretation lacks sufficient provenance.** 24 of 50 sampled tables have unresolved header-role or grouped-value interpretation despite matching cells. No wrong numeric source association was demonstrated in the sample. Treat this as a review bottleneck and avoid equating it to a measured error rate.

For a live conclusion about misunderstanding or omission after correct evidence delivery, retain the exact request, final prompt passages and original draft, then compare the retained and rejected claims against the versioned source. Existing artifacts support the failure localization above without establishing any overall desktop answer-quality rate.


