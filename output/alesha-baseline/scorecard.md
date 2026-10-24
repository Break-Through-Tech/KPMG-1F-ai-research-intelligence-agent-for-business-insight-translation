# Alesha Baseline Retrieval Scorecard

## Run and scope

- **Run ID:** `79ba9c5b875fd85eeed8c019cb31fef1830d241810a75f2aa45ff7b11a2c4749`
- **Created:** 2026-10-24T20:24:09.950953+00:00
- **Benchmark:** `alesha-baseline-v1`, 10 queries, top 5 passages per query
- **Recorded commit:** `5bed6eace6bda1a5d31bda23108865fd235dc2e9`
- **Recorded dirty state:** `true`
- **Corpus mode:** `unverified_local_index`
- **Indexed corpus SHA-256:** unavailable (`null` in the run record)
- **Embedding model:** `all-MiniLM-L6-v2`
- **Generation:** not requested (`null`); this is a retrieval-only review, not a summary or answer-quality evaluation.
- **Query outcomes:** 10/10 status `ok`, 50/50 passages captured, no query errors. Summary status is `insufficient_evidence` on each case because generation was not requested.
- **Reviewer:** Alesha. Ratings are based on the retrieved `text` stored in `run.json`, not paper title alone.

The run records hashes for `data/metadata/arxiv_csAI_25_pdf_sample.csv` and `data/metadata/arxiv_csAI_100_metadata.csv`; both match the files currently present. It also records a hash for `data/processed/chunks.parquet`, but that file was not present in the inspected workspace. The local index identity and exact indexed corpus therefore cannot be independently established. The run record's three input hashes remain the provenance source; the recorded chunks hash is `d6c7e00292f3b57c6286acfaeb80669216cd047543a8500d5cad540c1b4c8b19`.

## Precision@5

Precision@5 counts ratings of 1 or 2 as relevant and divides by 5. Each query has five retrieved passages and five completed ratings; no ratings are pending manual review.

| Query ID | Relevant passages (ratings 1–2) | Precision@5 |
|---|---:|---:|
| `alesha-v1-q01` | 5/5 | 1.00 |
| `alesha-v1-q02` | 5/5 | 1.00 |
| `alesha-v1-q03` | 3/5 | 0.60 |
| `alesha-v1-q04` | 4/5 | 0.80 |
| `alesha-v1-q05` | 4/5 | 0.80 |
| `alesha-v1-q06` | 4/5 | 0.80 |
| `alesha-v1-q07` | 4/5 | 0.80 |
| `alesha-v1-q08` | 5/5 | 1.00 |
| `alesha-v1-q09` | 5/5 | 1.00 |
| `alesha-v1-q10` | 4/5 | 0.80 |
| **Mean** | **43/50** | **0.86** |

The denominator is 5 for each query and 10 queries for the unweighted mean. This result is a manual retrieval-relevance score for this recorded run only.

## Verified irrelevant results (rating 0)

These are directly supported by the captured passage text:

| Query ID | Rank | Chunk ID | Source paper/version | Why it misses |
|---|---:|---|---|---|
| `alesha-v1-q03` | 4 | `2604.00324v1_c0071` | `2604.00324v1` | Passage discusses latent-space adversarial training against harmful behaviors/jailbreaks, not multi-turn unlearning robustness. |
| `alesha-v1-q03` | 5 | `2604.00324v1_c0099` | `2604.00324v1` | Passage discusses latent adversarial training and removal of unwanted behaviors, not interaction-driven recovery after unlearning. |
| `alesha-v1-q04` | 5 | `2604.00324v1_c0231` | `2604.00324v1` | Retrieved passage is a references list; it does not explain interpretability approaches. |
| `alesha-v1-q05` | 3 | `2602.00931v2_c0025` | `2602.00931v2` | Retrieved passage is the CU-DPO paper's bibliography/impact material, not how it uses continuous utility scores. |
| `alesha-v1-q06` | 4 | `2605.00276v1_c0026` | `2605.00276v1` | Passage is a references list and provides no single-agent versus multi-agent comparison. |
| `alesha-v1-q07` | 2 | `2606.01494v1_c0039` | `2606.01494v1` | Passage is references for a skill-security paper; it does not describe safety/reliability evaluation approaches. |
| `alesha-v1-q10` | 1 | `2603.00829v2_c0026` | `2603.00829v2` | Passage is a bibliography, not evidence a company can use to validate a vendor's safety/reliability claim. |

## Partial or noisy results (rating 1)

These passages are relevant background or supporting evidence, but do not directly answer the query:

| Query ID | Rank | Chunk ID | Source paper/version | Why only partial |
|---|---:|---|---|---|
| `alesha-v1-q01` | 1 | `2602.00933v3_c0036` | `2602.00933v3` | Server/tool inventory and deployment setup support context, but do not themselves report the benchmark's capabilities or limitations. |
| `alesha-v1-q01` | 4 | `2602.00933v3_c0038` | `2602.00933v3` | Server selection/containerization rationale is useful context, not a direct evaluation result. |
| `alesha-v1-q02` | 3 | `2604.00324v1_c0140` | `2604.00324v1` | Role-playing caveat and rarity/context qualify agentic-misalignment findings but do not enumerate failure modes. |
| `alesha-v1-q05` | 2 | `2602.00931v2_c0003` | `2602.00931v2` | Lists strategy types but does not explain how continuous scores are used in preference optimization. |
| `alesha-v1-q05` | 4 | `2602.00931v2_c0037` | `2602.00931v2` | Aggregate phase/pair statistics are relevant context but not the scoring/training mechanism asked about. |
| `alesha-v1-q05` | 5 | `2602.00931v2_c0016` | `2602.00931v2` | Utility/strategy alignment results provide context, not the mechanism for using the scores. |
| `alesha-v1-q07` | 3 | `2606.01498v1_c0055` | `2606.01498v1` | Describes agent capability and correctness scoring, but in time-series reasoning rather than safety/reliability evaluation specifically. |
| `alesha-v1-q07` | 4 | `2606.01498v1_c0088` | `2606.01498v1` | General deployment safeguards and validation recommendations, not a method for evaluating LLM-agent safety/reliability. |
| `alesha-v1-q07` | 5 | `2603.00829v2_c0034` | `2603.00829v2` | Gives a taxonomy/examples of misaligned tasks; only partially describes an evaluation approach. |
| `alesha-v1-q08` | 1 | `2602.00933v3_c0038` | `2602.00933v3` | MCP server-selection criteria are useful background but do not directly specify a company's access-control/security review. |
| `alesha-v1-q08` | 5 | `2606.01498v1_c0088` | `2606.01498v1` | General time-series agent deployment guidance supports due diligence, but is not specific to MCP/tool access. |
| `alesha-v1-q10` | 4 | `2604.00324v1_c0168` | `2604.00324v1` | Proposes future safety mitigations; it is not itself evidence that a vendor's system has been independently validated. |
| `alesha-v1-q10` | 5 | `2603.00829v2_c0025` | `2603.00829v2` | Warns that monitoring is imperfect and not standalone; relevant qualification, but not a specific validation result. |

## Khoi investigation priorities

1. **Q3 confirmed retrieval misses:** ranks 4–5 (`2604.00324v1_c0071`, `2604.00324v1_c0099`) are from `2604.00324v1`, titled *The Persistent Vulnerability of Aligned AI Systems* in the run metadata. Their actual text concerns adversarial training/jailbreak behavior, not multi-turn unlearning. Ranks 1–3 are on-topic passages from `2603.00823v2`. Check cross-topic nearest-neighbor contamination and chunk/source routing.
2. **Q4 title/content provenance anomaly:** ranks 1–4 contain ACDC/mechanistic-interpretability text and are relevant (ranks 1–3 and 4 rated 2); rank 5 is a references passage (0). However, the run metadata associates all five chunks with `2604.00324v1` and title *The Persistent Vulnerability of Aligned AI Systems*, while the retrieved text explicitly discusses ACDC/circuit discovery. Verify source-document boundaries and paper metadata/chunk attribution before relying on the source title. Relevance ratings are based on the captured text.
3. **Bibliography contamination:** Q5 rank 3 (`2602.00931v2_c0025`), Q6 rank 4 (`2605.00276v1_c0026`), Q7 rank 2 (`2606.01494v1_c0039`), and Q10 rank 1 (`2603.00829v2_c0026`) are clearly bibliography/reference passages and score 0.
4. **Mixed-paper noise:** Q7 ranks 3–5 and Q8 rank 5 are only partially relevant. Q8 ranks 1–4 are MCP-Atlas passages; ranks 1 and 4 are supporting background, while ranks 2–3 directly discuss MCP evaluation and risk.

No passage needed a manual-pending rating because all 50 captured text values were present and sufficient to judge relevance. The corpus/index provenance limitation remains unresolved; this scorecard does not establish reproducibility of a fresh run.

This run did **not** measure summary accuracy, citation-grounding accuracy, or business-implication accuracy.
