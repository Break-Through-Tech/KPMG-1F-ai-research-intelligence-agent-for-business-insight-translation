# Unseen S2 vs S2-R2 evaluation protocol

**Status:** awaiting the Codex key review and the project lead's final approval. No live calls have been made.

## Questions and maximum score

| Type | Questions | Points each | Subtotal |
|---|---|---|---|
| Named two-paper | U1 (HaloGuard and PGuard, multilingual), U2 (MedPsy and MatMoE, edge), U3 (RAG-TRACE and ECGJev) | 5 | 15 |
| Unnamed multi-part, single paper | U4 (social-media translation benchmark), U5 (compiled agent harness), U6 (DP fine-tuning audit) | 5 | 15 |
| Simple control | U7 (ERIA internal dataset) | 3 | 3 |
| Evidence-limit control | U8 (HaloGuard reasoning traces, refusals, insurer miss rate) | 3 | 3 |
| **Maximum score** | | | **36** |

**How the questions were written:**

- **Source material:** the passages of the 10 validation-index papers. No engine, retriever or model has seen the questions.
- **New facts:** every point uses facts that no existing key point uses.
- **Shared passages:** two anchor passages (ECGJev c0008 and Latent Harness c0003) are also cited by fresh-v4 points, but for different facts.
- **Disclosure: the questions are new, but the papers are not.** The corpus cannot be expanded this round, so this is evidence on unseen questions, not unseen papers.
- **Files:**
  - `answer-key.md`, `references.json` and `rules.json` hold the key, the anchors and the scoring rules.
  - `build_unseen.py` checks that every anchor exists and contains every required fact.
- **The engines never receive the key.** The runner reads only `questions.json`.

## Provider, model and configuration (identical for both arms)

**Configuration:**

| Setting | Value |
|---|---|
| Provider | Codex CLI with the ChatGPT subscription login |
| Model | `gpt-6.1-sol` |
| Reasoning effort | low |
| Call timeout | 300 s |
| Calls per question | 2 (synthesis, then review) |
| Corpus and index | the fresh-v4 validation bundle (parents sha256 `0039ce20…`) |
| Evidence budget | 6,000 passage tokens plus 800 C2 |
| Generation settings and prompts | identical frozen V2 code |

**Limitation: this is not the Azure application's Gemini configuration.**

- No authorised, isolated Gemini evaluation environment is available here.
- This research environment is restricted to the Codex subscription login, and API keys may not be used.
- Absolute latency and answer style may differ on Gemini.
- The relative S2 vs R2 comparison is valid within this provider. Transfer to Gemini needs the separate provider smoke test before integration.

## Arms and execution

- **S2:** frozen `ConsolidatedResearch('standard')`, unchanged.
- **R2:** `S2R2Research(retrieval_strategy='r2')`. It uses B1 for named two-paper questions and component-rank fusion otherwise. The code is frozen in `code-freeze.json` (14 files).
- **Counterbalanced order:** odd questions run S2 then R2; even questions run R2 then S2. Both run in one process, back to back per question.
- **Budget:** 32 calls expected. Each arm has a persistent cap of 20 calls, so the **hard cap is 40, including failures and retries**.
- **Retries:** at most one resume per question per arm.
- **Logging:** every attempt is logged in `attempts.json`, `calls.json`, `status.json` and `unseen-r2-order.json`. **No question may be excluded.** A failed question scores 0 and is reported.

## Scoring

1. **Blind A/B packet:** labels randomised per question; the key stays with Claude. A fresh Codex session scores it from the packet only.
2. **Programmatic audit:** exact quotes, number recall and uncited absence claims, for both arms.
3. **Claude check:** every flag is checked against the passages.
4. **Adjudication:** the project lead's ruling is final.

## Frozen acceptance criteria

R2 passes only if **all** of these hold:

| # | Criterion |
|---|---|
| 1 | R2 completeness ≥ S2 + **2 points** (of 36) |
| 2 | **Zero new** safety flags (citation-grounding, numerical, misleading or unsupported) and no critical unsupported claim |
| 3 | R2 median total latency ≤ **1.25×** S2 **and** ≤ **120 s** absolute |
| 4 | R2 p90 total latency ≤ **180 s** |
| 5 | R2 input tokens ≤ **1.10×** S2 |
| 6 | No silent failures, excluded questions or unreported retries |

**For comparison only, not a gate:** the earlier **1.10× latency** threshold. The report states whether R2 also passes it.

## Reporting

**Results:**

- aggregate and per-question points, including every regression;
- fully answered questions;
- evidence coverage (anchored points in the live packets);
- citation correctness and unsupported claims.

**Cost:**

- input and output tokens;
- retrieval, generation (synthesis plus review) and total latency, relative and absolute.

## Rules during the evaluation

- No prompt or answer-length changes.
- No Deep Research changes.
- No corpus expansion.
- No tuning of R2 on these questions.

**If R2 passes:** it stays a candidate for further validation and eventual Azure integration. It is **not** deployed automatically.

---

## Codex key-review prompt (paste into a fresh Codex session)

```
You are an independent reviewer of an evaluation answer key. Work ONLY inside D:\KPMG-unseen-review. Do not open any other folder (no engine code, no results). Do not edit any file except the report you write.

Files: answer-key.md (8 questions U1–U8, 36 points, expected answers and anchor passage IDs; alternatives separated by "|"), rules.json, questions.json, and one <arxiv_id>.md per paper containing every extracted passage with its chunk ID. Use only these passages as evidence.

For EVERY point check: (1) the expected answer is factually exact per the passages (numbers, units, conditions, attribution to the right model/dataset/setting); (2) the anchor passages state every required fact; list any other passage that is an equally valid anchor; (3) the point is fair for the question as worded; (4) U8.3 is genuinely not established anywhere in the HaloGuard 2.0 passages; (5) the misleading probes in rules.json are correct; (6) the question text does not leak the answer, and U4–U6 do not name the paper's title.

Write your findings to D:\KPMG-unseen-review\KEY-REVIEW.md: per finding give point ID, severity (ERROR / MISSING-ANCHOR / UNFAIR / AMBIGUITY / OK-NOTE), passage ID with a short quote (under 25 words), and the recommended correction. End with APPROVE or CHANGES and counts by severity. Then reply with the same summary.
```

## Key review record (completed 2026-11-26)

The review was run automatically in a fresh, non-interactive Codex CLI session, confined to `D:\KPMG-unseen-review` (key, rules and paper passages only). The full report is in `KEY-REVIEW-CODEX.md`.

**Verdict:** CHANGES. ERROR 1, MISSING-ANCHOR 2, UNFAIR 2, AMBIGUITY 4, OK-NOTE 29. No numerical transcription errors were found.

**All findings were applied before sealing.** No engine had seen the questions.

| Point | Correction |
|---|---|
| U1.5 | Rewritten: both papers report PolyGuardPrompts results, but a matched protocol is not demonstrated, so a comparison must be qualified. Only an unqualified ranking counts as misleading. Adds PGuard c0026 |
| U3.1 | Now requires both models' counts. A qualitative contrast scores 0.5 |
| U4.2 | Reworded as a "200K-pair collection", with development sets held out |
| U5 wording | Now asks about prompt-phase injection (the U5.4 fairness issue) and about instructions that reduce task performance |
| U5.5 | Now uses the paired -10.7 / -6.7 values, with c0016 as the only anchor |
| U6.4 | Conditional wording: a grouped kernel would skip 1.5–7.5% of correction work; the kernel is not implemented |
| U7 wording | Now asks who authored the reports and under which guidelines (the U7.3 fairness issue) |
| U8.3 | Adds the c0038 anchor; narrows the misleading-claim rule to presenting an invented rate as a study result |
| Probes | U1.5 and U8.3 rules revised as above; U2.4 notes that 1.2–1.3x GPU speedups do exist |

**Overlap with existing keys:** after the corrections, only U3.5 shares an anchor chunk (ECGJev c0008) with a fresh-v4 point, and for a different fact.

**Sealing:** the set was sealed with `run_unseen.py --seal-set` after the corrections. Human sign-off is pending: the project lead's approval of this protocol.
