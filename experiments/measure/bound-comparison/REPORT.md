# Offline source-bound numerical verification

**Offline gate passed.** Given explicit source and claim bindings, the prototype rejects the known CU-DPO range and scope errors. It preserves all 29 existing non-range decisions. The study covers deterministic comparison and rendering with frozen inputs. The research application still uses its current verifier.

## Replay results

| Cohort | Current numerical checker | Source-bound replay |
| --- | --- | --- |
| Four established CU-DPO range cases | Valid comparison accepted. All 3 invalid comparisons accepted. | Valid comparison accepted. All 3 invalid comparisons rejected. |
| Four earlier boundary probes | Valid comparison accepted. 2 of 3 invalid comparisons accepted. | Valid comparison accepted. All 3 invalid comparisons rejected. |
| Twelve source-checked transfer drafts | 0/4 supported examples accepted. 6/8 unsupported examples rejected and 2/8 referred. | All 4 supported examples accepted. All 8 unsupported examples rejected. |
| Twenty-nine established non-range controls | 17/18 supported examples accepted. All 11 unsupported examples rejected. | All 29 decisions preserved, including the existing false rejection. |

Across the original 33 engineering cases, unsupported acceptances went from **3/14 to 0/14**. Supported false rejections remained **1/19**. The original cases preserve their review flags. The four boundary probes and 12 transfer cases carry `reviewed=false`. These are engineering checks with source references. The sample has no independent human adjudication or estimate of general accuracy.

The 12 new tests also check missing endpoint rows, changed source versions and text, changed structured cells, matching numbers at different cell IDs, ambiguous bindings, percent-to-proportion conversion, and conversion precision. All 6 tests from the earlier experiment passed.

An offline shadow replay also preserved both archived Baseline CU-DPO findings. Their cited text and version matched the pinned parent, and both report the correct comparison. The current standalone numerical check reports uncertainty for the two excerpts. The archived answers themselves had already been published by the demo. This replay uses explicitly annotated bindings and the saved passages. [Raw archived-answer replay](retained-answers.json)

## What the prototype verifies

- Source records declare the metric, subject, setting, relevant qualifiers and population, plus the mapping of each operand to exact abstract spans or table cells. The comparison checks these relationships before accepting equivalent numeric values.
- The expected digest covers each canonical parent delivered to the verifier, including its versioned paper identity, location, text, and any structured table content. A missing, altered, or ambiguous record requires review.
- Accepted wording uses source-bound fields. Table comparisons keep their method or condition labels and keep the reported scale. Unstructured wording alone receives a review decision.

The replay assumes trusted bindings. The typed claim inputs are explicit annotations of the frozen prose or independently specified transfer cases. They exercise scope and operand verification. A live shadow check needs generated claim bindings and the exact evidence packet used for synthesis. It should measure the proportion of comparisons that can be bound, disagreements with the current verifier, and supported comparisons that would be held. Reliable construction of bindings by the application remains an open test.

## Source anchors

| Paper and locator | Source relationship checked |
| --- | --- |
| [CU-DPO v2 abstract](https://arxiv.org/html/2602.00931v2#abstract1), `2602.00931v2_c0000` | Strategy selection accuracy on mathematical reasoning benchmarks across seven base models, with 35–46% before and 68–78% after. The abstract supplies the population for this fixture. |
| [HAMMER v1 Table 1](https://arxiv.org/html/2509.25240v1#S5.T1) | Qwen3-1.7B-DAPO pass@1 across AIME 2024 and 2025 at k=100. |
| [ACDC v1 Table A.1](https://arxiv.org/html/2604.00324v1#A1.T1) | AUC across IOI and Docstring for the random baseline and ACDC. Equivalent percent and proportion inputs pass. Percentage-point deltas require a different measurement. |
| [AccurateRAG v2 Table 2](https://arxiv.org/html/2510.02243v2#S2.T2) | Newly used source. AST-match scores across the three APIBench subsets for fine-tuned Llama-2-7B. The six cells yield 74.00–86.86 for RAFT with GPT-4 CoT and 68.36–88.71 for AccurateRAG. |
| [AgreeMate v1 Table 3](https://arxiv.org/html/2412.18690v1#S6.T3) | Newly used source. The fairness score is 0.3021 without CoT and −0.4385 with CoT. |

The experiment checked the archive hashes and exact original HTML cell values and headers for the two new transfer papers. The saved replay includes source-version URLs, parent and source digests where available, and the exact span or cell ID for each operand. The CU-DPO abstract has an exact parent digest and span references.

## Reproduce

From the desktop worktree, use Python 3.11+ and the existing demo-100 bundle and cached source HTML referenced by the frozen audit. The validation is model-free and uses the standard library.

```powershell
python -I -B experiments/measure/bound-comparison/test_verify.py
python -I -B experiments/measure/structured-ranges/test_adapter.py
python -I -B experiments/measure/bound-comparison/bound_replay.py
python -I -B experiments/measure/bound-comparison/bound_replay.py --output replay-new.json
python -I -B experiments/measure/bound-comparison/bound_replay.py --retained
```

[Raw 49-case replay](results.json) includes all original claims, typed inputs, decisions and source references. Context integrity and ambiguity cases are covered in [the regression suite](test_verify.py). This run used Python 3.11.9, made zero provider calls, and did not access the live ledger. All written files are in this experiment directory.
