# Simplified-wire Gemini paired comparison

The separately labeled run stopped on F03 handoff synthesis after a 60-second read timeout. It completed two of the ten pairs. F04 through F10 ran no stages. No retries or configuration changes occurred after the first provider request. The recovered Windows paging-file error preceded any provider use. Historical runs remain separate.

## Frozen-rule results

| Question | Current Multi-Agent | Evidence handoff | Pair |
|---|---|---|---|
| F01 | 0/2 published, false abstention (quote validation) | 0/2 published, false abstention (quote validation) | Tie |
| F02 | 2/2 complete and source-supported | 2/2 complete and source-supported | Tie |
| F03 | 0/2 published, false abstention (quote validation) | Unscorable execution failure (provider read timeout) | Incomplete |
| F04–F10 | Unrun | Unrun | Unrun |

F01 delivered both original table-row anchors to each arm. One draft quote in each arm did not occur in the cited chunk 2506.20821v1_c0017. The local check rejected both drafts. F03 current delivered both original table anchors, but draft quotes attributed to 2405.17602v1_table_d97384047b764e44_1 and _3 did not match. The F03 handoff packet contained both anchors, but no draft was returned. A timeout is not scored as an abstention.

F02 accurately reported the daily FundAR dataset, 675 time points and Apply&Redeem target, and the hourly Solar dataset, 8,760 time points and Power target. Both cited their correct versioned Table 1 rows. All four published claims across both arms pass exact quote membership and entailment against the locked references. Zero unsupported published claims among four checked. These adjudications are machine-assisted source review and are not independent human sign-off.

## Latency and usage

| Question | Current wall time | Handoff wall time |
|---|---:|---:|
| F01 | 94.747 s | 64.664 s |
| F02 | 137.604 s | 151.315 s |
| F03 (incomplete pair) | 138.675 s | 182.744 s |

For matched pairs, current median 116.18 s and interpolated p90 133.32 s. Handoff median 107.99 s and interpolated p90 142.65 s. These include quota waits, and the first arm bears the shared planner's live call. Two timing pairs do not establish a performance difference. Team demo wall time must be measured separately.

The run sent 23 HTTP requests, including 11 generation attempts out of 90 authorized. Ten generations returned usage receipts with 97,498 prompt tokens and 3,747 candidate output tokens, no reported thinking tokens. Usage for the timed-out request is unknown. The new schema got past the former F03 rejection in the current arm. The test observed no HTTP 400, but it independently exposed the read timeout and quote-related false abstentions. The live comparison is incomplete and does not establish an architectural improvement.

Decision: stop additional Multi-Agent experiments. Keep evidence handoff experimental and prioritize the Baseline demo handoff.
