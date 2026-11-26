# Final evaluation record (2026-11-23)

All automated reviewer runs use `gpt-6.1-sol`, low effort, ChatGPT login and the pinned B2 index `78d8efd7…`. Results live under `D:\KPMG-source-grounded\data\processed\`. Earlier Gemini runs are kept separately and never mixed into these comparisons.

| Comparison | Folders | Result |
|---|---|---|
| Multi-Agent current vs handoff (F01–F10) | `automated reviewer-paired-v1-full` | Tie in all 10 pairs. Handoff dropped |
| Baseline deployed vs tables vs Multi-Agent (F01–F10, development) | `automated reviewer-baseline-v1-deployed`, `automated reviewer-baseline-v1-tables` | 20.0 / 19.5 / 21.0 of 22 points; 0 unsupported findings. Multi-Agent's +1 came only from extra searches |
| Baseline vs Baseline + decomposition (H01–H10, held-out, sealed) | `automated reviewer-heldout-v1-baseline`, `automated reviewer-heldout-v1-decomposed` | 22.0 / 22.0 of 27; 0 unsupported findings. Decision rule failed, so decomposition is not integrated |

**Detail write-ups:**

- `agentic-handoff/automated reviewer-FINAL-ASSESSMENT.md`
- `agentic-handoff/HEAD-TO-HEAD-RESULTS.md`
- `heldout-v1/RESULTS.md`
- `baseline-decomposition/README.md`
- `baseline-completion/README.md`

**Review status:**

- The held-out key was reviewed with AI assistance (`heldout-v1/REVIEW-STATUS.md`). Scores are machine-assisted source review; independent human verification is still outstanding.
- The F01–F10 questions were used during development and are not independent evidence.

## Addendum: current Multi-Agent on the business set (business-multiagent-v1, 2026-11-23)

Same frozen C01–C15 key, model and index; Baseline reused. Multi-Agent with quote grounding, interpretation policy and statistical fix scored **20.5 / 41** (Baseline 27.0), 3 full answers, 0 unsupported claims, 105/105 exact quotes, median 67.7 s, p90 107.9 s, 46 calls, 1 CLI timeout (C02). Retrieval was better (29 vs 22 anchored points; C07 now finds KG²RAG), but the deterministic number check held 15 source-supported numeric claims. **Not qualified** as an optional Deep Research mode under the pre-registered rule. Scoring AI-assisted. Details: `business-multiagent-v1/RESULTS.md`.
