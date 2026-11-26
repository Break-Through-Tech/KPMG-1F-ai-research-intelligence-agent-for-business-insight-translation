"""fresh-v3 arm B0: the Original Baseline exactly as in every earlier evaluation (codex_baseline 'fresh-top8':
create_research, quality review on, table comparisons off, top_k 8). NOT run until approved.

codex_baseline.py is NOT edited: this wrapper registers fresh-v3 in memory as the runner's 'fresh' set, so the existing
run() applies its one-resume rule, persistent per-arm ledger and request guard unchanged. Outputs go to
data/processed/fresh-v3-B0-original-baseline.

    python -I run_fresh3_b0.py --check
    python -I run_fresh3_b0.py --run
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'agentic-handoff'))
sys.path.insert(0, str(HERE))
import codex_baseline  # noqa: E402  (sets the frozen runner's paths)
import fresh3_arms as arms  # noqa: E402
import seal_v3  # noqa: E402

VARIANT = 'fresh3-top8'


def register():
    codex_baseline.SETS['fresh'] = (arms.SET, None)
    codex_baseline.VARIANTS[VARIANT] = (arms.ARM_DIRS['B0'], False, False, 'fresh')
    codex_baseline.FRESH_VARIANT_CAP[VARIANT] = arms.ARM_CAP['B0']


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    register()
    from prepare import BUNDLE, CLI, ENCODER, PIN, RERANKER
    ready = codex_baseline.codex_paired.checks(CLI)
    ready['fresh_v3_seal'] = seal_v3.verify()
    ready['free_commit_gb'] = round(codex_baseline.free_commit_gb(), 1)
    print(json.dumps({**ready, 'arm': 'B0', 'variant': VARIANT, 'evidence': 'fixed-8', 'call_cap': arms.ARM_CAP['B0'],
                      'expected_calls': arms.EXPECTED['B0']}, indent=1))
    print(json.dumps(arms.combined_check('B0')))
    if args.check:
        return
    if ready['free_commit_gb'] < codex_baseline.MIN_FREE_COMMIT_GB:
        raise SystemExit('Not enough free memory; nothing was run.')
    from src.codex_generation import create_codex_generate
    from src.experimental.b2 import open_b2
    from src.experimental.demo import create_research
    receipts = []
    generate, metadata = create_codex_generate(model=codex_baseline.MODEL, binary=str(CLI), effort=codex_baseline.EFFORT,
                                               timeout=codex_baseline.TIMEOUT, receipts=receipts)
    retrieval = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER, table_comparisons=False)
    if retrieval[1]()['indexed_records_sha256'] != PIN:
        raise SystemExit('Unexpected B2 index')
    research = create_research(retrieval, generate, metadata, 8)
    status = codex_baseline.run(VARIANT, research=research, generate=generate, receipts=receipts, out_root=arms.OUT)
    print(json.dumps(status, indent=1))


if __name__ == '__main__':
    main()
