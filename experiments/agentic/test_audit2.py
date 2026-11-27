"""Permanent regressions for Codex audit #2 (2026-11-19): numeric grounding, business grounding,
targeted-retry evidence, round selection and agentic brief revisions. Model-free.

Run from the repository root:  py -3.14 -I -B experiments/agentic/test_audit2.py
Ledger findings (cross-process reservations, crash-truncated records) are covered by
experiments/table-endpoint/test_call_ledger.py.
"""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'experiments' / 'table-endpoint'))
import route  # noqa: E402
from agents import MAX_EVIDENCE, OrchestratorAgent  # noqa: E402
from envelope import to_envelope  # noqa: E402
from numeric_checks import ground_text, screen_business  # noqa: E402
from test_agentic import CORPUS, Provider, Retriever, X, Y, draft, passage, plan, verdicts  # noqa: E402

PROVENANCE = {'execution': 'persistent_index_ui', 'index': {'indexed_records_sha256': 'f' * 64}}

# (name, claim, cited quote, expected status, expected issue or None). Valid and invalid cases come in pairs.
NUMERIC_FIXTURES = [
    # Codex: direction word contradicts the numbers
    ('latency rose (valid)', 'Latency rose from 1.2 seconds to 3.4 seconds.',
     'Latency rose from 1.2 seconds to 3.4 seconds when retrieval was enabled.', 'grounded', None),
    ('latency decreased 1.2s to 3.4s (Codex)', 'Latency decreased from 1.2 seconds to 3.4 seconds.',
     'Latency rose from 1.2 seconds to 3.4 seconds when retrieval was enabled.', 'contradicted', 'reversed_comparison'),
    # Codex: "improved" on a lower-is-better metric
    ('error rate improved 20% to 10% (Codex, valid)', 'Error rate improved from 20% to 10%.',
     'The error rate improved from 20% to 10% with verification.', 'grounded', None),
    ('accuracy improved but fell', 'Accuracy improved from 78.0% to 64.5%.',
     'Accuracy fell from 78.0% to 64.5% after pruning.', 'contradicted', 'reversed_comparison'),
    ('accuracy improved and rose (valid)', 'Accuracy improved from 64.5% to 78.0%.',
     'Accuracy rose from 64.5% to 78.0% after fine-tuning.', 'grounded', None),
    # Codex: flipped signs
    ('same sign (valid)', 'Accuracy changed by -5.2% after pruning.', 'Accuracy changed by -5.2% after pruning.', 'grounded', None),
    ('flipped explicit sign (Codex)', 'Accuracy changed by +5.2% after pruning.', 'Accuracy changed by -5.2% after pruning.',
     'contradicted', 'sign_flip'),
    ('increase stated for a negative value', 'Accuracy increased by 5.2% after pruning.', 'Accuracy changed by -5.2% after pruning.',
     'contradicted', 'sign_flip'),
    # Codex: numbers swapped between subjects
    ('subjects kept (valid)', 'Model X reached 78.0% and Model Y reached 64.5%.',
     'Model X reached 78.0% and Model Y reached 64.5%.', 'grounded', None),
    ('subjects swapped (Codex)', 'Model X reached 64.5% and Model Y reached 78.0%.',
     'Model X reached 78.0% and Model Y reached 64.5%.', 'contradicted', 'subject_mismatch'),
    ('comparative with subjects (valid)', 'Model X reached 78.0%, higher than 64.5% for Model Y.',
     'Model X: 78.0%; Model Y: 64.5%.', 'grounded', None),
    # Codex: a changed condition that reuses "only"
    ('condition kept (valid)', 'Agreement reached 91.4% only on English-language policies.',
     'Agreement reached 91.4% only on English-language policies.', 'grounded', None),
    ('condition changed, "only" reused (Codex)', 'Agreement reached 91.4% only on Spanish-language policies.',
     'Agreement reached 91.4% only on English-language policies.', 'contradicted', 'changed_condition'),
    ('condition dropped', 'Agreement reached 91.4%.', 'Agreement reached 91.4% only on English-language policies.',
     'contradicted', 'missing_condition'),
    # metric, unit and denominator
    ('metric kept (valid)', 'Model X reached 78.0% accuracy.', 'Model X reached 78.0% accuracy on the benchmark.', 'grounded', None),
    ('metric changed', 'Model X reached 78.0% recall.', 'Model X reached 78.0% accuracy on the benchmark.', 'contradicted', 'metric_mismatch'),
    ('unit kept (valid)', 'Accuracy rose by 5 percentage points.', 'Accuracy rose by 5 percentage points.', 'grounded', None),
    ('unit changed', 'Accuracy rose by 5%.', 'Accuracy rose by 5 percentage points.', 'contradicted', 'unit_mismatch'),
    ('denominator kept (valid)', 'The method improved 3 of 7 base models.', 'The method improved 3 of 7 base models.', 'grounded', None),
    ('denominator changed', 'The method improved 3 of 5 base models.', 'The method improved 3 of 7 base models.', 'contradicted', 'denominator_error'),
    # explicit uncertainty: code cannot establish the meaning
    ('improved on a metric of unknown direction', 'Performance improved from 20 to 10.', 'Performance improved from 20 to 10.',
     'uncertain', 'direction_unconfirmed'),
    ('number reused in another context', 'Roughly 78.0 sites adopted the tool.', 'Model X reached 78.0% accuracy on the benchmark.',
     'uncertain', 'context_unconfirmed'),
    # Audit #3: a benchmark number restated about hospitals is a setting transfer, not merely "unconfirmed".
    ('benchmark share restated for hospitals', 'About 78.0% of hospitals adopted the tool.', 'Model X reached 78.0% accuracy on the benchmark.',
     'contradicted', 'setting_transfer'),
    # Audit #3: code cannot tell a different population from a paraphrase, so it must not reject: uncertain.
    ('share of a population code cannot match', '12% of hospitals reported errors.', '12% of clinics reported errors.',
     'uncertain', 'population_unconfirmed'),
    ('share of the same population (valid)', '12% of clinics reported errors.', 'Overall, 12% of clinics reported errors.', 'grounded', None),
]


class NumericGrounding(unittest.TestCase):
    def test_paired_fixtures(self):
        for name, claim, quote, status, issue in NUMERIC_FIXTURES:
            with self.subTest(name):
                result = ground_text(claim, [quote])
                self.assertEqual(result['status'], status, result)
                if issue:
                    self.assertIn(issue, result['contradictions'] + result['uncertain'], result)
                else:
                    self.assertEqual(result['contradictions'], [], result)

    def test_every_codex_case_has_a_valid_twin(self):
        codex = [f for f in NUMERIC_FIXTURES if 'Codex' in f[0]]
        self.assertEqual(len(codex), 5)  # Codex reported five numeric cases
        self.assertGreaterEqual(sum(f[3] == 'grounded' for f in NUMERIC_FIXTURES), 10)

    def test_uncertain_numbers_are_kept_only_with_the_verifier_and_flagged_for_a_person(self):
        CORPUS['U1'] = passage('U1', 'Performance improved from 20 to 10 in the second phase.')
        try:
            uncertain = {'text': 'Performance improved from 20 to 10.', 'kind': 'finding',
                         'support': [{'chunk_id': 'U1', 'quote': 'Performance improved from 20 to 10 in the second phase'}]}
            p = Provider(plan=[plan()], research=[draft(uncertain, limits=[])], verify=[verdicts(('supported', []))])
            r = OrchestratorAgent(generate=p, retrieve=Retriever({'Model X': ['U1']}), top_k=4).run('How did Model X performance change?')
            env = to_envelope(r, top_k=4, provenance=PROVENANCE, context_id='c')
            row = r['summary']['claims'][0]['verification']
            self.assertEqual((row['decision'], row['number_grounding']['status'], row['needs_human_number_check']), ('accepted', 'uncertain', True))
            self.assertEqual(env['result']['provenance']['agentic']['claims_needing_number_check'], [uncertain['text']])
            p = Provider(plan=[plan()], research=[draft(uncertain, limits=[])], verify=[verdicts(('unsupported', ['numeric_misread']), coverage='none')])
            r = OrchestratorAgent(generate=p, retrieve=Retriever({'Model X': ['U1']}), top_k=4).run('How did Model X performance change?')
            self.assertEqual(r['status'], 'insufficient_evidence')
        finally:
            del CORPUS['U1']


# ---------------------------------------------------------------- business grounding
A1 = CORPUS['A1']
VERIFIED = [{'text': X['text'], 'chunk_ids': ['A1']}]
GOOD = {'text': 'Fine-tuned models may improve accuracy on comparable review tasks.', 'chunk_ids': ['A1'],
        'suggested_action': 'Run a scoped pilot on a sample of past cases.', 'assumptions': ['The benchmark resembles the task.']}


def business(*implications, risks=(), limitations=('Evidence comes from a single benchmark.',)):
    return {'status': 'ok', 'industry': 'Healthcare', 'implications': list(implications), 'risks': list(risks), 'limitations': list(limitations)}


def removed(screening):
    return [item for item in screening if item['status'] == 'removed']


class BusinessGrounding(unittest.TestCase):
    def test_cross_context_number_is_removed_even_though_the_number_is_in_the_passage(self):
        row = {**GOOD, 'text': 'About 78.0% of hospitals using fine-tuned models saw better accuracy.'}
        screened, screening = screen_business(business(row), [A1], VERIFIED)
        self.assertEqual(screened['implications'], [])
        self.assertIn('setting_transfer', removed(screening)[0]['issues']['implication'])

    def test_grounded_number_in_its_own_context_is_kept(self):
        row = {**GOOD, 'text': 'Model X reached 78.0% accuracy after fine-tuning, so fine-tuned models may suit review tasks.'}
        screened, _ = screen_business(business(row), [A1], VERIFIED)
        self.assertEqual(len(screened['implications']), 1)

    def test_every_field_is_grounded(self):
        cases = {
            'action': {**GOOD, 'suggested_action': 'Fine-tune models to cut review time by 30%.'},
            'assumption': {**GOOD, 'assumptions': ['Clinical notes are 40% shorter than the benchmark items.']},
            'unsupported advice in action': {**GOOD, 'suggested_action': 'Fine-tuning is production-ready; deploy immediately.'},
            'implication unrelated to verified findings': {**GOOD, 'text': 'Hospitals should restructure billing departments.'},
        }
        for name, row in cases.items():
            with self.subTest(name):
                screened, screening = screen_business(business(row), [A1], VERIFIED)
                self.assertEqual(screened['implications'], [], name)
                self.assertEqual(screened['status'], 'insufficient_evidence', name)

    def test_fabricated_limitations_and_risks_are_removed(self):
        screened, screening = screen_business(business(GOOD, risks=['Accuracy drops to 40% on clinical notes.'],
                                                       limitations=['The study covered 3 hospitals in one country.',
                                                                    'The study was conducted only in German hospitals.',
                                                                    'Transfer to clinical documentation has not been tested.']),
                                              [A1], VERIFIED)
        self.assertEqual(screened['risks'], [])
        self.assertEqual(screened['limitations'], ['Transfer to clinical documentation has not been tested.'])
        reasons = {item['text']: item['issues'] for item in removed(screening)}
        self.assertIn('unsupported_study_fact', reasons['The study was conducted only in German hospitals.']['text'])

    def test_kept_advice_is_labelled_unverified(self):
        _, screening = screen_business(business(GOOD), [A1], VERIFIED)
        self.assertTrue(screening and all(item['status'] == 'kept_unverified' for item in screening))


# ---------------------------------------------------------------- targeted retry and round selection
REQUEST = {'needed': True, 'query': 'Model Y accuracy on the benchmark', 'reason': 'Y result missing'}


def fillers(count):
    return {f'F{i}': passage(f'F{i}', f'Filler passage {i} reports a score of {i}0 points.') for i in range(count)}


def filler_claim(i, j):
    return {'text': f'Fillers {i} and {j} report scores of {i}0 and {j}0 points.', 'kind': 'finding',
            'support': [{'chunk_id': f'F{i}', 'quote': f'Filler passage {i} reports a score of {i}0 points'},
                        {'chunk_id': f'F{j}', 'quote': f'Filler passage {j} reports a score of {j}0 points'}]}


class TargetedRetry(unittest.TestCase):
    def setUp(self):
        self.many = fillers(13)
        CORPUS.update(self.many)
        self.addCleanup(lambda: [CORPUS.pop(k) for k in self.many])

    def run_saturated(self, round1_claims, round1_verdicts):
        p = Provider(plan=[plan()], research=[draft(*round1_claims, limits=[]), draft(X, Y, limits=[])],
                     verify=[verdicts(*round1_verdicts, coverage='partial', request=REQUEST),
                             verdicts(('supported', []), ('supported', []))])
        retriever = Retriever({'Model Y': ['A2'], 'Model X': ['A1'] + list(self.many)})
        return p, OrchestratorAgent(generate=p, retrieve=retriever, top_k=20).run('How accurate is Model X?')

    def test_codex_case_rejected_drafts_citing_all_14_passages_do_not_block_new_evidence(self):
        drafted = [X] + [filler_claim(i, i + 1) for i in range(0, 12, 2)] + [
            {'text': 'Filler 12 reports a score of 120 points.', 'kind': 'finding',
             'support': [{'chunk_id': 'F12', 'quote': 'Filler passage 12 reports a score of 120 points'}]}]
        self.assertEqual(len({s['chunk_id'] for c in drafted for s in c['support']}), MAX_EVIDENCE)  # all 14 cited
        p, r = self.run_saturated(drafted, [('supported', [])] + [('unsupported', ['missing_support'])] * 7)
        second = [prompt for role, prompt in p.prompts if role == 'research'][1]
        self.assertIn('"chunk_id": "A2"', second)
        self.assertEqual(r['verification'][1]['new_passage_ids'], ['A2'])
        self.assertIn('A1', r['verification'][1]['passage_ids'])  # the retained claim's citation stays
        self.assertEqual(len(r['summary']['claims']), 2)

    def test_retained_claims_citing_all_14_still_leave_room_for_new_evidence(self):
        drafted = [X] + [filler_claim(i, i + 1) for i in range(0, 12, 2)] + [
            {'text': 'Filler 12 reports a score of 120 points.', 'kind': 'finding',
             'support': [{'chunk_id': 'F12', 'quote': 'Filler passage 12 reports a score of 120 points'}]}]
        p, r = self.run_saturated(drafted, [('supported', [])] * 8)
        second = r['verification'][1]
        self.assertIn('A2', second['passage_ids'])
        self.assertEqual(len(second['passage_ids']), MAX_EVIDENCE)

    def test_retry_with_nothing_new_spends_no_call(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []), coverage='partial', request=REQUEST)])
        r = OrchestratorAgent(generate=p, retrieve=Retriever({'Model': ['A1']}), top_k=4).run('How accurate is Model X?')
        self.assertEqual(p.calls, ['plan', 'research', 'verify'])
        self.assertTrue([e for e in r['trace'] if e.get('decision') == 'targeted_retrieval_result'])

    def test_best_round_is_chosen_by_supported_coverage_not_claim_count(self):
        # Round 1 keeps two claims but covers the question only partly; round 2 keeps one claim with full coverage.
        two = {'text': 'Model X reached 78.0% accuracy on the benchmark.', 'kind': 'finding',
               'support': [{'chunk_id': 'A1', 'quote': 'Model X reached 78.0% accuracy on the benchmark'}]}
        p = Provider(plan=[plan()], research=[draft(X, two, limits=[]), draft(Y, limits=[])],
                     verify=[verdicts(('supported', []), ('supported', []), coverage='partial', request=REQUEST),
                             verdicts(('supported', []), coverage='full')])
        r = OrchestratorAgent(generate=p, retrieve=Retriever({'Model Y': ['A2'], 'Model X': ['A1']}), top_k=4).run(
            'How accurate is Model X?')
        self.assertEqual(r['selected_round'], 2)
        self.assertEqual([c['text'] for c in r['summary']['claims']], [Y['text']])
        self.assertEqual(r['summary']['answer_scope'], 'full')


# ---------------------------------------------------------------- agentic brief revisions
class Revisions(unittest.TestCase):
    class Research:
        provenance, context_id = PROVENANCE, 'c'

        def check_context(self, context_id):
            pass

    def setUp(self):
        from src.brief_store import BriefStore
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.library = BriefStore(Path(self.tmp.name) / 'briefs.sqlite3')

    def call(self, payload):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))])
        orchestrator = OrchestratorAgent(generate=p, retrieve=Retriever({'Model X': ['A1']}), top_k=4)
        status, body = route.handle({'query': 'How accurate is Model X?', 'context_id': 'c', **payload}, orchestrator=orchestrator,
                                    research=self.Research(), usage=lambda: {'remaining': 40, 'stopped': False, 'cap': 40},
                                    top_k=4, library=self.library)
        return status, body, p.calls

    def test_answers_are_saved_like_baseline_answers(self):
        status, body, _ = self.call({})
        self.assertEqual(status, 200)
        self.assertEqual(body['library']['version']['number'], 1)
        self.assertTrue(self.library.load(body['library']['brief']['id'])['result']['provenance']['agentic'])

    def test_a_revision_becomes_the_next_version_of_the_same_brief(self):
        _, first, _ = self.call({})
        brief = first['library']['brief']
        status, body, _ = self.call({'library_revision': {'brief_id': brief['id'], 'expected_version': brief['current_version']}})
        self.assertEqual(status, 200)
        self.assertEqual((body['library']['brief']['id'], body['library']['version']['number']), (brief['id'], 2))

    def test_stale_unknown_or_malformed_revisions_are_refused_before_any_model_call(self):
        _, first, _ = self.call({})
        brief = first['library']['brief']
        cases = [({'brief_id': brief['id'], 'expected_version': 'stale-version'}, 409),
                 ({'brief_id': 'f' * 32, 'expected_version': 'v'}, 404),
                 ({'brief_id': brief['id']}, 400)]
        for revision, expected in cases:
            status, body, calls = self.call({'library_revision': revision})
            self.assertEqual(status, expected, (revision, body))
            self.assertEqual(calls, [], revision)

    def test_revision_without_a_library_is_refused_not_dropped(self):
        p = Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))])
        orchestrator = OrchestratorAgent(generate=p, retrieve=Retriever({'Model X': ['A1']}), top_k=4)
        status, body = route.handle({'query': 'q', 'context_id': 'c', 'library_revision': {'brief_id': 'a', 'expected_version': 'b'}},
                                    orchestrator=orchestrator, research=self.Research(),
                                    usage=lambda: {'remaining': 40, 'stopped': False, 'cap': 40}, top_k=4)
        self.assertEqual((status, body['code'], p.calls), (400, 'bad_revision', []))


if __name__ == '__main__':
    unittest.main(verbosity=1)
