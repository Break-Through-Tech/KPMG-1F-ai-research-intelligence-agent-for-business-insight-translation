"""Capture Alesha's versioned baseline using the shared frozen benchmark runner.

Example: python -m src.evaluation_retrieval --output output/baseline-run
Default mode is retrieval-only; --mode summary uses the shared provider config.
This collects evidence, not human scores or approval.
"""
from pathlib import Path
import sys

from evaluation.run_benchmarks import main as capture_main

CASES = Path(__file__).resolve().parents[1] / "evaluation/baseline_alesha_v1.json"


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    return capture_main(["--cases", str(CASES), *args])


if __name__ == "__main__":
    raise SystemExit(main())
