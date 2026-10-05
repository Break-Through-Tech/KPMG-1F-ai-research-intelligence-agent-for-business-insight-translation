# Evaluation Framework

## 5.1 — Benchmark Questions

**Factual:**
1. What approaches improve reasoning efficiency in LLMs?
2. What risks have recent papers identified with multi-agent LLM systems?
3. What techniques are used for fine-tuning LLMs with limited data?
4. How are sparse autoencoders used to interpret model behavior?

**Comparative:**
5. How do different preference-optimization approaches (e.g. DPO variants) compare?
6. What are the tradeoffs between supervised and self-supervised reasoning methods?
7. How does single-agent vs. multi-agent research differ in reported outcomes?

**Business-translation:**
8. What should a company evaluate before deploying an AI agent for customer-facing tasks?
9. What risks should a business weigh when fine-tuning an LLM on proprietary data?
10. What should a business ask a vendor claiming their AI agent is "interpretable"?


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

