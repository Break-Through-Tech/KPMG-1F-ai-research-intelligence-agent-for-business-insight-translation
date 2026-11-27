"""Permanent regressions for audit #5 (2026-11-19): every number is checked against ONE source mention, with its
setting and conditions taken from that mention's own clause or clearly shared context, never from a neighbouring
number. Model-free; end to end through the orchestrator with a PERMISSIVE fake verifier.

Run from the repository root:  py -3.14 -I -B experiments/agentic/test_audit5.py
The lookalike-experiment ledger hardening is in experiments/table-endpoint/test_ab_profile.py.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
from agents import OrchestratorAgent  # noqa: E402
from numeric_checks import ground_text  # noqa: E402
from test_agentic import CORPUS, Provider, Retriever, draft, passage, plan, verdicts  # noqa: E402

S1 = 'Model X reached 78% accuracy on the benchmark and 64% accuracy in hospitals.'
S2 = 'Model X reached 78% accuracy overall and 90% only on English tasks.'
# (name, claim, source, code status, end-to-end outcome, expected issue)
CASES = [
    # Audit #5 case 1 and its counterparts
    ('case 1: 78% (benchmark) claimed for hospitals', 'Model X reached 78% accuracy in hospitals.', S1, 'contradicted', 'held', 'setting_transfer'),
    ('case 1 twin: 64% in hospitals', 'Model X reached 64% accuracy in hospitals.', S1, 'grounded', 'kept', None),
    ('case 1 twin: 78% on the benchmark', 'Model X reached 78% accuracy on the benchmark.', S1, 'grounded', 'kept', None),
    ('case 1 reverse: 64% (hospitals) claimed for the benchmark', 'Model X reached 64% accuracy on the benchmark.', S1,
     'contradicted', 'held', 'setting_mismatch'),
    # Audit #5 case 2 and its counterparts
    ('case 2: 78% overall (condition belongs to 90%)', 'Model X reached 78% accuracy overall.', S2, 'grounded', 'kept', None),
    ('case 2 twin: 90% claimed overall', 'Model X reached 90% accuracy overall.', S2, 'contradicted', 'held', 'missing_condition'),
    ('case 2 twin: 90% with its condition', 'Model X reached 90% accuracy only on English tasks.', S2, 'grounded', 'kept', None),
    ('case 2 twin: 90% with a changed condition', 'Model X reached 90% accuracy only on Spanish tasks.', S2, 'contradicted', 'held', 'changed_condition'),
    # shared context stays associated with every value it governs
    ('shared lead-in condition applies to all values', 'Model X reached 78% accuracy.',
     'Only on English tasks, Model X reached 78% accuracy and Model Y reached 64% accuracy.', 'contradicted', 'held', 'missing_condition'),
    ('shared lead-in condition kept', 'Model X reached 78% accuracy only on English tasks.',
     'Only on English tasks, Model X reached 78% accuracy and Model Y reached 64% accuracy.', 'grounded', 'kept', None),
    ('shared lead-in setting applies to all values', 'Model X reached 78% accuracy in hospitals.',
     'On the benchmark, Model X reached 78% accuracy and Model Y reached 64% accuracy.', 'contradicted', 'held', 'setting_transfer'),
    ('single-number trailing condition applies', 'Model X reached 78% accuracy.',
     'Model X reached 78% accuracy, only on English tasks.', 'contradicted', 'held', 'missing_condition'),
    # genuinely ambiguous scope: uncertain, not invented support or a false rejection
    ('ambiguous trailing condition over two values', 'Model X reached 78% accuracy.',
     'Model X reached 78% accuracy and Model Y reached 64% accuracy, only on English tasks.', 'uncertain', 'kept', 'condition_scope_unconfirmed'),
    # subjects: an elliptical clause inherits the earlier subject; a new subject does not
    ('elliptical clause inherits its subject', 'Model X reached 64% accuracy in hospitals.', S1, 'grounded', 'kept', None),
    ('contrast clause with another subject', 'Model X reached 60% accuracy.',
     'Model X reached 78% accuracy, while the baseline reached 60% accuracy.', 'uncertain', 'kept', 'subject_unconfirmed'),
    # a comma inside a number is not a clause break
    ('thousands separator', 'Agreement reached 91.4% in 1,240 cases.', 'Agreement reached 91.4% in 1,240 cases.', 'grounded', 'kept', None),
]


def run(claim_text, source):
    CORPUS['S5'] = passage('S5', source)
    try:
        claim = {'text': claim_text, 'kind': 'finding', 'support': [{'chunk_id': 'S5', 'quote': source.rstrip('.')}]}
        provider = Provider(plan=[plan()], research=[draft(claim, limits=[])], verify=[verdicts(('supported', []))])
        return OrchestratorAgent(generate=provider, retrieve=Retriever({'Model': ['S5'], 'Agreement': ['S5']}), top_k=4).run(
            'How did Model X perform?')
    finally:
        del CORPUS['S5']


class SameMention(unittest.TestCase):
    def test_code_status(self):
        for name, claim, source, status, _outcome, issue in CASES:
            with self.subTest(name):
                result = ground_text(claim, [source])
                self.assertEqual(result['status'], status, result)
                if issue:
                    self.assertIn(issue, result['contradictions'] + result['uncertain'], result)

    def test_end_to_end_with_a_permissive_verifier(self):
        for name, claim, source, status, outcome, _issue in CASES:
            with self.subTest(name):
                r = run(claim, source)
                kept = bool(r['summary']['claims'])
                self.assertEqual('kept' if kept else 'held', outcome, r['summary'].get('held_claims'))
                if kept:
                    # Uncertain claims are kept only with the verifier AND a flag for a person.
                    self.assertEqual(r['summary']['claims'][0]['verification']['needs_human_number_check'], status == 'uncertain')


if __name__ == '__main__':
    unittest.main(verbosity=1)
