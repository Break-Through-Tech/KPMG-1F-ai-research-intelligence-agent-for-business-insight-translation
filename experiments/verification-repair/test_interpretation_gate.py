"""Labelled-interpretation gate: valid bounded business recommendations publish; explanations, misattributions and
unsupported advice stay held. Run: python -I test_interpretation_gate.py"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / 'agentic'), str(HERE.parents[1]), str(HERE.parent / 'agentic-handoff')]
import numeric_checks_v2 as nc  # noqa: E402
from interpretation_gate import gate  # noqa: E402
from test_scope_review import C16, C17, IMAGE_CAUSE, MISATTRIBUTED  # noqa: E402

C0299 = {'chunk_id': 'c0299', 'text': 'More generally, model weights do not guarantee transparency on the upstream resources used to '
         'build the foundation model (e.g. data sources, labor practices, energy expenditure) nor transparency on the '
         'downstream impact of the foundation model (e.g. affected markets, adverse events, usage policy enforcement).'}
FINDINGS = ['Model weights do not guarantee transparency on data sources, labor practices or energy expenditure, nor on '
            'downstream impact such as adverse events and usage policy enforcement.']
DUE_DILIGENCE = ('For vendor due diligence, these findings support prioritizing requests for evidence on training-data '
                 'sources, labor practices, energy expenditure, and deployed impacts, including adverse events and '
                 'usage-policy enforcement.')


def row(verdict='partially_supported', issues=('missing_support',)):
    return {'deterministic': {'quote_membership': 'passed'},
            'automated': {'verdict': verdict, 'issues': list(issues), 'reason': 'r'}}


def claim(text, quote=C0299['text'][:60], cid='c0299'):
    return {'text': text, 'kind': 'interpretation', 'chunk_ids': [cid], 'support': [{'chunk_id': cid, 'quote': quote}]}


def run(text, verdict=row(), passages=(C0299,), findings=FINDINGS, **kw):
    return gate(verdict, claim(text, **kw), nc, list(passages), findings)


class Gate(unittest.TestCase):
    def test_bounded_recommendation_publishes(self):
        self.assertEqual(run(DUE_DILIGENCE), [])

    def test_f01_misattribution_stays_held(self):
        c = dict(MISATTRIBUTED)
        failed = gate(row('supported', ()), c, nc, [C16, C17], ['Accuracy increases from 0% with the Baseline framework '
                                                                'using Gemma 3 to 40% with MultiFinRAG using Gemma 3.'])
        self.assertIn('G5', failed)

    def test_causal_explanation_stays_held(self):
        failed = gate(row('supported', ()), dict(IMAGE_CAUSE), nc, [C16], ['The Baseline cannot extract image details.'])
        self.assertTrue({'G4', 'G5'} & set(failed))

    def test_contradicted_or_unsupported_premises_stay_held(self):
        self.assertIn('G3', run(DUE_DILIGENCE, verdict=row('unsupported', ())))
        self.assertIn('G3', run(DUE_DILIGENCE, verdict=row('partially_supported', ('missing_condition',))))

    def test_roi_and_readiness_claims_stay_held(self):
        self.assertTrue(any(f.startswith('G6') for f in run(DUE_DILIGENCE + ' This will cut costs by 30% and the tool is production-ready.')))

    def test_workforce_replacement_stays_held(self):
        self.assertTrue(any(f.startswith('G6') for f in run('For vendor due diligence, these findings support using the index to replace analysts.')))

    def test_unverified_number_stays_held(self):
        self.assertIn('G2', run('For vendor due diligence, these findings support requesting evidence from the 12 weakest vendors.'))

    def test_must_build_on_published_findings(self):
        self.assertIn('G7', run(DUE_DILIGENCE, findings=['Larger models scored higher on reasoning benchmarks.']))

    def test_inexact_quote_stays_held(self):
        bad = row()
        bad['deterministic']['quote_membership'] = 'failed'
        self.assertIn('G1', run(DUE_DILIGENCE, verdict=bad))


if __name__ == '__main__':
    unittest.main()
