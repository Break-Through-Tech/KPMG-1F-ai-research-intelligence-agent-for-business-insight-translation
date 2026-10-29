# Experimental indexed answer-quality check

For concise business advice, stage timings, the explicit lower-effort experiment,
and related papers, see [Latency and redundancy findings](answer-quality-latency-research.md).

The banking/multi-agent walkthrough showed a useful bounded answer, but research
interpretations repeated business recommendations and adjacent framing evidence
distracted from the architecture comparison. It did not establish banking benefits.

Run a separate local development mode:

```powershell
.\.venv\Scripts\python.exe -m src.research_demo --index data/chroma_db --codex-model gpt-6.1-sol --quality-check --port 8769
```

Use a configured account-accessible model. The mode also works with the existing
explicit `--configured-provider` route. It requires independent indexed queries;
it cannot be combined with `--clarification`, paper mode, or replay.

For business queries, synthesis is constrained to findings; interpretations and
pilot advice belong in the business stage. A separate structured model call
assesses each draft claim against the question and full supplied passages for
support and direct relevance. Every claim needs exactly one decision. Rejected
claims remain in `summary.quality_review.original_claims` with decisions/reasons.
They are omitted from displayed findings and from business-stage inputs.
Business receives only retained findings and the passages those findings cite.
The original retrieved evidence remains intact for inspection and diagnostics.

Partial coverage adds a short `answer_lead`, displayed before findings and retained
in limitations for exports. It describes missing evidence in the supplied passages,
not an absence throughout the literature. An all-rejected draft abstains and skips
business generation. Review provider/schema failures remain execution failures;
they never masquerade as evidence absence. No automatic retry or fallback is added.

This adds one model call after a successful summary. Empty retrieval and an
already-abstaining draft skip that call. The reviewer uses the same configured
provider/model: it is not an independent human or a semantic correctness oracle.
It can miss errors or reject useful findings. Existing exact-quote checks remain;
approval remains pending. Business actions remain proposed inferences, not proven
results. This change does not establish their semantic correctness.

Provenance records the review policy/prompt hash and relevant implementation
hashes, because a Git commit alone does not identify local edits. Quality-check
configuration participates in the indexed context identity and result fingerprint.
Retrieval defaults, corpus, embeddings, and ranking are unchanged. New startup
flags are opt-in; existing servers need restarting to load changes.

## Development comparison

Capture a successful unmodified indexed result as a private JSON envelope. Then:

```powershell
.\.venv\Scripts\python.exe -m evaluation.check_answer_quality_dev --baseline data/processed/answer-quality-dev/before.json --output data/processed/answer-quality-dev/new-run --model gpt-6.1-sol
```

The harness freezes the evidence from the baseline, records case expectations
before generation, and checkpoints outputs/failures and provider receipts in a
new directory. It includes the banking question, an answerable architecture
control, and an unrelated wheat-yield control. This isolates generation behavior;
it does not measure retrieval recall or generalization. Cases are development
probes, not held-out benchmarks, and repeated runs are retained separately.

Inspect support, relevance, hedges, adverse results, transferred assumptions, and
rejected claims against original passages. Do not count valid JSON, model approval,
or more abstentions as accuracy. Use independent human labels and a predeclared
held-out set before making broader accuracy claims or promoting this mode.

Offline tests cover complete review decisions, invalid/duplicate decisions,
support/relevance filtering, findings-only schema, preserved audit/evidence,
business input filtering, abstention, and failure-stage behavior. These scripted
checks establish transport and boundaries, not semantic quality.

## Recorded development observations — October 28, 2026

Local `data/processed/answer-quality-dev/` retains the actual baseline envelope,
two separate frozen runs, and provider receipts. These artifacts contain research
text/results and are intentionally outside the tracked source diff.

- First run: the banking answer retained relevant findings and separate advice;
  both controls behaved as expected. Its coverage warning was overly long and
  reintroduced adjacent framing material. That output is retained in `frozen-v1`.
- Bounded revision: require a gap of at most 300 characters containing missing
  setting/comparison/results only. The new `frozen-v2` run retained two architecture
  findings, led with absent banking-specific comparative/pilot evidence, and gave
  one conditional pilot proposal. It did not present framing findings as evidence
  of an architecture advantage.
- The supported control retained both the single-agent-over-Swarm finding and the
  orchestrated-system finding; the unrelated wheat-yield control abstained.
- A final HTTP request through the restarted quality-check server completed with
  `scenario=full`, two research findings, `answer_scope=partial`, an explicit
  banking-evidence gap, and successful business translation (`live-final.json`).
- All 88 focused synthesis/indexed/HTTP/clarification/business/provider regression
  tests passed. JavaScript syntax and diff whitespace checks passed. Initial HTTP
  tests failed only because the restricted execution sandbox denied localhost;
  they passed when run with localhost access.

These observations were inspected by the coding assistant, not independently
human-labeled. No held-out accuracy percentage, retrieval improvement, model
entailment certification, broad regression guarantee, or stakeholder approval is
claimed. Added provider calls increase latency and use subscription/provider quota.
