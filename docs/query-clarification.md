# Opt-in query clarification (backend and local UI)

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

The standalone backend does not provide index identity or an HTTP/UI host. The
opt-in host below supplies those integration seams, with separate proof limits;
neither component establishes stakeholder acceptance or model semantic quality.

## Indexed research desk integration (stacked on #155)

The optional host is now wired with `--index ... --clarification`, using the same
explicit `--codex-model`/`--codex-bin` or `--configured-provider` routes documented
in `docs/local-research-interface.md`. Defaults do not change: indexed mode without
this flag keeps independent questions; single-paper and fixture modes are unchanged.

```sh
python -m src.research_demo --index /absolute/path/to/data/chroma_db \
  --clarification --codex-model YOUR_CONFIGURED_MODEL \
  --codex-bin /absolute/path/to/compatible/codex
```

Each tab's configuration request creates an opaque conversation token. State stays
in the local Python host: no client-supplied history, cookie, persistent session
store, or browser local-storage transcript. Completed turns are bounded by the
existing `ClarifyingResearch` contract. Index/config/provider identity is checked
before work, after research, and after optional business translation. The host
serializes generation; a short separate lock guards session allocation and expiry.
Sessions expire after 30 idle minutes, maximum 32 retained sessions. Running sessions
are not expired/evicted. Capacity exhaustion is explicit, not silent eviction of
someone else's pending question. Restarting loses all sessions.

The UI renders a clarification question with **no completed draft**, using the
B+C layout: a contained decision card in the conversation and a **Why these options?**
evidence rail alongside it. The card has native radio choices, an optional own-answer
field, and **Submit answer**. Selecting a choice does not submit. Typing an own answer
clears the selection; Ctrl/Command+Enter submits, native radio arrow keys navigate,
and number keys outside the text field select an option. Nothing is selected by default.

When source support exists, the rail opens with exact quotes, source identity and
links. It can be closed and reopened from the card. On narrow screens clarification
support is a non-modal section below the conversation, so it never blocks answering.
Normal answer citations retain their existing mobile modal drawer. Questions without
support do not open an evidence rail. After completion or a new conversation, the
question and collapsed source support remain inspectable in the transcript.

Submitting resumes the original request with its original industry context and
fresh retrieval. Industry controls, entry preferences and research-only hints are
hidden while answering; industry is disabled until completion or a new conversation.
Failed submissions keep the answer editable and retryable. Completion restores the
normal research composer and its focus. Up to three exchanges are permitted by the
backend; after its limit, start a new research conversation.

“New research conversation” creates clean server-owned intent state. Previous answers
remain on screen but are not supplied to the new session. Old pending choices and
failed-request retry controls cannot submit into a different conversation. Provider
failure keeps pending state retryable and shows a failed stage; it is not relabeled
as insufficient evidence. Expired/mismatched sessions prompt new-conversation/reload.
The UI allows up to 21 minutes for the configured sequential clarification/synthesis/
business calls; it does not switch providers or bypass a running request lock.

### Proof boundaries

Session/HTTP tests and Chrome desktop/mobile checks use deterministic synthetic
**development** adapters: pending/no-draft, editable and open-ended choices, source
support, resume, provider failure/retry, tab isolation, clean sessions, expiry/capacity,
and stale index rejection. These do not establish semantic decision accuracy,
trained-model performance, real-provider latency, or stakeholder acceptance.
The real-provider execution blocker documented in #155 still applies. No auth or
user config was changed to bypass the adapter's isolation requirements.
