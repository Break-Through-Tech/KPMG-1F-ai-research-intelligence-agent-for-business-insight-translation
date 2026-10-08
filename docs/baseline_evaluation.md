# Baseline Evaluation

## 1. Overview

This document evaluates the baseline RAG pipeline using the evaluation
framework defined in `evaluation_framework.md`.

The evaluation measures:
- Retrieval relevance using Precision@5
- Summary quality
- Business usefulness

## 2. Retrieval Evaluation

Each of the top 5 retrieved chunks for each benchmark question was
manually scored:

- 2 = directly relevant
- 1 = partially relevant
- 0 = not relevant

### Precision@5 Results

| Question | Chunk Scores | Precision@5 |
|---|---|---:|
| Q1 | 2, 2, 2, 2, 2 | 1.00 |
| Q2 | 2, 2, 2, 1, 2 | 1.00 |
| Q3 | 2, 2, 2, 0, 0 | 0.60 |
| Q4 | 2, 2, 2, 2, 0 | 0.80 |
| Q5 | 2, 1, 0, 1, 1 | 0.80 |
| Q6 | 2, 2, 2, 0, 2 | 0.80 |
| Q7 | 2, 0, 2, 2, 1 | 0.80 |
| Q8 | 2, 1, 2, 2, 2 | 1.00 |
| Q9 | 2, 2, 2, 2, 2 | 1.00 |
| Q10 | 0, 2, 2, 1, 2 | 0.80 |

**Overall Precision@5: 0.84**

**Target: ≥ 0.70 — PASS**

## 3. Summary Quality

Each answer was scored from 1–5 for accuracy, clarity, and completeness.

| Question | Accuracy | Clarity | Completeness | Average |
|---|---:|---:|---:|---:|
| Q1 | 5 | 5 | 4 | 4.67 |
| Q2 | 5 | 5 | 5 | 5.00 |
| Q3 | 5 | 5 | 5 | 5.00 |
| Q4 | 5 | 4 | 5 | 4.67 |
| Q5 | 5 | 5 | 4 | 4.67 |
| Q6 | 5 | 5 | 5 | 5.00 |
| Q7 | 4 | 5 | 4 | 4.33 |
| Q8 | 5 | 5 | 5 | 5.00 |
| Q9 | 5 | 5 | 5 | 5.00 |
| Q10 | 5 | 5 | 5 | 5.00 |

**Overall Summary Quality: 4.83 / 5**

**Target: ≥ 4.0 — PASS**

## 4. Business Usefulness

Each answer was scored from 1–5 for actionability, KPMG relevance, and citation quality.

| Question | Actionability | KPMG Relevance | Citation Quality | Average |
|---|---:|---:|---:|---:|
| Q1 | 4 | 4 | 5 | 4.33 |
| Q2 | 4 | 4 | 5 | 4.33 |
| Q3 | 4 | 4 | 5 | 4.33 |
| Q4 | 4 | 4 | 5 | 4.33 |
| Q5 | 3 | 2 | 5 | 3.33 |
| Q6 | 5 | 5 | 5 | 5.00 |
| Q7 | 4 | 4 | 5 | 4.33 |
| Q8 | 5 | 5 | 5 | 5.00 |
| Q9 | 3 | 5 | 5 | 4.33 |
| Q10 | 5 | 5 | 5 | 5.00 |

**Overall Business Usefulness: 4.43 / 5**

**Target: ≥ 4.0 — PASS**

## 5. Overall Baseline Assessment

The baseline retrieval and generation pipeline met all three evaluation
targets.

- Precision@5: **0.84**
- Summary Quality: **4.83 / 5**
- Business Usefulness: **4.43 / 5**

The main observed limitation was Question 5, where the retrieved excerpts
did not provide enough information to fully explain how continuous utility
scores are used during preference optimization. The system appropriately
abstained rather than introducing unsupported information.

The evaluation suggests that the baseline performs well on questions where
the indexed research contains direct evidence, while more specific
questions may require improved retrieval or additional context.