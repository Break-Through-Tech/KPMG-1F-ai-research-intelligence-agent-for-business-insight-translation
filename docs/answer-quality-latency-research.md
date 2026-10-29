# Concise business advice and latency — development findings

## What changed

The opt-in indexed `--quality-check` mode now requests implications organized by
distinct business decisions rather than by each research claim. Overlapping pilot
and orchestration recommendations should become one integrated action, retaining
supporting citations and transfer assumptions. Genuinely distinct decisions and
conflicting conditions must remain separate. This instruction is not a guarantee
of semantic deduplication.

A deterministic final pass merges only identical text/action pairs (whitespace
normalized, case preserved), combining citations and assumptions without changing
their order or input objects. It never uses a word-overlap threshold to discard
paraphrases, numbers, negation, conditions, or different actions. Oversized compact
output is rejected, not silently truncated; the existing business-failure path
preserves the accepted research summary.

Independent indexed requests record context, retrieval, synthesis, quality-review,
business-translation and total elapsed seconds. Timers are per request, include
failed measured stages, and participate in the final review fingerprint. The
reported total covers backend research processing, including identity checks;
it excludes server startup, HTTP transfer, presentation rewriting and SQLite saving.
The UI shows the total; stage details remain in result provenance.

`--codex-effort low` exposes the existing provider's explicit effort setting. The
default remains medium. The faster development server uses low effort on the
same model; it retains the separate quality review, exact-quote validation,
pending approval, full retrieval evidence, and failure behavior. No extra agents,
new models, new dependencies, corpus changes or ranking changes were introduced.

## Research consulted

| Primary source | Relevant finding | Decision for this app |
| --- | --- | --- |
| [Goldstein & Carbonell, MMR summarization (1998)](https://aclanthology.org/X98-1025.pdf) | Combines relevance with novelty to reduce redundant selected passages. | Useful future retrieval/selection experiment. Current repetition arose in generated advice, so we added a distinct-decision policy and conservative exact deduplication. We did **not** implement or claim an MMR ranking algorithm. |
| [Asai et al., Self-RAG (2023)](https://arxiv.org/html/2310.11511v1) | Trains retrieval, generation and relevance/support reflection using reflection tokens. | Supports evaluating relevance/support as separate dimensions. Retain our explicit review call; it is a prompting-based experiment, **not** a reproduction of trained Self-RAG. |
| [Chen et al., FrugalGPT (2023)](https://arxiv.org/pdf/2305.05176) | Studies prompt adaptation, approximation and learned model cascades for cost/quality tradeoffs. | Motivates measured allocation of inference effort. Our same-model low-effort option is **not** a learned cascade, and the paper's cost results do not establish this app's latency improvement. |

MMR cannot establish factual support. A cheaper/shorter route must preserve useful
findings and abstention behavior. Additional sequential critics or multi-sample
ensembles would add calls; no paper is used to justify a speed guarantee here.

## Observed live timings

Actual local development envelopes are retained in ignored
`data/processed/answer-quality-dev/timing-before.json` and `timing-after.json`.
Both runs used the same question and identical five retrieved passages. They used
the same existing subscription model, gpt-6.1-sol, with the quality check enabled.
The before run used medium effort and the earlier business policy; after used low
effort plus the concise policy. Both changes varied together, so their individual
effects cannot be separated by this comparison.

| Stage | Before, seconds | After, seconds |
| --- | ---: | ---: |
| Business-context extraction | 5.1003 | 4.9571 |
| Retrieval | 0.0158 | 0.0156 |
| Synthesis | 17.9291 | 11.5202 |
| Quality review | 7.1052 | 6.7647 |
| Business translation | 11.7043 | 11.5175 |
| Total processing | 41.9691 | 34.8889 |

The total decreased by about 17% in this one paired observation. Network/provider
variation and stochastic outputs mean this is not a stable latency estimate or
quality-equivalence result. Retrieval was negligible; synthesis was the largest
observed stage. Both measured runs happened to produce one implication, while the
earlier user-provided result contained two overlapping pilot recommendations.
The after run retained an upfront banking-evidence gap, two bounded research
findings, adverse results, transfer assumptions and one integrated proposed pilot.
Claims were inspected by the coding assistant, not independently human-reviewed.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m src.research_demo --index data/chroma_db --codex-model gpt-6.1-sol --codex-effort low --quality-check --port 8772
.\.venv\Scripts\python.exe -m evaluation.check_answer_quality_dev --baseline data/processed/answer-quality-dev/timing-before.json --output data/processed/answer-quality-dev/new-low-run --model gpt-6.1-sol --effort low --compact-business
```

Keep development/held-out cases separate. The harness retains failures, frozen
evidence identity, model/effort, policy hashes, actual outputs and call receipts in
a new output directory. Inspect supported and unrelated controls as well as the
banking answer before drawing conclusions. No automated human approval is granted.

All 72 non-HTTP focused regressions passed. The lower-effort frozen development
run completed all three cases: the banking answer retained partial coverage and
one business implication, the supported control retained useful comparative
findings, and the unrelated control abstained. These are development observations,
not independent accuracy scores. The combined Windows HTTP suite encountered
intermittent WinError 10053 while rejecting requests before reading their bodies;
the failing isolated case passed on rerun, but another early-rejection case failed
in the next combined run. Do not describe that combined suite as a clean pass.
The actual before/after browser HTTP research requests completed successfully.
