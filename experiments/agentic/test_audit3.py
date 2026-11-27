"""Permanent regressions for Codex audit #3 (2026-11-19): numeric grounding and business-advice
grounding. Paired valid and invalid fixtures, plus end-to-end runs through the orchestrator with a
lenient verifier (so the code, not the model, is what is tested). Model-free.

Run from the repository root:  py -3.14 -I -B experiments/agentic/test_audit3.py
Ledger findings (A/B profile, init race) are in experiments/table-endpoint/test_ab_profile.py.
"""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from agents import OrchestratorAgent  # noqa: E402
from envelope import to_envelope  # noqa: E402
from numeric_checks import ground_text, screen_business  # noqa: E402
from test_agentic import CORPUS, Provider, Retriever, draft, passage, plan, verdicts  # noqa: E402

# (name, claim, cited quote, expected status, expected issue or None). "(Codex)" marks the audit's probes.
FIXTURES = [
    ('unsigned 3.2% against -3.2% (Codex)', 'Accuracy changed by 3.2% after pruning.', 'Accuracy changed by -3.2% after pruning.',
     'contradicted', 'sign_flip'),
    ('decrease stated for -3.2% (valid)', 'Accuracy decreased by 3.2% after pruning.', 'Accuracy changed by -3.2% after pruning.',
     'grounded', None),
    ('-3.2% against -3.2% (valid)', 'Accuracy changed by -3.2% after pruning.', 'Accuracy changed by -3.2% after pruning.', 'grounded', None),
    ('negated claim (Codex)', 'Model X did not reach 78.0% accuracy on the benchmark.', 'Model X reached 78.0% accuracy on the benchmark.',
     'contradicted', 'negation_mismatch'),
    ('negation kept (valid)', 'Model X did not reach 80.0% accuracy on the benchmark.', 'Model X did not reach 80.0% accuracy on the benchmark.',
     'grounded', None),
    ('"not only" is not a negation (valid)', 'Model X not only reached 78.0% accuracy on the benchmark.',
     'Model X reached 78.0% accuracy on the benchmark.', 'grounded', None),
    ('benchmark result moved to clinical notes (Codex)', 'Model X reached 78.0% accuracy on clinical notes in hospitals.',
     'Model X reached 78.0% accuracy on the benchmark.', 'contradicted', 'setting_transfer'),
    ('benchmark result kept on the benchmark (valid)', 'Model X reached 78.0% accuracy on the benchmark.',
     'Model X reached 78.0% accuracy on the benchmark.', 'grounded', None),
    ('clinical result kept clinical (valid)', 'Model X reached 78.0% accuracy on clinical notes.',
     'Model X reached 78.0% accuracy on clinical notes from two hospitals.', 'grounded', None),
    ('0.5 seconds as 500 milliseconds (Codex, valid)', 'Latency was 0.5 seconds per query.', 'Latency was 500 milliseconds per query.',
     'grounded', None),
    ('3 ms against 3 s', 'Latency was 3 ms per query.', 'Latency was 3 s per query.', 'contradicted', 'unit_mismatch'),
    ('$2 million as $2,000,000 (valid)', 'The pilot cost $2 million.', 'The pilot cost $2,000,000.', 'grounded', None),
    ('population paraphrase is not rejected (Codex)', '12% of surveyed hospitals reported errors.',
     # Audit #4: the metric is now read from the number's clause, so this valid paraphrase is grounded (was uncertain).
     '12% of hospital sites in the survey reported errors.', 'grounded', None),
    ('same population, reordered (valid)', '12% of hospitals reported errors in the survey.',
     'In the survey, 12% of hospitals reported errors.', 'grounded', None),
]


def run(question, claim_text, quote, chunk='Q1', verifier=('supported', [])):
    CORPUS[chunk] = passage(chunk, quote)
    try:
        claim = {'text': claim_text, 'kind': 'finding', 'support': [{'chunk_id': chunk, 'quote': quote.rstrip('.')}]}
        p = Provider(plan=[plan()], research=[draft(claim, limits=[])], verify=[verdicts(verifier)])
        return OrchestratorAgent(generate=p, retrieve=Retriever({'Model': [chunk]}), top_k=4).run(question)
    finally:
        del CORPUS[chunk]


class NumericFixtures(unittest.TestCase):
    def test_paired_fixtures(self):
        for name, claim, quote, status, issue in FIXTURES:
            with self.subTest(name):
                result = ground_text(claim, [quote])
                self.assertEqual(result['status'], status, result)
                if issue:
                    self.assertIn(issue, result['contradictions'] + result['uncertain'], result)
                if status != 'contradicted':
                    self.assertEqual(result['contradictions'], [], result)

    def test_every_codex_probe_is_covered(self):
        self.assertEqual(sum('(Codex' in f[0] for f in FIXTURES), 5)


class EndToEnd(unittest.TestCase):
    """A lenient verifier says "supported" every time; the code must still decide correctly."""

    def test_misleading_numbers_are_held_even_when_the_verifier_agrees(self):
        cases = [('Accuracy changed by 3.2% after pruning.', 'Accuracy changed by -3.2% after pruning.', 'sign_flip'),
                 ('Model X did not reach 78.0% accuracy on the benchmark.', 'Model X reached 78.0% accuracy on the benchmark.', 'negation_mismatch'),
                 ('Model X reached 78.0% accuracy on clinical notes in hospitals.', 'Model X reached 78.0% accuracy on the benchmark.', 'setting_transfer')]
        for claim, quote, issue in cases:
            with self.subTest(issue):
                r = run('How did Model X perform?', claim, quote)
                self.assertEqual(r['status'], 'insufficient_evidence')
                self.assertIn(issue, r['summary']['held_claims'][0]['verification']['deterministic']['numbers_and_qualifiers'])

    def test_valid_conversions_and_paraphrases_reach_the_answer(self):
        r = run('How fast is Model X?', 'Model X answered in 0.5 seconds per query.', 'Model X answered in 500 milliseconds per query.')
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['summary']['claims'][0]['verification']['number_grounding']['status'], 'grounded')
        r = run('How many Model X hospitals reported errors?', '12% of surveyed hospitals reported errors with Model X.',
                '12% of hospital sites in the survey reported errors with Model X.')
        row = r['summary']['claims'][0]['verification']
        self.assertEqual((r['status'], row['needs_human_number_check']), ('ok', row['number_grounding']['status'] == 'uncertain'))


VERIFIED = [{'text': 'Model X reached 78.0% accuracy on the benchmark after fine-tuning.', 'chunk_ids': ['A1']}]
PASSAGES = [{'chunk_id': 'A1', 'text': 'Model X reached 78.0% accuracy on the benchmark after fine-tuning.'}]
PROPOSAL = {'text': 'Fine-tuned Model X may suit clinical documentation if its benchmark accuracy transfers.', 'chunk_ids': ['A1'],
            'suggested_action': 'Pilot fine-tuned Model X on a sample of clinical notes before any deployment.',
            'assumptions': ['Clinical notes resemble the benchmark items.']}


def screen(*implications, risks=(), limitations=()):
    return screen_business({'status': 'ok', 'industry': 'Healthcare', 'implications': list(implications),
                            'risks': list(risks), 'limitations': list(limitations)}, PASSAGES, VERIFIED)


def by_text(screening):
    return {item['text']: item for item in screening}


class BusinessSeparation(unittest.TestCase):
    def test_codex_case_clinical_accuracy_from_benchmark_accuracy_is_withheld(self):
        row = {**PROPOSAL, 'text': 'Model X reached 78.0% accuracy in clinical deployment after fine-tuning.'}
        screened, screening = screen(row)
        self.assertEqual(screened['implications'], [])
        item = screening[0]
        self.assertEqual((item['status'], item['categories']['implication']), ('removed', 'withheld'))
        self.assertIn('setting_transfer', item['issues']['implication'])

    def test_factual_deployment_claim_without_numbers_is_withheld(self):
        screened, screening = screen({**PROPOSAL, 'text': 'Fine-tuned Model X is accurate in clinical deployment.'})
        self.assertEqual(screened['implications'], [])
        self.assertIn('setting_transfer', screening[0]['issues']['implication'])

    def test_conditional_proposal_and_explicit_assumption_are_kept_and_labelled(self):
        screened, screening = screen(PROPOSAL)
        self.assertEqual(len(screened['implications']), 1)
        self.assertEqual(screening[0]['categories'], {'implication': 'conditional_proposal', 'action': 'conditional_proposal',
                                                      'assumption 1': 'assumption'})

    def test_every_field_withholds_unsupported_facts(self):
        cases = {
            'action with a transferred number': {**PROPOSAL, 'suggested_action': 'Deploy Model X, which reaches 78.0% accuracy in hospitals.'},
            'assumption with an invented number': {**PROPOSAL, 'assumptions': ['Clinical notes are 40% shorter than benchmark items.']},
        }
        for name, row in cases.items():
            with self.subTest(name):
                screened, _ = screen(row)
                self.assertEqual(screened['implications'], [], name)
        screened, screening = screen(PROPOSAL,
                                     risks=['Model X reached 78.0% accuracy with real patients.', 'Benchmark accuracy may not transfer to clinical notes.'],
                                     limitations=['The study covered 3 hospitals in one country.', 'Model X was validated in production at two hospitals.',
                                                  'The evidence comes from a single benchmark.'])
        self.assertEqual(screened['risks'], ['Benchmark accuracy may not transfer to clinical notes.'])
        self.assertEqual(screened['limitations'], ['The evidence comes from a single benchmark.'])
        items = by_text(screening)
        self.assertEqual(items['Benchmark accuracy may not transfer to clinical notes.']['categories']['text'], 'conditional_proposal')
        self.assertEqual(items['The evidence comes from a single benchmark.']['categories']['text'], 'caveat')
        self.assertEqual(items['Model X was validated in production at two hospitals.']['status'], 'removed')

    def test_verified_findings_stay_separate_from_business_output(self):
        CORPUS['B1'] = passage('B1', 'Model X reached 78.0% accuracy on the benchmark after fine-tuning.')
        try:
            claim = {'text': 'Model X reached 78.0% accuracy on the benchmark after fine-tuning.', 'kind': 'finding',
                     'support': [{'chunk_id': 'B1', 'quote': 'Model X reached 78.0% accuracy on the benchmark after fine-tuning'}]}
            unsupported = {**PROPOSAL, 'chunk_ids': ['B1'], 'text': 'Model X reached 78.0% accuracy in clinical deployment after fine-tuning.'}
            supported = {**PROPOSAL, 'chunk_ids': ['B1']}
            business = {'status': 'ok', 'industry': 'Healthcare', 'implications': [unsupported, supported], 'risks': [],
                        'limitations': ['The evidence comes from a single benchmark.']}
            p = Provider(plan=[plan()], research=[draft(claim, limits=[])], verify=[verdicts(('supported', []))], business=[business])
            r = OrchestratorAgent(generate=p, retrieve=Retriever({'Model': ['B1']}), top_k=4).run('How accurate is Model X?', industry='Healthcare')
            env = to_envelope(r, top_k=4, provenance={'index': {'indexed_records_sha256': 'f' * 64}}, context_id='c')
        finally:
            del CORPUS['B1']
        result = env['result']
        self.assertEqual([c['text'] for c in result['summary']['claims']], [claim['text']])          # verified finding
        self.assertEqual([i['text'] for i in result['business_insight']['implications']], [PROPOSAL['text']])  # proposal only
        withheld = [s for s in result['provenance']['agentic']['business_screening'] if s['status'] == 'removed']
        self.assertEqual([s['text'] for s in withheld], [unsupported['text']])                        # withheld, recorded


if __name__ == '__main__':
    unittest.main(verbosity=1)
