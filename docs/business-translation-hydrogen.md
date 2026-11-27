# Business Insight Translation with Gemini 4 Hydrogen

**Status:** integrated on `feat/business-translation-v1`, not merged or deployed. Business translation remains optional and off by default.

## Validated configuration

The evaluation used AI-assisted blind scoring, not human certification:
- 5/5 on the development cases
- 4/4 on fresh cases
- fresh-case means of 4.75 usefulness, 5.00 fidelity and 5.00 limitations
- zero critical unsupported claims

The evaluation artifacts are in the main checkout under `evaluation/business-translation-capability-diagnostic/`.

| Setting | Value |
|---|---|
| Model | `gemini-4-hydrogen` only (`src/business_generation.py`). Any other value is refused |
| Thinking | `thinking_level=high` |
| Temperature / output | 0 / `application/json` |
| Prompt | `prompts/business_translation/downstream-v1.2.txt`, unchanged |
| Calls | One generation attempt, with a second attempt only after HTTP 503 |
| Transient HTTP 503 | One retry after 5s. If it fails again, the business stage is `unavailable` and the research answer is retained |
| Other provider errors | Not retried. The business stage is `failed` |
| Fallback | None. The research model or Flash-Lite is never used for business reasoning |
| Local timeout budget | 75s per provider attempt and a 5s retry delay. The provider budget is 155s, the UI proxy waits 170s, and the browser waits 180s. |

## Publication checks

The heuristic semantic screen (`src/business_checks.py`) is no longer a publication gate. The module remains for reference, and `translate_result` no longer calls it.

These checks are retained:
- accepted-evidence handoff (`src/business_handoff.py`)
- exact BusinessInsight JSON shape
- citations limited to accepted evidence
- industry match
- concise length limits
- preservation of accepted research limitations
- fingerprint and saved-version checks

Provenance records `publication_gate.policy = structural-only-v1`, the prompt hashes, the model metadata, `attempted_calls` and `provider_attempts`.

## Configuration

Set these locally. Never commit values.

```powershell
$env:BUSINESS_TRANSLATION_ENABLED = '1'
$env:BUSINESS_TRANSLATION_API_KEY = Read-Host 'Dedicated Hydrogen API key' -MaskInput
# Optional: read the key from another variable name instead
# $env:BUSINESS_TRANSLATION_API_KEY_ENV = 'BUSINESS_EVAL_API_KEY'
```

- The business key must be a dedicated variable. The code refuses research key variables (`GOOGLE_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `RESEARCH_API_KEY`) and refuses a business key equal to any of them.
- Use the official Gemini Developer API. The client pins `https://generativelanguage.googleapis.com/` and rejects conflicting Gemini base URL and Vertex or Enterprise overrides.
- **Data:** this is a free-tier evaluation configuration, and Google uses free-tier content to improve its products. Use only public research and hypothetical or non-confidential business context. The UI shows this warning above the business form.

## Run locally

1. Seed a new demo library from the nine validated, reviewed research packets. This step is offline and makes no model calls:
   ```powershell
   python -m scripts.seed_business_demo_library --library data/briefs/business-demo.sqlite3
   ```
2. Start the business host. It serves saved research only and never runs research:
   ```powershell
   python -m src.business_demo --library data/briefs/business-demo.sqlite3 --configured-provider --port 8791
   ```
3. Start the UI:
   ```powershell
   python ui-consult/serve.py 8792 --backend http://127.0.0.1:8791
   ```
4. Open http://127.0.0.1:8792, choose a saved brief from **Library**, and expand **Business implications**. Enter the industry, workflow and decision that the seed script printed for that case, then select **Translate these findings**. Inspect the recommendation, its citations, and the new saved version. Past successful requests took about 10–30 seconds.

## Offline replay and historical evaluations

The nine replay fixtures hold the original UTF-8 response text. Each archived response file was checked against its historical ledger before extraction. The replay verifies the raw text and dispatched prompt hashes, then checks the complete published object. Publication preserves the model's generated fields and prepends accepted research limitations with exact duplicates removed.

The previous evaluation manifests still pin their original adapters. Their preflight must use the matching historical checkout. It is expected to reject this branch's new downstream adapter. The original v1 and final v1.2 evaluation commits are `90ce47ca` and `1eeb869a`, respectively.

## Known limits

- **Sample size:** the evidence is 9 cases. No human reviewer has scored the outputs.
- **Free tier:** rate limits for Hydrogen are not published. The development run returned two HTTP 503 errors in 10 calls; this code retries once.
- **Latency:** about 10–30s per translation.
- **Data use:** free-tier content is used to improve Google products.
