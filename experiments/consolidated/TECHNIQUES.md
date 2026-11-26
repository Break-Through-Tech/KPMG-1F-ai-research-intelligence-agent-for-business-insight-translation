# Techniques adopted from the reference implementations

I reviewed each source on 2026-11-24, using its paper or abstract, README and the named source files.

- **No external code was copied, vendored or added as a dependency.** Each technique is a re-implementation of the idea in the existing Python code, so no licence text has to be carried. The references are recorded here for attribution.
- **Licences, as listed on GitHub** (the LICENSE files themselves were not read):
  - PaperQA2: Apache-2.0
  - ALCE: MIT
  - FActScore: MIT
  - LangGraph: MIT

| # | Technique | Source and what it does there | Our adaptation (location) | Failure addressed | Regression tests |
|---|---|---|---|---|---|
| 1 | **Claim-level citation recall** | ALCE (Gao et al., 2023, arXiv 2305.14627; `eval.py`): a statement counts as supported only if the concatenation of its *own* cited passages entails it, checked with an NLI model | **Deterministic:** every reported number must occur in the claim's attached quotes (P4, `publication.number_recall`). **Model:** the review judges `quotes_entail` against the attached quotes, not the full passage (`review.EXTENSION`). **Prompt:** the attached-quote rule is in `synthesis.ATOMIC_RULES` | G03-B F2 (figures cited to the wrong table row); G03-C F1 (a fact taken from the passage but not the quote) | `CitationGroundingTests` (7) |
| 2 | **Atomic facts, verified independently** | FActScore (Min et al., 2023, arXiv 2305.14251; `atomic_facts.py`): split a generation into atomic facts, verify each against evidence, and score the supported fraction rather than the whole text | **Generation:** decomposition happens at generation time (one result per finding), so no extra call is needed (`synthesis.ATOMIC_RULES`). **Per-claim gates:** one bad claim is withheld and the others publish (`publication.publish`). **Partial retention:** the reviewer returns `supported_text` holding only the entailed facts, and P3 checks it is a pure reduction | M1 lost correct figures bundled with unquoted ones (G03, G04, G08); Baseline rejected whole answers | `PreservationTests`, `test_replay_g03_b_f2_reduced_to_supported_part`, `test_unit_reduction_may_not_add_numbers` |
| 3 | **Keyed citations with an explicit "cannot answer" path** | PaperQA2 (Skarlinski et al., 2024, arXiv 2409.13740; `prompts.py`): the answer may cite only the listed context keys, and has a sentinel for insufficient context | Already present in Baseline: a schema `enum` of chunk IDs, plus `insufficient_evidence` with cited limitations. Kept as is. Status is now *derived* from the validated claims (`synthesis.parse`) | G10 contract failure (status contradicted the claims) | `test_replay_g10_status_contract_failure_recovers_validated_claims`, `test_sim_g10_style_reply_through_engine` |
| 4 | **Prompt chaining with programmatic gates; simplest workflow that works** | Anthropic, "Building Effective Agents" (2024): chain fixed LLM calls with code checks between them, and add agentic loops only when they demonstrably help | **Standard:** synthesis, then review. **Deep:** plan, then synthesis, then review. Deterministic gates sit between and after the calls. No orchestrator loop, extra reviewer or repeated synthesis (`engine.py`) | Multi-Agent's extra calls and agent hand-offs lost information without improving answers | `EngineTests` (call counts exactly 2 and 3) |
| 5 | **Durable execution with per-step checkpoints** | LangGraph checkpoint (`libs/checkpoint`): a thread-scoped checkpoint per step, plus pending writes, so a failed step resumes without re-running completed ones | Minimal re-implementation (`engine.CheckpointStore`): one atomic JSON file per completed stage, and an attempt log. A resume loads finished stages and repeats only the failed one. The planner fallback decision is itself checkpointed | combined-v1: 9 of 30 questions timed out and every resume restarted from scratch | `test_sim_review_timeout_then_resume_repeats_only_review`, `test_sim_synthesis_timeout_then_resume_keeps_plan`, `test_sim_one_resume_only` |

**Not adopted, and why:**

- **PaperQA2's per-chunk summarisation and re-scoring calls:** they would add LLM calls beyond the approved 2 for Standard and 3 for Deep.
- **ALCE's NLI model and FActScore's LLM decomposer:** they add a model dependency or extra calls. The same principles are enforced by the deterministic number-recall gate and inside the existing single review call.
- **LangGraph as a framework:** too heavy for four linear stages.
