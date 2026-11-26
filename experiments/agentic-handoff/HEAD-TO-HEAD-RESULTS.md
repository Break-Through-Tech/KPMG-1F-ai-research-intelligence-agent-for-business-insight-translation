# Baseline/B2 (deployed) vs current Multi-Agent: development results (2026-11-23)

- **Model:** `gpt-6.1-sol`, low effort, on the same frozen F01–F10 questions.
- **Multi-Agent:** the saved current-arm runs from `automated reviewer-paired-v1-full`, with the offline statistical-report correction for F09.
- **Baseline:** `automated reviewer-baseline-v1-deployed`, as the app builds it.
- **Scope:** development questions only. Source review is machine-assisted, not human sign-off.

## Tables variant failure: diagnosis (offline)

- **What failed:** F01 completed, using 2 calls. F02 failed inside retrieval (`retrieval_failed`, the wrapper's label for any exception). F03–F10 each raised `MemoryError` within 0.2 s, before any model call.
- **Mechanism:** system-wide commit exhaustion, not the LLM and not a retrieval bug.
  - Windows commit headroom was about 3.7–4.6 GB free of a 44.8 GB limit, dominated by many Edge and Chrome processes from automated browser sessions.
  - Local reproduction with table comparisons on: F01–F07, including F02, retrieve and validate fine. The process commits about 1.15 GB after loading and peaks at about 1.41 GB, gaining about 0.03 GB per question before levelling off. Nothing accumulates and no single operation is large.
  - No duplicate Python model or index loads were running.
- **Recovery** (`codex_baseline.py`, tests in `test_codex_baseline.py`, 6 passing):
  - `MemoryError` now stops the run, so later questions are not burned through; a rerun resumes.
  - The run refuses to start below 6 GB of free system commit. It currently refuses (4.6 GB free).
  - Rerunning `--run tables` resumes F02–F10 only. That is 18 calls expected; 28 remain under its cap.

## Source-reviewed scores (out of 22 required points)

| Q | Baseline (deployed) | Multi-Agent (current, corrected) | Cause of difference |
|---|---|---|---|
| F01 | 1.5: table-based count and baseline missing | 2 | Retrieval: Baseline never received Table 1 row 3 |
| F02 | 1.5: Solar time points missing | 2 | Retrieval: Baseline never received Table 1 row 2 |
| F03 | 2 | 2 | |
| F04 | 2: "converts image documents into text" covers captions | 1.5: captions omitted | Multi-Agent draft omission |
| F05 | 2.5: advisor and investor sources missing | 3 | Retrieval: Baseline never received c0020 |
| F06 | 3 | 3 | |
| F07 | 2 | 2 | |
| F08 | 1.5 | 1.5 | Both retrieval-limited: c0054 never retrieved |
| F09 | 2 | 2 (with correction; 1 uncorrected) | Baseline's path does not run the number check |
| F10 | 2 | 2 | |
| **Total** | **20.0** | **21.0** | |

| Measure | Baseline (deployed) | Multi-Agent (current) |
|---|---|---|
| Complete / partial / abstained | 6 / 4 / 0 | 8 / 2 / 0 |
| Unsupported findings | 0 | 0 |
| Interpretations published | 2 (F06 "practical reading", extrapolated from an error analysis but labelled interpretation; F08, faithful to c0055) | 0 (policy) |
| Calls | 20 (2 per question) | 32 (about 3.2 per question) |
| Input / output tokens | 0.37M / 8.6k | about 0.58M (estimated share of the paired run) / about 11k |
| Wall time per question | median 36 s, max 56 s | median 44 s, max 271 s |

## Decision rule (pre-registered)

**Deployed comparison.** Multi-Agent publishes more required points (21 vs 20) and no more unsupported or misleading claims. The rule's condition is met, by a margin of **1 point in 22**, on development questions.

**Attribution.** All three of Baseline's lost half-points are retrieval-limited: one search of 8 passages, without table comparisons, never delivered the needed rows or passage. Multi-Agent gained them through broader retrieval (planner sub-searches, more passages, table comparisons), not through its verifier. It lost one half-point to its own draft omission.

**Retrieval-adjusted comparison.** Unavailable until the tables variant is recovered. That variant tests whether Baseline with table comparisons closes F01 and F02 (likely). F05 depends on multi-search decomposition.

## Recommendation

- Multi-Agent's extra quality on these questions is small, and it comes from retrieval breadth.
- It costs about 1.6× the calls and tokens, a much longer latency tail, and substantially more moving parts.
- That **does not justify making Multi-Agent the default.**
- Keep Baseline/B2 as the default, and improve its retrieval instead: table comparisons, plus decomposition for multi-part questions.
- Keep Multi-Agent's safeguards (quote grounding, interpretation policy, statistical fix) as opt-in candidates for Baseline, to be tested separately.
- Recover the tables variant (about 18 calls) to confirm the attribution, then decide on the held-out set.

## Tables variant recovered (2026-11-23): three-way comparison

- **Run:** `automated reviewer-baseline-v1-tables`. All 10 questions complete. F01 was kept from the first run; F02–F10 ran with 8.5 GB of free commit.
- **Usage:** 20 calls total, 0.375M input / 8.8k output tokens, wall time median 31 s and max 52 s.

| Q | Baseline deployed | Baseline + tables | Multi-Agent (corrected) | What decided it |
|---|---|---|---|---|
| F01 | 1.5 | 1 | 2 | Neither Baseline packet had Table 1 row 3 (identical packets). In the tables run, the answer-quality review dropped the partial table-based claim, correctly noting that 72 was derivable (generation variance on the same evidence). Multi-Agent's sub-searches retrieved row 3 |
| F02 | 1.5 | 1.5 | 2 | Neither Baseline packet had the Solar row (identical packets); Multi-Agent's sub-search found it |
| F03 | 2 | 2 | 2 | |
| F04 | 2 | 2 | 1.5 | Multi-Agent omitted image captions (synthesis) |
| F05 | 2.5 | 2.5 | 3 | Advisor/investor passage c0020 never retrieved by either Baseline; Multi-Agent's sub-searches found it |
| F06 | 3 | 3 | 3 | Both Baselines published an extrapolated "classify the whole response" interpretation, labelled as such; Multi-Agent withheld it |
| F07 | 2 | 2 | 2 | |
| F08 | 1.5 | 1.5 | 1.5 | c0054 retrieved by no system |
| F09 | 2 | 2 | 2 | |
| F10 | 2 | 2 | 2 | |
| **Total /22** | **20.0** | **19.5** | **21.0** | |

Unsupported findings: 0 / 0 / 0. Complete questions: 6 / 5 / 8. Abstentions: 0 / 0 / 0.

### Attribution

- **Improved by table retrieval:** none. For F01, F02 and F05, the tables variant returned exactly the same evidence IDs as deployed. The facet "table comparison" path did not fetch the missing rows for these questions.
- **Needs multiple searches (decomposition):** F01.2, F02.2 and F05.2. Multi-Agent's planner split each question into parts (for example, a separate Solar search) and each part's evidence reached synthesis.
- **Needs better synthesis:** F04.2, the captions Multi-Agent omitted, and F01, where the answer under-claimed the derivable count (Baseline + tables).
- **Unresolved by any configuration:** F08.1. Passage c0054 is never retrieved.

### Smallest practical improvement to Baseline/B2

Add **question decomposition to Baseline retrieval only**:

- search the original question plus one search per named part or entity (for example "FundAR … / Solar …");
- merge the results round-robin into at most 14 passages;
- keep Baseline's single synthesis and its answer-quality review.

This reproduces the only mechanism behind Multi-Agent's +1 point, without the orchestrator, the verifier stage or the extra latency tail.

Prefer a deterministic splitter, such as the existing V2/V3 question-part splitter on `khoi/research-retrieval-v3`, at zero extra model calls. The fallback is Multi-Agent's one-call planner (+1 call per question).

Table comparisons can stay off; on this set they changed nothing. Validate the change offline on F01–F10 packets (evidence coverage only, no generation), then on the held-out set.
