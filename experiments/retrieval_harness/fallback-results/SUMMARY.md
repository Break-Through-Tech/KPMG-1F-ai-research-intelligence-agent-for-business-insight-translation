# Additive semantic fallback results

Retrospective development data, not answer accuracy or a blind test. Fixed E5 and original chunks; 38 inspected questions on 19 papers. All arms deduplicate.

| Source | Budget | Hybrid | Semantic fallback |
| --- | ---: | ---: | ---: |
| html | 800 | 14/18 | 14/18 |
| html | 1600 | 17/18 | 17/18 |
| tex | 800 | 14/18 | 14/18 |
| tex | 1600 | 16/18 | 16/18 |
| pdf | 800 | 12/18 | 12/18 |
| pdf | 1600 | 14/18 | 14/18 |

No complete-question gains or losses on validation. Incumbent evidence is preserved by construction. Filling leftover space increases token utilization without recovering a complete missing answer. This is not evidence of improved answer quality. Two PDF questions still lack required anchors in extracted input.

The top 40 hybrid seeds supply whole source units of at most 160 tokens, scored by pinned E5 query cosine. Full hybrid packing runs first; only afterward are fitting units appended. No eviction, clipping, target paper, answer anchor, or split is used by selection. Added units may be redundant, fragmentary, or distracting; no minimum semantic score is imposed.

Conclusion: keep unchanged hybrid. The remaining packing failures require substitution/repacking or reserving capacity earlier, not just filling the tiny leftover budget. Any substitution policy needs explicit paired-loss checks and fresh fact-reviewed evaluation.

Reproduce: uv run --python 3.12 --with-requirements requirements.txt python -m experiments.retrieval_harness.run_fallback --corpus CORPUS --cache CACHE --output NEW_DIRECTORY. Raw source contexts retained in local kpmg-semantic-fallback-20261104 output; compact outcomes, protocol, verification, and hashes committed.
