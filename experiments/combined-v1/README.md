# combined-v1: improved Baseline and Multi-Agent (built, offline-tested, not run live)

The original engines are unchanged: `src`, `agents.py`, `numeric_checks.py` and `interpretation_policy.py` are not edited. Everything below is opt-in.

## Components

| Piece | File | What it does |
|---|---|---|
| Shared evidence budget | `experiments/evidence-budget/evidence_budget.py` | `fixed(k)`, `skip_fit(tokens, window)` and `select()` keep whole parent rows in B2 order with original chunk IDs. `open_ranked()` gives B2's first 30, using the same index and models, beyond the public top-20 cap. Tokens are counted with B2's MiniLM tokenizer on passage text, the proxy automated reviewer used |
| Budgeted Multi-Agent research | `experiments/evidence-budget/budgeted_research.py` | First round: the original-question search gets the budgeted packet, kept whole and first. Sub-searches stay top-8 and are added round-robin. Every round is bounded by 8,000 passage tokens or 40 passages. Targeted rounds keep the original order and the reserved new slots |
| Corrected number check | `experiments/verification-repair/numeric_checks_v2.py` | Eight parsing corrections (R1–R8). Values, units, signs, negation, attribution, conditions, direction and the veto are all kept |
| Interpretation gate | `experiments/verification-repair/interpretation_gate.py` + `verification_v2.py` | Interpretations are never published as findings. One that passes G1–G7 goes to `summary['interpretations']` with a label |
| Baseline arms | `agentic-handoff/codex_baseline.py` | `fresh-top8` (control), `fresh-top16` (`create_research` top_k 16), `fresh-skipfit6k` (6k skip-fit, window 30). `quality_check=True`, table comparisons off, 2 calls per question |
| Multi-Agent arms | `agentic-handoff/codex_multiagent.py --fresh EVIDENCE VERIFICATION` | EVIDENCE is top8, top16 or skipfit6k. VERIFICATION is frozen (number check + interpretation policy) or v2 (v2 + gate). Table comparisons on, as before; quote grounding and the statistical rule in every arm; 5 calls per question cap |

## Offline verification (no model calls)

**Real pinned B2** (`check_real_retrieval.py`):

- `ranked()[:20]` equals `retrieve(q, 20)`.
- On C01–C15 it reproduces automated reviewer’s results exactly:

  | Evidence | Points / 41 | Mean passages | Max tokens |
  |---|---|---|---|
  | Top-8 | 22 | 8 | 2,693 |
  | Top-16 | 31 | 16 | 5,208 |
  | 6k skip-fit | 34 | 22.0 | 5,998 |

**Tests:**

- `test_combined.py` (8 tests): budget selection, whole-packet-first, targeted-round bound and reserve. Both engines' fresh arms also run end to end with scripted automated reviewer replies, checking the evidence policy recorded, the call caps, no interpretation in the claims, gate records present, and the v2 check active.
- Regression suites still pass:

  | Suite | Tests |
  |---|---|
  | Frozen agentic suites | 206 |
  | `test_numeric_v2` | 21 |
  | `test_interpretation_gate` | 9 |
  | `test_codex_baseline` | 6 |
  | `test_codex_multiagent` | 5 |
  | `test_codex_paired` | 8 |
  | `test_completion_eval` | 5 |
  | `test_codex_heldout` | 5 |
  | `test_handoff` | 8 (when run after `codex_paired` sets the import paths, as before) |

## Before live validation

1. Build the fresh set in this folder: `questions.json`, `references.json` and `seal.json` (8–10 questions, automated reviewer review, human sign-off). Both runners read question IDs from `questions.json`, and `--check` refuses to run until `seal.json` verifies.
2. Fix the arms and call budget.
3. Each command is run by the user from the VS Code terminal:
   - Baseline: `python -I codex_baseline.py --run fresh-top16`
   - Multi-Agent: `python -I codex_multiagent.py --run --fresh top16 v2`
