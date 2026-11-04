# Retrieval harness: eight isolated experiments

Fixed E5, original semantic chunks, 19 matched papers / 38 previously inspected development questions. Counts are exact designated-span coverage, not answer accuracy. No tuning or winner selection.

| Arm | HTML 800 / 1600 | TeX 800 / 1600 | PDF 800 / 1600 |
| --- | --- | --- | --- |
| baseline | 9 / 15 | 9 / 12 | 7 / 13 |
| selective_expansion | 10 / 16 | 10 / 13 | 7 / 13 |
| budget_allocation | 7 / 9 | 9 / 11 | 5 / 8 |
| deduplication | 9 / 15 | 9 / 12 | 7 / 13 |
| hybrid_search | 14 / 17 | 14 / 16 | 12 / 14 |
| reranking | 13 / 17 | 13 / 14 | 10 / 11 |
| question_aware | 7 / 14 | 9 / 9 | 8 / 13 |
| evidence_gap | 9 / 13 | 9 / 11 | 7 / 10 |
| source_aware | 4 / 5 | 9 / 12 | 7 / 13 |
| combined | 4 / 5 | 9 / 13 | 11 / 14 |

Each score is out of 18 validation questions. PDF has designated anchors available for only 16; HTML/TeX for all 18. Retrieval never reads paper targets, anchors, or split labels. Full source-backed contexts retained outside Git; summaries and hashes committed.
