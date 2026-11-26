# Baseline/B2 question decomposition (opt-in, offline prototype)

**Goal:** better Baseline evidence without Multi-Agent and without extra model calls.

**Status:** offline only. No live model calls, no app change, no merge.

## What it is

- `question_parts.py`: the retrieval-v3 deterministic splitter (`khoi/research-retrieval-v3` @ f6efa05). Only its relative import changed. Nothing else from that branch was copied.
- `decomposed_retrieval.py`: wraps B2 `retrieve(query, top_k)`.
  - It searches the original question, then each splitter part (at most 3), each with the same top-k.
  - Results are merged round-robin with the original question first and deduplicated by `chunk_id`; passages pass through unchanged.
  - The merged result is capped at 14.
  - A failed or empty part search is skipped; a failure of the original search still propagates.
- Baseline's synthesis, answer-quality review and default configuration are unchanged: still 2 model calls per question.

## Offline evidence coverage on F01–F10

Command: `coverage.py`. Output: `coverage-v1.json`. Configuration: deployed B2, table comparisons off, top-k 8. The original packets match the saved live Baseline packets exactly (10 of 10).

| Required anchors in packet | Original Baseline | Decomposed | Multi-Agent (saved) |
|---|---|---|---|
| Points with anchor present (of 22) | 15 | **18** | 20 |

- **Recovered by decomposition:** F01.2 (Table 1 row 3), F02.2 (Solar row), F05.1 (c0000).
- **Still missing:**
  - **F05.2 (c0020).** Multi-Agent found it only through its verifier-requested second-round search. The splitter sees one named target in F05, so it falls back to clause parts. A dataset-specific search ranks c0020 first. *Not tuned*, to avoid overfitting the development set.
  - **F05.3 (anchor c0032).** Its content is available through the equivalent passages c0000 and c0005.
  - **F04.2.** No system has the anchor; the caption content is available via c0022.
  - **F08.1 (c0054).** It ranks 10th for the original question, just outside top-8. This is a depth problem, not a decomposition one.
- **Crowding:** no previously covered anchor was lost. The original 8 passages are kept in full in 8 of 10 questions; 7 of 8 are kept in F05 and F07, where the cap displaced one low-rank original passage.
- **Irrelevance proxy:** passages from papers outside a question's reference papers rose from 8 of 80 to 33 of 125. That is more noise for synthesis to ignore, and its effect on answers is unmeasured.
- **Resources:**
  - Retrieval wall time per question: median 4.6 s to 12.2 s (3–4 B2 searches, CPU).
  - Peak process commit: 1.48 GB, versus about 1.41 GB without decomposition.
  - No model calls added.

## Tests

`test_decomposed_retrieval.py`, 10 tests, all passing. They cover:

- a simple question searched once
- a multi-part question with original and part searches
- no duplicate searches
- round-robin order with deduplication
- the cap, with the original top 3 guaranteed
- passages passed through unchanged
- a failed or empty part search skipped
- failure of the original search propagating
- top-k passed through
- Baseline receiving the 14-passage packet with still exactly 2 model calls

## Assessment

Decomposition recovers 3 of the 5 anchor points that Multi-Agent's retrieval had and Baseline lacked, at zero model calls, about 8 s more retrieval and about 0.07 GB more memory. Retrieval coverage is not answer quality.

It is worth a held-out test as **Baseline + decomposition** versus Baseline. Optionally add a depth variant (original query top-k 10), which would address F08.1-type misses. Do not tune the splitter on F01–F10.
