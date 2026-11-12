# Research engine reliability v2

**Status:** opt-in experimental B2 demo with `--arxiv-fallback`. Every answer stays pending and unapproved.

**Depends on PR #181** (`khoi/arxiv-research-fallback`, commit `cc98bd7`). The branch was cut from that commit while #181 is unmerged. Merge #181 first, then rebase this branch onto `main`.

## Why

An independent 30-scenario evaluation of #181 found these problems:
- **Incomplete answers.** Answer completeness was 12/19.
- **Two retrieval misses.**
- **Two avoidable hard failures.**

Citation correctness was already 18/18. The root causes were:

1. **Crowding.** One long paper could take nearly every evidence slot (14 of the top 20 in one case). On multi-part questions, the second part's paper never entered the evidence.
2. **Missing key passages in new papers.** Passages from newly read arXiv papers were ranked by word overlap only. Abstracts and headline results lost to table rows and background text.
3. **Wording-specific shortcuts.** Result and study-date passages were added only when the question contained phrases such as "how often" or "still".
4. **Indistinguishable failures.** A provider failure (for example a usage limit) and a citation-validation rejection both produced the same generic `summary_failed`, and the reason was not recorded. A model that invented a number once got no second chance, so the question ended as an execution error rather than an abstention.

## What changed

### Evidence coverage (`src/experimental/evidence_coverage.py`, `question_parts.py`)

- **Part coverage.** Questions are split syntactically into parts: clause boundaries, interrogative clause starts, and explicit comparisons such as "compare A and B". Each part with enough content is retrieved on its own, and every part list's best passages are anchored.
- **Paper balance.** On a multi-part question, no paper may take more than half the evidence budget while another part's paper is waiting.
- **Role coverage.** A paper holding three or more slots keeps its most relevant abstract passage and its most relevant results passage (at least two reported values). Externally discovered papers also keep a dated study-scope passage. These replace the paper's lowest-ranked passages.
  - The budget never grows.
  - A paper's best passage and other papers' slots are never displaced.
  - A paper with one or two slots can receive its abstract from a crowded paper's tail, but only when that abstract matches the question at least as well.
- **Semantic ranking for new papers.** Externally read papers are reranked with the library's local cross-encoder, then the same coverage rules apply.
- **No hardcoding.** No titles, topics, expected answers or trigger phrases are used.

### Failure handling (`src/answer_validation.py`, `src/indexed_research.py`)

- **Provider failures stay execution errors.** Every provider call is wrapped. A failure keeps the execution-error envelope with a coarse `cause`: `rate_limited`, `timeout` or `provider_error`. These are never retried as validation and never become abstentions, and provider text is never echoed.
- **Validation rejections are recorded and retried once.** A rejection at synthesis, quality review or the numeric citation check records a sanitized reason in `summary.validation.attempts`. The answer is retried once with that reason as feedback: synthesis is regenerated, while a rejected review is re-reviewed.
- **A second rejection becomes a qualified abstention.** No draft is shown, and the result says explicitly that this is not an evidence finding. It does not trigger arXiv search. If an external answer is rejected twice, the library draft is kept, with `arxiv_search.status = answer_failed` and `cause = validation_rejected`.
- **Validators are unchanged.** Exact-quote, numeric-literal, schema and review contracts are the same as before.

### UI (`ui/app.js`)

There are two new notes:
- the draft was withheld after validation failed;
- the answer passed on a checked retry.

## Verification

See the final report in the pull request description for scores and commands. The focused suite is:

```powershell
python -m pytest tests/test_research_reliability.py tests/test_arxiv_fallback.py tests/test_indexed_research.py tests/test_research_chat.py tests/test_answer_quality.py tests/test_experimental_b2_integration.py tests/test_business_evidence_handoff.py -q
```

## Results (November 11, 2026)

**Setup:** an independent harness that is not part of this repository. Fixture mode uses real B2 retrieval, validators and HTTP, with model and arXiv replies scripted; the arXiv replies are real versioned HTML. Live mode uses the configured model and public arXiv.

**Previous 30 scenarios (graded scenarios only):**

| Mode | Before | After |
|---|---|---|
| Fixture | 19/24 | 22/24 |
| Live | 2/5 | 1/3 (arXiv rate limiting made 2 live scenarios unverifiable) |
| Overall | 21/29 PASS | 23/27 PASS |

Citation correctness stayed at 18/18.

**10 unseen scenarios:**

| Mode | v2 | Base |
|---|---|---|
| Fixture | 7/7 | 4/7 |
| Live | — | — |
| Overall (graded) | 7/9 PASS | 5/9 PASS |

Live answers are single runs, not repeated measurements.

## Limitations

- **Splitting is syntactic.** Questions without explicit clause or comparison markers are treated as single-part.
- **Role selection uses the whole question,** not the part, so a part-specific results passage can lose to another value-bearing passage from the same paper.
- **One retry only.** A model that repeats the same mistake ends in a qualified abstention.
- **The retry adds time:** one extra synthesis or review call. Latency was not optimized.
- **The cross-encoder truncates long passages when scoring.** Citations always use the full passage.
