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


---

## 5.5–5.6 — Review protocol (v1)

This consolidates the existing questions and thresholds; it does not replace them.
Review research passages and generated claims separately from the regulatory
checkpoint in [Human checkpoint](../../docs/human-checkpoint.md). A model verdict
is not approval, and paper chunk IDs are not regulatory source IDs.

### Frozen artifact and reviewer sheet

Review one immutable benchmark export, not a mutable notebook view. Record its
run ID/content hash, repository SHA, corpus/index identity (unknown when not
verified), embedding model, generation model/settings, prompt version, top-k,
and fixture/real execution. Keep failed queries and unavailable stages visible.
Do not compare scores across differing versions as if they were one run.

One review record per query and reviewer uses this JSON-compatible format:

```json
{
  "run_id": "from the frozen benchmark export",
  "query_id": "q01",
  "reviewer": "actual reviewer name",
  "reviewer_kind": "human",
  "coverage": "partially_covered",
  "passage_ratings": [{"chunk_id": "from this query", "rating": 2, "notes": "source check"}],
  "claim_checks": [{"stage": "summary", "item_index": 0, "chunk_ids": ["from this claim"], "supported": true, "notes": "location checked"}],
  "summary_scores": {"accuracy": 4, "clarity": 4, "completeness": 3},
  "business_scores": null,
  "abstention": "not_applicable",
  "notes": "actual observations, not guessed approval"
}
```

Allowed coverage values: `answerable`, `partially_covered`, `unanswerable`, or
`not_checked`. Passage ratings are integers 0–2. Summary/business rubric dimensions
are integers 1–5; use `null` for an unavailable/unreviewed stage, with a reason in
notes. Business keys are `actionability`, `kpmg_relevance`, `citation_quality`.
Abstention is `correct`, `incorrect`, `not_applicable`, or `not_checked`.
`reviewer_kind` is `human` or `fixture`; fixture arithmetic never counts as actual
team review. Identify the frozen export with its `run_id` on every record.

Identify each reviewed statement with `stage` (`summary` or `business_insight`)
and zero-based `item_index` in the frozen `claims` or `implications` array.
Keep that statement's citation IDs in `chunk_ids`; a source chunk is not a
claim identifier. Check each available statement once, including statements that
share citations. For example, two summary claims citing `chunk-a` can have
opposite verdicts without ambiguity:

```json
[
  {"stage": "summary", "item_index": 0, "chunk_ids": ["chunk-a"], "supported": true, "notes": "First statement confirmed on page 2."},
  {"stage": "summary", "item_index": 1, "chunk_ids": ["chunk-a"], "supported": false, "notes": "Second statement goes beyond the same source."}
]
```

`business_insight` item 0 is distinct from `summary` item 0. Missing checks are
incomplete review, not supported claims. This locator does not change the pipeline
output schema.

Check each passage against the linked original source and exact page/heading.
Check every claim for factual support, omissions and contradiction—not just an
existing citation ID. For business implications, distinguish research findings,
assumptions, proposed actions, jurisdiction constraints and regulatory evidence.
Sources, applicability and any approval decision require explicit human review.

### Denominators, missing stages and abstention

- Precision@5 retains denominator **5**, even with fewer hits. Unreturned ranks
  contribute zero. Rate at most the first five passages; top-k above five does
  not change the metric. Unrated returned passages are **incomplete**, not zero.
- A completed no-hit review has Precision@5 = 0. A failed retrieval has no score
  and is reported as a failure; no overall target pass is claimed while benchmark
  queries are failed or incompletely reviewed.
- Report the all-question macro average and its completed/total query denominator.
  Also report the answerable/partially-covered subset separately. An uncovered
  question is a corpus coverage gap, not automatically a retrieval implementation
  defect. Never silently remove it from the headline benchmark denominator.
- Summary/business means use only scored available outputs. Report scored/available/
  total counts and missing, failed, or insufficient-evidence stages alongside them.
  Never claim target attainment from incomplete scoring or silently turn missing
  output into a successful score. Keep the existing targets ≥0.7 and average ≥4.
- Score abstention correctness separately against human-checked coverage. Do not
  invent an answer for an uncovered question, reward unsupported fluency, or treat
  all `insufficient_evidence` outputs as correct without inspecting coverage.

### Locked-corpus coverage screen — October 12, 2026

Screened titles/abstracts in the committed 100-paper metadata snapshot, restricted
by ID to the locked 25-paper manifest. These are **tentative coverage candidates**,
not full-paper support checks or verified live publication facts. Original
pages/sections still require reviewers to confirm answerability before scoring.
A topic absent from these abstracts is not proven absent from every paper body.

| Query | Tentative coverage | Candidate locked IDs / gap |
|---|---|---|
| q01 | partially_covered | 2602.00931v2 (reasoning strategies), 2608.00335v1 (web-agent step efficiency); not a comprehensive LLM-efficiency survey |
| q02 | partially_covered | 2604.00319v1 (collaboration), 2603.00829v2 (agent monitoring); multi-agent-specific risk coverage needs checking |
| q03 | unanswerable, tentative | CLAMP concerns robotic policies, not limited-data LLM fine-tuning; no direct abstract match found |
| q04 | unanswerable, tentative | 2603.00824v2 discusses representations, not a demonstrated sparse-autoencoder study; no direct abstract match found |
| q05 | partially_covered | 2602.00931v2 covers CU-DPO vs binary preference supervision; breadth of DPO variants is limited |
| q06 | partially_covered | 2608.00335v1 covers SFT/RL recipes, but self-supervised-reasoning comparison is not established |
| q07 | partially_covered | 2605.00276v1 explicitly compares an orchestrated trip-planning system with single-agent/workflow baselines |
| q08 | partially_covered | 2602.00933v3 tool-use evaluation, 2603.00829v2 monitoring, 2606.01498v1 reasoning failures; business advice remains inference |
| q09 | unanswerable, tentative | Safety/security papers do not establish proprietary-data fine-tuning/privacy guidance in the abstract screen |
| q10 | partially_covered | 2604.00324v1 discusses circuit discovery; vendor due diligence and interpretability claims need separate checking |

Coverage ownership and final page/section checks are unassigned, not presumed to
be any teammate's commitment. Use the source metadata/manifest hashes in the
benchmark export to bind this screen to a snapshot; recheck it after corpus changes.

### Pilot and reviewer allocation

Worked synthetic arithmetic: two returned passages rated 2 and 1 produce
Precision@5 = 2/5 = **0.4**, not 1.0. A supported synthetic claim can demonstrate
the sheet shape; it says nothing about actual paper accuracy. This is a protocol
example, **not a completed team pilot**.

Before final Week 7.5/8 scoring, teammates must claim query batches in #65 and
name actual reviewers. Double-review at least one shared question per question
type, plus failures/abstentions. A feature author should get a second reviewer
where possible. Preserve both independent records. Resolve disagreements with a
separate adjudication note quoting the evidence and naming the actual resolver;
never overwrite original scores or average disagreement away without disclosure.
Report KPMG stakeholder feedback only when received, separately from team review.

Remaining acceptance: full-paper coverage confirmation, a pilot by actual team
reviewers, claimed reviewer allocation, and final frozen-run scoring. These are
not supplied or fabricated by this documentation PR.
