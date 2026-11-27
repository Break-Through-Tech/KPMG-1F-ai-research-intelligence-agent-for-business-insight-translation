# Final corrective round: component-coverage retrieval and synthesis (plan for approval)

**Date:** 2026-11-25. **Status: plan only.**
- **Not done:** no live calls, no engine changes, no merges.
- **Done:** an offline investigation, 0 model calls. CPU retrieval only, on cached B2 rankings.
- **Code:** isolated in `experiments/retrieval-v3/`. The frozen engines and historical results are untouched.

## 1. What the offline experiment found

### Measurement

**Coverage metric:** a required point counts as *covered* when a complete anchor group for it is in the evidence packet. This is a proxy for answerability.

**Data:**
- 5 development sets: heldout-v1, completion-eval-v1, combined-v1, fresh-v2 and fresh-v3.
- 51 questions and 185 anchored points.

**Reconstruction check:** the offline rebuild of the frozen V2 Standard packet matches the saved live S2 packet **exactly on 8/8** fresh-v3 questions.

### Why evidence is missed (frozen V2 Standard, 43 missed points)

| Cause | Points | Meaning |
|---|---|---|
| Ranked 31–120 | 27 | In B2's candidate pool, but outside the 30-passage window |
| Ranked ≤ 30, cut by budget | 11 | Skip-fit ran out of the 6k budget |
| Not in the candidate pool | 5 | No route surfaces it |

**Root cause:** B2 builds the order from the whole question, plus at most 2 "facets" taken from a narrow split pattern (`, and what…` or `;`). Consultant questions have 4–6 asks, and fresh-v3 got 0–2 facets per question (J02, J04 and J05 got none). The middle asks therefore have no dedicated ranking, and their evidence sits at ranks 30–60.

**Not caused by:** query wording for the main subject (the papers are almost always found); table handling (the table-group logic works); or the gates (see §1.4).

### Policies compared

All use the same cached rankings and the frozen `select_grouped` and C2 conclusion logic, so only the candidate order and budget differ.

| Policy | Covered / 185 | Lost vs V2 | Tokens / q | Off-paper | Retrieval s / q | fresh-v3 |
|---|---|---|---|---|---|---|
| **P0: frozen V2 Standard (6k)** | 142 | — | 6,003 | 15% | 6.4 | 23/38 |
| P0 at 8k (budget only) | 153 | 0 | 7,634 | 18% | 6.4 | 25/38 |
| PS: earlier 3-part decomposition | 135 | 9 | 6,022 | 25% | 12.0 | 23/38 |
| PC: top-2 quota per component | 141 | 5 | 6,021 | 15% | 10.9 | 25/38 |
| FM: fusion, best component | 149 | 8 | 5,988 | 11% | 10.9 | 27/38 |
| **FA: fusion, mean over components (6k)** | **152** | 5 | 5,979 | **9%** | 10.9 | 24/38 |
| FA at 7k | 158 | 4 | 6,792 | 10% | 10.9 | 26/38 |
| **FA at 8k (window-bound, about 7.4k used)** | **162** | **3** | 7,416 | 11% | 10.9 | **28/38** |

**Pre-stated selection rule:** best total coverage with no set regressing. FA meets it; FM regresses completion-eval-v1. The rule was fixed before these two fusion variants were run, and nothing else was tuned.

**The prior approaches fail again**, as before:
- the decomposition re-run (PS) loses 9 points and adds off-paper noise;
- the simple per-component quota (PC) is flat.

**What works is fusion.** It generalises B2's own facet rule, `1/(20 + rank)`:
- from at most 2 facets to every component;
- every component search is paper-scoped to the original question's papers.

**FA at 6k:**
- +10 points;
- matches what a budget increase alone buys;
- with less off-paper evidence.

**FA at 8k:** +20 points (+10.8 pp of anchored points) and +5 on fresh-v3. 8k is the evidence budget V2 Deep already uses, so it is not a new bound.

### Synthesis side (saved S2 and D2 runs)

- **The gates withheld no items:** 0 across all 16 S2/D2 answers. The completeness lost with evidence present comes from drafting omissions, not from verification. **The gates stay exactly as they are.**
- **Evidence-limit statements were never published as limitations.** The review's `gap` sentence named the evidence limit correctly in 7 of 8 partial answers, for example "do not establish performance on the client's proprietary chemistry database". But it is published only as the uncited answer lead, so it scores at most 0.5 (J05.5, J06.4).
- **The draft omitted parts of asks whose evidence was present.** Examples: the band-gap condition in J01.2, the 10B/37 GB example in J07.4, and "learned affinities" in J02.2. No component of the question was checked.

## 2. Proposed change: one engine, "S3"

**S3 = V2 Standard + R (retrieval) + C (component-complete synthesis).**

**Unchanged:** verification, publication gates (P1–P5, V1–V5), numerical checks, citation protections, compact serialization, the ProviderGuard and the 2-call structure.

### R: component-fusion retrieval (no model calls)

1. **Components:** `components.py`, a deterministic split of the asks, at most 6. Each component query carries the question's named terms (MARASON, MedQA-CS…) and no business preamble.
2. **Searches:** one B2 search per component, run 3 at a time. Its results are restricted to papers in the original question's top-30.
3. **Fused order:** `1/(20 + r_original) + mean over components of 1/(20 + r_component)`. The original top-4 are always kept first.
4. **Selection:** the frozen `select_grouped` skip-fit over the top-30 of the fused order, at **8,000 passage tokens (hard cap)**. Whole table groups or incomplete-table notes, and C2 conclusions, are unchanged.
5. **Cost:**
   - Retrieval: +4.5 s per question sequentially, measured on cached timings; less when run in parallel.
   - Evidence: about +1.4k passage tokens per question. Estimated provider input is about +8–10% over S2, about 0.72 × S1, still under the frozen 0.80 × S1 bound. To be measured from receipts.

### C: component-complete synthesis (no extra calls)

1. **Input:** the same component list goes into the synthesis prompt as a checklist. The model must account for every component in a `component_map`, using exactly one of three statuses:

   | Status | Meaning | Required support |
   |---|---|---|
   | `answered` | Indices of published findings or limitations that answer it | Those items |
   | `not_retrieved` | Nothing in the supplied evidence addresses it | Uncited by design |
   | `not_established` | The study's own text shows it is outside its scope | A cited limitation, e.g. "evaluated only on our drug-screening database", "experiments on GPT-3.5" |

2. **Deterministic validator (no LLM):**
   - every component is mapped;
   - mapped indices exist and survived the gates;
   - a `not_established` item must pass every existing limitation gate (exact quote, number recall). If it fails, it is **downgraded to `not_retrieved`**, never published uncited.
   - A component claimed as `answered` whose items were all held is re-labelled `not_retrieved`.
3. **Rendering, so "not retrieved" and "not established" are never conflated:**
   - `not_established` becomes a normal cited limitation and counts toward evidence-limit points.
   - `not_retrieved` becomes a visible coverage note: "Not found in the retrieved evidence. This does not mean the paper does not report it." It is never a claim about the paper, and it carries no citation.
4. **Review gap:** the review still produces the gap. Uncited gap text stays as the answer lead, as now.
5. **Cost:** a few hundred more output tokens and no extra calls. The review call is unchanged apart from seeing the map.

## 3. Offline acceptance criteria (all must pass before any live call)

| # | Criterion | Target | Status |
|---|---|---|---|
| R1 | Anchored coverage on the 5 development sets | ≥ 157 / 185 (P0 + 15) and no set below P0 | measured: **162**; met |
| R2 | Crowding: points P0 covered that S3 loses | ≤ 3 | measured: **3**; met |
| R3 | Off-paper share of evidence | ≤ P0's 15% | measured: 11%; met |
| R4 | Evidence budget | every packet ≤ 8,000 passage tokens + C2 ≤ 800; serialized ≤ the 38k request-guard estimate | to verify per packet |
| R5 | Added retrieval latency | median ≤ +8 s per question (3 workers) | measured: +4.5 s sequential; met |
| C1 | Gates unchanged | publication, numeric-check and review modules byte-identical to V2 (hash list); all 90 V2 tests pass | to verify |
| C2 | Validator safety | Unit and adversarial fixtures: an uncited "the paper does not report X" is never published; `not_established` without an exact quote is downgraded; held items never count as answered | to build |
| C3 | Replay on saved S2 outputs | With no `component_map`, published output is identical to the saved S2 result (8/8) | to verify |

**What replay cannot show:** it validates only deterministic safeguards. **It is not evidence of live synthesis reliability.** That is judged only in §4.

## 4. Final live validation (one run, bounded)

### Fresh material

Development and evaluation are kept apart:
- **Development:** the five existing sets only. Nothing more is tuned on them after this plan.
- **Evaluation:** a new set, as follows.
  - 10 recently published arXiv papers outside the 100-paper corpus.
  - Collected with the existing `src.arxiv_collection` tool; download approval is needed.
  - Added to a **separate** validation bundle: demo-100 plus the new papers, so the existing distractors remain. The demo-100 index is not modified.
  - 10 questions, about 45 required points (1 point is about 2.2 pp). Authored from passages only, one independent AI key review, sealed before any engine sees them, and then your sign-off.
  - The questions follow the fresh-v3 style (multi-part, business framing, evidence-limit and misleading-evidence probes).
  - Points are atomic (one fact each), and every equivalent passage is listed as an alternative anchor.

### Arms and budget

| Arm | Why it is needed | Calls (expected / cap) |
|---|---|---|
| **S3** (candidate) | Tests both fixes against the absolute targets | 20 / 25 |
| **S2** (frozen V2 Standard) | Same-question control: attributes the gain, and is the fallback demo engine | 20 / 25 |
| **Total** | | **40 / 50, persistent ledger, retries included** |

**Not re-run:**
- **B0:** fresh-v3 already measured it at 46.1% against S2's 65.8%, with an execution failure.
- **S1:** superseded by S2 at equal score and 34% fewer tokens.
- **D2:** the planner added complete evidence for only 2 points; not adopted.

You can add **B0 (+20 calls)** if you want a same-set baseline in the delivery comparison.

**Execution:** one run per question, one resume, the 300 s timeout, and a memory guard as before. Scoring uses the same three safety passes (programmatic, a fresh blind Codex scorer, a Claude audit), with your adjudication final.

### Acceptance criteria for S3

| Criterion | Target | Change from fresh-v3 |
|---|---|---|
| Completeness | **≥ 80%** of points | kept |
| Safety | **0** citation-grounding failures, **0** misleading or fabricated claims, 100% exact quotes, 100% numerical correctness, **0 uncited "the paper does not…" statements** | kept, plus one rule |
| Improvement | S3 points ≥ S2 points + 2 on the same questions | replaces "≥ S1 (exact)" |
| Execution | 10/10 complete, ≥ 9/10 first pass | kept (scaled) |
| Latency (total, including failures) | median ≤ 120 s, p90 ≤ 180 s | kept |
| Tokens | S3 actual input ≤ 1.15 × S2 on the same questions | replaces "≤ 0.80 × S1" (S1 not run) |
| Fully answered | reported, **not gated** | **revision, needs your approval**: 0/8 for every arm on fresh-v3, because a single 0.5 blocks a full answer |
| Versus Baseline | carried over from fresh-v3 (S2 +19.7 pp), or measured if you add B0 | revision |

### Stopping conditions

1. **Before the live run:**
   - If any of R1–R5 or C1–C3 fails after implementation, stop, with no live calls and no redesign.
   - Then go straight to the delivery decision between S2 and B0.
2. **Fresh-set go/no-go:**
   - Before live runs, with the key sealed, compute offline anchored coverage for S2 and S3 on the fresh set. No code may change after this point.
   - If S3 coverage < S2 coverage, stop live testing of S3.
3. **During the live run:**
   - No code, prompt or threshold changes.
   - No reruns beyond the single resume.
   - No second validation.
4. **After scoring, whatever the outcome:** an evidence-based engine decision for the supervised demonstration, then integration.
   - **S3 qualifies:** S3 is the demo engine.
   - **S3 misses 80% but is safe and beats S2 by ≥ 2 points:** S3 is the demo engine, with its measured completeness disclosed.
   - **Otherwise:** S2.
   - **B0** is chosen only if both V2 engines fail safety.

## 5. Honest expectation

**Projection.** On fresh-v3, S2 converted about 80% of the evidence it had into points and earned about 43% partial credit where evidence was missing. The projection keeps the partial-credit rate and makes two assumptions:

| Variant | Assumptions | Projected score on fresh-v3 |
|---|---|---|
| R alone | 28/38 coverage, conversion unchanged | about 70% |
| R + C | C raises conversion to about 90%, and evidence-limit routing adds about 1 point | **about 80%** |

**What this means:**
- **80% is reachable, but with no margin.** One sample point is worth about 2.2 pp.
- **The improvements over S2 are likely**; the absolute 80% target is uncertain.
- **Some missing details are out of reach of any query** derived from the question wording: specific figures that rank 90–100 under every query. Those are residual losses that no bounded retrieval change fixes.

## 6. Scope and effort

| Item | Effort | Calls |
|---|---|---|
| R in `experiments/retrieval-v3` (a wrapper around frozen B2 and `select_grouped`) | small | 0 |
| C prompt, schema field and validator (copied V2 synthesis module plus validator; gates imported unchanged) | moderate | 0 |
| Tests, replay and hash checks | moderate | 0 |
| Fresh papers: collect, validation bundle and index (separate), key, review, seal | the largest item | 0 |
| Live validation | — | 40, cap 50 |

## Decisions needed from you

1. Approve S3 as specified, including the **8,000-token hard cap**: V2 Deep's existing budget, and window-bound at about 7.4k in practice.
2. Approve downloading about 10 new arXiv papers and building a separate validation bundle.
3. Approve the arms (S3 + S2; 40 calls, cap 50; optional B0 +20) and the revised criteria (fully-answered reported only; ≥ S2 + 2; tokens ≤ 1.15 × S2).

**Artifacts:** `components.py`, `rank_cache.py`, `analyze.py`, `coverage.json`, `cache/rankings.json`, `rank_cache.log`.
