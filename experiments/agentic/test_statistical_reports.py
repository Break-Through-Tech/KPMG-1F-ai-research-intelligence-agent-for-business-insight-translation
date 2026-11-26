"""Regression tests for the opt-in statistical-report fix. Saved F09 text is verbatim from the Codex full run."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE), str(HERE.parent / 'agentic-handoff')]
import numeric_checks  # noqa: E402
import statistical_reports  # noqa: E402

F09_CLAIM = ('No statistically significant increase in willingness to help was found for either empathetic tone or physical '
             'embodiment. Mean stated volunteering hours were 3.4 (SD 2.97) for the empathetic robot, 4.0 (SD 2.93) for '
             'the neutral robot, 4.6 (SD 2.03) for the empathetic chatbot, and 3.0 (SD 3.00) for the neutral chatbot; the '
             'overall comparison was not significant, \\(F(3,26)=0.341, p=.796\\).')
F09_SOURCES = [
    'Results indicate that neither robotic embodiment nor empathetic tone significantly influenced participants’ '
    'willingness to volunteer.',
    'The mean volunteering hours were 3.4 (SD = 2.97) for the empathetic robot, 4.0 (SD = 2.93) for the non-empathetic '
    'robot, 4.6 (SD = 2.03) for the empathetic chatbot, and 3.0 (SD = 3.00) for the non-empathetic chatbot. A one-way '
    'ANOVA revealed no statistically significant difference in volunteering hours across groups, (F(3, 26) = 0.341, '
    'p = .796).']
SIGNIFICANT_SOURCE = ['A one-way ANOVA revealed a statistically significant difference across groups, (F(2, 40) = 5.12, p = .011).']


def check(text, sources):
    return numeric_checks.ground_text(text, sources)


class Fixed(unittest.TestCase):
    def setUp(self):
        statistical_reports.enable()

    def tearDown(self):
        statistical_reports.disable()

    def test_saved_f09_null_result_is_no_longer_contradicted(self):
        self.assertEqual(check(F09_CLAIM, F09_SOURCES)['contradictions'], [])

    def test_null_result_stated_as_significant_is_caught(self):
        flipped = F09_CLAIM.replace('was not significant', 'was statistically significant')
        self.assertIn('significance_mismatch', check(flipped, F09_SOURCES)['contradictions'])

    def test_significant_result_stated_as_null_is_caught(self):
        claim = 'There was no significant difference across groups (F(2,40)=5.12, p=.011).'
        self.assertIn('significance_mismatch', check(claim, SIGNIFICANT_SOURCE)['contradictions'])

    def test_matching_significant_result_passes(self):
        claim = 'Groups differed significantly, F(2,40)=5.12, p=.011.'
        self.assertEqual(check(claim, SIGNIFICANT_SOURCE)['contradictions'], [])

    def test_changed_test_statistic_is_still_absent(self):
        claim = F09_CLAIM.replace('0.341', '0.431')
        self.assertIn('numbers_absent', check(claim, F09_SOURCES)['contradictions'])

    def test_ordinary_negated_numbers_keep_the_original_rule(self):
        self.assertIn('negation_mismatch', check('Model X did not reach 78% accuracy.', ['Model X reached 78% accuracy.'])['contradictions'])
        # A number outside the test report in the same sentence is still checked for negation.
        claim = 'Model X did not reach 78% accuracy (t(28)=2.10, p=.04).'
        self.assertIn('negation_mismatch', check(claim, ['Model X reached 78% accuracy (t(28) = 2.10, p = .04).'])['contradictions'])

    def test_disable_restores_the_frozen_behaviour(self):
        statistical_reports.disable()
        self.assertEqual(check(F09_CLAIM, F09_SOURCES)['contradictions'], ['negation_mismatch'])
        statistical_reports.enable()


class SavedRuns(unittest.TestCase):
    """Replay the saved Codex F09 drafts and verifier replies through the real orchestrators (no model calls)."""

    def test_f09_required_null_result_is_published_with_the_fix(self):
        from replay_scope_review import ROOT, replay
        run = ROOT / 'data/processed/codex-paired-v1-full'
        if not run.exists():
            self.skipTest('Codex full run not present')
        for arm in ('current', 'handoff'):
            before = replay(run / 'F09' / arm, scope=False, label=None, policy=True)
            statistical_reports.enable()
            try:
                after = replay(run / 'F09' / arm, scope=False, label=None, policy=True)
            finally:
                statistical_reports.disable()
            null = [t for t in after['published'] if t.startswith('No statistically significant increase')]
            self.assertEqual(len(null), 1, arm)
            self.assertFalse(any(t.startswith('No statistically significant increase') for t in before['published']))
            self.assertEqual(len(after['published']), len(before['published']) + 1)  # nothing else changed
            self.assertEqual(after['answer_scope'], 'full')


if __name__ == '__main__':
    unittest.main()
