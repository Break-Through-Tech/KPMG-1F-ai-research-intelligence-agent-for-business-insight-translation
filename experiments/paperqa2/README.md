# Isolated PaperQA2 pilot

Windows Python 3.11 with the pinned dependencies in requirements-lock.txt. Install inside a short-path virtual environment outside the application, for example using `py -3.11 -m venv C:/venvs/kpmg-paperqa2` and that environment's Python with `-m pip install -r experiments/paperqa2/requirements-lock.txt`. The ChatGPT provider requires the LiteLLM MCP extra. The lock includes its resolved dependencies.

From the checkout, set `TIKTOKEN_CACHE_DIR` to a dedicated cache containing the public cl100k_base vocabulary. To prime an empty cache when downloads are permitted, use `python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"`. Set `LITELLM_OFFLINE_MODE=True` for offline use.

```powershell
python -B experiments/paperqa2/adapter.py <demo-100-parents.jsonl> experiments/paperqa2/pilot-copy.json 2402.01622v4 2510.02243v2
$env:PAPERQA_PILOT_COPY = "experiments/paperqa2/pilot-copy.json"
python -B -m unittest discover -s experiments/paperqa2 -v
python -m pip check
```

The copy command verifies the approved demo-100 parent-file SHA-256 and refuses to overwrite an existing copy. It selects 92 original passages from two versioned papers. PaperQA2 builds its own in-memory sparse index from those passages. The adapter returns query, answer status, answer text and cited original chunk IDs, exact arXiv versions, source URLs and source text. The offline tests use scripted generation and mocked authentication. Windows asyncio requires local loopback for these tests.

## Candidate live pilot, pending explicit approval

Use previously disclosed development topics only. Ask for TravelPlanner's benchmark design and its reported final pass rate, and for AccurateRAG versus RAFT with GPT-4 CoT across the three Table 2 score columns. Run each once through the standalone adapter and record selected passages, answer, citation mapping and elapsed time. Compare against the source sections and Table 2, including the model, metric and conditions for every number. Use the documented LiteLLM ChatGPT device sign-in into the existing subscription with an isolated credential cache. Confirm authentication and retry policy before making generation requests. No paid provider fallback is configured.

This profile uses PaperQA2's native retrieval and answer path with evidence summarization disabled. It does not exercise the default agent search loop, PDF ingestion, semantic citation entailment, numeric verification or shared brief integration. A citation identity check confirms which original text was supplied, while a source review is still required to establish support.
