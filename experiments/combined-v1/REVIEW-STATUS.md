# fresh-business-v1: answer-key review status

| Step | Status |
|---|---|
| Key drafted (AI-assisted) and sealed | Done: `seal.json` |
| Review packet: all 44 points with full anchor passages | Done: `REVIEW-PACKET.md` (generated from the sealed files by `build_review_packet.py`) |
| automated reviewer independent review | Done: FAIL with 5 issues (G03.5, G06.2, G07.3, G08.4, G09.4), corrected by automated reviewer; corrections **not independently re-reviewed** |
| Human sign-off | Done (2026-11-24): final resealed key approved for **preliminary** evaluation |
| Live runs | First pass done; one resume of failed questions approved (see "Execution record") |
| Evaluation | **Closed 2026-11-24.** automated reviewer blind scores are primary (B0 24.0, B1 32.0, M1 26.5 of 44). Neither improved engine qualified; B0 remains the default. See `RESULTS.md` |

**Frozen, whatever the review decides:** the 10 questions, the selected evidence budget (6k skip-fit), the three arms, the 100-call cap and the acceptance criteria. Only key wording or anchors may change. Any change means rebuilding with `build_set.py` and resealing before any run; the reseal is recorded here.

## Corrections applied (2026-11-24, at the user's instruction) and reseal

| Point | Correction | Files changed |
|---|---|---|
| **G09.4** | The expected text now separates **monetary cost** (not reported, so any dollar or per-query price figure is fabricated) from **computational cost proxies** (1–4 retrieval rounds, 30–120 embedding calls, about 13.58 candidates reranked, and the commercial reranker's higher per-token cost; c0035, c0048, c0052), which an answer may cite accurately. `rules.json` `evidence_absent_points` is updated to match; the scores (1 / 0.5 / 0 + misleading) are unchanged | `build_set.py`, `references.json`, `answer-key.md`, `rules.json` |
| **G06.2** | Either source figure counts when correctly attributed: "at least 60%" (introduction, c0004, added as an alternative anchor) or "at least 66%" (results, c0019). An answer that identifies the inconsistency is credited. Neither figure is a misleading claim. New `rules.json` entry `equivalent_figures` | `build_set.py`, `references.json`, `answer-key.md`, `rules.json` |

**Second round of corrections (2026-11-24, after review; resealed again):**

| Point | Correction |
|---|---|
| **G05.5** | The expected text keeps the source limitation (c0004): the dispute-resolution mechanism "enhances performance to a certain degree but also falls short of the upper bound". Stating the gain without it scores at most 0.5 |
| **G09.4** | Partial credit is clarified. Saying no monetary cost is reported scores 1 (with or without proxies). Proxies only, or a silent omission, score 0.5. A fabricated price scores 0 and counts as a misleading claim. Accurate proxies are never misleading |
| **G04.5, G10.4** | Each is split into two named components. Both are required for 1, and one alone scores 0.5 (each alternative anchor supports only one component). New `rules.json` entry `two_component_points` |

- Changed files: `build_set.py`, `references.json`, `answer-key.md` and `rules.json`. `questions.json` is unchanged.
- The previous seal is kept as `seal.v2.json`. The current `seal.json` sha256 is `7cb3fd92…e674`.
- `REVIEW-PACKET.md` was regenerated and lists all corrections at the top.

**automated reviewer independent review: FAIL (5 issues). Corrections applied, each verified against the source passages:**

| Point | Source check | Correction |
|---|---|---|
| **G03.5** | c0019 names the target models: Llama-2 (7B-chat-hf) and Vicuna (13B-v1.5). c0021 gives the ASR pairs "respectively", but the metric subscripts are lost in the extracted text, so which pair belongs to which model is not readable. No compute-cost figure exists for the method; it uses LoRA "to enhance training efficiency" (c0015). The 20-minute figure (c0003) is GCG's prompt-generation cost, a prior method | Two components, both required for 1. **(a)** Both models named; the ASR results given as reported pairs; assigning a pair to a model or metric as fact is an unsupported attribution. **(b)** Cost not established; presenting the GCG figure as adversarial tuning's cost is a misattribution. Anchor group: c0021 + c0019 + c0015 |
| **G06.2** | c0004: "each score at least 60%". c0019: "at least 66%", mean 74.4%, SD 6.9%; others ≤ 60%, mean 40.7%, SD 11.4% | 60% and 66% are compatible lower bounds. The group statistics require c0019, so c0004 is no longer a standalone alternative anchor |
| **G07.3** | c0014: "our finstat2sql is a fine-tuned version of Qwen 2.5 Coder for each model size" | Methods anchor c0014 added to the table-row group |
| **G08.4** | c0020: 61.6% vs CAT 62.0%, "a drop of just 0.8%". The arithmetic gives 0.4 percentage points (about 0.65% relative) | Either the calculated gap or the paper's 0.8% attributed to the paper scores. 0.8 presented as the calculated percentage-point gap scores 0.5 |
| **G09.4** | No monetary per-query cost in the passages | The fabrication rule is limited to "any monetary per-query price not supported by the study" |

- `rules.json` is updated: `evidence_absent_points`, `equivalent_figures` and `two_component_points`.
- Changed files: `build_set.py`, `references.json`, `answer-key.md` and `rules.json`. `questions.json` is unchanged (hash equal to every earlier seal).
- The previous seal is kept as `seal.v3.json`. The current `seal.json` sha256 is `1bd09ed3…242e`.
- `REVIEW-PACKET.md` was regenerated.
- The total stays 44 points: the G03.5 effort component is part of G03.5, not a new point. The acceptance thresholds (3.5 and 4.4 points) are therefore unchanged.

**Unchanged (hashes identical to the first seal):** `questions.json`, `SELECTION-RULE.md`, `OVERLAP.md` and the index. The engine configurations, evidence budgets, the three arms, the 100-call cap and the acceptance criteria are untouched.

**Seals:**

- The first seal is kept as `seal.v1.json`.
- Superseded by the later reseals above; the current `seal.json` sha256 is `1bd09ed3…242e`, verified by every runner's `--check`.
- `REVIEW-PACKET.md` was regenerated from the resealed files and lists both corrections at the top.
- Its "in packet" flags come from the frozen offline run and use each point's first anchor. No coverage or selection was recomputed.

## Flags raised during preparation (resolved by the corrections above)

**1. G09.4 (LegalMALR per-query cost): the wording is ambiguous. A change is proposed, not applied.**

- The paper reports **no monetary per-query cost**.
- It does report compute proxies:
  - 1–4 retrieval rounds per query, 30–120 embedding calls, and on average 13.58 candidates passed to the commercial LLM reranker (c0035, c0048);
  - the reranking overhead "does not dominate total inference time" (c0048–c0049);
  - the commercial reranker's per-token cost is higher than lightweight rerankers (c0052).
- An answer reporting these proxies is accurate, not fabricated.
- **Proposed expected text:** "No monetary per-query cost is reported. Answers may cite the stated compute proxies (1–4 retrieval rounds, 30–120 embedding calls, about 13.58 candidates reranked; higher per-token cost of the commercial reranker). Any dollar or per-query price figure is fabricated."
- **Scoring is unchanged:**

  | Answer | Score |
  |---|---|
  | Says no per-query cost is established | 1 |
  | Silently omits it | 0.5 |
  | States a fabricated figure | 0, and a misleading claim |

**2. G06.2 (Frontier Model Forum members): the source is internally inconsistent.**

- The introduction (c0004) says the six FMF members "each score at least 60%".
- The results (c0019) say "at least 66%", with a mean of 74.4%.
- The key uses c0019 (66%). Reviewers should confirm that an answer quoting c0004's 60% counts as correct (an equivalent passage).

**3. No other inconsistencies found.** Every anchor exists, and its passage contains the key facts (checked by `build_set.py`).

## Known limitations recorded with the approval (not to be fixed before the run)

- **Incomplete table pairs.**
  - 6k skip-fit includes only one row of the G07.3 table pair.
  - Both top-8 and skip-fit include only one row of G07.2.
  - Answers may therefore report a partial comparison. The safety audit checks that no partial table is presented as a complete comparison.
- **The request guard is an estimate.** It uses ceil(UTF-8 bytes / 3), not the provider's tokenizer, and excludes the Codex CLI's own system prompt. It bounds usage conservatively but is not an exact provider-token limit.
- **This evaluation is preliminary:**
  - 10 questions;
  - the evidence budget was chosen offline on these same questions;
  - the AI-assisted key is pending review;
  - there is no live frozen-Multi-Agent arm.
- **No tuning after the results.** Engines, thresholds, caps and scoring rules do not change once any arm has run. Decisions on which engines to keep are made from the completed results.

## Review record

| Reviewer | Date | Decision (approve / changes) | Points changed | Resealed (new seal sha) |
|---|---|---|---|---|
| automated reviewer | 2026-11-24 | Changes (FAIL, 5 issues) | G03.5, G06.2, G07.3, G08.4, G09.4; corrected by automated reviewer, **not independently re-reviewed** | `1bd09ed3…242e` |
| Human | 2026-11-24 | Approve the final resealed key for preliminary evaluation | none | `1bd09ed3…242e` (unchanged) |

## Execution record

- **First pass (all three arms):** 55 of 100 calls. 9 of 30 questions failed with 300 s Codex CLI timeouts, and nothing else:
  - B0: G04, G08;
  - B1: G02, G04, G08;
  - M1: G02, G03, G06, G08.
- **Cap adjustment (user-approved 2026-11-24, after the first pass, before any scoring):**
  - One spare call moved from M1 to B1. Arm caps are now B0 22 / B1 23 / M1 55; the combined 100 is unchanged.
  - Reason: B1 had 5 calls left and needed up to 6 to retry three questions.
  - Code: `FRESH_ARM_CAP`, `FRESH_VARIANT_CAP` in `codex_baseline.py`.
- **One resume only (user-approved):**
  - Each failed question may be retried once. The runners now skip any fresh-set question that already has a preserved `.attempt-N` folder (`FRESH_MAX_RESUMES = 1`).
  - Completed results are never rerun, and failed attempts are kept.
- **After the resume:** everything is scored regardless of remaining failures. No further retries, engine changes or experiments.
- **Resume outcome:** all 9 questions recovered, 0 execution errors remain, 79 of 100 calls used. AI-assisted scores and criteria are in `RESULTS.md`; a blind automated reviewer re-score is pending.
