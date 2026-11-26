# Evidence handoff prototype

This opt-in, research-only adapter replaces the current orchestration policy of choosing one round and discarding the other. The planner's existing search parts reach synthesis as a proposed outline. A retry drafts missing or changed findings and can see prior findings and caveats whose exact sources remain in the current packet. Earlier verified claims are carried as candidates, then checked alongside new claims by the existing verifier. The latest validated answer is published. A retry with no new evidence keeps the previous answer and spends no calls. A rejected revision does not restore earlier claims over newer evidence. Caveats are reconsidered by synthesis using the latest sources and pass the existing exact-quote checks.

B2, top-k, evidence assembly, the existing synthesis schema, deterministic contradiction checks, independent verifier, review envelope, and original table row metadata all remain in use. Neither active UI selects this adapter. Limitations retain their existing citation-membership protection. This change does not introduce independent semantic verification of limitations. The claim cap is still eight, with retained findings first. The retry context and verifier prompt may be longer. A malformed revision can leave no final answer. The adapter cannot recover facts that were never selected or repair wrong source data. It does not alter the numerical checker, including its sensitivity to wording.

## Alternatives inspected

- [STORM article generation](https://github.com/stanford-oval/storm/blob/main/knowledge_storm/storm_wiki/modules/article_generation.py) passes an outline and collected snippets into section writers. We reused the handoff pattern with the existing planner output, inside the existing synthesis request. Importing STORM's section writers would add calls and a separate retrieval/citation contract.
- [Open Deep Research final report](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/deep_researcher.py) accumulates research findings and hands them to a writer. The prototype accumulates typed, cited claim objects and keeps source identifiers, instead of using compressed free-text notes or borrowing its extra writer/retry machinery.
- [Docling document types](https://github.com/docling-project/docling-core/blob/main/docling_core/types/doc/document.py) provide a structured table and provenance model for ingestion. Mapping or re-extracting the already-indexed tables would introduce migration and source-cell mapping risk without fixing a lost draft finding.
- [ALCE entailment evaluation](https://github.com/princeton-nlp/ALCE/blob/main/eval.py) and [RAGChecker evaluator](https://github.com/amazon-science/RAGChecker/blob/main/ragchecker/evaluator.py) use per-claim or sentence evidence checks. They would introduce a separate model-backed scorer or replace the integrated verifier with a different trust contract. Kept the existing claim-level verifier and deterministic safeguards for this experiment.

## Frozen comparator and offline results

current-multi-agent.zip captures the exact pre-experiment Python files in src and experiments/agentic, including the current research, retrieval, gate, provider adapter and envelope. current-multi-agent.json lists per-file hashes, key dependency versions and the corpus manifest hash. Unpack into a new scratch directory and import from it when evaluating the comparator. Do not unpack over the current checkout. Model files and the frozen corpus stay in their existing locations.

Synthetic and source-backed paired tests use identical fixture retrieval and partial synthesis inputs. Both paths use the real gate and final envelope. The verifier replies are scripted to confirm coverage based on the claims each arm actually offers. Four eligible revision replays were complete in 0/4 current versus 4/4 prototype runs. These cover a methodology/scope control, previously source-reviewed AccurateRAG and cross-paper benchmarks, and a fresh GAIA Table 3 transcription (valid Level 1 and Level 3 questions at 75% and 47%). Each arm needed five scripted stages in those cases. The evidence-insufficient control abstained in both arms, and swapped values and fabricated quotes remained blocked. The GAIA fixture uses source wording because a paraphrase was held by the unchanged numerical checker in both arms. Neither replays nor test turnaround measure live quality or latency. [GAIA v1](https://arxiv.org/html/2311.12983v1)

From the checkout root, using the existing project Python:

```powershell
$env:PYTHONPATH='.;experiments/agentic;experiments/agentic-handoff;experiments/measure/end-to-end-diagnostic;experiments/measure/trace-diagnostics'
python -B -m unittest test_handoff test_agentic test_adversarial test_publication_gate test_diagnose test_audit5 -q
```

## Proposed paired live comparison, approval required

Use all ten previously frozen questions and their original references and scoring rules. This comparison protocol is separate from the original diagnostic plan. Verify the original seal, the current-workflow archive and the prototype digest after approval. Keep references entirely out of generation. Reuse the existing evidence capture and trace diagnostic. Randomize arm order by a predeclared alternating schedule and blind final answers and evidence during scoring. No early result can change configurations or questions.

Use the same pinned demo-100 B2 route with table comparisons, eight passages per search, at most 14 in synthesis and at most one evidence-bearing targeted round. Generate one shared planner reply per question with the unchanged planner, then use it in both arms. This gives identical initial queries and synthesis evidence. If verifiers trigger different second searches, the corpus, route and budget remain matched. Record any difference in delivered evidence and report matched-packet pairs separately for claims about the handoff itself. One bad planner call consumes its slot and can stop the pair. Keep optional business, chart and shadow stages disabled.

Use the existing ChatGPT subscription with gpt-6.1-sol, low effort and a 300-second timeout. Expected around 50 actual application invocations with one complete round per arm, and a hard maximum of 90 (10 shared plans plus 10 x 2 x 4 downstream slots). Each arm has the same five logical stages including the shared plan. Record failed attempts, no provider retries or selective reruns. Stop on authorization, configuration, provider-wide or integrity failures. Do not use the historical ledger.

Compare paired complete supported answers, unsupported publication, false abstentions and passage coverage against the frozen references. Report paired wins/losses/ties, both arms' latency (with and without the shared planning cost), and actual calls and input/output token counts. Treat success as a development signal only. No live results exist at this checkpoint.
