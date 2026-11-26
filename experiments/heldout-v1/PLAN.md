# Held-out retrieval experiment (heldout-v1): plan for approval, not run

The final controlled retrieval experiment before an integration decision.

## Frozen set

Sealed in `seal.json`, with SHA-256 for each file plus the index hash, which equals the pinned B2 `78d8efd7…`.

| ID | Category | Paper (never used before) |
|---|---|---|
| H01 | table | Metadata-driven RAG for financial QA (2510.24402v1) |
| H02 | numeric | CodeAct (2402.01030v4) |
| H03 | table (multi-row) | CodeAct Table A.9 (2402.01030v4) |
| H04 | multi-paper comparison | QuantMCP (2506.06622v2) + metadata-driven RAG |
| H05 | numeric | AgentLAB (2602.16901v1) |
| H06 | qualitative | Persona bias in LLM agents (2602.12285v1) |
| H07 | numeric | SkillSentry (2608.09253v1) |
| H08 | limitations | SpeechT-RAG (2502.10950v2) |
| H09 | qualitative + limitation | SynLLM (2508.08529v1) |
| H10 | comparison + limitations | Causality extraction from medical guidelines (2407.10020v1) |

**Points.** 27 required points, each with anchor passage IDs. All anchors exist in the pinned index; this was checked by ID, not by retrieval.

**Paper selection.** Papers come only from the 23 corpus papers never mentioned in any prior question, reference, label, test or live-run file.

**Answer key.** `answer-key.md` reproduces each anchor passage verbatim, with a reviewer sign-off line per question.

## Arms (only difference: retrieval decomposition)

- **A, `heldout-baseline`.** Baseline/B2 exactly as deployed (`create_research`, quality review on, table comparisons off, top-k 8).
- **B, `heldout-decomposed`.** A plus the opt-in deterministic decomposition: the retrieval-v3 splitter, original question + at most 3 parts, round-robin merge, cap 14.
- **Shared:**
  - same model: `gpt-6.1-sol`, low effort, 300 s timeout, ChatGPT login
  - same index and frozen questions
  - same synthesis and answer-quality review
- **Excluded:** no table comparisons and no top-k change. Decomposition is frozen as prototyped; nothing was tuned on H01–H10. No retrieval was run on the held-out questions before the live run, to avoid peeking.

## Measures

Recorded per question and arm:

- required-point score (1 / 0.5 / 0), source-reviewed, then human review
- complete / partial / abstained
- unsupported and misleading claims
- citation accuracy
- anchor evidence coverage
- evidence crowding (original passages displaced) and off-paper passages
- retrieval seconds and total seconds
- calls and tokens
- a per-question verdict: helped / hurt / no difference

## Decision rule (frozen in `rules.json`)

Prefer B only if **all** of these hold:

- at least 2.0 more points out of 27;
- more question wins than losses;
- no more unsupported or misleading claims;
- no more abstentions;
- median total response time no more than 15 s above A, and p90 no more than 30 s above A.

A gain of 0.5–1.5 points is inconclusive: B stays opt-in, not integrated. Otherwise keep A.

If more than 2 pairs hit execution errors, the result is inconclusive.

## Budget and safeguards

- **Calls:** 2 per question per arm, so 40 expected. The cap is 30 per arm, 60 total, persistent in each arm's `calls.sqlite3`, and resume never repeats finished questions.
- **Tokens:** about 0.37M input for A and about 0.5–0.6M for B (14-passage packets), so about 0.9M input and 17k output in total.
- **Time:** about 6 minutes for A and about 8–10 minutes for B.
- **Run order:** A first, then B, one at a time.
- **Pre-flight refuses to start if** the seal fails, ChatGPT login or the model is missing, or free commit is below 6 GB.
- **Stops on:** login, quota or rate-limit errors, MemoryError, budget exhaustion.

## Readiness (offline, 2026-11-23)

- `--check heldout-baseline` and `--check heldout-decomposed` pass. Free commit is 6.1–6.2 GB, which is marginal, so close browsers first.
- `test_codex_heldout.py` passes 5 tests:
  - the arms differ only by decomposition;
  - the ten frozen questions run at 2 calls each;
  - B feeds the merged packet with the same call count;
  - resume does not repeat work;
  - the seal detects tampering.
- The full offline suite passes. `src` is identical to the automated reviewer worktree.

## Limitations

1. **The questions are written by the same assistant that built the decomposition.** The questions were written from source passages before any run, without retrieval. Even so, scoring needs independent human review of `answer-key.md` and of every published claim.
2. **The sample is small:** 10 questions and 27 points. Only H04 (and partly H03 and H10) strongly needs multi-part retrieval, so B's benefit may be underestimated for business questions that span several sources.
3. **Each question runs once per arm, with no repeats.** Run-to-run variance of about ±0.5–1 point per question was seen earlier on identical evidence (F01). The 2-point threshold only partly absorbs that.
4. **Single model and single corpus snapshot.**
