# AccurateRAG Table 2 retrieval replay

**Both required rows reached synthesis with the fix enabled.** The same two rows fit within the first 13 passages, the number the original run delivered. Retrieval kept its top-eight limit per search and synthesis kept its 14-passage cap.

## Where the rows were lost

The before replay reproduced all three saved top-eight search lists and the original synthesis packet in order. The pinned corpus already contained both rows, their original cell identifiers, and values. AccurateRAG was the first shortlisted paper for all three searches, and both rows were in the reranker pool every time.

| Saved search | RAFT with GPT-4 CoT, hybrid → final rank | AccurateRAG, hybrid → final rank |
| --- | ---: | ---: |
| Original question | 3 → 21 | 13 → 37 |
| AccurateRAG subquestion | 5 → 27 | 3 → 23 |
| RAFT subquestion | 6 → 29 | 17 → 45 |

For the original question, the cross-encoder ranked the rows 53rd and 63rd. The legacy exact-label bonus did not cover table abbreviations such as FT and w/. The top-ranked prose discussed the opposite RAFT condition. The target rows were already outside all three top-eight searches when the agent assembled synthesis, so the synthesis cap did not cause the loss.

## Change and measured outcome

The optional B2 comparison rule normalizes common configuration notation and preserves explicit exclusion wording such as w/o. It promotes a pair only when both most-specific row labels match the question, the table topic matches, and one eligible table supplies a unique pair. Candidate search and reranking remain in place. Each promoted row remains a separate original citation. The option is off by default.

| Offline check | Expected rows in top eight, before → after |
| --- | ---: |
| Saved AccurateRAG question | 0/2 → 2/2 |
| Opposite RAFT condition | 0/2 → 2/2, selecting the row without CoT |
| ACDC IOI vs. Docstring | 2/2 → 2/2 |
| Agent-SafetyBench automated reviewer model comparison | 2/2 → 2/2 |
| AgreeMate control | 1/1 → 1/1 |
| Training dataset counts control | 2/2 → 2/2 |

The ACDC, Agent-SafetyBench, AgreeMate and training-count top-eight lists kept their exact ordering. For the saved AccurateRAG question, the rows entered the actual scripted synthesis input at positions 1 and 3. The original live audit checked the source cells. AccurateRAG's APIBench range is 68.36–88.71 and RAFT with GPT-4 CoT is 74.00–86.86. [AccurateRAG v2 Table 2](https://arxiv.org/html/2510.02243v2#S2.T2)

The six-case replay used the frozen index and installed local retrieval models with the saved planner response. The synthesis reply was scripted solely to capture its exact input. It yielded no evidence about generated-answer accuracy, other tables with ambiguous or paraphrased labels, or wider ranking regressions. No provider calls were made. The previous numerical verifier and shared demo configuration were untouched.

## Reproduce

From the research worktree with local demo-100 and both cached retrieval models, run:

```powershell
python -I -B experiments/measure/accuraterag-table-retrieval/replay.py
```

[Raw replay](results.json) includes the before and after search lists, index identity, and the passage IDs in both synthesis packets. The 27 B2 and comparison tests and 44 focused Multi-Agent tests passed.
