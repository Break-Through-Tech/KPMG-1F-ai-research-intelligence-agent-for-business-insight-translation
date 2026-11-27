# Automatic business-intent detection: before vs after (offline, no model calls)

Reproduce: `python -B experiments/business-intent/measure.py [--before <old business_insights.py>] [--verbose]`.
The "before" run uses `src/business_insights.py` at `7d762c8`.

| Split (who wrote it, role) | Business recall before → after | False positives before → after |
|---|---|---|
| dev (implementer, tuning) | 2/10 → 10/10 | 0/10 → 0/10 |
| heldout (implementer; visible while writing rules) | 1/12 → 12/12 | 0/12 → 0/12 |
| blind v1 (separate model; informed one revision) | 5/43 → 43/43 | 0/41 → 0/41 |
| blind v2 (separate model; informed one revision) | 0/22 → 18/22 | 0/28 → 0/28 |
| **blind v3 (separate model; never used for tuning)** | **2/22 → 16/22 (9% → 73%)** | **0/28 → 1/28** |

The blind v3 row is the honest estimate for unseen phrasings. False positives cover research and ambiguous ("optional") questions.

## Root cause at 7d762c8
1. Workflow extraction needed a closed list of task nouns (for example "dispatch" or "claims triage") or a few
   fixed connectives. "use LLM agents to improve delivery route planning" matched none, so derivation raised and
   automatic mode returned nothing, even though intent was detected.
2. Ten sectors, and only plural actors counted ("logistics companies" did, "a law firm" didn't).
3. A narrow decision vocabulary: no "might", "is it worth", "pay off", "cost-effective", "considering" or "weighing".

## Change
The existing validated rules run first and are unchanged. A generalized second pass runs only when they find
nothing. It requires an organisation actor (a sector taxonomy, organisation nouns or the first person), an
adoption, economic or deliberation signal, and a workflow. Workflows come from general patterns or the
question's own clause around the AI capability. Academic objects (paper, benchmark, dataset, authors and so on),
research actors, "research only" and vague markers keep a question research-only. A question with business
intent but no workflow returns a prefill hint (the known industry and decision), and the UI asks only for the workflow.

## Known limits (blind v3)
- 1 false positive: "Are there reported cases in the legal AI evaluation where the model cited a real statute
  but misread it?" Automatic business insights would run once (1 Hydrogen call) on this research question.
- 6 misses. Their wording has no adoption verb ("Feasibility of…", "Vendor lock-in exposure…"), or compares
  options ("fine-tune or prompt", "hiring vs licensing"). These fall back to the manual button.
- Extracted workflows are verbatim but sometimes coarse ("Payback period", "easy queries"). They are context for
  the Hydrogen prompt, and the user can edit them under Customize.
