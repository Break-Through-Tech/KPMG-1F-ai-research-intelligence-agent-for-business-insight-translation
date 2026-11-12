# Research review bridge (Issue #81)

This module connects a completed research result to a human decision without rebuilding the regulatory checkpoint. Inputs and outputs are JSON-compatible dictionaries; functions return defensive copies.

## Build a packet and record a decision


```python
draft = run_research(...)
packet = make_review_packet(draft)
# Inspect query, original passages and source links, claims, implications, limitations,
# provenance, and any advisory regulatory checkpoint. Pending is not approval.
reviewed = record_human_decision(
    packet, reviewer="Reviewer Name", decision="revise", notes="Add support for claim 2",
)
require_current_review(reviewed)
```

Allowed decisions are approve, revise, and reject. Only an explicit human approve sets approved=true. The packet remains pending by default; making a fresh packet resets any earlier approval. Review uses the shared src.research_pipeline.content_fingerprint contract and binds complete result/context JSON except review metadata, so packets and pipeline results interoperate. Changing request/context, evidence, summary, business insight, provenance, or regulatory checkpoint makes the old fingerprint fail; create and review a new packet. Version 2 binds all result/context fields except review metadata. Historical saved results without a version marker use the exact version 1 fixed-field projection (including null defaults for absent optional fields), so unchanged saved reviews remain verifiable; a new packet or recorded human decision upgrades the artifact to version 2 and binds additive fields. Treat the fingerprint as a change detector, not as an authenticated signature or immutable audit log.

If a regulatory checkpoint is attached, approval is blocked unless its assessment verdict is potentially_feasible. Conflicting, insufficient, missing, or unrecognized assessments stay unresolved. A model verdict is advisory and never sets approved=true.

## Optional regulatory adapter

Pass the existing human_checkpoint functions rather than duplicating policy or API calls:

```python
from src.human_checkpoint import create_client, retrieve_regulations, assess_insight
advisory = review_adapter(
    draft,
    client=create_client(),  # initialized explicitly; API access is opt-in
    retrieve_regulations_fn=retrieve_regulations,
    assess_insight_fn=assess_insight,
    as_of="2026-10-14",  # optional; use the intended assessment date
)
```

The adapter derives industry and jurisdiction from request and insight from business implications unless explicitly passed. It requires all three before retrieval; missing context returns a pending advisory without invoking either function. When context is complete, pass an explicitly initialized client; the adapter forwards it to retrieve_regulations(client, industry=..., insight=..., jurisdiction=..., as_of=...) and assess_insight(client, evidence). Both retrieval evidence and the full assessment schema, source citations, and verdict consistency are validated through shared dependency-free gates also used by human_checkpoint. The resulting regulatory evidence bundle is separate from the original research passages and their chunk IDs. Missing, malformed, conflicting, or insufficient assessments cannot pass approval. Do not treat successful execution, a potentially_feasible model verdict, or cited paper passages as human approval.

The indexed backend accepts this adapter only after explicit user opt-in and
requires industry plus jurisdiction. Provider failure is recorded as failed rather
than as missing evidence; unavailable supported business context is recorded as
skipped. Indexed startup does not initialize the regulatory client or require its
API key unless an assessment is requested.

### Indexed request and response contract

The existing `POST /api/research` request accepts these optional fields in
addition to `query` and `context_id`:

```json
{
  "industry": "financial services",
  "risk_assessment": true,
  "jurisdiction": "United States"
}
```

`risk_assessment` defaults to false. When true, `industry` and `jurisdiction`
must be non-empty text; missing values are rejected before retrieval or provider
calls. Risk assessment also requires at least one supported business implication.

The normal response remains unchanged when the option is omitted. When requested,
the research result includes `result.regulatory_checkpoint`, separately from
`result.evidence` (academic paper passages):

```json
{
  "schema_version": "1.0",
  "evidence_namespace": "regulatory",
  "status": "assessed",
  "industry": "financial services",
  "jurisdiction": "United States",
  "summary": "Advisory summary",
  "regulatory_evidence": {
    "as_of": "YYYY-MM-DD",
    "sources": [{"source_id": 1, "title": "Source title", "url": "https://..."}],
    "evidence": [{"text": "Retrieved source excerpt", "source_ids": [1]}]
  },
  "assessment": {
    "verdict": "insufficient_evidence",
    "regulatory_compliance": {"status": "unknown", "explanation": "Evidence limitation", "source_ids": []},
    "legal_constraints": {"status": "supported", "explanation": "Finding", "source_ids": [1]},
    "governance": {"status": "unknown", "explanation": "Evidence limitation", "source_ids": []},
    "operational_feasibility": {"status": "supported", "explanation": "Finding", "source_ids": [1]},
    "risks": []
  },
  "reason": null,
  "approved": false,
  "human_review": {"status": "pending", "reviewer": null, "notes": null}
}
```

Every checkpoint includes `schema_version`, `evidence_namespace`, `status`,
`industry`, `jurisdiction`, `summary`, `regulatory_evidence`, `assessment`,
`reason`, `approved`, and `human_review`. For `skipped` or `failed`, evidence
and assessment are null, and `reason` explains the state. `provenance.stages.regulatory`
matches the checkpoint status. Failures also return the ordinary top-level error
envelope while preserving the valid research result. The four finding statuses
are `supported`, `conflicts`, `not_applicable`, and `unknown`; `unknown` requires
an explanation and does not require a citation. The assessment verdict can be
`potentially_feasible`, `conflicts`, or `insufficient_evidence`, with conflicts
and unknown findings validated against that verdict.

The UI can use source IDs within `regulatory_evidence` only for regulatory
citations. Academic claim citations continue to refer to research evidence
`chunk_id`s. A cited regulatory source is not proof of legal applicability or
compliance. A failed provider/validation stage is not an evidence finding, and
all generated assessments remain advisory and pending human review.

## Human handoff and limits

1. Inspect the source passages and URLs, claim/implication citations, assumptions, and limitations.
2. If regulatory review applies, verify the regulatory sources, jurisdiction, and date. Resolve missing/conflicting evidence before approval.
3. Record the human reviewer, decision, and notes. Re-run review after any content or context change.
4. Keep checkpoint definitions and policy in Issue #56 / docs/human-checkpoint.md; hand the advisory integration to workflow Issue #78 and reviewer guidance to Issue #57. This bridge does not provide authenticated identity, immutable audit storage, legal clearance, or live model/API quality evidence.

## Offline tests

Run bridge regressions with no API key or network:

```bash
python -m unittest tests.test_research_review -v
```

The fakes verify the adapter contract only; they do not validate live regulatory evidence or research quality.
