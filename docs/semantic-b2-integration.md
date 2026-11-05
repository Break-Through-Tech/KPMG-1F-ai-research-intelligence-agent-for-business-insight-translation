# Semantic chunking + B2 integration

## Stack and ownership

This agent-owned branch merges Khoi's PR #172 (eec2750) above PR #171
(89de90f), which already descends from #170 (d9d4d6a). Original contributor
branches are not rewritten. Khoi's #172 is already merged into main; the
integration PR targets main and adds the remaining #170/#171 work and adapter.
Do not merge duplicate copies independently without reconciling ancestry.
This is experimental, not a production promotion.

## Shared boundary

Complete source records remain the citable evidence. Optional semantic boundaries
only determine retrieval views, which are token-bounded and mapped back to exact
original parent offsets/hashes. Table rows (including headers, cells, notes) and
figure records bypass semantic splitting. Retrieval returns original parents.

Build a new isolated bundle using the existing command in
`src/experimental/README.md`, adding:

```
--strategy semantic95_token224_parent
```

Omit it to retain Khoi's `token224_parent` default. Both use the same local
MiniLM encoder for index and query; existing E5 vectors are NOT compatible.
No automatic model download or generation is introduced. Rebuild into a new
bundle, then use the B2 preflight and separate demo. Strategy is recorded in
retrieval provenance and semantic implementation changes require a restart.

## Evaluation and training

No training, fine-tuning, or weight edit is needed to use this integration.
Index rebuilding is embedding computation, not model training. The cross-encoder
is already pretrained; loading it does not train it. Generation review remains
an optional AI check, not a human judgment or ground-truth training label.

First compare token-only vs semantic views on identical source parents, MiniLM,
queries, reranker, and generation settings. Record returned-parent tokens and
latency as well as evidence recall; top-k full parents is not an equal-token
comparison. Then separately test added extraction and reranking. The old E5
span-coverage scores and B2's development answer-point scores are not directly
comparable. No combined corpus or answer-quality gain has been established.

Only after this retrieval baseline is evaluated should fine-tuning be considered:
freeze evidence/index/version provenance; regenerate examples with the combined
retriever; review claim support and abstention labels; split by paper/source
lineage, not individual chunks. Do not use AI quality-review decisions as
unreviewed gold labels. Earlier weight-space experiments are not resumed.

## Verification scope

Offline integration tests exercise exact offsets, immutable parents, bounded
views, table source-binding preservation, corruption rejection, and B2 wiring
with fixture encoders/rerankers. They are not live-corpus or answer-quality proof.
Production defaults and existing experiment artifacts remain unchanged.
