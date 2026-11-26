# Optimized S2-R2: duplicate original search removed

**Date:** 2026-11-26.

**Branch:** `exp/s2-r2-opt`, one commit on top of the validated reference `1d0e0ae` (`exp/s2-r2-fusion`). The reference branch is unchanged.

## Change

**New file:** `s2_r2_opt.py`, `S2R2OptResearch(S2R2Research)`. It overrides only `r2_packet`.

**What it does:**
- The original-question B2 search runs **once** per request.
- Its result is reused for paper resolution, the B1 route and the fusion route.
- The reuse goes through a memo scoped to one `r2_packet` call, keyed by (query, depth).

**What it does not do:** keep a global cache or any cross-request or cross-user state. A test checks this.

**Unchanged:**
- all validated files, including `s2_r2.py`, `s3_evidence.py`, `paper_balance.py` and the frozen V2 modules;
- evidence selection, ranking weights, budgets, generation, review and gates.

## Offline verification (0 LLM calls; `verify_r2_opt.py`, `r2-opt-verification.json`)

**Identity:**
- **61 of 61** development and fresh-v4 questions produce **byte-identical** evidence packets: passages, order, chunk IDs, notes, tokens and route.
- **8 of 8** unseen questions are byte-identical under real, uncached retrieval.

**Measured retrieval:** real B2 on the validation index, 8 unseen questions, live parallel setting, order alternated.

| | Validated R2 | Optimized R2 | Change |
|---|---|---|---|
| Median retrieval wall time | 25.0 s | **15.3 s** | **−39%** |
| Total retrieval wall time | 185.9 s | 112.8 s | −39% |
| Total process CPU time | 882.2 s | 555.7 s | −37% |
| B2 searches | 33 | 25 | −8 (one per question) |

**Per route:**
- **B1 questions (U1–U3):** 1 search instead of 2; retrieval wall time roughly halved (for example U1: 25.7 s to 13.0 s).
- **Fusion questions:** 1 fewer search; −3 to −11 s.

**Searches across all 61 cached questions:** 271 to 210.

**Note:** the component searches still run in 3 threads that give no speed-up on this CPU (measured earlier). This was left unchanged on purpose: it is out of scope, and removing the threads would not change wall time.

## Tests and seals

- **New:** `test_s2_r2_opt.py`, 5 tests. They check byte-identical packets and exactly one search saved for simple, named cross-paper and multi-part questions; that no query is searched twice; parallel and sequential runs are identical; and no state is carried across requests.
- **All suites pass:** 64 retrieval-v3 tests (R2-opt 5, R2 8, B1 11, S3 40), plus test_v2, test_consolidated and test_runner.
- **All frozen seals verify:** `s3-freeze.json`, `b1-freeze.json`, and the unseen-r2 `code-freeze.json` and `seal.json`. **The validated code is untouched.**

## Integration (for Laptop Claude; not deployed by me)

| Item | Detail |
|---|---|
| Construct | `S2R2OptResearch(retrieval_strategy='r2', ranked=..., count=..., tables=..., generate=..., v2=..., gate=..., rows=...)` |
| Evaluated configuration | Exactly the validated S2-R2 behaviour (unseen: 29.5/36 vs S2 25.0/36), with lower retrieval latency |
| Dependencies | none new. Same B2 index, models and budget |
| Default | keep frozen S2. Expose R2 behind a flag (`retrieval_strategy`) |
| Rollback | use `S2R2Research` (validated, `1d0e0ae`), or `retrieval_strategy='s2'` for exactly frozen S2 |
| Live validation | none required for this change: outputs are byte-identical, and only latency is affected |

**Also included, for future work only:**
- `GENERATION-DIAGNOSIS.md`: the reviewer-completion proposal. It is preserved but not implemented.
- `R2-RETRIEVAL-BOTTLENECK.md`: the analysis showing that retrieval coverage tuning is stopped.
