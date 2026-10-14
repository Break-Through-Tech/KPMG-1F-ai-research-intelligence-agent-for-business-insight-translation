# Answer-quality experiments

These opt-in routes address source-selection and synthesis errors without
changing the existing dense/BYOK defaults or weakening output validation.
Synthetic review is the working quality evaluation. It is recorded as AI review,
never attributed to a human reviewer or stakeholder.

## What changes

- `src.hybrid_retrieval.HybridRetriever`: BM25 + dense candidates (25 each),
  reciprocal-rank fusion, an optional local cross-encoder, and lexical candidate expansion for interpretability, SAEs, limited-data terminology and multi-agent
  coordination risks. Final selection follows the cross-encoder (or RRF),
  without keyword-based overrides. No benchmark
  IDs, known answer IDs, or fixed per-paper caps are used.
- `src.evidence_led.summarize`: extraction first, then synthesis from an exact-
  quotation ledger. Unknown citations, fabricated quotations, quotations from
  text hidden by truncation, and unsupported study-limitations without evidence
  locators fail closed. v2 additionally classifies full/partial/unavailable query
  coverage, leads partial answers with the extracted gap, and permits only direct
  facts in at most four summary claims. Source membership does **not** prove semantic entailment.
- `src.evidence_led.translate`: the existing strict business contract, with a
  scoped comparison/check and a decision metric instead of an unsupported
  deployment prescription. Partial evidence may support conditional advice.
- `src.codex_generation.create_codex_generate`: an explicit local experiment
  adapter using an existing ChatGPT Codex login. No API-key provider fallback.
  It allowlists runtime/auth-location environment variables, uses an empty
  temporary working directory, read-only ephemeral execution, and ignores user
  config. Shell/exec, code mode, integrations, browsing, computer use,
  multi-agent, hooks, image access and memory features are disabled before
  evidence is supplied. Unexpected tool-using output is also rejected. The CLI still needs network access to the model service.

## Run locally using a Codex subscription

Use Python 3.12 and installed project requirements. Supply the actual installed
CLI path and an account-accessible model; model availability is not inferred
from its name. This route uses subscription limits and is not a deployed API
replacement. It belongs on the account owner's trusted local machine, not in
public CI or on shared runners. Never copy authentication files into this repo.

```sh
python main.py --query 'How are sparse autoencoders used to interpret model behavior?' \
  --mode business --industry 'professional services' \
  --generation-route codex --codex-model gpt-6.1-sol \
  --codex-bin /absolute/path/to/codex \
  --evidence-led --retrieval-mode hybrid \
  --reranker-model cross-encoder/ms-marco-MiniLM-L6-v2
```

The reranker is local and may download its weights on first use. Retrieval
signals, including cross-encoder scores, are never confidence probabilities.
The benchmark experiment verifies the persistent index against the frozen
corpus before using hybrid retrieval. The regular CLI records corpus identity
as unverified rather than asserting that same stronger reconciliation proof.

## Controlled comparisons

`evaluation.compare_answer_variants` compares explicitly named Codex models on
identical frozen evidence and the unchanged baseline summary prompt.

`evaluation.run_answer_improvements` supports:

- `model-only`: new generator, original dense evidence/prompts.
- `evidence-led-frozen`: new evidence-led generation, original dense evidence.
- `evidence-led`: new generator, hybrid retrieval and evidence-led generation.

All modes require the integrated frozen baseline and its retrieval-only export.
The latter recovers the retrieved passages for a failed integrated case without
silently pretending that case was successfully generated in the original run.
Input run hashes, corpus hashes, code/prompt hashes and per-invocation usage/
latency receipts identify each experiment. Output directories refuse overwrite.
`run.json` checkpoints accumulate during execution; only a completed run is a
finished comparison. Original baseline artifacts are never edited.

Model-only isolates the generator change. Comparing it with evidence-led-frozen
isolates the extraction/synthesis change. Comparing frozen vs hybrid evidence-led
isolates retrieval. A combined treatment alone cannot identify which component
caused a gain. Assess exact source support, question responsiveness, omissions,
scope and abstentions; counting valid JSON or nonempty answers is insufficient.

## Quality safeguards and remaining limits

Quote membership is deterministic; semantic support remains an AI-review task.
Generic rerankers may favor adjacent topics; lexical expansion is not proof of
relevance. Keep results that underperform. Do not suppress malformed responses,
convert missing stages to scores, treat abstention as inherently good or bad,
or move a study's limitations to another paper. New questions over the same
corpus are useful probes, not proof of generalization to unseen research.

These experimental modules leave the existing approval fields unchanged. No
approval or external publication is inferred from synthetically scored outputs.
