# Numerical shadow in the Multi-Agent workflow

The experimental orchestrator accepts an optional `numerical_shadow` adapter. The Research Agent extracts proposals from its regular prose draft and the exact evidence it passed to synthesis. After ordinary verification, the adapter checks the proposals with the existing source-bound verifier. The envelope stores per-round diagnostics separately, including the delivered evidence packet and old decision. With the adapter disabled, the workflow follows its existing path. The running demo and Baseline use that default.

The deterministic producer discovers source operands in a narrow prose comparison form and in eligible audited two-value table rows. It derives source fields and exact offsets or cell IDs from the delivered passages, checks the passage against the pinned source identity, and reads proposed values from the draft separately. Unsupported formats and incomplete citations go to review. Table roles use the original header labels. The producer uses no manually mapped gold bindings, extra model instructions, or extra model calls. Broader prose forms, complex tables, and reliable coverage on live generated answers remain open.

## Scripted workflow results

Fifteen cases exercised the actual planner, Research Agent, quote validation, Verification Agent, and sealed answer builder, with scripted provider responses and fixture retrieval over pinned evidence. Two drafts came from archived CU-DPO answers. The other cases are source-checked engineering fixtures, including AgreeMate and an ACDC table. Independently human-reviewed cases and new live provider outputs were both zero.

| Measure | Count |
| --- | --- |
| Eligible numerical drafts | 15 |
| Complete structured proposals | 7 |
| Correct bindings accepted by the independent verifier | 4 |
| Unsupported bindings among complete proposals | 3, all rejected |
| Additional malformed numerical relationships rejected before a proposal | 2 |
| Referred for review | 6, including 2 otherwise valid comparisons with incomplete or unauditable evidence |
| Decisive disagreements with the ordinary verifier | 5, plus 2 ordinary acceptances referred by shadow |
| Valid cases wrongly rejected by shadow | 0 of 6. Four linked and two referred. |
| Source-backed incorrect claims accepted by shadow | 0 of 9 unsupported or corrupted fixtures |

The fixture retriever delivered source records without running B2 ranking. The fixture verification model replied with a scripted supported verdict. Every comparison of ordinary envelopes, review fingerprints and synthesis evidence matched with shadow enabled and disabled. The raw snapshot preserves those observations and evidence. This demonstrates automatic linkage in the running code path for the covered inputs. It does not establish a live coverage or accuracy improvement.

## Reproduce

```powershell
py -3.14 -I -B experiments/measure/bound-comparison/test_workflow_shadow.py
```

[Raw workflow results](workflow-shadow-results.json)
