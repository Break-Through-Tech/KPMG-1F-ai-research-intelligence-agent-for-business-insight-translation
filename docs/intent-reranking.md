# Opt-in source-checked intent reranking

`create_intent_rerank(generate)` assesses the actual question against every
hybrid candidate. Scores 0–3 are ordinal relevance judgments, not confidence.
Each nonzero assessment needs a quote from that candidate's **displayed** text;
unknown/duplicate/missing IDs, invalid scores, hidden-tail quotations and provider
errors fail closed without falling back to another ranking method.

The final ranking follows assessment scores and RRF ties, never a keyword-based
slot reservation. Topic terms still expand lexical candidates only. Metadata
retains the reason, supporting quote and displayed-text length. Quote membership
does not prove that the relevance judgment is correct; audit the selected and
missed sources. Candidates are limited to 50 and text to 2,000 characters each;
over-budget requests fail rather than silently dropping candidates.

The existing dense/BYOK defaults and optional local cross-encoder are unchanged.
This mode makes model-service calls through the same configured generation
adapter. A Codex route uses the existing ChatGPT login and its text-only controls;
a BYOK route uses the explicitly configured provider and may incur its usual costs.
The module itself does not initialize a provider or download weights.

```sh
python main.py --query 'What coordination failures occur in multi-agent systems?' \
  --retrieval-mode hybrid --intent-rerank --evidence-led \
  --generation-route codex --codex-model gpt-6.1-sol --codex-bin /path/to/codex
```

The CLI requires summary/business mode, hybrid retrieval and no cross-encoder
flag. Retrieval-only evidence comparisons can inject the factory directly into
`HybridRetriever`. Controlled full captures support:

```sh
python -m evaluation.run_answer_improvements \
  --baseline /path/to/frozen-integrated/run.json \
  --retrieval-baseline /path/to/frozen-retrieval/run.json \
  --output /path/to/new-run --variant evidence-led --intent-rerank \
  --codex-bin /path/to/codex --model gpt-6.1-sol
```

The capture records the relevance prompt hash and budgets separately from answer
prompt provenance. Keep uniform captures, paraphrased-query controls and adverse
results; recovering a known paragraph is not evidence of generalization.

Controlled captures retrieve inside each checkpointed case. A rejected ranking
records an explicit error row, saves model receipts and earlier successful
retrievals, continues subsequent cases, and exits nonzero. Failed cases receive
no fallback passages. Corpus/index preflight failures still stop before capture.
