# 5.1 — Benchmark Questions

Version: **alesha-baseline-v1**. The executable source of truth is
[`evaluation/baseline_alesha_v1.json`](../evaluation/baseline_alesha_v1.json).
Numbers 1–10 correspond to IDs `alesha-v1-q01` through `alesha-v1-q10`;
they are not the `q01`–`q10` cases in the existing main benchmark.

## Factual

1. What capabilities and limitations does MCP-Atlas identify when evaluating LLM tool use with real MCP servers?

2. What risks or failure modes of AI agents are identified in research on agentic misalignment?

3. How does multi-turn interaction affect the robustness of LLM unlearning?

4. What approaches are used to improve the interpretability of neural network representations?

## Comparative

5. How does Continuous-Utility Direct Preference Optimization use continuous utility scores during preference optimization?

6. How do single-agent and multi-agent approaches compare in agentic trip-planning tasks?

7. What are the different approaches used to evaluate safety and reliability in LLM agents?

## Business Translation

8. What should a company evaluate before giving an AI system access to external tools or MCP servers?

9. What risks should a business consider when deploying autonomous AI agents in workflows where the system can take actions on its own?

10. If a vendor claims that its AI system is safe or reliable, what evidence should a business look for before trusting that claim?

## Capture inspectable evidence

Run from the repository root with the supported Python environment:

```bash
# No model/key required: capture actual passages from the existing persistent index.
python -m src.evaluation_retrieval --output output/alesha-retrieval-run
# Uses the documented shared provider settings in .env.example.
python -m src.evaluation_retrieval --mode summary --output output/alesha-summary-run
# Offline smoke proof only, not real-paper evaluation.
python -m src.evaluation_retrieval --demo --mode summary --output output/alesha-fixture-run
```

Each output directory must be new. The existing benchmark runner preserves full
passages/results and run identity in `run.json` and emits blank reviewer/rating
cells in `review.csv`. A file hash does not prove the live index matches that
file; the runner leaves indexed-corpus identity unknown. Do not overwrite frozen
runs, substitute fixture ratings for human review, or commit private outputs.
The old score tables in [Baseline Evaluation](baseline_evaluation.md) are not
bound to these new captures.

For a single cited draft, use `python -m src.agent --query "your question"`.
Add `--industry "your industry"` for explicit business translation; the full
result remains a pending, unapproved research draft. Provider/model configuration
is shared with `main.py` and [BYOK generation](byok-generation.md); no separate
`GEMINI_API_KEY` or hardcoded model is required.
