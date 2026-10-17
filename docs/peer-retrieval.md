# Opt-in peer-inspired retrieval helpers

No production caller or default is changed. `src.peer_retrieval` exposes:

- `fuse`: passage-ID RRF with channel ranks and citation conflict checks.
- `cap_papers`: bounded per-version paper diversity; may return fewer than top_k.
- `fuse_papers`: metadata/chunk paper RRF with within-paper evidence lookup.
- `NeighborContext`: frozen-table neighbors with exact paper version, source and
  section/subsection boundaries; reserves anchors before adding whole passages.

Neighbors retain their own pages/locators and explicit anchor provenance. They
receive no fabricated relevance score. Token budgets count passage text only;
source-table adjacency does not establish complete raw-document continuity.
Ranking signals and broader paper coverage are not semantic confidence.

Inspired by 1B neighbors (`bc782a8ac0c8104a814d3c2ba83ba53004ac6d52`) and
1J diversity (`78e7ba17be7014dd648efca44a1327431923ba8b`) / metadata fusion
(`3b931d89d42ab1324917ecb91978c79acd9900a6`). These are 1F adaptations, not
replications of peer benchmark scores.

Run: `python -m unittest discover -s tests -p test_peer_retrieval.py -v`.
The separate comparison-harness PR depends on these helpers.
