# Opt-in query clarification (draft backend)

Inspired by [A Small Model Asks Better](https://arxiv.org/html/2610.28686v1)
and [ClariEdge](https://huggingface.co/datasets/ibm-research/ClariEdge). This
implements the two-check architecture with a prompted baseline, not the paper's
trained model or a reproduction of its reported accuracy. No dataset is downloaded.

## Scope

`ClarifyingResearch` is an opt-in in-process wrapper around `run_research`:

Question + bounded history → pre-check → retrieval → post-check → existing
synthesis / optional business translation → pending, unapproved draft.

`clarification_required` is an envelope with `result=None`, never a finding or
an `insufficient_evidence` research result. A clear query with empty retrieval
skips the post-check and generation, returning the existing insufficient-evidence
result. Nonempty but irrelevant evidence proceeds to synthesis for abstention.
Provider/contract failures raise sanitized stage-specific errors, never a
clarification or a previous answer. Existing CLI/UI defaults remain unchanged.

## Integration

```python
from functools import partial
from src.query_clarification import ClarifyingResearch, clarification_with_generation
from src.research_chat import synthesize

# generate/metadata: explicitly configured existing generation adapter.
# retrieve(query, top_k): existing index retrieval/ranking adapter.
session = ClarifyingResearch(
    context_id=active_context_identity,
    clarify_fn=partial(clarification_with_generation, generate=generate),
    retrieve=retrieve,
    summarize_fn=partial(synthesize, generate=generate),
    provenance={"generation": metadata},
)
response = session.ask({"query": "What are its limitations?"},
                       context_id=active_context_identity)
if response["status"] == "clarification_required":
    # Render response['clarification']['question'] and optional cited options.
    # On a later user answer, use the SAME session and original context:
    response = session.resume("Granite", context_id=active_context_identity)
```

The hosting application owns **one instance per conversation**, serialized access,
and lifecycle. It must calculate context identity from the active mode, index and
collection, available corpus identity, retrieval/ranking configuration, and provider/
model settings. A file hash alone is not indexed-corpus identity. Recreate the
instance on any change; do not reuse a stale identity, share between users, accept
client-owned history, or serialize arbitrary client-supplied session objects.
No distributed/persistent session store or index identity discovery is provided.

History is server-owned: at most six complete turns, 6000 characters/message and
24000 total, evicting oldest pairs. Long summaries are truncated for intent context;
full findings stay in results. Original questions, clarification answers, resolved
queries, decisions and used history are retained in fingerprinted provenance.
History only resolves intent; it never enters retrieved evidence. The pre-check's
resolved query drives retrieval and synthesis; post-check cannot silently rewrite
it after retrieval. Reviewers should inspect intent rewrites as well as findings.

Resume reruns both checks and retrieval, rather than reusing stale passages. Up to
three clarification exchanges are allowed. Each original question and answer is
bounded to 6000 characters; the internal intent input (including ordered option
text) is bounded to 60000 characters and serialized without ASCII expansion.
Resolved queries remain bounded to 6000 characters and are stored before optional
exchange detail in completed history. After a limit error, create a new session with an
explicit question. Retryable failures preserve the pending clarification. Starting
a fresh session also abandons pending state. Caller must not render old answers
as results of failed operations.

Document-derived options require supplied chunk IDs and exact supporting quote
membership (whitespace normalized). This is NOT proof that an option or question
is semantically justified. Open-ended questions can have no options. Optional
business translation uses the existing explicit industry requirement and contracts.

## Development evaluation

Eight synthetic development cases cover ambiguity, context-resolvable hard
negatives, clear questions, and missing evidence before/after retrieval. They are
not held-out data, real paper findings, or an evaluation of generated answers.

```sh
python -m pytest tests/test_query_clarification.py
# Uses only the explicitly configured existing provider; may incur its usual cost:
python scripts/evaluate_clarification.py --configured-provider > /tmp/clarification-dev.json
# Alternatively, existing subscription-backed text-only experimental adapter:
python scripts/evaluate_clarification.py --codex-model YOUR_CONFIGURED_MODEL > /tmp/clarification-dev.json
```

The report separates adapter errors, unnecessary questions, missed ambiguities,
correct decisions, and per-case latency. Errors count as incorrect, never silently
disappear from the total. It retains generated questions/options for human review;
it does not score their semantic quality. No model evaluation has been run for this
draft. Next: independently label BTT held-out cases; compare configured baseline
against a small LoRA using separate training data; assess option grounding and
final-answer quality with human/source review, alongside latency and abstention.

This is backend groundwork related to #130, not completion of its persistent-index
UI, corpus identity, real-index walkthrough, browser proof, or stakeholder criteria.
