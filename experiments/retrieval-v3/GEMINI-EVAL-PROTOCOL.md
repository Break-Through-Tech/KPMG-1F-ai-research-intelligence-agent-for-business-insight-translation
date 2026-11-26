# Final evaluation proposal: frozen S2 vs optimized S2-R2 on Azure's Gemini configuration

**Status:** proposal only. No live calls; nothing is configured.

## 1. The exact Azure configuration (read from `deploy/azure-vm`, unchanged)

| Item | Value | Source |
|---|---|---|
| Provider | Google Gemini, through the application's existing Gemini adapter (`src/generation.py`) | `docs/byok-generation.md` |
| Model | **`gemini-3.1-flash-lite`** | `deploy/azure/HANDOVER.md` |
| Settings | temperature 0, JSON (schema) output | `README.md` |
| Credential | `GOOGLE_API_KEY` | `deploy/azure/README.md`, `.env.example` |
| Index | the demo-100 bundle (`78d8efd7…`) | HANDOVER |

**Discrepancy to note:** the repository's `.env.example` and the README still name `gemini-2.5-flash`; HANDOVER names `gemini-3.1-flash-lite` for the live deployment. **Please confirm which model is live.**

**Per-call timeout:** the production adapters use 60 s per call. S2's synthesis calls took about 35–80 s on Codex, so the timeout behaviour on Gemini is part of what this evaluation measures.

## 2. Authorised, isolated environment: what is needed from you

This research environment has used **only** the Codex subscription login; API keys have never been handled. A Gemini evaluation needs a key, so it needs your explicit authorisation and a setup that keeps the key out of my hands:

1. **A dedicated evaluation key.** Create a **separate** Google AI or Cloud project for evaluation, not Azure's production key or project.
2. **Hard cost limits on that project.** Set a budget and alert (proposed **USD 10**) and per-day request quotas, so spending is capped by Google regardless of software.
3. **Supply the key yourself.** Set it as a user environment variable, `GEMINI_EVAL_API_KEY`, on this machine. The runner reads it at run time and never prints, logs or stores it. I will not read or handle the value.
4. **No Azure access.** Nothing touches the Azure VM, its `/etc/kpmg/preview.env` or the production key.

If you prefer not to authorise a key here, the alternative is for Laptop Claude or you to run the same automated runner where the key already lives, with the same frozen protocol.

## 3. Smallest meaningful design

**Questions:**
- A **new reserved unseen set**: 8 questions, 36 points, with the same distribution as before (3 named two-paper, 3 unnamed multi-part, 2 controls).
- Built from facts that no existing key uses, with the Codex CLI key review and sealing as in unseen-r2.
- **Disclosure:** the questions are new, but the papers are not.

**Arms:** frozen S2 vs optimized S2-R2 (`a462275`). Both use the same Gemini model, temperature 0, schema output, the application's 60 s adapter timeout, the same index and the same 6k budget. The order alternates per question.

**Phase 0, a provider smoke test (inside the budget):**
- U1 and U2 on S2 only, 4 calls.
- **Stop** if any structured-output or schema failure, malformed-output failure or timeout is not recovered by the single resume. Report it as a Gemini-compatibility finding before spending more.

**Budget:**

| Item | Value |
|---|---|
| Calls expected | 32 (16 per arm; smoke-test calls count) |
| **Hard cap on calls** | **40**, including failures and retries |
| Token caps | input ≤ **1.2 M** and output ≤ **150 k** in total; the runner stops if either would be exceeded |
| Cost ceiling | the project budget above (proposed USD 10). Expected spend is a small fraction of that for this token volume, but you should check current Gemini pricing |

**Scoring:** a blind A/B packet scored by a fresh Codex CLI session (your existing subscription, separate from the Gemini budget), the programmatic citation, number and absence audit, a Claude check of flags, and your adjudication.

## 4. Frozen acceptance criteria (proposed, to confirm before running)

| # | Criterion |
|---|---|
| 1 | R2 ≥ S2 + 2 points (of 36) |
| 2 | Zero new citation-grounding, numerical, misleading or unsupported flags |
| 3 | R2 median total latency ≤ 1.25× S2 **and** ≤ 120 s; p90 ≤ 180 s |
| 4 | R2 input tokens ≤ 1.10× S2 |
| 5 | No silent failures, exclusions or unreported retries |
| 6 | **Gemini compatibility:** ≥ 15 of 16 questions complete per arm, after at most one resume each |

**Also reported:**
- absolute completeness against the 85% goal;
- the stricter 1.10× latency reference;
- retrieval, generation and total latency;
- input and output tokens;
- any timeouts at the 60 s adapter limit.

**Outcome:** if R2 passes, it becomes the recommended integration candidate for Azure, behind a flag, with S2 as the default and fallback. It is not deployed automatically.

## 5. Work before any call (0 calls; after you approve this proposal)

1. Write and seal the new unseen set, with an automated Codex key review.
2. Extend `run_unseen.py` into a Gemini runner: it builds `generate` from the application's Gemini adapter (model and temperature from your confirmation, key from `GEMINI_EVAL_API_KEY`), adds the token caps, and records adapter timeouts. Then freeze it.
3. Run readiness checks: seal, key present (checked by name only), memory and caps.

Then I present the readiness result for your go-ahead.

## Decisions needed

1. Confirm the live model: `gemini-3.1-flash-lite` or `gemini-2.5-flash`.
2. Authorise an isolated evaluation key, or choose to run it on Laptop Claude.
3. Approve the budget (40 calls, the token caps and the cost ceiling) and the criteria.
