# Human-in-the-loop checkpoint

Run `notebooks/Human_in_Loop_Checkpoint.ipynb` with the repository's Python environment.
Install `requirements.txt`, copy `.env.example` to `.env`, and set `GOOGLE_API_KEY`.
The notebook explicitly creates a `google.genai.Client`; both retrieval and assessment
use its supported `client.models.generate_content` interface. No separate,
undefined `validator_model` is needed. Do not commit keys or private notebook output.

## Flow and limits

1. Supply the upstream `industry`, proposed `insight`, and deployment `jurisdiction`.
2. Search for regulatory evidence using Gemini's Google Search grounding tool.
   Preserve only segments with traceable Search source IDs, titles, and HTTPS URLs.
   An ungrounded response stops the flow; model recollection is not retrieval.
3. Use a separate structured-output call to assess regulatory compliance, legal
   constraints, governance, operational feasibility, and risks against that evidence.
4. A human opens the cited URLs and verifies authority, dates, applicability, and
   the business facts. Record `approve`, `revise`, or `reject` with reviewer and notes.

Search grounding does not guarantee official, complete, or current regulations.
It returns cited model-generated segments, not independently downloaded legal text.
The reviewer must check the actual sources, including any Search redirect URLs.
Regulatory permission alone cannot establish operational feasibility or the scientific
correctness of an insight. Missing evidence is `unknown`, not an assumed pass. This
standalone prototype is not yet wired to arXiv search or an insight generator and
does not provide authenticated review, immutable audit storage, or legal clearance.

## Output contract (`schema_version: "1.0"`)

| Field | Format / meaning |
| --- | --- |
| `industry`, `insight`, `jurisdiction` | Input strings |
| `as_of` | ISO date requested for retrieval (defaults to today); not proof of currency |
| `sources` | Objects containing integer `source_id`, `title`, and `url` |
| `evidence` | Cited segments containing `text` and `source_ids` |
| `assessment.verdict` | `potentially_feasible`, `conflicts`, or `insufficient_evidence` |
| `assessment.summary` | Advisory explanation |
| `assessment.regulatory_compliance`, `legal_constraints`, `governance`, `operational_feasibility` | Each has `status`, `explanation`, and `source_ids` |
| Finding `status` | `supported`, `conflicts`, `unknown`, or `not_applicable` |
| `assessment.risks` | List of risk strings |
| `human_review` | Initially `{ "status": "pending", "reviewer": null, "notes": null }`; after review, status is `approve`, `revise`, or `reject` |
| `approved` | Initially `false`; only explicit human approval can set it to `true` |

All non-unknown findings need citations to existing source IDs. A conflict takes
precedence; otherwise any unknown finding requires `insufficient_evidence`.
A verdict inconsistent with the findings is rejected. Conflicting or insufficient
assessments cannot be approved: gather evidence or revise and reassess first.
`record_human_review` returns a copy, leaving the pending checkpoint unchanged.
Downstream execution must use the reviewed result and require `approved is True`.

## Troubleshooting and verification

- Missing key: fill in your local `.env`; the helper fails before creating a client.
- HTTP 403/404: check key permissions and `GOOGLE_MODEL` availability for your account.
- HTTP 429: check account quota/billing; do not retry indefinitely.
- Missing Search evidence: do not substitute plain generated text. Verify model/tool
  access or retrieve authoritative evidence manually before resuming assessment.
- Invalid JSON, citations, or verdict: stop and inspect the response; do not approve.
- Unknown operational feasibility: provide applicable business evidence in a future
  integration or keep the result unresolved; regulations alone may be insufficient.

Offline checks (no API key, quota, or model downloads required by the checkpoint tests):

```bash
python -m unittest discover -s tests -p 'test_human_checkpoint.py' -v
```

Run the complete suite after installing the repository dependencies:

```bash
python -m unittest discover -s tests -v
```

Mocks check SDK request configuration, citations, structured validation, and review
gates. They do not establish live API access or the quality of regulatory advice.
