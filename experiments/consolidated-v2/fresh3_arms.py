"""fresh-v3 validation arms: output folders, per-arm caps and the persistent combined cap (no model calls here).

    B0  Original Baseline (codex_baseline fresh top-8 + quality review)   expected 16, cap 20
    S1  Consolidated Standard v1 (frozen, ../consolidated)                expected 16, cap 20
    S2  Optimized Consolidated Standard (consolidated-v2)                 expected 16, cap 20
    D2  Optimized Consolidated Deep (consolidated-v2)                     expected 24, cap 30
    Combined: expected 72, HARD CAP 90 (retries included), counted from the persistent ledgers of all four arms.
Adaptive is excluded from this evaluation.
"""
from contextlib import closing
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed'
SET = Path(__file__).resolve().parent / 'fresh-v3'
ARM_DIRS = {'B0': 'fresh-v3-B0-original-baseline', 'S1': 'fresh-v3-S1-consolidated-v1-standard',
            'S2': 'fresh-v3-S2-consolidated-v2-standard', 'D2': 'fresh-v3-D2-consolidated-v2-deep'}
ARM_CAP = {'B0': 20, 'S1': 20, 'S2': 20, 'D2': 30}
EXPECTED = {'B0': 16, 'S1': 16, 'S2': 16, 'D2': 24}
COMBINED_CAP = 90
assert sum(ARM_CAP.values()) == COMBINED_CAP and sum(EXPECTED.values()) == 72


def calls_used(directory, out_root=OUT):
    path = out_root / directory / 'calls.sqlite3'
    if not path.is_file():
        return 0
    with closing(sqlite3.connect(path)) as db:
        return db.execute('SELECT COUNT(*) FROM calls').fetchone()[0]


def combined_check(arm, out_root=OUT):
    """Refuse before running if this arm's remaining allowance could push all four arms past COMBINED_CAP."""
    used = {a: calls_used(d, out_root) for a, d in ARM_DIRS.items()}
    worst = sum(used.values()) + (ARM_CAP[arm] - used[arm])
    if worst > COMBINED_CAP:
        raise SystemExit(f'Combined cap: {sum(used.values())} used; {arm} could use {ARM_CAP[arm] - used[arm]} more, '
                         f'exceeding {COMBINED_CAP}. Nothing was run.')
    return {'combined_used': sum(used.values()), 'arm': arm, 'arm_remaining': ARM_CAP[arm] - used[arm],
            'combined_cap': COMBINED_CAP}
