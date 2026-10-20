# Issue #122: Retrieval and contract diagnostics

## What I tested

I checked whether our research agent retrieves useful evidence and handles invalid inputs correctly. I used the existing 25-paper corpus (877 HTML chunks) and the team's retrieval and contract tests. I did not change production code, the frozen corpus, or ranking settings.

## What I found

### 1. Evaluation criteria

I tried two questions about how AI agents are evaluated. Both returned relevant evidence in the top five results. For the more specific question, another useful passage (`2604.00319v1_c0019`) appeared at rank 19 when I expanded the search to 20 results.

I checked that passage against [the original paper](https://arxiv.org/html/2604.00319v1#S3.SS2). It includes criteria such as accuracy, relevance, completeness, and clarity. The information was preserved in the corpus, and other top-five passages already answered the question. **This is a ranking observation, not a confirmed retrieval failure.** These were earlier runs that have not been reproduced on the pinned implementation below.

### 2. XGBoost compared with LLM agents

I asked how XGBoost compared with LLM-based agents on accuracy, precision, recall, and speed. The retriever found the paper's qualitative conclusion at ranks **1** (`2604.00319v1_c0007`) and **4** (`2604.00319v1_c0029`): XGBoost performed better and faster in the paper's fault-detection experiment.

The more useful finding came from checking [Table 1 in the original paper](https://arxiv.org/html/2604.00319v1#S5.T1):

| Approach | Accuracy | Precision | Recall |
|---|---:|---:|---:|
| XGBoost agents | 0.9644 | 0.9397 | 0.9929 |
| Llama3.2 agents/critics with RAG | 0.5882 | 0.8000 | 0.6154 |
| Llama3.2 agents/critics without RAG | 0.4612 | 0.4027 | 0.6648 |

These numbers come from **the original HTML table, not the retrieved passages**. I checked the searchable chunks and found that the table's exact metric values were missing. The existing HTML parser keeps table captions but excludes table bodies, which explains the omission.

**Result:** The system successfully retrieved *which approach performed better*, but its indexed text did not contain the exact numbers needed for a precise comparison. This is an extraction-policy limitation, not a confirmed new code bug. I did not run answer generation, so I cannot claim a generation failure.

## Contract checks

I reused existing tests instead of writing duplicates.

| Test suite | Result |
|---|---:|
| Research contracts and pipeline | 22 passed |
| Generation BYOK | 7 passed |
| Retrieval | 6 passed |

The passing tests exercised duplicate or invalid IDs, invalid distances, missing citation metadata, inconsistent HTML/PDF source locations, and provider failures. I did not find a new confirmed contract defect. I still need to verify whether **duplicate ranking entries** are covered separately from duplicate IDs. The generation-schema suite was not run in this test environment.

## What I would investigate next

1. **Numerical evidence:** Try preserving Table 1 values in a small development-only extraction experiment. Check whether numerical questions become answerable and whether citations still point to the correct table. Leave the frozen corpus unchanged.
2. **Contract coverage:** Check the duplicate-ranking and schema cases against existing tests. Only add a regression test or fix if there is a reproducible gap.

No production changes or bug fixes are included in this work. These cases are useful diagnostics, but they do not establish overall retrieval quality.

## Evidence and reproduction

The verified XGBoost run used commit `2e7c3463c2d42d087c7294350d79ea1b6a86a4dd`, `all-MiniLM-L6-v2` embeddings (384 dimensions), and an index reconciled with all 877 input chunks. The input Parquet SHA-256 was `593944df0172f51734451d92c16707d58da714b4f823eb2c4b660dfaa7bd0029`.

**Exact queries**

- **Q1:** `How are AI agents evaluated?`
- **Q2:** `What criteria do AI critics use to evaluate agent responses?`
- **Q3:** `How does XGBoost compare with LLM-based AI agents for fault detection in terms of accuracy, precision, recall, and speed?`

The following are the recorded top-five results for Q1 and Q2 from earlier runs. Their original commit and raw JSON were not retained, so these are **historical observations**, not reproduced results from the pinned run.

| Query | Rank | Chunk ID | Distance | Original source |
|---|---:|---|---:|---|
| Q1 | 1 | `2608.00339v1_c0009` | 0.7204969525337219 | [Section 5](https://arxiv.org/html/2608.00339v1#S5) |
| Q1 | 2 | `2604.00319v1_c0018` | 0.8369321823120117 | [Section 3.2](https://arxiv.org/html/2604.00319v1#S3.SS2) |
| Q1 | 3 | `2604.00319v1_c0014` | 0.8579881191253662 | [Section 3](https://arxiv.org/html/2604.00319v1#S3) |
| Q1 | 4 | `2608.00339v1_c0001` | 0.8668950200080872 | [Section 1](https://arxiv.org/html/2608.00339v1#S1) |
| Q1 | 5 | `2604.00319v1_c0004` | 0.8684289455413818 | [Section 1](https://arxiv.org/html/2604.00319v1#S1) |
| Q2 | 1 | `2604.00319v1_c0018` | 0.6625474691390991 | [Section 3.2](https://arxiv.org/html/2604.00319v1#S3.SS2) |
| Q2 | 2 | `2604.00319v1_c0004` | 0.7052348256111145 | [Section 1](https://arxiv.org/html/2604.00319v1#S1) |
| Q2 | 3 | `2604.00319v1_c0014` | 0.7933472394943237 | [Section 3](https://arxiv.org/html/2604.00319v1#S3) |
| Q2 | 4 | `2608.00339v1_c0001` | 0.7967307567596436 | [Section 1](https://arxiv.org/html/2608.00339v1#S1) |
| Q2 | 5 | `2604.00319v1_c0010` | 0.8789467811584473 | [Section 2](https://arxiv.org/html/2604.00319v1#S2) |

For Q2 with `top_k=20`, `2604.00319v1_c0019` was rank 19; its distance was not retained. The complete Q3 results, including all five passages, ranks, distances, and URLs, are in [the JSON evidence file](issue-122-case2-laptop-receipt.json). Retrieval distance is not a confidence score or proof of relevance.

To reproduce a search, prepare the existing frozen corpus and Chroma index, then run this checked-in entrypoint from the repository root, replacing the query text with Q1, Q2, or Q3:

```powershell
.\.venv\Scripts\python.exe src/retrieval.py --query "How are AI agents evaluated?" --top-k 5
```

For Q2, repeat with `--top-k 20` to check the deeper-ranked passage. The earlier Q1/Q2 runs used `python main.py --query "<question>" --top-k 5 --mode retrieval`. Exact rankings may vary across model revisions and index builds.
