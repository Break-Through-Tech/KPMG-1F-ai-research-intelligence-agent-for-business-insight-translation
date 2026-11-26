# Offline research trace diagnostics

This experiment adapts RAGChecker's reference-point retrieval recall and response coverage to saved KPMG traces. It adds a draft-to-publication comparison because the existing publication gate can withhold a correct draft. It replaces the manual comparison of separate evidence, draft and envelope files once the evidence anchors and claim labels have been recorded. It consumes the existing artifacts without importing the application or rewriting the original passage, citation, or table-cell records.

## Upstream review

- [RAGChecker computation](https://github.com/amazon-science/RAGChecker/blob/main/ragchecker/computation.py) computes claim recall and context utilization from entailment matrices. Our trace diagnostic adapts that method using explicit versioned evidence anchors and adjudicated draft/final claim indices. Anchor coverage is an approximation of entailment. A point may require a conjunction of passages, such as a cross-paper caveat.
- [RAGChecker evaluator](https://github.com/amazon-science/RAGChecker/blob/main/ragchecker/evaluator.py) can consume exported KPMG question, selected context, reference and response, with retained IDs mapped to doc_id. The full evaluator uses RefChecker and ordinarily needs models for claim extraction and entailment. Supplying pre-adjudicated matrices avoids those calls for metric calculation, but importing the package pulls in the evaluator and attaching a KPMG publication stage still requires a trace adapter. A scorer model would also need calibration on numeric scope and table relationships. No upstream code was copied and no new dependency was installed. The saved artifacts cover factual claims; limitations are not scored by this diagnostic.
- [PaperQA2 retrieval](https://github.com/Future-House/paper-qa/blob/main/src/paperqa/docs.py) wraps maximal marginal relevance (MMR) over its own embedding-backed vector-store interface. The installed 2026.8.12 implementation in paperqa/llms.py shows the exact relevance/diversity tradeoff. Using that selector without reindexing is possible only behind a bridge exposing B2 candidate objects, relevance scores and compatible vectors. Keeping original chunks as opaque returned objects could preserve citation identity. Using native Docs ingestion would create a separate index, while per-passage evidence summaries can require additional model calls. Generic diversity could displace complementary rows from the same table. B2 already has clause coverage, a hybrid anchor and optional paired table rows. Multi-Agent already uses per-search interleaving, protected cited evidence and new-evidence slots. The shared envelope already preserves citation identity, verification, and review provenance. The saved failures support comparing these existing stages before replacing any of them.

## Reproducibility

Run these commands from the checkout root. Choose a fresh output filename each time.

```powershell
python -B -m unittest discover -s experiments/measure/trace-diagnostics -v
python -B experiments/measure/trace-diagnostics/diagnose.py data/processed/controlled-live-three-arm experiments/measure/trace-diagnostics/replay-new.json
```

The development manifest is limited to six previously disclosed runs on two questions. Labels were transcribed from the historical single-observer source review and checked against the exact packets, drafts and published claims. This is machine-assisted review and contains no independent human adjudication. The manifest binds claim indices to the three saved input file hashes. The separate offline regression set exercises joint-source requirements, version mismatch, draft omission, held claim, execution failure, missing gate audit, tampering, and unsupported and unreviewed publication.

## Observations

| Saved development run | Evidence points | Published points | Original calls | Original seconds |
| --- | ---: | ---: | ---: | ---: |
| AccurateRAG A | 0/2 | 0/2 | 1 | 11.089 |
| AccurateRAG B | 0/2 | 0/2 | 2 | 25.201 |
| AccurateRAG C | 2/2 | 1/2 | 3 | 35.384 |
| Agent-SafetyBench vs. TravelPlanner A | 2/6 | 0/6 | 1 | 15.240 |
| Agent-SafetyBench vs. TravelPlanner B | 5/6 | 4/6 | 3 | 57.220 |
| Agent-SafetyBench vs. TravelPlanner C | 5/6 | 4/6 | 3 | 49.479 |

Zero of six complete, zero of three full abstentions had all required anchors, one of three had enough for a partial answer, and zero unsupported claims among seven reviewed published claims. Three supported drafted points were recorded as held by the historical gate. The AccurateRAG C hold involved the RAFT row, while both TravelPlanner agentic runs held a caveat about comparing unlike metrics. The two TravelPlanner agentic packets also lacked the explicit two-stage ReAct configuration. The adapter does not infer whether missing evidence was absent from the index, ranked too low, or dropped before synthesis. The source anchors can miss other valid evidence and labels may be incomplete on new cases.

Seven tests passed. Reprocessing the six records took about 9 ms in one local run, with zero added provider calls. The original results and latencies remain historical. This experiment does not change their publication outcomes or independently establish live answer accuracy. The locked 20-question evaluation was not read or rescored.

Use this diagnostic on separately source-reviewed development traces before changing the runtime. No live evaluation is needed for the adapter itself. If a future runtime change is proposed, freeze fresh questions and reference points before running a paired comparison.
