# fresh-v4 final validation: readiness report (S3 vs frozen S2)

**Status:**

- **Ready:** every check passes except free memory, which is 5.4–5.6 GB against the 6 GB minimum.
- **Not done:** no live calls have been made.
- **Pending:** your approval.

## Checks

| Check | Result |
|---|---|
| S3 code freeze (29 files, written 14:22 before any fresh material) | verified |
| Set seal (questions, key, rules, bundle record) | verified |
| S3 tests (40) and V2 regression suites (test_v2, test_consolidated 40, test_runner 4) | pass |
| Replay of 8 saved S2 answers through the S3 publication path | byte-identical |
| Offline retrieval criteria R1–R5 on the development sets | all pass (162 vs 142 points, 3 lost) |
| Codex login and model (gpt-6.1-sol, low) | OK for both arms |
| Persistent ledgers | 0 of 50 used; cap 25 per arm |
| Free memory | **5.4–5.6 GB, below the 6 GB minimum: close programs first; the runner refuses otherwise** |

## Fresh set (final key)

**Material:**

- **Papers:** 10 new arXiv papers from November 2026, selected mechanically by `SELECTION-RULE.md`.
- **Index:** a separate validation bundle; the demo-100 corpus is unchanged.
- **Questions:** 10, with 50 points; 80% = 40 points.

**Key review:** one independent AI review. Its corrections are recorded in `fresh-v4/KEY-REVIEW-RECORD.md`. Human sign-off is pending.

**Evidence coverage (offline, frozen code):**

| | Points with full evidence retrieved | Share |
|---|---|---|
| S2 | 36 / 50 | 72% |
| S3 | 39 / 50 | 78% |

- **Weak spot:** both arms retrieve only 1 of 5 points' evidence on the cross-paper questions K05 and K07.
- **Projection:** realistic S3 completeness is about 78–80%. **Reaching 80% is uncertain.**

## Risks to the frozen criteria

- **Completeness ≥ 80% (≥ 40 points):** uncertain, as above.
- **S3 ≥ S2 + 2 points:** the retrieval head start is 3 evidence points.
- **Input tokens ≤ 1.15 × S2:** S3's evidence is about 1.26× S2's (serialized estimate). The development-set prediction was 1.12×. **There is a material risk of failing this criterion.**
- **Latency:** retrieval adds about +9.9 s per question (median). S2's fresh-v3 median was 94.8 s and p90 145.8 s, so the limits are probably met but not certain.

## Execution

Run from `D:\KPMG-source-grounded\experiments\retrieval-v3`. Run S3 first, then S2; each takes about 15–20 minutes. Rerunning a command resumes it, with at most one resume per question.

```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_fresh4.py --run S3
```

```powershell
D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -I run_fresh4.py --run S2
```

## Afterwards (0 calls)

1. Run the programmatic audit: `fresh4_scoring.py audit`.
2. Build the blind packet: `fresh4_scoring.py blind`. A fresh Codex session scores it.
3. A Claude audit pass follows, then your adjudication.
4. Evaluate the criteria: `fresh4_scoring.py criteria`.
5. Make the final engine recommendation for the supervised demonstration, then move to integration.
