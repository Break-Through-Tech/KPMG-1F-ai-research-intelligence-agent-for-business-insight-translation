# Multi-Agent verification failures: investigation and proposed repair (offline, development data)

**Status:** offline investigation only. No model calls. `src`, `agents.py`, `numeric_checks.py`, `interpretation_policy.py` and the app are unchanged. The business evaluation (business-multiagent-v1, C01–C15) was used as **development data**, so its numbers below are not validation evidence. Adjudication and score estimates are **AI-assisted, not independently verified by a human**.

## 1. Bottom line

- Of the 21 held claims:
  - **11 were wrong rejections**: the claim is correct as written.
  - **6 were defensible holds** of claims whose substance is supported and could be repaired with a small edit.
  - **4 were well-grounded business recommendations** withheld by design.
- **No held claim was a material misstatement.** The genuine catches were minor: a dropped "loss-framed" qualifier, a trailing causal caveat the sources do not state, and two edition years not in the quotes.
- **The LLM verifier was right where the code was wrong.** It judged 11 of the 13 false number-check rejections fully supported. The losses come from the deterministic number check (a veto), not from the model verifier.
- **Causes:** ten specific parsing defects in `numeric_checks.py`, all in how a number is tied to its subject, metric, condition, unit or denominator. None involves the value itself.
- **Recommendation:** keep the Multi-Agent verifier and its veto, and repair the parser (`numeric_checks_v2.py`, eight rules). Replace the blanket interpretation hold with a labelled-interpretation gate built from Baseline's rule and the existing business screen. Do **not** swap in Baseline's review wholesale.
- **Expected effect (development estimate, optimistic):** about **+4.5 points** (20.5 → about 25 / 41), all 4 recommendations restored, 0 new unsupported claims. That is about Baseline's level (27.0), **not** the +5 over Baseline required. Repairing verification removes Multi-Agent's handicap. Whether it then beats Baseline depends on combining it with the retrieval findings, and must be shown on fresh questions.

## 2. Adjudication of all 21 held claims (against full passages and surrounding context)

| # | Q | Held by | Verdict | Why |
|---|---|---|---|---|
| H01 | C01 | policy | **Grounded recommendation** | A bounded rollout-testing recommendation built on cited findings. The verifier said supported |
| H02 | C03 | number check: subject_mismatch | **Wrong rejection** | All 4 residual ASRs match Table 3 row by row. Parser gave "43.3% for Llama-2-7B" the subject Llama-3-8B |
| H03 | C04 | verifier: missing_support | **Grounded recommendation** | "Test as an aid with independent checks". The verifier demanded the passages state the advice itself |
| H04 | C05 | number check: numbers_absent | **Wrong rejection** | "3.5" is the model name "Claude 3.5 Sonnet" (source: `claude-3-5-sonnet`) |
| H05 | C05 | number check: subject_mismatch | **Wrong rejection** | $0.00066 Llama, $0.07 Claude, 7–10 calls and $4–$12 humans are all exact. "Figure 5/6" were parsed as subjects. The closing caveat (trajectory price ≠ voted-answer or training cost) is a fair inference from c0020/c0030 |
| H06 | C05 | number check: subject_mismatch | **Wrong rejection** | 0.89 vs 0.67, about 20 pp, and the sample-count conditions are all stated. "Claude" vs "Claude 3.5 Sonnet", plus dataset/system in one subject slot |
| H07 | C06 | number check: missing_condition; verifier: missing_condition | **Defensible, repairable** | Numbers exact. The check misread emphatic "only dropped". The verifier's point is real but minor: masking kept answers retrievable. "Decline not smaller" is correct arithmetic (6.8 vs 6.1, 7.6 vs 6.0) against the authors' framing |
| H08 | C06 | number check: metric/subject_mismatch | **Wrong rejection** | Movies values exact. "F1" vs "F1 score"; "Movies" (dataset) vs "MultiRAG" (system) |
| H09 | C06 | number check: metric_mismatch | **Wrong rejection** | Flights values exact. "F1" vs "F1 score" |
| H10 | C07 | number check: metric/subject_mismatch | **Wrong rejection** | ≥ 8%, 2.5%, 6.4%, 7.9% and 6.9% all exact. "KG²RAG" vs "KG 2 RAG"; "recall" taken from the next clause; the "respectively" list was not mapped |
| H11 | C07 | number check: missing_condition; verifier: missing_condition | **Defensible, repairable** | As H07. The check also read "**not only** demonstrates" as a restriction |
| H12 | C08 | verifier: missing_support | **Justified as written, repairable** | Supported finding plus an unsupported analyst sentence ("do not isolate a causal effect") |
| H13 | C08 | verifier: missing_condition | **Justified, repairable** | Drops "in loss-framed queries" from the GPT-4 loss-aversion statement |
| H14 | C09 | number check: subject_mismatch | **Wrong rejection** | "32"/"70" are model sizes in "Qwen Pro Finance 32B" / "Llama Pro Finance 70B" |
| H15 | C11 | number check: denominator_error | **Wrong rejection** | "37/100" is correct (100 indicators, mean 37). The check wanted the literal pair |
| H16 | C11 | number check: numbers_absent | **Justified, repairable** | "2024 results": the year is not in the quotes or the cited passage (the edition is inferable only from section structure) |
| H17 | C11 | number check: numbers_absent | **Justified, repairable** | "2023 comparison": the year is in the cited passage c0262 but not in any quote. Repair: quote it or drop it |
| H18 | C11 | verifier: missing_support | **Grounded recommendation** | The vendor-diligence list mirrors c0299 almost word for word |
| H19 | C14 | number check: 5 issues | **Wrong rejection** | Every value matches the two Table 1 rows. "Table 1" counted as a number; "(s)" header unit; "F1-score"; "precision/recall of 43.0/70.3" read as a ratio |
| H20 | C14 | number check: subject_mismatch | **Wrong rejection** | 44.4 vs 43.2 exact. The source names the config "Architecture 4" (which uses Cohere); the claim says "with Cohere" |
| H21 | C15 | verifier: missing_support | **Grounded recommendation** | "Evaluate task skill and financial rationality separately" rests on the cited c0025 pair |

## 3. Exact functions and rules responsible (all in `experiments/agentic/numeric_checks.py`)

| Defect | Function / rule | Held claims |
|---|---|---|
| D1 Post-number subject ignored: an elliptical clause inherits the previous subject before "… for X" is considered | `_clause_subject` (elliptical branch runs before the "first entity after" branch) | H02, H05, H20 |
| D2 Non-systems counted as subjects ("Figure 5", "F1-score", "F1 44.1", "Architecture 4", "Cohere-powered") | `_counts_as_subject` via `MODEL_NAME` (any digit or hyphen) | H05, H19, H20 |
| D3 One subject slot compared by exact string. Dataset vs system, "Claude" vs "Claude 3.5 Sonnet", "KG²RAG" vs "KG 2 RAG" | `_judge` subject block (`c['subject'] == mention['subject']`, else contradicted) | H06, H08, H10, H14 |
| D4 "F1 score" parsed as the generic metric "score" | `METRICS` (no "f1 score"); `_judge` metric block | H08, H09, H19, H20 |
| D5 Metric taken from the neighbouring clause or the previous number | `_mentions` → `nearest(metric_spans, 40)` (either side, across clause breaks) | H10, H19 |
| D6 Emphatic "only" and "not only" read as scope restrictions | `QUALIFIER`, `_qualifiers`, `_condition_issues` | H07, H11 |
| D7 Model versions and sizes, and "Table 1", read as measurements | `_NUM` / `_measurements` (`_IDENTIFIER` only covers hyphenated forms) | H04, H14, H19 |
| D8 Header units ignored ("Mean Latency (s): 10.39") | `_UNIT_AFTER` (after-number only) → `_compatible_unit` | H19 |
| D9 Ratios must appear literally in the source | `ground_text` RATIO loop | H15, H19 |
| D10 "A and B, respectively" lists not mapped | `_clause_subject` / `_judge` | H10 |

How these combine into holds:

- **Veto:** `agents.VerificationAgent.run` (agents.py:240) holds on any deterministic contradiction, even when the verifier judged the claim supported. The veto is right in principle; the defects above make it fire on parse noise.
- **Interpretations:**
  - `interpretation_policy.apply` holds every accepted interpretation (H01).
  - `VERIFIER_PROMPT` defines *supported* as "the cited passages state the claim fully", applied to recommendations too (H03, H18, H21).

## 4. Multi-Agent verification vs Baseline's answer-quality review

| | Multi-Agent (VerificationAgent) | Baseline (`src/answer_quality.review_summary`) |
|---|---|---|
| Model review | 1 call, full passages, per-claim verdict and issues | 1 call, full passages and question, per-claim supported + relevant |
| Interpretations | Must be "stated fully" by the passages, then held by policy anyway | "Check its explicitly qualified premises, not whether a study proved advice"; a separate business stage gives labelled, conditional proposals |
| Deterministic layer | Exact quotes **plus a number-check veto** | Exact quotes only |
| Repairs | None (keep or hold) | None for claims; rebuilds limitations for the retained answer |
| Coverage | Verifier view, adjusted to kept claims | Retained claims only; names omitted-but-available details |

**Can Baseline's approach be reused?** Partly:

- **Not by swapping the whole verifier.** On these 21 holds, Multi-Agent's own model verifier already agreed with the evidence. Baseline's review would only help if the number veto were removed, which is not acceptable. It also has no deterministic attribution guard, and the F01 history shows model judgment alone missed a misattribution.
- **Worth reusing:**
  1. Baseline's interpretation rule (premises, not proof).
  2. Its publication structure: findings separate from labelled, conditional business statements screened by code.
  3. Optionally, its coverage instruction to name details available in the passages but omitted.

## 5. Proposed repair (prototyped here, offline)

### 5a. `numeric_checks_v2.py`: fix the parser, keep the veto

`numeric_checks_v2.py` is built reproducibly from the frozen file by `patch_v2.py` (asserted exact replacements). It applies eight rules:

- **R1 attribution:**
  - A subject mismatch must be explicit in **both** numbers' own clauses. An inherited subject can only make a number *uncertain*, which flags it for the person.
  - Aliases are compared by name ("Claude" ~ "Claude 3.5 Sonnet"). "GPT-4" vs "GPT-4o" and "Llama-2-7B" vs "Llama-3-8B" stay different.
  - Figure/table labels and metric names are not subjects.
- **R2 metrics:**
  - "F1 score" counts as F1.
  - The generic "score" cannot contradict a specific metric.
  - A metric after a number counts only in its own clause. A metric before it must not belong to a number in between.
- **R3 conditions:** "only dropped" and "not only" are not restrictions. "Only on X" still is.
- **R4 names:** a version or size inside a model name, and a "Table N" label, are names, not values, only when the same name appears in the cited quotes or passage. Values are still matched in the quotes only.
- **R5 units:** a header unit counts ("Mean Latency (s): 10.39" is 10.39 s).
- **R6 ratios:**
  - "37/100" is accepted when the source states the base ("54 of the 100 indicators") and 37 is grounded.
  - A slash pair whose values are both present and in no source ratio is a pair of values, each still checked.
- **R7** superscripts are read as digits.
- **R8** "respectively" lists map each number to its listed subject. This adds a protection the frozen check lacked (a swapped "respectively" is now caught).

Unchanged: values, signs, units, negation, settings, populations, `with`/`without` conditions, direction, ranges, and the statistical-report rule.

### 5b. `interpretation_gate.py`: labelled interpretations instead of a blanket hold

An interpretation is published **only** as a separately labelled "Interpretation: inferred from the cited findings for this decision; not a research result", and never as a finding. All seven rules must hold:

- **G1:** exact quotes.
- **G2:** every number grounded.
- **G3:** the verifier finds no contradiction or unsupported premise, and the only issue allowed is "missing_support" for the advice itself. Live, the verifier prompt adopts Baseline's premises rule for interpretations.
- **G4:** a prescriptive frame addressed to the reader's decision.
- **G5:** no explanatory or causal claim about the studied systems ("indicates that X is more effective", "reflects", "because", "helps explain").
- **G6:** the existing `advice_issues` screen passes: no ROI or savings, guarantee, compliance, readiness or workforce-replacement wording the passages do not state, and unhedged factual premises are fact-checked.
- **G7:** it shares content with the findings published for the question.

### Offline results

- **Frozen suites:** 206 / 206 pass with v2 substituted for `numeric_checks` (`run_frozen_suites.py`).
- **New tests:** `test_numeric_v2.py` has 21 tests (7 releases and 14 protections). The frozen check fails 5 of the 7 releases and misses the "respectively" swap. `test_interpretation_gate.py` has 9 tests. The F01 misattribution, causal explanations, contradicted premises, ROI/readiness and replacement claims, unverified numbers, ungrounded and inexact-quote interpretations all stay held.
- **Replay of every saved Multi-Agent verification** (`replay.py`; saved verifier verdicts, no calls; 131 findings and 11 interpretations across the business, Codex paired, three-arm and Gemini runs):
  - Frozen-check replay matches the saved decisions, except 3 claims saved under an older check (F09 ×2 before the statistical fix; one three-arm claim before the identifier fix).
  - v2 **releases 10 findings, all of them business-set wrong rejections** (H02, H04, H05, H06, H08, H09, H10, H14, H15, H19). **0 newly held. 0 releases on any earlier run.**
  - **Still held by v2:**
    - H16 and H17: correct.
    - H20: a config named "Architecture 4" in the source. Code cannot know this alias, so it stays a residual false rejection.
    - H07 and H11: still held by the verifier.
  - Interpretations published: the 4 business recommendations (H01, H03, H18, H21). The **3 F01 misattribution drafts stay held** (G4, G5), and so do the other research-level interpretations.
- **Development score estimate** (AI-assisted; same key; optimistic because the fixes were made on this data):
  - Changes: C03 +0.5, C05 +1.5, C06 +1, C07 +1 (C07.2: both KG²RAG gains now published), C11 +0.5. H19's rows are not the full-pipeline rows C14 requires, so C14 +0.
  - Total about **25 / 41** against 20.5. Baseline is 27.0. A C02 resume could add up to about 2.5–4.
  - The 4 restored recommendations add business value but no factual points.

## 6. Recommendation (simplest reliable solution)

1. **Adopt `numeric_checks_v2`** as Multi-Agent's number check. Keep the deterministic veto. It removes 10 of the 11 wrong rejections and keeps every existing protection, plus one new one.
2. **Replace `interpretation_policy` with `interpretation_gate`**, and add Baseline's one-sentence interpretation rule to the verifier prompt for interpretation claims. Interpretations then publish only as labelled, conditional recommendations.
3. **Do not** replace the verifier with Baseline's review, add a repair/rewrite call, or relax value matching. The remaining defensible holds (H07, H11, H12, H13, H16, H17) are correct to stop as written. A repair loop would add a call and new risk for about 1–1.5 points.
4. **Validate only on fresh questions:**
   - Pre-register a new consultant-style set with an independent answer key.
   - Run three arms: Baseline, frozen Multi-Agent, and Multi-Agent with v2 and the gate.
   - Report wrong rejections, unsupported claims, labelled-interpretation quality and latency.
   - Do this together with Codex's retrieval recommendation, so the final architecture decision is made once.

## Files

- `numeric_checks_v2.py` (generated) and `patch_v2.py` (generator)
- `interpretation_gate.py`
- `replay.py` (offline replay of saved decisions) and `diagnose.py` (per-number rule trace)
- `run_frozen_suites.py`, `test_numeric_v2.py`, `test_interpretation_gate.py`
- Source dump for review: `data/processed/ma-held-claims.txt` (all 21 claims with quotes and ±500 characters of passage context)
