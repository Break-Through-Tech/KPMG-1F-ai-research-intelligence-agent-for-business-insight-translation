# Completion evaluation (completion-eval-v1): frozen plan for approval, not run

**Purpose:** the final research experiment. It decides whether the opt-in completion pass is integrated, kept experimental, or abandoned.

## Frozen set

Sealed in `seal.json`, together with the frozen `completion.py` hash and the index hash `78d8efd7…`.

15 questions framed for a KPMG consultant, with **41 required points**:

| ID | Topic | Type |
|---|---|---|
| C01 | AI coding assistants vs malicious-code jailbreaks (MalwareBench) | numeric, risk |
| C02 | Role-based access control for LLM answers (sudoLLM): fail-closed, robustness, cost | governance, cost |
| C03 | Poisoned training data and malicious fine-tuning (Ctrl) | risk, trade-offs |
| C04 | Knowledge graphs for financial numerical reasoning | numeric, limitations |
| C05 | Small trained agent vs frontier model vs human experts (Aviary) | cost-performance |
| C06 | RAG robustness to sparse or contradictory sources (MultiRAG) | numeric |
| C07 | KG²RAG vs MultiRAG | cross-paper |
| C08 | Irrational financial biases in LLMs (FBI) | qualitative, limitations |
| C09 | Multilingual finance LLMs (LLM Pro Finance) | numeric, applications |
| C10 | Where LLMs help and fall short in finance | qualitative, adoption |
| C11 | Foundation-model vendor transparency (FMTI) | governance, numeric |
| C12 | Clinical-deployment challenges for medical reasoning LLMs | limitations, risk |
| C13 | Proactive agents: task success vs user burden (BAO) | qualitative, customer experience |
| C14 | Commercial vs in-house reranker: F1 and latency (Table 1) and the authors' business implications | table, business |
| C15 | Should a bank use a finance-specialized LLM? (LLM Pro Finance vs FBI) | cross-paper, business |

**Published vs inferred.** Required points are published findings only, including implications the authors state themselves (C14). Any business implication a system infers must be labelled as interpretation; otherwise it is scored as misleading.

**Answer key.** `answer-key.md` quotes every anchor passage verbatim, for human review.

**Paper reuse.** `OVERLAP.md`: 7 papers never used anywhere; 6 not in F01–F10 or H01–H10; one documented overlap (2510.24402v1, H01/H04, a different aspect).

## Arms

- **A:** Baseline/B2 unchanged, run once per question (`codex_baseline.py --run completion-eval-baseline`). The hard cap is 30 calls, exactly 2 per question. Output: `automated reviewer-completion-v1-baseline`.
- **B:** the frozen completion pass applied to A's **saved** answers, with no regeneration (`apply_completion.py --run`).
  - It makes calls only when A's review reports an available-but-omitted detail: a re-draft plus a review, at most 2 per triggered question.
  - Hard cap: 30 calls. Output: `automated reviewer-completion-v1-completed`.

## Measures

- Required-point scores for A and B.
- Complete / partial / abstained.
- **Detection:** trigger recall over omitted-but-available points, recovery rate, and a list of missed omissions that never triggered.
- **Added-claim audit:** numbers, exact quotes, citations, duplicates, unsupported or misleading interpretation, and that every A claim and limitation is unchanged.
- Calls, tokens, latency.

## Decision rule (frozen in `rules.json`)

| Decision | Conditions |
|---|---|
| **Integrate** | B ≥ A + 2.0 points; zero unsupported or misleading added claims; zero removed or altered A content; zero duplicates; median extra latency on triggered questions ≤ 45 s |
| **Leave experimental** | Safe (zero unsupported, zero removals) but below the integrate bar |
| **Abandon** | Any unsupported or misleading addition, any removed or altered A content, or no point recovered on any triggered question |

## Expected usage

| | Calls | Input tokens | Time |
|---|---|---|---|
| A | exactly 30 | about 0.55M | about 8–10 min |
| B, expected | 2–6 (about 1–3 triggered questions; observed trigger rate 5/40 = 12.5%) | about 40–110k | about 1–2 min |
| B, maximum | 30 | — | — |
| **Total** | about 32–36 expected, **hard cap 60** | — | — |

## Readiness (offline)

- `apply_completion.py --check` passes: seal verified, login and model fine.
- `codex_baseline.py --check completion-eval-baseline` currently **refuses**: free commit is 4.8 GB, below 6 GB. Close browsers first.
- `test_completion_eval.py` passes 5 tests:
  - A runs C01–C15 at 30 calls;
  - the seal covers the completion code;
  - B spends calls only on triggered questions and leaves A's saved files byte-identical;
  - resume and the cap work;
  - a quota error stops B.
- The full offline suite passes. `src` is unchanged.

## Limitations

- Completion can only fire when the review itself reports an omission. In held-out runs, two of three omission cases went unreported, so recall may be low regardless of correction quality.
- One run per arm, one model. The key is AI-prepared; independent human verification is outstanding.
- I wrote the questions and the completion mechanism. Human review of the key and of added claims is required before relying on the decision.
