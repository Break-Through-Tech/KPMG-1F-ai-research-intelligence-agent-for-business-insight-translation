# Consolidated research: final improvement plan (proposal, not implemented)

**Basis:** saved traces from the live validation (`data/processed/consolidated-v1-{standard,deep}`: stage checkpoints, attempt logs, call ledgers, provider receipts), the existing code, and offline B2 ranking (0 model calls). automated reviewer’s blind scoring was not inspected. No engine code was changed.

- **Point causes** come from the AI-assisted, non-blind scores in `scoring/scores.json`. If the blind re-score changes a point, its cause may change.
- **Constraints kept:** both modes stay, and the production default is unchanged.
- **Validation caveat:** every completeness fix below was found on the fresh-v2 questions. Re-measuring on fresh-v2 would be tuning on the test set, so any re-validation needs new fresh questions.

## 1. Latency: where Standard's 119 s goes

| Stage (Standard, 8 questions) | Median | Share | Evidence |
|---|---|---|---|
| Retrieval and evidence management | 6.7 s | 6% | `attempts.json` timings |
| Synthesis call | 73.5 s | 62% | about 37k input / 3.0k output tokens |
| Review call | 42.0 s | 35% | about 41k input / 1.8k output tokens |
| Publication gates | < 0.1 s | 0% | |

**Deep** adds the planner call (6.6 s, of which 168 output tokens) and three extra B2 searches, run one after another (evidence stage 16.8 s instead of 6.7 s).

**Root cause:** latency is dominated by generated output, at roughly 45–50 output tokens per second.

- **Quotes:** 4–5k characters per answer, about 40% of synthesis output. Atomic findings repeat long table-row quotes. For example, H01's six Table 2 findings each re-quote the caption.
- **Review reasons:** the review writes a reason of up to 600 characters for each of about 14 claims.
- **Outlier:** H05 synthesis took 190.7 s for only 1,595 output tokens. That is a provider stall, not prompt size.

**Proposals:**

| | Change | Expected benefit | Regression risk | Priority |
|---|---|---|---|---|
| L1 | Quote the shortest exact span that states every fact of the claim (number, subject, condition), at most about 300 characters | Synthesis output down about 20–30%, roughly 15–20 s | Low–medium: a span that is too short can trip the P4/P5 gates and withhold the claim. Covered by the existing gate tests plus new tests | P1 |
| L2 | Review reasons at most about 160 characters; `supported_text` empty unless reducing | Review output down about 35%, roughly 8–12 s | Low | P1 |
| L3 | Deep: run the up-to-3 supplementary B2 searches in parallel | Evidence stage down about 8 s | Low (the order is merged deterministically afterwards) | P2 |
| L4 | Slimmer prompts (see section 4) | Fewer input tokens; small latency gain | Low | P1 |

**Expected result:** Standard median about 90–100 s, Deep about 110–120 s. These are estimates, not measured. Provider stalls like H05 are not addressed: there is still no retry within the 300 s timeout.

## 2. Completeness: every Standard point lost (26.5 / 36, 9.5 points lost)

Where an anchor is missing, its B2 rank is shown with the cumulative MiniLM tokens up to that point. The Standard packet is ranks 1–30 within 6k tokens.

| Point | Lost | Cause | Evidence |
|---|---|---|---|
| H03.2 | 0.5 | Retrieval | HarmNet results paragraph c0008 is not in B2's top 200 for the combined two-paper question; Deep's planned "how successful" search found it |
| H03.3 | 1 | Retrieval | c0022 is at rank 51 (11.9k tokens) |
| H04.2 | 0.5 | Retrieval | c0004 is at rank 20 but reaches 6,061 tokens, 61 tokens over budget |
| H04.5 | 0.5 | Retrieval | c0029 not in the top 200; conclusion c0030 at rank 63 |
| H06.2 | 0.5 | Retrieval | Table 1 rows at ranks 46–64 |
| H07.1 | 1 | Retrieval | CLINIC **conclusion** c0024 at rank 64 |
| H08.2 | 0.5 | Retrieval | c0022 at rank 42 |
| H08.3 | 1 | Retrieval | CLINIC **conclusion** c0024 at rank 61 |
| H02.5 | 0.5 | Retrieval | Intended-use statement c0020 at rank 46 (7.6k tokens) |
| H02.2 | 0.5 | Synthesis | The authors' "over 10%" summary (c0019, rank 8) was in the packet but not stated |
| H05.4 | 0.5 | Synthesis | The ASR benefit in c0028 (rank 1) was omitted |
| H03.5 | 1 | Synthesis | AutoEvaluation's purpose is stated in c0000, which was in the packet, but appears only inside an interpretation |
| H01.1 | 0.5 | Verification | The reviewer rejected a conflating claim **and supplied a correct reduced version**, which the gate discarded (section 3, V1) |
| H02.4 | 1 | Review relevance | Three correct figures for MedES's RAG variant were rejected as "not relevant" (section 3, V3) |

**Totals:** retrieval 6.0, synthesis 2.0, verification and review 1.5. No point was lost to execution.

**Why no question was fully answered:** every question lost at least one point to a cause above. Two systematic patterns stand out:

- **Conclusion passages rank low.** CLINIC c0024 and CAT c0030 sit at ranks 61–64, yet they carry the headline scope figures and conclusions.
- **The finding cap binds.** 15 of 16 answers used 13–14 of the 14 findings. Up to 13 findings per answer went to separate rows or cells from one passage, for example H08's nine per-model leak rates and H03's six automated reviewer table cells. That crowded out requested points (H02.2, H05.4, H03.5).

**Proposals:**

| | Change | Expected benefit | Regression risk | Priority |
|---|---|---|---|---|
| C1 | **Coverage-first synthesis:** state one finding for each requested part before any row-level detail; one finding may give one subject's values across a table's columns; raise the cap to 18 | Addresses the 2.0 synthesis points | Medium: longer output, offset by L1/L2; atomicity weakens slightly, but the number gates (P4/P5) are unchanged | P1 |
| C2 | **Conclusion completion:** for the two papers contributing most passages to the protected packet, add each one's conclusion passage within a reserved allowance of about 800 tokens; nothing protected is displaced | Addresses H07.1, H08.3 and part of H04.5 (up to about 2 points) | Low–medium: about 13% more evidence tokens; a targeted completion rule, not a new ranker | P2 |
| C3 | Keep the 6k budget. Raising it to 8k would recover only H02.5 and H04.2 (about 1 point) for about 33% more tokens | — | — | not recommended |

## 3. Verification: why correct claims are still lost

| | Root cause (evidence) | Fix that keeps safety | Benefit | Risk | Priority |
|---|---|---|---|---|---|
| V1 | **Gate ordering.** S H01 claim 0: the reviewer set `supported=false` and gave a correct `supported_text` (the 50,000+ conversations, 67 guidelines, seven strategies, 22 models). `publication.publish` checks P1 "supported and relevant" *before* considering `supported_text`, so the correct part was dropped | If `supported_text` is non-empty and the claim is relevant, evaluate the reduced text through P2–P5, as already done when `quotes_entail` is false | +0.5 (H01.1); generally preserves the correct part of a rejected claim | Low: the reduced text still passes the number-subset (P3), number-recall (P4) and attribution (P5) gates | P1 |
| V2 | **Entity rule too broad.** "GPT-5 sustained 8.0–9.0" was withheld in both arms although the reviewer gave the right span ("GPT-5 and GPT-5-mini sustain scores between 8.0 and 9.0."). P5 requires *every* capitalised name in the claim clause to appear in the attached quotes, and the context name "JMedEthicBench" was only in the cited passage. The GPT-5-mini twin published because v2 raised no flag on it | Require the subject named nearest the number (GPT-5) to appear **in the resolution span**; context names (paper or benchmark) only need to appear in a cited passage (the v2 R4 principle). Keep the respectively-mapping check | Stops these false rejections; table-heavy answers keep more facts | Low–medium: the existing wrong-subject and swapped-mapping tests still apply (the subject is checked in the span); add the GPT-5 replay as a test | P1 |
| V3 | **Relevance judgment.** S H02: three correct, quote-entailed RAG-variant figures were rejected as "a separately reported RAG variant rather than the requested aligned SFT model", although the question asked how the aligned 7B model compares and where the evidence applies | (a) Review extension: results for variants, ablations or comparators reported by the same study for the requested comparison are relevant when labelled as such. (b) A supported, entailed claim judged not relevant is published in a separate labelled "related results" list instead of being discarded | +1 (H02.4); fewer silent losses | Low for safety (still fully verified); some risk of scope drift, contained by the separate label | P2 |
| V4 | **Remaining v2 false alarms** on serialized table rows (the "No defense" header read as negation, the "(s)" unit). No live loss was observed this time, because atomic claims and the reviewer's resolutions worked | No change: keep monitoring | — | — | — |

## 4. Token efficiency and accounting

**Root causes:**

- **T1, duplicated evidence.** Each passage is sent with both `text` and `text_with_context`. On S H03 these are 40.8% and 40.9% of the serialized evidence; in 20 of 22 passages `text` is contained verbatim in `text_with_context`. Quote membership is checked against `text` only, so the extra copy adds no grounding.
- **T2, metadata the model never needs.** `source_sha256`, `source_url`, `html_url`, `pdf_url`, `page_number`, `high_value`, extractor, version and header provenance fields: about 12% of evidence bytes.
- **T3, evidence sent twice per question.** Synthesis and review each carry the full packet. The provider receipts show **0 cached input tokens** in Standard, because the two prompts share no prefix.
- **T4, accounting.** Actual minus estimated input is +6.3k tokens per call (median; Standard) and +9.2k (Deep). The planner call shows it most clearly: an estimated prompt of about 1k became 11k actual input. This is the Codex CLI's own system and tooling prompt, which the guard excludes; the bytes/3 estimate otherwise over-states our own content.

**Proposals:**

| | Change | Expected benefit | Regression risk | Priority |
|---|---|---|---|---|
| T1/T2 | Send the model `chunk_id`, `arxiv_id`, `title`, `section`, `subsection`, `text` (plus the table caption/header for table rows). Keep all metadata in the result evidence for the UI and citations | About 50% fewer evidence tokens; about 30–35% fewer input tokens per call | Low: section headings and titles are kept; quotes were always checked against `text` | P1 |
| T3 | Shared prompt prefix: evidence first, stage instructions after, so a caching provider can reuse it in the review | Possible review input-cost cut (provider-dependent) | Low | P3 |
| T4 | Guard: add a per-provider measured call overhead (Codex CLI about 10.5k tokens; 0 for direct APIs) to the request check, and log estimate vs actual per call | An accurate cap and usage reports | Low | P1 |

## 5. Production readiness

**What fits today:**

- **Backend seam.** `IndexedResearch.execute` calls `run_research(..., summarize_fn=self.summary)`. The consolidated synthesis, review and publication can be one `summary` implementation. Retrieval already accepts a budgeted `retrieve`: the Improved Baseline was run exactly this way via `create_research` with the skip-fit retriever.
- **Contract compatibility.** The published summary keeps Baseline's shape: `status`, `claims[{text, kind, support, chunk_ids}]`, `limitations`, `limitation_support`, `answer_lead`, `answer_scope`. This is the shape `validate_output`, the business translation, the regulatory stages and `ui/app.js` read (`summary.claims`, `limitations`, `limitation_support`, `answer_lead`, `quality_review`).
- **Provider compatibility.** The engine only needs `generate(prompt, response_schema=...)`. `src/generation.py` supports Gemini, OpenAI, OpenAI-compatible and Bedrock with JSON-schema output, and the Codex adapter. Every reply is re-validated by the engine itself, so provider-side schema differences (for example, Gemini's partial support for `minLength`/`maxItems`) fail safe.

**Gaps:**

| Gap | Detail | What closes it |
|---|---|---|
| G1 Production model untested | Prompts were exercised only on gpt-6.1-sol (automated reviewer, low effort). The atomic decomposition, quote-entailment judgment and flag resolutions may behave differently on the production provider | A small paired smoke run on the production provider (live calls; needs approval) |
| G2 Output limits | Synthesis returns 3–4k output tokens | Provider configs need max output ≥ 8k |
| G3 Additive fields | `held_claims`, `evidence_notes`, `label`, `reduced_from` are extra fields. The UI ignores them; interpretations already carry `kind`. Showing labels, evidence notes and a Standard/Deep toggle is a frontend contract change owned by the UI session | Approval and coordination with the UI owner |
| G4 Checkpoints | Currently local folders. In the app they would key on the request fingerprint so that "retry" resumes only the failed stage | Small adapter; P2 |
| G5 Latency | The Codex CLI per-call overhead (about 10k tokens plus process start) disappears with direct APIs, so production latency should be lower | To be measured, not assumed |

**Integration path (P2, after the fixes, each step needing approval):**

1. Add `create_consolidated_research(mode)` in `src/experimental` behind an opt-in flag, as B2 was introduced. This is a shared-app change and needs approval.
2. Run the existing app contract tests plus the consolidated suites.
3. Run the provider smoke test.
4. Make the UI change, coordinated with the frontend owner.

## Recommended order (one implementation round, offline-tested, then one fresh validation)

1. **P1: V1, V2, T1/T2, T4, L1, L2, C1.** Each gets a replay test from the saved consolidated traces: the H01 reduction, the GPT-5 resolution, and the prompt-size drop measured on the saved packets.
2. **P2: V3, C2, L3**, then the production adapter (G4, step 1 of the integration path).
3. **P3: T3 caching.**

**Validation:** one new fresh question set (not fresh-v2) for Standard vs Deep, within a call cap you set, plus the provider smoke test (G1). The production default stays unchanged until separate promotion criteria are met.
