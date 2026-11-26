# Responses to the automated reviewer audits

All changes are uncommitted on `khoi/research-evidence-integration` (HEAD `9994eed`), are model-free, and are limited
to `experiments/` and `ui-consult/`. Nothing in `src/`, `tests/` or `ui/`, the shared backend or the provider
defaults changed. No provider call was made.

**Status: ready for a automated reviewer spot-check of the audit #5 fix. Not production-ready. The live A/B waits for that clearance.**

# Audit #5 (2026-11-19): narrow numeric fix + ledger hardening

Audit #5 (a read-only self-audit with fresh probes; not independent) found that HIGH 2 was only partly fixed. The
**setting** and **conditions** of a number were still read across its whole sentence or quote, not from its own
mention. Only `experiments/agentic/numeric_checks.py` changed for the numeric fix. The agents, retry, dashboard and
call-budget infrastructure are unchanged.

| Case | Before (reproduced) | After |
|---|---|---|
| Source "Model X reached 78% accuracy on the benchmark and 64% accuracy in hospitals." Claim "Model X reached 78% accuracy in hospitals." | **grounded** (78% borrowed "hospitals" from the 64% clause) | **contradicted** (`setting_transfer`); held end to end with a permissive verifier |
| Same source. Claim "Model X reached 64% accuracy in hospitals." (valid) | uncertain (`subject_unconfirmed`) | **grounded** (the elliptical clause inherits Model X) |
| Same source. Claim "64% on the benchmark" | grounded | **contradicted** (`setting_mismatch`, the reverse direction) |
| Source "Model X reached 78% accuracy overall and 90% only on English tasks." Claim "78% overall." (valid) | **contradicted** (`missing_condition`: the 90%'s condition was applied to the 78%) | **grounded** |
| Same source. "90% overall" / "90% only on English tasks" / "90% only on Spanish tasks" | contradicted / contradicted (`subject_mismatch` via "English") / contradicted | **contradicted** (`missing_condition`) / **grounded** / **contradicted** (`changed_condition`) |

**How (per mention, not by cutting at every conjunction):** `_scope` gives each number its own clause plus only clearly shared context.
- A number-free clause before the first number ("On the benchmark, …", "Only on English tasks, …") applies to every number.
- A number-free clause after the last number applies when the sentence has one number. With several numbers its scope is ambiguous, and the result is **uncertain** (`condition_scope_unconfirmed` / `setting_unconfirmed`), never invented support or a false rejection.
- An elliptical clause ("…and 64% accuracy in hospitals") inherits the earlier **subject** only. A clause with its own noun phrase ("while the baseline reached 60%") does not.
- Conditions are judged against the matched source number. The old quote-wide condition check now runs only for claims without numbers.
- A comma inside a number ("1,240") is no longer a clause break.
- All previously passing sign, negation, population, unit-conversion and paraphrase cases still pass.

**Ledger hardening (secondary):** `ab_profile.AUTHORIZATIONS['automated reviewer-laptop-40']['experiments'] = ('ab-agentic-1',)`.
- `CallLedger` and the launcher refuse any other experiment name on a ledger built from the approved seed, such as `AB-AGENTIC-1`, `ab_agentic_1` or `ab-agentic-2`, before anything is written. Previously, a lookalike could lock the approved ledger before the first profile run.
- Use without an experiment, the 40-call total, the 14-call cap and the 20 historical records are unchanged.
- A future, separately approved purpose is added to that list deliberately.

### Tests (model-free, fake providers only)

| Suite | Result |
|---|---|
| `agentic/test_audit5.py` (new) | 2 tests × 16 paired cases each: code status, and end to end with a permissive verifier (uncertain cases are flagged for a person) |
| `table-endpoint/test_ab_profile.py` | 19/19. Adds the lookalike-name test. Two assertions are updated for the new rule: a rename is refused as "locked or not approved", and after close the remaining 6 calls are spent without an experiment because an unlisted name is refused. |
| `test_agentic`, `test_integration`, `test_adversarial`, `test_audit2`, `test_audit3`, `test_audit4` | 33/33, 34/34, 44/44, 16/16, 9/9, 9/9 (unchanged expectations) |
| `test_call_ledger` | 16/16 |
| Chart-first, evidence tables (423 verified), proxy | 13/13, 21/21, 10/10 with the local fixtures |
| Audit #5 probe set (22 numeric and 6 premise cases, outside the repo) | All pass |
| Baseline `tests/` | Not re-run in this pass (`src/` and `tests/` are untouched). Audit #5 showed the same intermittent WinError 10053 failures in the untouched baseline export. |

### Real ledger (read-only)

Bytes unchanged. Integrity `ok`, 40 authorized, **20 used** (19 completed, 1 failed), 20 remaining, **no experiment lock**, no caps, nothing closed.

# Audit #4 (2026-11-19): 2 HIGH + 1 MEDIUM, narrow remediation

Modules automated reviewer verified were left unchanged: architecture, retries, charts, UI, saved briefs and review workflow.
Each probe was reproduced first with `scratchpad/probes/repro_audit4.py` (outside the repo; disposable ledgers only;
real ledger read-only), and the script was re-run after the fixes.

| Finding | Original probe (before) | Fix | After | Regressions |
|---|---|---|---|---|
| **HIGH 1:** a second ledger initialized from the approved seed got its own 14-call allocation | 2 databases from the same seed: **28** A/B reservations; the profile check **accepted** the second database | **One authoritative ledger** (`ab_profile.AUTHORIZATIONS['automated reviewer-laptop-40']`): the canonical path `D:/KPMG-demo-corpus/table-endpoint-exp/automated reviewer-authorization-40.ledger.sqlite3`, plus the seed SHA-256, plus its `created_at` identity. (1) `call_ledger.init` refuses the approved seed anywhere, because its one ledger exists: no duplicate initialization. (2) `CallLedger` refuses to register or use `ab-agentic-1` in any file whose path or identity is not canonical, or with another cap. (3) `--profile ab-agentic-1` refuses other paths, a missing identity (`created_at` absent) or a different one (re-created). The 40-call total and the 14-call allocation are enforced in the same `BEGIN IMMEDIATE` transaction of that one ledger. (4) New explicit owner action `call_ledger.py close-experiment` ends the allocation for good: it is never reopened, its calls stay counted, and the lock is released so the **6 remaining calls** stay available for a separately approved purpose (still under the 40 cap). | Both initializations **refused**: **0** extra reservations. Two copies of the canonical file: **14** reservations in total; the second copy is refused by the launcher and the API. | `table-endpoint/test_ab_profile.py`, class `OneAuthoritativeLedger` (5 tests), plus the existing profile, restart, concurrency and race tests updated to the canonical rule |
| **HIGH 2:** numeric support assembled from different source mentions | X +3.2% (source X −3.2%, Y +3.2%) **grounded**; 78% adult from 78% pediatric **grounded**; affirmative claim from negated evidence **uncertain** and **kept** by a permissive verifier; the minors paraphrase (variant) **uncertain** | `_judge` evaluates **each source mention on its own**: unit or converted quantity, sign, negation, setting, population group, subject and metric must all hold for that one mention. The result is the best single mention, never a combination. Sign and negation cues are read in the number's own clause. Explicit negation attached to either number is a contradiction. Population groups that exclude each other (minor/pediatric/"under 18" vs adult; men vs women; inpatient vs outpatient) contradict, and the same group across a paraphrase grounds it. Model-like names such as "Model Y" count as subjects even when the claim does not name them. When no metric sits within 40 characters, a clause with exactly one metric supplies it. | X +3.2%: **contradicted** (`sign_flip`, `subject_mismatch`); adult vs pediatric: **contradicted** (`population_mismatch`); negated evidence: **contradicted** (`negation_mismatch`); minors paraphrase: **grounded**. End to end with a permissive verifier: the three bad claims are **held**, the valid one **kept**. Conversions and comparisons preserved. | `agentic/test_audit4.py::SingleMentionEndToEnd`: 13 paired end-to-end cases (5 automated reviewer probes) |
| **MEDIUM:** unsupported factual premise inside a conditional proposal | "Model X has already achieved accuracy in clinical deployment, so consider a pilot." **kept** as a conditional proposal | Proposals and caveats are split at premise joints (so, therefore, because, since, `;`, `,`). Every unhedged clause that asserts something is checked as a fact on its own: same setting as the evidence, content shared with the verified findings. Numbers are grounded within their own premise segment. | **Withheld** (`unsupported_premise`, `setting_transfer`). A supported premise with a clinical pilot proposal is kept. | `agentic/test_audit4.py::FactualPremises` (4) |

**Business Translation is disabled for the initial A/B** regardless: `ab-agentic-1` is `research_only`.
- In the launcher, `/api/research` refuses `industry`, `interpret_context` or `risk_assessment`, and `/api/agentic-research` refuses `industry`, before any call.
- The orchestrator never routes business insight in this mode.
- Tests: `test_audit4.py::ResearchOnly`.

### Trust boundary

This is a purely local ledger. Copying the file AND editing `ab_profile.py` (or the ledger code) can create another allocation, and no local mechanism prevents that. The tests do exactly this in memory, as a labelled test-only stand-in, to drive disposable copies. Every supported application path fails closed: the launcher, `call_ledger.init`, `CallLedger`, and the capped wrapper.

### Tests (model-free)

| Suite | Result |
|---|---|
| `table-endpoint/test_ab_profile.py` | 18/18 (+6) |
| `table-endpoint/test_call_ledger.py` | 16/16 |
| `agentic/test_audit4.py` (new) | 9/9 |
| `agentic/test_audit3.py` | 9/9 (one fixture now expects grounded instead of uncertain: the valid survey paraphrase is now confirmed) |
| `test_audit2`, `test_adversarial`, `test_agentic`, `test_integration` | 16/16, 44/44, 33/33, 34/34 |
| Chart-first, evidence tables (423 verified), proxy | 13/13, 21/21, 10/10 with the local fixtures |
| Baseline `tests/` (11 files) | 150 passed plus 1 intermittent WinError 10053 HTTP failure per run (a different test each time; each passes alone; the same flake as the untouched baseline export). `src/`, `tests/` and `ui/` are unchanged. |
| UI and browser suite | Not re-run: no UI file changed in this pass |

### Real ledger (read-only)

Integrity `ok`, 40 authorized, **20 used** (19 completed, 1 failed), 20 remaining, **no experiment lock**, no caps. Its identity (path,
seed, `created_at` 2026-11-18T20:49:37) is now pinned in `ab_profile.py`.

### Remaining limitations

- **Word lists:** population groups, settings, negation and premise joints come from fixed lists. Groups outside them (for example "veterans") are only uncertain, and premises joined without a listed joint are checked as one statement.
- **Local trust boundary:** described above.
- **Closing is a person's decision:** `close-experiment` must be run by a person; nothing closes an allocation automatically.

# Audit #3 (2026-11-19): 4 HIGH, narrow remediation

The components audit #3 cleared were left unchanged: architecture, retry behaviour, chart provenance and brief revisions.
Each finding was reproduced on the pre-fix code with `scratchpad/probes/repro_audit3.py` (outside the repo, disposable
ledgers only), and the script was re-run after the fixes.

| # | Finding | Before (reproduced) | Fix | After |
|---|---|---|---|---|
| 1 | Removing or renaming the experiment bypassed the 14-call A/B cap | After 14 `ab-agentic-1` calls, opening the ledger **without** an experiment, or as `ab-agentic-2`, made an **extra call**. The launcher accepted `--call-ledger` with no experiment flags. | **Ledger:** registering a capped experiment now **locks** the ledger to it (`meta.locked_experiment`, written in the same transaction). Every later open must use that experiment; omission or renaming is refused, and `reserve()` re-checks the lock inside its transaction, so a process opened before the lock cannot spend after it. A ledger belongs to one experiment; there is no unlock operation. **Launcher:** new `--profile ab-agentic-1` (`table-endpoint/ab_profile.py`). It requires the approved ledger (seed SHA-256 `4bdef6d0…`), `--authorized-calls 40`, `--experiment ab-agentic-1` and `--experiment-cap 14`, all explicit and exact. The profile's experiment name cannot be used without the profile, and a ledger that records it refuses launches without it. All of this is checked before any index or model is loaded (`validate_budget`, exit 2). `--budget-check-only` validates read-only and exits. The 40-call total still applies inside the experiment. | Omitted or renamed: **refused** at the ledger and by the launcher (exit 2). Two processes across restarts make exactly 14 calls (10 + 4). 5 concurrent profile processes make exactly 14. A process opened early is refused after the lock. With 35 of 40 used, only 5 experiment calls are possible. |
| 2 | Init race: one initializer could replace a ledger another had just published | With a competitor publishing between the existence check and `os.replace`: **both succeeded**, and the competitor's 5 records were replaced by 1 | Each initializer builds in its own uniquely named temporary file and publishes with `os.link`, a create-if-absent operation in the file system (NTFS and POSIX) that fails if the name exists. It never overwrites; volumes without hard links are refused. The temporary file is always removed. | The second initializer is **refused**, the competitor's 5 records are kept, and no temporary files remain. 4 competing processes publish exactly one ledger with the winner's records intact. |
| 3 | Numeric grounding over- and under-blocked | `3.2%` vs `-3.2%`, a negated claim, and benchmark → clinical were all **grounded**; `0.5 s` vs `500 ms` and a population paraphrase were **contradicted** | Each claim number is matched to its source mention by quantity (with standard conversions: ms/s/min/h, thousand/million/billion, currency scales; same dimension AND same converted value), sign as read (explicit minus, or no sign with only a "down" word), negation attached to the number ("did not reach"; "not only" excluded), measurement setting (evaluation: benchmark, dataset, simulation…; deployment: clinical, hospital, production, real-world…), subject, metric and population. A population or metric code cannot match becomes **uncertain**, not contradicted. Repaired a latent bug: two regexes held literal backspace characters instead of `\b`, so clause breaks on "and", "while"… never matched. | `sign_flip`, `negation_mismatch`, `setting_transfer` are **contradicted**; `0.5 s` = `500 ms` is **grounded**; the population paraphrase is **uncertain** (not rejected). Valid twins pass. |
| 4 | The business screen accepted 78% "clinical deployment" accuracy from 78% benchmark accuracy | Implication **kept** as `kept_unverified` | Every business statement (implication, action, assumption, risk, limitation) is classified as `conditional_proposal`, `assumption`, `caveat`, `supported_fact` or `withheld`. Past tenses such as "was validated" are facts, not hedges. A statement asserted as fact must be supported in the **same measurement setting** as the evidence (a deployment or clinical fact cannot rest on benchmark evidence) and share most of its content with the verified findings. Numbers must be grounded, and uncertain counts as unsupported. Any issue means **withheld**; the "unverified" label is never used to show a known-unsupported statement. Verified findings stay in the summary, and business output shows only proposals, assumptions, caveats and supported facts. The UI note says how many statements were withheld. | **Withheld** (`setting_transfer`). A factual deployment claim without numbers is withheld; a hedged clinical pilot proposal and an explicit assumption are kept and labelled. |

### Tests (all model-free)

| Suite | Result |
|---|---|
| `table-endpoint/test_ab_profile.py` (new) | 12/12: actual-launcher omission, renaming, cap raise, authorization change, profile experiment without the profile, wrong ledger, restart, concurrency, early-open process, the 40 cap inside the experiment, the ledger-level lock without the launcher, and init races in-process and across 4 processes. The real ledger is checked read-only and unchanged. |
| `agentic/test_audit3.py` (new) | 9/9: 14 paired valid and invalid numeric fixtures (5 automated reviewer probes), end-to-end runs with a lenient verifier, and business separation including the automated reviewer case |
| `agentic/test_agentic.py`, `test_integration.py`, `test_adversarial.py`, `test_audit2.py` | 33/33, 34/34, 44/44, 16/16 |
| `table-endpoint/test_call_ledger.py` | 16/16 |
| `test_chart_first.py`, `test_evidence_tables.py`, `ui-consult/tests/test_serve.py` | 13/13, 21/21 (423 tables verified), 10/10, with the local audit and recorded fixtures |
| Browser `evidence.test.html` | Not re-run in this pass: no file it loads changed (`ui-consult/app.js` changed only the business note text, checked in the mock UI) |
| Baseline `tests/` (11 files) | 150–151 passed. 1–4 HTTP tests fail intermittently with WinError 10053, the same pre-existing Windows socket flake as in the untouched baseline export. `src/` and `tests/` are unchanged. |

Fixture changes, each stricter or as audit #3 asked:
- "78% of hospitals" against 78% benchmark accuracy is now `setting_transfer` (contradicted), where audit #2's fixture expected uncertain.
- "12% of hospitals" against "12% of clinics" is now uncertain rather than contradicted, because code cannot tell a different population from a paraphrase.
- A test helper that wrote a session log into the repo now writes it beside its disposable ledger; the stray file, containing only fake test calls, was deleted.

### Remaining limitations

- **Approximate settings:** the setting and negation checks use fixed word lists. A deployment described in unlisted words is not caught, and a negation more than 40 characters before its number is only "uncertain".
- **Proposal versus fact:** classification depends on hedge wording. A factual claim phrased with "may" is treated as a proposal, though its numbers and advice wording are still checked.
- **Lock is permanent:** once a ledger is locked to `ab-agentic-1`, any calls left after the A/B cap (up to 6 of the 40) cannot be spent under another name. A person must decide whether to issue a new authorization.
- **NTFS or POSIX only:** publishing relies on hard links. Other volumes are refused, which is safe.
- **Still not resolved by code:** meaning-level errors still need the verifier and a person.

### Ledger

The real ledger reads integrity `ok`, 40 authorized, 20 used (19 completed, 1 failed), 20 remaining, not yet locked, no experiment caps.
It will be locked to `ab-agentic-1` by the first `--profile ab-agentic-1` launch. No call was spent.

# Audit #2 (2026-11-19): 4 HIGH, 2 MEDIUM

Each finding was reproduced on the pre-fix code before any change, with
`scratchpad/probes/repro_audit2.py` (outside the repo). The same script was re-run after the fixes, and
every case is now a permanent regression test.

| # | Finding | Reproduced before the fix | Fix | After the fix | Regressions |
|---|---|---|---|---|---|
| 1 HIGH | Ledger: two wrappers can take the same last slot; a crash-truncated record undercounts | 2 processes, 1 slot left: **both called**. 38 records plus 1 truncated: **2 calls** allowed where 1 should be (two records collapsed onto one line). | New `table-endpoint/call_ledger.py`: a SQLite ledger. `BEGIN IMMEDIATE` makes check-and-insert one cross-process transaction. `synchronous=FULL` with the rollback journal: a reservation is durable before the provider call, and a crash before COMMIT leaves nothing. Unique IDs (uuid4; seeds `seed-<sha>-NNN`). States: `reserved`, `completed`, `failed`, `unresolved` (another or a crashed process's open reservation, still counted). Fails closed on: missing file, failed integrity check, unknown schema or state, changed authorization, rows below the high-water mark (reset or rollback). It is created only by `init` from a strictly parsed seed (incomplete, malformed or blank lines refused) and never overwritten. An optional experiment cap is enforced in the same transaction, recorded once, never raised. JSONL ledgers are refused. | 8 processes, 3 slots → exactly 3 calls; 2 processes, 1 slot → 1 call; crash mid-call → counted as unresolved; crash mid-transaction → clean rollback and lock released; corrupted, reset, tampered or mismatched → refused | `table-endpoint/test_call_ledger.py` (16) and `test_integration.CumulativeLedger` (5) |
| 2 HIGH | Numbers: accepted "latency decreased 1.2 s → 3.4 s", flipped signs, swapped subjects, a changed "only" condition; rejected the valid "error rate improved 20% → 10%" | All 4 misleading cases returned no issue; the valid one was flagged `reversed_comparison` | `numeric_checks.py` rewritten around structured mentions. Each number is compared with its cited quotes by value, explicit sign, unit, subject (clause-attributed named entity both texts share), metric (within 40 characters), population ("x% **of** hospitals") and context. Pairs are checked for order and direction, with metric polarity: "improved" is evaluative, so lower-is-better metrics improve downward. Conditions compare the qualifier's object words, not the keyword. Three states: **contradicted** (claim held whatever the verifier says), **uncertain** (code cannot establish meaning: kept only if the independent verifier supports it, and flagged for a person in the UI and in `provenance.agentic.claims_needing_number_check`), **grounded**. | All 5 automated reviewer cases behave correctly | `test_audit2.NumericGrounding`: 25 paired valid and invalid fixtures, plus the uncertain-state path |
| 3 HIGH | Business: a number anywhere in the cited passage was enough; fabricated limitations passed | "78.0% of hospitals adopted the tool" kept (the passage had 78.0% *accuracy*); "The study covered 3 hospitals" kept | `screen_business` grounds **implications, actions, assumptions, risks and limitations** with the same mention matcher against the cited passages' own sentences. Uncertain counts as unsupported, because no model verifies advice. It also removes ROI or savings, guarantees, compliance, readiness or replacement claims the passages don't state; study facts not backed by the verified findings; and implications sharing fewer than 2 content stems with the verified claims they cite. Kept items are recorded as `kept_unverified`. The UI shows business output under an "Unverified recommendations" note, separate from findings. With nothing left, the result is an explained abstention. | Cross-context implication and fabricated limitation removed | `test_audit2.BusinessGrounding` (5) |
| 4 HIGH | Retry: rejected drafts pinning all 14 old citations could drop the new evidence | Second synthesis call **spent**, and the new passage A2 **not** in it | Only claims that were *retained and verified* pin citations. 4 slots are reserved for new passages. The decision to synthesize is made on the **effective** merged evidence: no new passage in context means no call. The best round is chosen by verified coverage, then verified-claim count, then fewer missing parts. | A2 reaches synthesis; `new_passage_ids == ['A2']` | `test_audit2.TargetedRetry` (4), including the saturated 14-passage case in both variants |
| 5 MEDIUM | Chart decision, sealed provenance and trace disagreed | Displayed `unavailable`, sealed `available`, trace `available` | The orchestrator receives the answer's index (`index_sha256`) and makes the single decision. A mismatch, or no bound index, gives `unavailable` with `rejected: index_mismatch`. The trace, `result.charts`, `provenance.agentic.charts` and `agentic_charts` all come from that one object, and the envelope refuses an `available` chart from another index. | All three `unavailable` | `test_adversarial.Binding` (updated), `test_agentic.Charts` (+1) |
| 6 MEDIUM | `library_revision` silently ignored by the agentic route | 200, no library save, no error | Same contract as baseline `/api/research`. The revision target is validated **before any model call** (400 malformed or no library, 404 unknown brief, 409 stale version, 503 storage). Every answer is then saved, as the next version when revising, and a storage failure returns `library_error` without dropping the answer. The mock honours revisions too. | Valid revision → version 2 of the same brief; stale, unknown or malformed → refused with 0 calls | `test_audit2.Revisions` (4) |

### Test totals (all model-free, 2026-11-19)

| Suite | Result |
|---|---|
| `experiments/agentic/test_agentic.py` | 33/33 |
| `experiments/agentic/test_integration.py` | 34/34 |
| `experiments/agentic/test_adversarial.py` | 44/44 |
| `experiments/agentic/test_audit2.py` (new) | 16/16 (25 numeric fixture subtests) |
| `experiments/table-endpoint/test_call_ledger.py` (new) | 16/16, including the read-only check of the real ledger at 20/40 |
| `experiments/table-endpoint/test_chart_first.py` | 13/13 with the local audit beside it (3 fail without it: missing fixture) |
| `experiments/table-endpoint/test_evidence_tables.py` | 21/21 with the audit (423 verified, 13 refused) |
| `ui-consult/tests/test_serve.py` | 10/10 with the recorded fixtures (1 fails without them: missing fixture) |
| Browser `ui-consult/tests/evidence.test.html` | 37/37 |
| Baseline `tests/` (11 files: research demo, brief store and HTTP, indexed research, pipeline, contracts, chat, answer quality, business translation, B2) | 151 passed. Intermittently 1–2 HTTP tests fail with WinError 10053 (connection aborted). The **untouched baseline export** `D:/KPMG-demo-corpus/main-727b0b3` fails the same way, and each test passes alone, so this is a pre-existing Windows socket flake, not a regression. |

Tests changed to new contracts (none loosened):
- The chart tests now bind an index.
- The business tests pass the verified claims the screen now requires, and count removed items, because the screening record now lists kept items too.
- The ledger tests use SQLite.

### Remaining limitations and risks

- **Surface checks only.** The numeric and advice checks are surface-level. The subject comes from clause structure plus capitalized names both texts share; the metric comes from a fixed lexicon within 40 characters. Unusual phrasing becomes **uncertain**, which is safe but noisy for a reviewer. Meaning still depends on the verifier and a person.
- **Unknown direction.** "Improved" on a metric outside the lexicon is uncertain, not judged.
- **Business screen can over-remove.** It may drop a reasonable implication that rephrases the findings with fewer than 2 shared content stems.
- **Unresolved reservations.** A crash leaves a reservation `unresolved`. It counts against the budget, and nothing reclassifies it automatically; only a person can.
- **Same machine only.** The SQLite ledger relies on file locking on a local disk. It is not designed for a network share.
- **Uneven A/B arms.** The baseline arm still runs fewer numeric checks than the multi-agent arm.

### Call budget

The real ledger, `D:/KPMG-demo-corpus/table-endpoint-exp/automated reviewer-authorization-40.ledger.sqlite3`, was created from the 20-record
JSONL seed, which is kept unchanged. Status (read-only): integrity `ok`, authorized 40, used **20** (19 completed, 1
failed), remaining **20**, high-water 20. No calls were spent.

# Audit #1 (2026-11-18)

## High-severity findings

| # | Finding | Fix | Where | Regressions |
|---|---|---|---|---|
| 1 | Coverage could be reported as full after claims were rejected | Coverage is recomputed from the claims actually kept: no kept claim → `none`; any held claim downgrades `full` to `partial`, with an answer lead naming what is missing. A verifier reply that says `none` while judging claims supported, or claims coverage with nothing supported, is rejected (fail closed). The verifier's own value is kept as `coverage_reported`. | `agents.py` VerificationAgent, final assembly | `test_adversarial.Coverage` (3) |
| 2 | A targeted retry could re-synthesize unchanged evidence | The retry search must return a passage not already in the evidence, or no synthesis or verification call is made (`no_new_evidence`). New passages are guaranteed a place: passages cited by earlier claims stay, new ones come next, and uncited earlier passages give way under the 14-passage limit. `new_passage_ids` and `dropped_passage_ids` are recorded. | `agents.py` ResearchAgent | `test_adversarial.TargetedRetry` (3) |
| 3 | Numerically misleading claims and unsupported business advice could pass | Checks in code, per claim and against its own cited quotes: numbers absent (now for interpretations too), unit mismatch (% vs percentage points, time and scale units, currency), denominator pairing ("3 of 7"), reversed comparisons (swapped from/to pairs, a direction word contradicting the numbers, reversed comparatives), and dropped qualifiers ("only on …", "except …"). A failure holds the claim whatever the verifier says. The verifier gained the matching issue types. Business output is screened after translation: an implication with a number, ROI or savings, a guarantee, a compliance claim, deployment readiness or workforce replacement that its cited passages do not state is removed. If none remain, the business result becomes an explained abstention. | `numeric_checks.py`, `agents.py` | `test_adversarial.NumericGuards` (13), `BusinessAdvice` (6) |

## Remaining audit items

| Item | Fix | Regressions |
|---|---|---|
| Bind results to index, evidence IDs and round | The answer is built from one selected round only (its claims, evidence and limitations); `selected_round`, `evidence_ids` and the index SHA-256 are in `provenance.agentic`. The route re-checks the index after the run and returns 409 with no answer if it changed. A chart whose index differs from the answer's is replaced by "unavailable". | `Binding` (5) |
| Provenance for limitations and charts | Cited limitations keep their `limitation_support` (chunk IDs and quotes) from the selected round. Agent-added notes are labelled "Verification note:" and listed separately. Chart provenance records status, reason, index SHA-256, per-table status and reason, and 0 model calls. | `Binding` |
| Provider failure vs insufficient evidence | Errors carry `kind`: `provider` (timeout, rate limit, outage) or `budget` (per-run cap, cumulative cap, stopped after an earlier error). Neither ever becomes an abstention. Abstentions carry a reason: `insufficient_evidence`, `no_supported_claims`, `verification_rejected` or `synthesis_rejected`. A provider failure in the optional business step keeps the verified answer and reports the business step as failed. | `FailureKinds` (4) |
| Cumulative accounting and progress across modes | One research request at a time across baseline and multi-agent (shared lock, 409 before any call). Both modes check the same ledger-backed budget. `/api/progress` reports `mode`, `max_calls` and the active agent. The UI shows "Research agent is waiting for the AI · model call 2 of up to 6". | `SharedLimits` (2), `test_integration.CumulativeLedger` (5) |
| Misleading trace labels | The retry task is `targeted_research`; routing decisions are `business_routing` / `chart_routing`, separate from `business_run`; coverage text says "coverage of the kept claims" and shows the verifier's original value when adjusted; an abstaining research reply no longer says claims were drafted; budget refusals are not called provider failures. | `SharedLimits.test_trace_labels_name_what_actually_happened` |
| Prompt injection | Prompts state that embedded directives are data. Tests prove the guarantees hold even when the model obeys an injection: the question is JSON-escaped after fixed instructions, an invented quote or number is held despite a "supported" verdict, approval or tool fields are rejected by schema, injected subquestions only search the local index, an injected industry is ignored, and review stays pending. | `PromptInjection` (7) |

## Call-budget reconciliation

- Ledger: `D:/KPMG-demo-corpus/table-endpoint-exp/automated reviewer-authorization-40.ledger.jsonl`, 20 lines. Provenance is in `automated reviewer-authorization-40.README.md` beside it.
- Counted (provisional, per owner instruction): the four `live-calls*.jsonl` session logs there, 3 + 7 + 6 + 4 = 20 calls on 2026-11-17 between 00:59:40 and 21:53:19. Each log matches one backend launch log with its cap (4, 9, 9, 9). There are no duplicate timestamps, and the sessions do not overlap. The last call was a 300 s timeout.
- Not counted: the Fable live test, `D:/KPMG-library-data/experiments/competitor-demo-readiness/fable-live/calls-automated reviewer.jsonl` (2026-11-16, its own 12-call authorization). Its log has 10 lines where its RESULTS.md says 9 calls; this discrepancy is not resolved. The 2026-11-04 stage-c ledgers are older work and are not counted either.
- Codex CLI calls are `--ephemeral`, and `~/.automated reviewer/logs_2.sqlite` holds only desktop-app processes, so the provider side cannot cross-check them.
- Remaining: **20**. The backend reads the ledger at every check, reserves a line before each call, and refuses a missing ledger.

## Not changed / known limits

- The checks in code catch surface errors (numbers, units, pairings, directions, qualifier keywords). Meaning-level errors still depend on the verifier and a person.
- The qualifier check is conservative and may hold a correct claim that rephrases "only". This is preferred over passing a claim that drops the condition.
- The baseline arm still runs the reported-number check only with the arXiv fallback. The multi-agent arm runs stricter checks, so the A/B comparison has a known asymmetry.
- Risk assessment and clarification remain baseline-only.
