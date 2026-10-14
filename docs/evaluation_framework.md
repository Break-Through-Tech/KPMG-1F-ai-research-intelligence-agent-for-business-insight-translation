# Evaluation Framework

## 5.1 — Benchmark Questions

This baseline uses **alesha-baseline-v1**. Its authoritative questions are in
[`evaluation/baseline_alesha_v1.json`](../evaluation/baseline_alesha_v1.json),
with a readable copy in [Benchmark Questions](benchmark_questions.md).
Q1–Q10 below refer to `alesha-v1-q01` through `alesha-v1-q10` in that file.

This is a different question set from the existing
[`evaluation/benchmark_cases.json`](../evaluation/benchmark_cases.json).
Do not combine scores or compare per-question results across those versions.

---

## 5.2 — Retrieval Relevance Metric

**Precision@5**, scored by a human reviewer on each of the top 5 retrieved chunks per question:
- 2 = directly relevant · 1 = partially relevant · 0 = not relevant

Precision@5 = (chunks rated 1–2) ÷ 5, averaged across all benchmark questions. **Target: ≥0.7.**

---

## 5.3 — Summary Quality Rubric

Score 1–5 on each; target average ≥4.

| Dimension | Low | High |
|---|---|---|
| **Accuracy** | Unsupported/contradicted claims | Fully grounded in source |
| **Clarity** | Jargon-heavy, hard to follow | Plain-language, easy to follow |
| **Completeness** | Misses a key point | Covers all key points |

---

## 5.4 — Business Usefulness Rubric

Score 1–5 on each; target average ≥4.

| Dimension | Low | High |
|---|---|---|
| **Actionability** | Just restates research | Clear, specific action |
| **KPMG relevance** | Generic AI commentary | Maps to a real advisory scenario |
| **Citation quality** | No/vague citation | Ties claim to a specific source finding |
