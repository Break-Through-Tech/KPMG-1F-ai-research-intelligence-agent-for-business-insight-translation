"""Claude's exact repros, scoped controls and provenance/retranslation regressions."""
from copy import deepcopy
from hashlib import sha256
import json
import unittest

from src.business_checks import issues, screen
from src.business_insights import translate_result
from src.research_review import record_human_decision, require_current_review
from tests.test_downstream_business import CONTEXT, business, result_for

REPROS = [
    'It is not a pilot: it is production-ready and guarantees zero errors for audit teams.',
    'Compare memo error logs; there is no doubt it will save costs and increase revenue for the firm.',
    'This is not optional: roll it out firm-wide, it guarantees accuracy.',
]
EVIDENCE = result_for()['evidence']


class CorrectionTests(unittest.TestCase):
    def test_exact_repros_and_mixed_claims_across_every_field(self):
        variants = REPROS + [
            'The study does not establish enterprise savings, but it will save costs.',
            'No guaranteed savings; it will increase revenue.',
            'This is not only production-ready but also guarantees accuracy.',
            'The workflow is not not production-ready.',
            'The study does not establish enterprise savings\nand it guarantees accuracy.',
            'Not a rollout — deploy it at scale if appropriate.',
            'It will not only save costs but increase revenue.',
            'It will not fail to save money.',
        ]
        for value in variants:
            for field in ('text', 'suggested_action', 'assumptions', 'risks', 'limitations'):
                with self.subTest(value=value, field=field):
                    draft = business()
                    if field in ('risks', 'limitations'): draft[field] = [value]
                    else: draft['implications'][0][field] = [value] if field == 'assumptions' else value
                    screened, trace = screen(draft, result_for()['summary'], EVIDENCE, CONTEXT)
                    self.assertNotIn(value, json.dumps(screened))
                    self.assertTrue(any(t['status'] == 'withheld' for t in trace))

    def test_negative_statements_do_not_hide_independent_positive_matches(self):
        for kind in ('implication', 'action', 'assumption', 'risk', 'limitation'):
            for negative in ('The study does not establish enterprise savings.',
                             'The study does not guarantee annual savings.',
                             'No guaranteed savings are established.'):
                self.assertEqual(issues(negative, [EVIDENCE[0]['text']], kind=kind), [])
        draft = business(); draft['limitations'] = ['The study does not establish enterprise savings.']
        screened, _ = screen(draft, result_for()['summary'], EVIDENCE, CONTEXT)
        self.assertIn(draft['limitations'][0], screened['limitations'])
        for value in ('This is not production-ready.', 'The workflow does not guarantee accuracy.'):
            self.assertNotIn('deployment_claim', issues(value, [EVIDENCE[0]['text']], kind='action'))
            self.assertNotIn('exaggerated_benefit', issues(value, [EVIDENCE[0]['text']], kind='action'))

    def test_bounded_deployment_is_allowed_but_conditionals_do_not_excuse_rollout(self):
        action = 'Deploy workflow reconstruction in a sandbox with synthetic traces only if reviewers validate the task switches; compare missing steps before any wider use.'
        result = translate_result(result_for(), context=CONTEXT, generate=lambda p: json.dumps(business(action=action)))
        self.assertEqual(result['result']['business_insight']['status'], 'ok')
        for bounded in (
                'Deploy workflow reconstruction in a limited internal pilot only after reviewers validate reconstructed task switches.',
                'Ask process owners whether to deploy workflow reconstruction; request evidence of missing handoffs first.'):
            self.assertEqual(issues(bounded, [EVIDENCE[0]['text']], kind='action'), [])
        for value in ('If useful, roll it out firm-wide.',
                      action + ' It is production-ready.',
                      action + ' It guarantees accuracy.',
                      'If appropriate, deploy workflow reconstruction across the organization.',
                      'Compare task switches in a sandbox only if reviewed; deploy reconstruction to audit teams.',
                      'Deploy workflow reconstruction across the organization if appropriate.'):
            self.assertTrue(issues(value, [EVIDENCE[0]['text']], kind='action'))

    def test_application_questions_need_no_study_overlap_but_assertions_do(self):
        source = [EVIDENCE[0]['text']]
        for question in ('Confirm whether the ingestion environment has a CI/CD pipeline.',
                         'Transfer depends on whether archived sessions include timestamps.'):
            self.assertEqual(issues(question, source, kind='assumption'), [])
        for value, kind in (
                ('The firm has a standardized CI/CD pipeline.', 'action'),
                ('The firm has a standardized CI/CD pipeline.', 'assumption'),
                ('Confirm whether archived sessions are available, which were already validated.', 'assumption'),
                ('If the study demonstrated that encryption prevents data leaks, compare it locally.', 'action'),
                ('If the study demonstrated that encryption prevents data leaks, compare it locally.', 'assumption'),
                ('If traces are available, then the firm has a standardized CI/CD pipeline.', 'action'),
                ('Compare these logs. The firm has a standardized CI/CD pipeline.', 'action')):
            with self.subTest(value=value, kind=kind):
                self.assertTrue(issues(value, source, kind=kind))

    def test_equivalent_fraction_keeps_bound_metric_and_scope(self):
        source = ['In the benchmark the strongest system closed under a fifth of the gap to the optimum.']
        supported = 'In the benchmark the strongest system closed less than 20% of the gap to the optimum.'
        self.assertEqual(issues(supported, source, kind='implication'), [])
        reverse_wording = supported.replace('less than 20%', 'under a fifth')
        self.assertEqual(issues(reverse_wording, [supported], kind='implication'), [])
        changed_direction = reverse_wording.replace('under a fifth', 'over a fifth')
        self.assertIn('unsupported_or_transferred_number',
                      issues(changed_direction, [supported], kind='implication'))
        for altered in (
                supported.replace('less than 20%', '20%'),
                supported.replace('less than 20%', 'at least 20%'),
                supported.replace('less than 20%', 'less than 25%'),
                supported.replace('gap to the optimum', 'cost of production deployments'),
                supported.replace('In the benchmark', 'In production')):
            with self.subTest(value=altered):
                self.assertIn('unsupported_or_transferred_number', issues(altered, source, kind='implication'))

    def test_proposed_denominator_does_not_exempt_observed_values(self):
        source = [EVIDENCE[0]['text']]
        proposal = 'Compare total inference cost per 1,000 queries at matched routing quality.'
        self.assertEqual(issues(proposal, source, kind='action'), [])
        for value, kind in (
                (proposal + ' The study reported 25% cost savings.', 'action'),
                ('Compare the observed cost per 1,000 queries against the baseline.', 'action'),
                ('The system reduced errors by 10 per 1,000 queries.', 'implication'),
                ('Compare 25% savings per 1,000 queries against the baseline.', 'action')):
            with self.subTest(value=value):
                self.assertIn('unsupported_or_transferred_number', issues(value, source, kind=kind))

    def test_scoped_packet_gap_survives_but_claim_about_full_paper_does_not(self):
        gap = 'The supplied evidence does not establish enterprise ROI or payback.'
        draft = business()
        draft['limitations'] = [gap, 'Evidence gap: The paper never measured enterprise ROI.']
        screened, trace = screen(draft, result_for()['summary'], EVIDENCE, CONTEXT)
        self.assertEqual(screened['limitations'], [gap])
        self.assertIn('unsupported_source_wide_absence', trace[-1]['issues'])

    def test_conditions_and_proposed_metrics_do_not_hide_high_risk_claims(self):
        source = [EVIDENCE[0]['text']]
        safe = ('Confirm whether archived traces include timestamps. '
                'Compare workflow error logs per 1,000 tasks. '
                'The supplied evidence does not establish enterprise ROI or payback.')
        for assertion, expected in (
                ('If traces are available, it could deliver annual savings.', 'financial_projection'),
                ('If usable, it will generate $2 million in revenue.', 'financial_assertion'),
                ('If approved, it is legally compliant.', 'compliance_claim'),
                ('If useful, roll it out firm-wide.', 'deployment_claim'),
                ('If used, it guarantees accuracy.', 'exaggerated_benefit')):
            for kind in ('implication', 'action', 'assumption', 'risk', 'limitation'):
                with self.subTest(assertion=assertion, kind=kind):
                    self.assertIn(expected, issues(safe + ' ' + assertion, source, kind=kind))

    def test_dispatched_prompt_has_no_legacy_policy_and_is_completely_hashed(self):
        prompts = []
        def generate(prompt): prompts.append(prompt); return json.dumps(business())
        envelope = translate_result(result_for(), context=CONTEXT, generate=generate)
        info = envelope['result']['provenance']['business_translation']
        self.assertNotIn('CONCISE BUSINESS POLICY', prompts[0])
        self.assertNotIn('one integrated pilot checklist', prompts[0])
        self.assertEqual(info['complete_prompt_sha256'], sha256(prompts[0].encode()).hexdigest())
        self.assertEqual(info['instruction_suffixes'], [])
        self.assertEqual(info['prompt_version'], '1.2')
        oversized = business(); oversized['implications'][0]['text'] = 'x'*501
        failed = translate_result(result_for(), context=CONTEXT, generate=lambda p: json.dumps(oversized))
        self.assertEqual(failed['error']['stage'], 'business')

    def test_generation_origin_is_independent_of_fixture_research(self):
        # 'model' metadata is simulated here; no actual model call is made.
        origin = {'kind': 'fixture', 'fixture_file': 'handwritten-research.json'}
        first = translate_result(result_for(), context=CONTEXT, generate=lambda p: json.dumps(business()),
            metadata={'provider': 'simulated_model'}, research_input=origin)
        self.assertEqual(first['mode'], 'saved-real-result')
        info = first['result']['provenance']['business_translation']
        self.assertEqual(info['research_input']['kind'], 'fixture')
        self.assertEqual(info['generation_kind'], 'model')
        second = translate_result(first['result'], context=CONTEXT, generate=lambda p: json.dumps(business()),
                                  metadata={'provider': 'simulated_model'}, research_input={'kind': 'recorded_research'})
        self.assertEqual(second['result']['provenance']['business_translation']['research_input'], info['research_input'])

    def test_retranslation_resets_only_new_review_and_retains_original_research(self):
        first = translate_result(result_for(), context=CONTEXT, generate=lambda p: json.dumps(business()))
        reviewed = record_human_decision(first['result'], reviewer='Offline reviewer', decision='approve')
        before = deepcopy(reviewed)
        second = translate_result(reviewed, context=CONTEXT, generate=lambda p: json.dumps(business()))
        self.assertIsNone(second['error'])
        self.assertEqual(reviewed, before)
        self.assertTrue(reviewed['approved'])
        self.assertFalse(second['result']['approved'])
        self.assertEqual(second['result']['human_review']['status'], 'pending')
        self.assertEqual(second['result']['summary'], reviewed['summary'])
        require_current_review(second['result'])

    def test_usefulness_judgments_are_explicit_evaluation_criteria(self):
        envelope = translate_result(result_for(), context=CONTEXT, generate=lambda p: json.dumps(business()))
        self.assertEqual(envelope['result']['provenance']['business_translation']['usefulness_review_criteria'],
                         ['generic_recommendations', 'workflow_parroting', 'semantic_repetition', 'pilot_overreliance'])


if __name__ == '__main__': unittest.main()
