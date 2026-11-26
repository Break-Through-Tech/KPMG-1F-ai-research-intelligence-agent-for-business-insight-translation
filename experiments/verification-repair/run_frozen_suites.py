"""Run the frozen experiments/agentic test suites with numeric_checks replaced by numeric_checks_v2.

    python -I run_frozen_suites.py          # v2
    python -I run_frozen_suites.py --frozen # the original module, for comparison
Every expectation in those suites (including adversarial number cases) must still hold under v2.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENTIC = HERE.parent / 'agentic'
ROOT = HERE.parents[1]
sys.path[:0] = [str(AGENTIC), str(ROOT), str(HERE.parent / 'agentic-handoff')]
if '--frozen' not in sys.argv:
    sys.path.insert(0, str(HERE))
    import numeric_checks_v2
    sys.modules['numeric_checks'] = numeric_checks_v2
SUITES = ['test_adversarial', 'test_agentic', 'test_audit2', 'test_audit3', 'test_audit4', 'test_audit5',
          'test_statistical_reports', 'test_interpretation_policy', 'test_quote_grounding', 'test_scope_review',
          'test_integration']
loader = unittest.TestLoader()
suite = unittest.TestSuite(loader.loadTestsFromName(name) for name in SUITES)
result = unittest.TextTestRunner(verbosity=0).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
