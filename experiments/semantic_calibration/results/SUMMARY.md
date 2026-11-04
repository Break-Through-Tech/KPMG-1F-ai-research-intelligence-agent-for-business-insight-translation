# Matched-source semantic calibration results

**Development diagnostic, not generated-answer accuracy or a blind test.**

19 versioned papers; 38 questions (20 tuning / 18 validation). All 9 model/source runs completed.
11 policies × 4 retrieval conditions × 3 models × 3 formats = 396 ablation cells.

36/38 questions have designated anchors available in every source format.

## Tuning-selected semantic policy vs controls (validation only)

All methods below have a 1600-token cap. Fixed existing/token-only controls use no expansion. An additional baseline column matches the selected neighbor setting. No control is tuned.

| Model | Source | Selected semantic policy / context | Existing fixed | Existing matched expansion | Token-only fixed | Selected | Paired wins/losses vs fixed baseline | Mean tokens baseline → selected |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| bge-small-en-v1.5 | html | minimum80_token240_overlap32 / tokens1600 | 11/18 | 11/18 | 12/18 | 13/18 | 3 / 1 | 1574.22 → 1586.39 |
| bge-small-en-v1.5 | pdf | minimum80_token240_overlap32 / tokens1600 | 9/18 | 9/18 | 7/18 | 10/18 | 4 / 3 | 1585.0 → 1586.83 |
| bge-small-en-v1.5 | tex | original / tokens1600_neighbors | 13/18 | 10/18 | 13/18 | 16/18 | 4 / 1 | 1576.11 → 1595.39 |
| e5-small-v2 | html | percentile20_minimum80_token240 / tokens1600_neighbors | 14/18 | 12/18 | 15/18 | 13/18 | 2 / 3 | 1579.39 → 1571.39 |
| e5-small-v2 | pdf | percentile20_minimum80_token240 / tokens1600 | 14/18 | 14/18 | 12/18 | 14/18 | 2 / 2 | 1587.11 → 1586.94 |
| e5-small-v2 | tex | minimum80_token240_overlap32 / tokens1600 | 10/18 | 10/18 | 12/18 | 12/18 | 2 / 0 | 1566.56 → 1579.11 |
| all-MiniLM-L6-v2 | html | original / tokens1600 | 10/18 | 10/18 | 12/18 | 15/18 | 7 / 2 | 1591.78 → 1597.94 |
| all-MiniLM-L6-v2 | pdf | minimum80 / tokens1600 | 11/18 | 11/18 | 9/18 | 11/18 | 4 / 4 | 1592.67 → 1595.22 |
| all-MiniLM-L6-v2 | tex | threshold65 / tokens1600_neighbors | 10/18 | 9/18 | 13/18 | 15/18 | 7 / 2 | 1581.72 → 1597.5 |

## Same questions available in every format (validation)

| Model | Source | Available validation questions | Baseline (same expansion) | Selected semantic |
| --- | --- | ---: | ---: | ---: |
| bge-small-en-v1.5 | html | 16 | 9 | 11 |
| bge-small-en-v1.5 | pdf | 16 | 9 | 10 |
| bge-small-en-v1.5 | tex | 16 | 9 | 15 |
| e5-small-v2 | html | 16 | 11 | 12 |
| e5-small-v2 | pdf | 16 | 14 | 14 |
| e5-small-v2 | tex | 16 | 9 | 11 |
| all-MiniLM-L6-v2 | html | 16 | 9 | 13 |
| all-MiniLM-L6-v2 | pdf | 16 | 11 | 11 |
| all-MiniLM-L6-v2 | tex | 16 | 8 | 13 |

## Budget and expansion controls (validation, original semantic policy)

| Model / source | Original top5 | Original 1600 tokens | Original 1600 + neighbors | Baseline 1600 | Baseline 1600 + neighbors |
| --- | ---: | ---: | ---: | ---: | ---: |
| bge-small-en-v1.5 / html | 10/18 | 15/18 | 16/18 | 11/18 | 8/18 |
| bge-small-en-v1.5 / pdf | 8/18 | 11/18 | 11/18 | 9/18 | 9/18 |
| bge-small-en-v1.5 / tex | 11/18 | 15/18 | 16/18 | 13/18 | 10/18 |
| e5-small-v2 / html | 15/18 | 15/18 | 14/18 | 14/18 | 12/18 |
| e5-small-v2 / pdf | 14/18 | 13/18 | 10/18 | 14/18 | 10/18 |
| e5-small-v2 / tex | 13/18 | 12/18 | 12/18 | 10/18 | 10/18 |
| all-MiniLM-L6-v2 / html | 8/18 | 15/18 | 16/18 | 10/18 | 10/18 |
| all-MiniLM-L6-v2 / pdf | 6/18 | 13/18 | 15/18 | 11/18 | 9/18 |
| all-MiniLM-L6-v2 / tex | 7/18 | 15/18 | 15/18 | 10/18 | 9/18 |

## Extraction coverage (matched papers, both question splits)

| Source | Available anchors / questions | Missing question IDs |
| --- | --- | --- |
| pdf | 36/38 | n02, r02 |
| html | 38/38 | none |
| tex | 38/38 | none |

## Full ablations (validation)

All variants disclosed; only the tuning-selected row above is a selection-validation result. Do not pick the best validation row after viewing this table.

| Model / source | Policy | Chunks | Mean chars | Over encoder limit | Top5 | 800 tokens | 1600 tokens | 1600 + neighbors |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bge-small-en-v1.5 / html | original | 5230 | 172.08 | 13 | 10/18 | 14/18 | 15/18 | 16/18 |
| bge-small-en-v1.5 / html | threshold35 | 709 | 1269.37 | 36 | 8/18 | 8/18 | 9/18 | 9/18 |
| bge-small-en-v1.5 / html | threshold50 | 803 | 1120.78 | 36 | 9/18 | 8/18 | 10/18 | 9/18 |
| bge-small-en-v1.5 / html | threshold65 | 3336 | 269.78 | 25 | 11/18 | 10/18 | 15/18 | 12/18 |
| bge-small-en-v1.5 / html | minimum80 | 1653 | 544.45 | 12 | 7/18 | 8/18 | 13/18 | 10/18 |
| bge-small-en-v1.5 / html | minimum80_token240 | 1804 | 498.88 | 1 | 7/18 | 9/18 | 14/18 | 11/18 |
| bge-small-en-v1.5 / html | minimum80_token240_overlap32 | 1883 | 511.66 | 1 | 9/18 | 9/18 | 13/18 | 13/18 |
| bge-small-en-v1.5 / html | threshold50_minimum80_token240 | 1143 | 787.39 | 1 | 9/18 | 8/18 | 12/18 | 12/18 |
| bge-small-en-v1.5 / html | percentile20_minimum80_token240 | 1177 | 764.64 | 1 | 9/18 | 8/18 | 12/18 | 9/18 |
| bge-small-en-v1.5 / html | baseline | 758 | 1248.57 | 30 | 9/18 | 6/18 | 11/18 | 8/18 |
| bge-small-en-v1.5 / html | token_only240_overlap32 | 1159 | 809.17 | 1 | 9/18 | 7/18 | 12/18 | 10/18 |
| bge-small-en-v1.5 / pdf | original | 5812 | 152.22 | 0 | 8/18 | 10/18 | 11/18 | 11/18 |
| bge-small-en-v1.5 / pdf | threshold35 | 736 | 1202.06 | 4 | 7/18 | 5/18 | 7/18 | 6/18 |
| bge-small-en-v1.5 / pdf | threshold50 | 888 | 996.3 | 3 | 9/18 | 5/18 | 7/18 | 6/18 |
| bge-small-en-v1.5 / pdf | threshold65 | 3901 | 226.79 | 2 | 9/18 | 10/18 | 14/18 | 11/18 |
| bge-small-en-v1.5 / pdf | minimum80 | 1743 | 507.58 | 1 | 8/18 | 7/18 | 11/18 | 10/18 |
| bge-small-en-v1.5 / pdf | minimum80_token240 | 1815 | 487.45 | 0 | 8/18 | 9/18 | 10/18 | 11/18 |
| bge-small-en-v1.5 / pdf | minimum80_token240_overlap32 | 1896 | 500.42 | 0 | 7/18 | 8/18 | 10/18 | 10/18 |
| bge-small-en-v1.5 / pdf | threshold50_minimum80_token240 | 1117 | 792.05 | 0 | 5/18 | 5/18 | 9/18 | 8/18 |
| bge-small-en-v1.5 / pdf | percentile20_minimum80_token240 | 1143 | 774.03 | 0 | 5/18 | 6/18 | 9/18 | 7/18 |
| bge-small-en-v1.5 / pdf | baseline | 773 | 1169.58 | 3 | 9/18 | 5/18 | 9/18 | 9/18 |
| bge-small-en-v1.5 / pdf | token_only240_overlap32 | 1128 | 818.09 | 0 | 5/18 | 5/18 | 7/18 | 7/18 |
| bge-small-en-v1.5 / tex | original | 16703 | 118.62 | 65 | 11/18 | 11/18 | 15/18 | 16/18 |
| bge-small-en-v1.5 / tex | threshold35 | 1276 | 1552.78 | 314 | 12/18 | 7/18 | 9/18 | 9/18 |
| bge-small-en-v1.5 / tex | threshold50 | 1399 | 1416.26 | 313 | 12/18 | 7/18 | 9/18 | 7/18 |
| bge-small-en-v1.5 / tex | threshold65 | 9956 | 199.06 | 142 | 11/18 | 9/18 | 14/18 | 14/18 |
| bge-small-en-v1.5 / tex | minimum80 | 3247 | 610.38 | 92 | 7/18 | 7/18 | 10/18 | 10/18 |
| bge-small-en-v1.5 / tex | minimum80_token240 | 3714 | 533.62 | 60 | 9/18 | 9/18 | 10/18 | 11/18 |
| bge-small-en-v1.5 / tex | minimum80_token240_overlap32 | 3937 | 533.82 | 60 | 8/18 | 8/18 | 13/18 | 11/18 |
| bge-small-en-v1.5 / tex | threshold50_minimum80_token240 | 2473 | 801.41 | 60 | 12/18 | 11/18 | 13/18 | 11/18 |
| bge-small-en-v1.5 / tex | percentile20_minimum80_token240 | 2511 | 789.28 | 60 | 12/18 | 11/18 | 13/18 | 10/18 |
| bge-small-en-v1.5 / tex | baseline | 1604 | 1431.08 | 321 | 12/18 | 8/18 | 13/18 | 10/18 |
| bge-small-en-v1.5 / tex | token_only240_overlap32 | 2570 | 809.16 | 60 | 12/18 | 11/18 | 13/18 | 13/18 |
| e5-small-v2 / html | original | 709 | 1269.37 | 36 | 15/18 | 9/18 | 15/18 | 14/18 |
| e5-small-v2 / html | threshold35 | 708 | 1271.16 | 36 | 15/18 | 9/18 | 15/18 | 14/18 |
| e5-small-v2 / html | threshold50 | 708 | 1271.16 | 36 | 15/18 | 9/18 | 15/18 | 14/18 |
| e5-small-v2 / html | threshold65 | 708 | 1271.16 | 36 | 15/18 | 9/18 | 15/18 | 14/18 |
| e5-small-v2 / html | minimum80 | 708 | 1271.16 | 36 | 15/18 | 9/18 | 15/18 | 14/18 |
| e5-small-v2 / html | minimum80_token240 | 1144 | 786.7 | 1 | 11/18 | 11/18 | 14/18 | 13/18 |
| e5-small-v2 / html | minimum80_token240_overlap32 | 1167 | 798.66 | 1 | 11/18 | 11/18 | 15/18 | 12/18 |
| e5-small-v2 / html | threshold50_minimum80_token240 | 1144 | 786.7 | 1 | 11/18 | 11/18 | 14/18 | 13/18 |
| e5-small-v2 / html | percentile20_minimum80_token240 | 1169 | 769.88 | 1 | 14/18 | 11/18 | 15/18 | 13/18 |
| e5-small-v2 / html | baseline | 758 | 1248.57 | 30 | 14/18 | 9/18 | 14/18 | 12/18 |
| e5-small-v2 / html | token_only240_overlap32 | 1167 | 798.66 | 1 | 11/18 | 11/18 | 15/18 | 12/18 |
| e5-small-v2 / pdf | original | 738 | 1198.8 | 5 | 14/18 | 7/18 | 13/18 | 10/18 |
| e5-small-v2 / pdf | threshold35 | 736 | 1202.06 | 5 | 14/18 | 7/18 | 13/18 | 10/18 |
| e5-small-v2 / pdf | threshold50 | 736 | 1202.06 | 5 | 14/18 | 7/18 | 13/18 | 10/18 |
| e5-small-v2 / pdf | threshold65 | 736 | 1202.06 | 5 | 14/18 | 7/18 | 13/18 | 10/18 |
| e5-small-v2 / pdf | minimum80 | 736 | 1202.06 | 5 | 14/18 | 7/18 | 13/18 | 10/18 |
| e5-small-v2 / pdf | minimum80_token240 | 1107 | 799.2 | 0 | 11/18 | 7/18 | 14/18 | 9/18 |
| e5-small-v2 / pdf | minimum80_token240_overlap32 | 1131 | 809.45 | 0 | 11/18 | 9/18 | 12/18 | 10/18 |
| e5-small-v2 / pdf | threshold50_minimum80_token240 | 1107 | 799.2 | 0 | 11/18 | 7/18 | 14/18 | 9/18 |
| e5-small-v2 / pdf | percentile20_minimum80_token240 | 1127 | 785.02 | 0 | 11/18 | 8/18 | 14/18 | 10/18 |
| e5-small-v2 / pdf | baseline | 773 | 1169.58 | 4 | 15/18 | 7/18 | 14/18 | 10/18 |
| e5-small-v2 / pdf | token_only240_overlap32 | 1131 | 809.45 | 0 | 11/18 | 9/18 | 12/18 | 10/18 |
| e5-small-v2 / tex | original | 1278 | 1550.35 | 317 | 13/18 | 9/18 | 12/18 | 12/18 |
| e5-small-v2 / tex | threshold35 | 1276 | 1552.78 | 317 | 13/18 | 9/18 | 12/18 | 12/18 |
| e5-small-v2 / tex | threshold50 | 1276 | 1552.78 | 317 | 13/18 | 9/18 | 12/18 | 12/18 |
| e5-small-v2 / tex | threshold65 | 1276 | 1552.78 | 317 | 13/18 | 9/18 | 12/18 | 12/18 |
| e5-small-v2 / tex | minimum80 | 1276 | 1552.78 | 317 | 13/18 | 9/18 | 12/18 | 12/18 |
| e5-small-v2 / tex | minimum80_token240 | 2478 | 799.79 | 60 | 11/18 | 10/18 | 11/18 | 12/18 |
| e5-small-v2 / tex | minimum80_token240_overlap32 | 2576 | 802.43 | 60 | 12/18 | 11/18 | 12/18 | 10/18 |
| e5-small-v2 / tex | threshold50_minimum80_token240 | 2478 | 799.79 | 60 | 11/18 | 10/18 | 11/18 | 12/18 |
| e5-small-v2 / tex | percentile20_minimum80_token240 | 2519 | 786.77 | 60 | 11/18 | 10/18 | 11/18 | 11/18 |
| e5-small-v2 / tex | baseline | 1604 | 1431.08 | 324 | 12/18 | 9/18 | 10/18 | 10/18 |
| e5-small-v2 / tex | token_only240_overlap32 | 2576 | 802.43 | 60 | 12/18 | 11/18 | 12/18 | 10/18 |
| all-MiniLM-L6-v2 / html | original | 6457 | 139.38 | 6 | 8/18 | 12/18 | 15/18 | 16/18 |
| all-MiniLM-L6-v2 / html | threshold35 | 3473 | 259.14 | 139 | 7/18 | 11/18 | 14/18 | 15/18 |
| all-MiniLM-L6-v2 / html | threshold50 | 5310 | 169.49 | 30 | 7/18 | 12/18 | 15/18 | 14/18 |
| all-MiniLM-L6-v2 / html | threshold65 | 6257 | 143.84 | 10 | 7/18 | 12/18 | 15/18 | 15/18 |
| all-MiniLM-L6-v2 / html | minimum80 | 2161 | 416.47 | 7 | 5/18 | 10/18 | 14/18 | 15/18 |
| all-MiniLM-L6-v2 / html | minimum80_token240 | 2170 | 414.74 | 4 | 5/18 | 10/18 | 14/18 | 15/18 |
| all-MiniLM-L6-v2 / html | minimum80_token240_overlap32 | 2345 | 418.28 | 4 | 8/18 | 10/18 | 14/18 | 14/18 |
| all-MiniLM-L6-v2 / html | threshold50_minimum80_token240 | 1951 | 461.29 | 4 | 9/18 | 9/18 | 15/18 | 14/18 |
| all-MiniLM-L6-v2 / html | percentile20_minimum80_token240 | 1219 | 738.3 | 4 | 11/18 | 9/18 | 12/18 | 12/18 |
| all-MiniLM-L6-v2 / html | baseline | 758 | 1248.57 | 472 | 10/18 | 5/18 | 10/18 | 10/18 |
| all-MiniLM-L6-v2 / html | token_only240_overlap32 | 1159 | 809.17 | 4 | 10/18 | 9/18 | 12/18 | 12/18 |
| all-MiniLM-L6-v2 / pdf | original | 6892 | 128.37 | 5 | 6/18 | 12/18 | 13/18 | 15/18 |
| all-MiniLM-L6-v2 / pdf | threshold35 | 4041 | 218.94 | 100 | 6/18 | 11/18 | 13/18 | 15/18 |
| all-MiniLM-L6-v2 / pdf | threshold50 | 5784 | 152.96 | 17 | 5/18 | 11/18 | 13/18 | 14/18 |
| all-MiniLM-L6-v2 / pdf | threshold65 | 6723 | 131.6 | 6 | 5/18 | 12/18 | 13/18 | 14/18 |
| all-MiniLM-L6-v2 / pdf | minimum80 | 2147 | 412.07 | 6 | 4/18 | 6/18 | 11/18 | 11/18 |
| all-MiniLM-L6-v2 / pdf | minimum80_token240 | 2153 | 410.92 | 5 | 4/18 | 6/18 | 11/18 | 11/18 |
| all-MiniLM-L6-v2 / pdf | minimum80_token240_overlap32 | 2327 | 415.11 | 5 | 7/18 | 7/18 | 12/18 | 10/18 |
| all-MiniLM-L6-v2 / pdf | threshold50_minimum80_token240 | 1947 | 454.4 | 5 | 6/18 | 8/18 | 12/18 | 10/18 |
| all-MiniLM-L6-v2 / pdf | percentile20_minimum80_token240 | 1214 | 728.76 | 5 | 6/18 | 5/18 | 8/18 | 6/18 |
| all-MiniLM-L6-v2 / pdf | baseline | 773 | 1169.58 | 442 | 10/18 | 7/18 | 11/18 | 9/18 |
| all-MiniLM-L6-v2 / pdf | token_only240_overlap32 | 1128 | 818.09 | 5 | 4/18 | 5/18 | 9/18 | 9/18 |
| all-MiniLM-L6-v2 / tex | original | 18891 | 104.88 | 176 | 7/18 | 11/18 | 15/18 | 15/18 |
| all-MiniLM-L6-v2 / tex | threshold35 | 14720 | 134.6 | 412 | 8/18 | 11/18 | 13/18 | 13/18 |
| all-MiniLM-L6-v2 / tex | threshold50 | 17377 | 114.02 | 222 | 9/18 | 13/18 | 14/18 | 15/18 |
| all-MiniLM-L6-v2 / tex | threshold65 | 18669 | 106.13 | 179 | 7/18 | 11/18 | 15/18 | 15/18 |
| all-MiniLM-L6-v2 / tex | minimum80 | 4465 | 443.87 | 200 | 6/18 | 8/18 | 12/18 | 12/18 |
| all-MiniLM-L6-v2 / tex | minimum80_token240 | 4587 | 432.06 | 172 | 6/18 | 8/18 | 12/18 | 13/18 |
| all-MiniLM-L6-v2 / tex | minimum80_token240_overlap32 | 4967 | 428.26 | 172 | 7/18 | 8/18 | 13/18 | 11/18 |
| all-MiniLM-L6-v2 / tex | threshold50_minimum80_token240 | 4285 | 462.52 | 172 | 10/18 | 11/18 | 13/18 | 11/18 |
| all-MiniLM-L6-v2 / tex | percentile20_minimum80_token240 | 2591 | 764.7 | 172 | 11/18 | 11/18 | 12/18 | 11/18 |
| all-MiniLM-L6-v2 / tex | baseline | 1604 | 1431.08 | 1352 | 11/18 | 9/18 | 10/18 | 9/18 |
| all-MiniLM-L6-v2 / tex | token_only240_overlap32 | 2570 | 809.16 | 172 | 12/18 | 11/18 | 13/18 | 11/18 |

## Limitations

- Single development corpus; only nine validation papers, with correlated questions. No statistical superiority claim.
- Exact normalized span containment is a retrieval proxy; no generated-answer/human relevance scoring. See ../QUALITATIVE.md for two scored gains where baseline already supports the answer.
- HTML omits display equations/table bodies; cached TeX is raw parsed source with historical parser provenance, not rendered prose.
- Source-absent spans stay in overall denominators. Paired cross-format available-only results are in compact-results.json.
- Over-limit atomic sentences/math are retained; encoder truncation is counted. Context windows are never truncated.
- Shared cached embeddings/MPS timings are not production latency measurements. Defaults and persistent index are unchanged.

See protocol.json, compact-results.json, questions.json and source-receipts.json for reproducibility metadata. Full source blocks, contexts and vectors remain in the local artifact directory.
