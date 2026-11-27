# Proposed final fresh validation: Original Baseline vs Optimized Consolidated Standard (NOT run)

**Status:** design only. **No live calls have been made.**

- **Before any run:** you approve this design and the call budget.
- **Default unchanged:** the Original Baseline remains production default unless separately approved promotion requirements are met.
- **Not reused:** the fresh-v2 questions informed the v2 changes, so they are regression data only and not used here.

## Question set: fresh-v3 (to be built after approval)

- **Papers:** the 8 corpus papers that have never appeared in any question, reference, key, case, label, fixture or test file. Each appears only in 1–3 retrieval-trace or listing files as a distractor.

  | Domain | Papers |
  |---|---|
  | Clinical evaluation | CliBench 2406.09923v2, MedQA-CS 2410.01553v2, Med-CoDE 2504.15330v1 |
  | Materials and catalysis | high-entropy catalysts via RAG 2603.15712v1, neural graph matching for molecular RAG 2502.17874v2 |
  | Biology | SANE 2606.04500v1 |
  | Efficiency | LLM compression survey 2402.09748v1 |
  | Safety | subtoxic jailbreak questions 2404.08309v1 |

  This is the corpus's last clean set: after it, no unused papers remain.
- **8 consultant-framed questions**, covering:
  - single-paper research;
  - at least 3 cross-paper comparisons;
  - at least 2 numerical/table questions;
  - at least 3 questions with several requested parts;
  - business implications;
  - at least 2 partially unanswerable questions;
  - relevant limitations;
  - at least 1 question where an adjacent passage could mislead, for example a related-work number or a different model or setting.
- **Key process, the same as fresh-v2:**
  1. Claude drafts the key with anchor checks (every anchor group, alternatives included, must contain every required fact).
  2. One focused independent review.
  3. Human sign-off.
  4. Seal the question set and the code of every arm. The questions are written without running any engine on them.

## Arms (equivalent provider: Codex CLI, gpt-6.1-sol, low effort, 300 s timeout, ChatGPT login)

| Arm | Engine | Calls per question | Cap |
|---|---|---|---|
| **B0** Original Baseline | `codex_baseline` top-8 with quality review (the production default), frozen | 2 | 20 |
| **S2** Optimized Consolidated Standard | `consolidated-v2` Standard | 2 | 20 |
| **S1** Consolidated Standard v1 (control) | `consolidated` v1, frozen | 2 | 20 |

- **Total:** 48 calls expected; **hard cap 60, retries included**, with persistent ledgers and a combined-cap check before each arm.
- **Same inputs for all arms:** questions, corpus snapshot (index `78d8efd7…`), provider and settings.
- **Not included by default: Optimized Deep or Adaptive.** Deep did not qualify on fresh-v2, and the routing prototype could not be validated (see the final report). If you want it, add D2 = `consolidated-v2` Deep: +24 calls, cap +30 (total cap 90).
- **Comparisons:**
  - B0 vs S2 is the promotion comparison.
  - S1 vs S2 measures the optimization itself, descriptively.

## Measures

- **Completeness:** points and fully answered questions.
- **Citation entailment:** the attached quotes must entail each published finding, limitation, gap or summary sentence, and interpretation premise.
- **Numerical correctness:** value, unit, subject, metric and condition.
- **Unsupported or misleading claims.**
- **Business interpretation quality:** rubric 0–2.
- **Execution:** first-pass success.
- **Latency:** total including failed attempts, plus median and p90.
- **Usage:** actual provider input and output tokens (receipts), reported next to estimates.
- **v2 safeguard activity:** conclusion-coverage use, related-variant publications and withheld items.

## Acceptance criteria for S2 as a promotion candidate (frozen before execution)

**Safety.** Every one of these must hold:

- 0 citation-grounding failures;
- 0 misleading or fabricated claims;
- 100% exact quotes;
- 100% numerical correctness in published items.

**Completeness:** S2 ≥ B0 + 10% of P (P = total points), and S2 fully answers at least as many questions as B0.

**Execution:** first-pass success ≥ 7/8, and ≤ 1 execution error after one resume.

**Latency (Codex provider):** S2 median total ≤ 120 s and p90 ≤ 180 s. The B0 latency is reported alongside.

**Scoring:** blind (A/B/C shuffled per question), done independently, with disagreements adjudicated by you.

**Limitations:** 8 questions; one run per arm; the papers are the last clean subset of a 100-paper corpus; the key is AI-drafted.

## Separately bounded production-provider smoke test

- **Scope:** S2 on 3 fresh-v3 questions with the production provider adapter (Gemini, OpenAI, OpenAI-compatible or Bedrock: you choose).
- **Budget:** 6 calls, **hard cap 10**.
- **Purpose:** checks structured-output compliance, schema validation, malformed-output handling, maximum output (synthesis needs up to about 4k output tokens), actual token usage, and **the adapters' 60-second read timeout**. In v1, Codex synthesis took a median 73.5 s. This test measures whether v2's smaller prompts fit within 60 s; the timeout policy is not changed.
- **Not a qualification:** this smoke test does not qualify the provider. Codex results do not transfer automatically.

## What happens after approval (offline, before any call)

1. Build fresh-v3 (questions, key and anchors), run the single independent review, and get your sign-off.
2. Register fresh-v3 for B0 in `agentic-handoff/codex_baseline.py` (an experiment runner, not the shared app). Point `consolidated-v2/run_consolidated.py` at `fresh-v3` and set the arm caps above.
3. Seal; run the readiness checks; then you run the arms.
