# combined-v1: evidence budget + verification repair. Staged implementation and validation plan (DRAFT, not approved)

**Status:** this is a plan only. No code beyond what already exists. No live calls, no shared-app changes, no merges or deployment.

**Inputs:**
- automated reviewer retrieval handoff (`b2-adaptive-handoff.md`, development set C01–C15), which reports exact evidence points out of 41:

  | Evidence budget | Points / 41 |
  |---|---|
  | Top-8 (current) | 22 |
  | Top-16 | 31 |
  | 6k skip-fit | 34 |
  | 8k prefix | 37 |

  Adaptive policies were deferred.
- `verification-repair/FINDINGS.md`: `numeric_checks_v2` and `interpretation_gate`, with 10 false rejections released on development data and 0 new holds.

**Controls:** the original Baseline/B2 (top-8, `quality_check=True`) and the original Multi-Agent (frozen number check, interpretation policy, top-8 per search, 14 merged passages). Neither engine is modified. Every new behaviour is opt-in, in `experiments/`.

## 1. What is NOT repeated

The following are settled and will not be re-evaluated:

- F01–F10, H01–H10 and C01–C15 live runs. These sets are development data now.
- Question decomposition: 0 gain on the held-out set.
- The completion pass, which was abandoned.
- Table comparisons for Baseline: no evidence change.
- The handoff Multi-Agent: no benefit.
- Adaptive depth (complexity, facet/paper, score-gap): unreliable; deferred by automated reviewer.
- Fixed-30 and 8k prefix: offline recall references only, because of the token cost.
- Scope review: superseded.

Reused as is:

- completion-eval-v1 scoring rules: 1 / 0.5 / 0 per point, published vs inferred, the added-claim audit.
- The automated reviewer runner safeguards: persistent call caps, resume, fatal-error stops, the 6 GB commit preflight, seals.
- automated reviewer’s offline packet-coverage harness.
- `replay.py`.

## 2. Components to build (offline, before any live approval)

| # | Component | Location | Notes |
|---|---|---|---|
| C1 | **Evidence-budget module**: `select(ranked_parents, policy)` with `fixed(k)` and `skip_fit(tokens, window=30)` | `experiments/evidence-budget/evidence_budget.py` | Shared by both engines. Whole parent rows only, original B2 order, original chunk IDs. No text edits. The token budget counts the **serialized provider payload** (passages + metadata + prompt + output reserve) with a bounded estimator, and fails closed if it is over the cap |
| C2 | **Window-30 ranking adapter** | same folder | Calls the existing `FacetRetriever.rank_facets` + `resolve` to get the first 30. The adapter is needed because `open_b2.retrieve` caps top_k at 20; `src` stays unchanged. Test: its first 20 equal `retrieve(q, 20)` exactly |
| C3 | **Baseline arms** | new `VARIANTS` entries in `codex_baseline.py` | Same `create_research`, `quality_check=True` and 2 calls per question. Only the evidence policy changes |
| C4 | **Multi-Agent arms** | `codex_multiagent.py` options | Three switches: number check (frozen / v2), interpretation handling (policy / gate), initial evidence policy (top-8 / chosen budget). Following automated reviewer’s advice, the budget applies to the **initial search only**. Sub-searches stay at top-8. The merged cap becomes token-bounded through C1 (initial packet kept whole, then sub-search additions until the cap) |
| C5 | Gate publication field | `interpretation_gate.py` + envelope | Gated interpretations go to a separate labelled `interpretations` list, never into `claims` |
| C6 | Fresh question set and answer key | `experiments/combined-v1/` | See section 3 |

C1, C2 and C4 each get offline tests: payload cap, order preservation, no split rows, window equality, a scripted-adapter run of every arm, resume, and caps. The full frozen suite (206) and the verification-repair suites (30) must stay green.

**Safeguards unchanged in every arm:**

- exact-quote citation validation;
- number grounding of values, units, signs, attribution, conditions, qualifiers and direction (v2 changes parsing only);
- statistical-report rule;
- quote grounding;
- the verifier veto.

## 3. Fresh question set (fresh-business-v1)

- **16 consultant-framed questions**, 4 of each type:
  - single-paper;
  - multi-paper comparison;
  - numerical/table;
  - **insufficient evidence**: a part the corpus cannot answer, which tests honest abstention under larger packets.
- **No overlap:** no question reuses an anchor passage from F, H or C. An OVERLAP.md check, as before.
- The key is drafted with AI assistance from full passages: about 40–45 required points, with anchors.
- **automated reviewer independently reviews** every point and anchor.
- **Human sign-off** is required before sealing.
- The set is sealed (SHA-256) before any packet or answer is seen.

## 4. Testing sequence

### Stage 0: offline, 0 model calls

1. Build C1–C6 and run the tests.
2. Run packet coverage on the fresh set for every retrieval arm with automated reviewer’s harness: top-8, top-16, 6k skip-fit (and 8k prefix as a reference only). Report:
   - exact anchor points;
   - premature stops;
   - near-duplicates;
   - split table pairs;
   - p50/p90 payload tokens.
3. Check the real provider payload of each arm against the cap. The cap is 24k input tokens per call for Baseline and 30k for a Multi-Agent synthesis call; an arm over it is not run.
4. **Pruning rule (pre-registered):**
   - If offline coverage for 6k skip-fit is less than 2 points above top-16, **drop B2** and validate top-16 only. Top-16 is simpler and within the current API limit.
   - If both are within 1 point of top-8, stop. Retrieval budget is not the bottleneck on fresh data.

**Gate G0:** set sealed, tests green, payloads within caps, and the user approves Stage 1.

### Stage 1: Baseline, live (the user runs the commands)

| Arm | Evidence | Purpose |
|---|---|---|
| B0 | top-8 (control) | Fresh-set reference |
| B1 | top-16 | Fixed budget |
| B2 | 6k skip-fit, window 30 | Token budget, only if kept by the Stage 0 rule |

Result: **the chosen evidence budget E\*** (decision rule in section 6). Stage 2 uses E\*.

### Stage 2: Multi-Agent, live, then offline replay

| Arm | Evidence | Verification | How it is run |
|---|---|---|---|
| M0 | top-8 | frozen + policy (control) | live |
| M1 | E\* initial | frozen + policy | live |
| M3 | E\* initial | v2 + gate | live |
| M2 | top-8 | v2 + gate | **offline replay of M0** (0 calls) |
| M3′ | E\* initial | v2 + gate | **offline replay of M1** (0 calls), used to cross-check M3 |

The verifier prompt is unchanged, so verification changes are deterministic and replayable from saved verdicts. Replay is exact for first-round decisions. Where the frozen decision triggered a targeted round that v2 would not (or vice versa), that question is flagged and reported separately; the live M3 is the authority there.

**Contributions:**

| Effect | Computed as |
|---|---|
| Retrieval | M1 − M0 |
| Verification | M2 − M0, and M3′ − M1 |
| Combined | M3 − M0 |
| Interaction | (M3 − M1) − (M2 − M0) |

### Stage 3: review, 0 calls

- Points are scored against the sealed key. **automated reviewer independently re-scores** every arm, blind to arm labels.
- **Disagreements** go to the human.
- **Released-claim audit:** every claim that v2 accepted and the frozen check would have held (taken from replay) is individually checked for attribution, conditions and qualifiers.
- **Interpretation audit:** every gated interpretation is checked by hand.

## 5. Model-call and token budget (hard caps, persistent in `calls.sqlite3`)

| Stage | Arms | Expected calls | Hard cap |
|---|---|---|---|
| 1 | B0, B1, (B2) | 2 per question: 64–96 | **100** |
| 2 | M0, M1, M3 | about 3.3 per question: about 160 | **240** (5 per question per arm) |
| 2 | M2, M3′ replay | 0 | 0 |
| **Total** | | **about 225–255** | **340** |

- **Resume:** each arm may be resumed once for execution errors, within its cap. There are no re-runs for any other reason.
- **Tokens (estimate):**

  | Arm | Input tokens per call |
  |---|---|
  | B0 | about 18k |
  | B1 | about 20k |
  | B2 | about 22k |
  | Multi-Agent synthesis and verification | about 22–28k |

  Total about 5–6M input tokens and 60–80k output.
- **Model and safeguards:** gpt-6.1-sol at low effort, through the ChatGPT automated reviewer login only. Stops on login, quota, rate-limit, budget or memory errors. The 6 GB free-commit preflight applies.

## 6. Acceptance criteria (frozen before Stage 1; P = total required points)

**Safety gates for every candidate (any failure rejects the candidate):**

- 0 unsupported or misleading published claims;
- 100% of quotes exact;
- every v2-released claim correct on attribution, conditions and qualifiers;
- 0 unsupported recommendations among published interpretations;
- on insufficient-evidence questions: no fabricated answer to the unanswerable part, and an abstention or gap statement at least as often as the control.

**Improved Baseline (choosing E\*):**

1. Points ≥ B0 + max(3, 0.08·P).
2. Fully answered questions ≥ B0.
3. Median ≤ 1.5 × B0 and p90 ≤ 120 s.
4. Input tokens per question ≤ 2 × B0.
5. **B2 is chosen over B1 only if it scores ≥ 2 points more** with equal safety. Otherwise top-16, which is simpler and within the existing API limit.
6. If neither arm meets criteria 1–4, Baseline stays at top-8.

**Improved Multi-Agent (M3) as an optional Deep Research mode:**

1. Points ≥ improved-Baseline score + max(4, 0.10·P), with improved Baseline being B\* (or B0 if no arm qualified).
2. More fully answered questions than B\*.
3. Median ≤ 120 s, p90 ≤ 300 s.
4. At most 1 execution error after one resume.

Baseline remains the default regardless.

**Component adoption (kept even if M3 does not qualify):**

- **v2 + gate** is adopted as Multi-Agent's verifier fix if:
  - the false-rejection rate (source-supported held claims ÷ drafted claims) falls versus the control;
  - it passes the safety gates;
  - it makes 0 new holds of claims the frozen check accepted.
- **E\*** is adopted for Baseline by the Baseline rule above.

**Interpretation:** with 16 questions, differences of 1–3 points are within noise. The thresholds above are minimum effects, not significance tests. Safety gates are absolute.

## 7. After the results (separate approvals)

- Integrating E\* into the app is a separate change: an opt-in config, then the default. This needs a reviewed opt-in path if E\* needs window 30, because the current API limit is top_k 20.
- Multi-Agent stays experimental unless criterion M3 is met.
- Not in scope: grouping indivisible table pairs before packing (automated reviewer’s follow-up), adaptive depth, repair or rewrite loops, larger-library scaling.

## 8. Approvals needed, in order

1. This plan, including the caps and criteria.
2. Answer-key sign-off, by a human after automated reviewer review.
3. Stage 1 live runs, which the user launches.
4. Stage 2 live runs, which the user launches.
