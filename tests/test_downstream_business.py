"""Canned transport/adversarial checks, never model quality or generalization."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from src.business_handoff import accepted_research
from src.business_insights import translate_result, business_context
from src.business_translation import translate
from src.research_pipeline import run_research, content_fingerprint
from src.research_review import require_current_review
from tests.test_indexed_research import PASSAGES

FIXTURES = Path(__file__).parent / 'fixtures/business/downstream-reference-v1.json'


def result_for(text='The workflow reconstruction preserved task switches in observed traces.'):
    evidence = [{**deepcopy(PASSAGES[0]), 'text': text}]
    summary = {'status': 'ok', 'query': 'What workflow decision does this inform?',
        'claims': [{'text': text, 'kind': 'finding', 'chunk_ids': ['p1'],
                    'support': [{'chunk_id': 'p1', 'quote': text}]}],
        'limitations': [], 'limitation_support': [],
        'quality_review': {'coverage': 'partial', 'gap': 'Transfer has not been established.'},
        'answer_scope': 'partial', 'answer_lead': 'Transfer to this workflow has not been established.'}
    return run_research({'query': summary['query']}, retrieve=lambda q,k: evidence,
                        summarize_fn=lambda q,p: summary)


CONTEXT = {'industry': 'Advisory', 'workflow': 'Documenting onboarding task switches',
           'decision': 'Which handoffs should a process owner verify?'}


def business(text=None, action=None):
    return {'status': 'ok', 'industry': CONTEXT['industry'], 'implications': [{
        'text': text or 'The workflow reconstruction preserved task switches in observed traces. This could help identify onboarding handoffs missing from process documentation.',
        'chunk_ids': ['p1'], 'suggested_action': action or 'Ask process owners to compare reconstructed task switches with documented onboarding handoffs and record missing steps.',
        'assumptions': ['Transfer to onboarding remains untested.']}],
        'risks': [], 'limitations': ['Transfer gap: onboarding handoffs were not evaluated.']}


class DownstreamTests(unittest.TestCase):
    def call(self, response=None, result=None, context=None):
        generator = Mock(return_value=json.dumps(response or business()))
        envelope = translate_result(result or result_for(), context=context or CONTEXT,
            generate=generator, metadata={'provider': 'injected', 'api_key': 'SECRET'})
        return envelope, generator

    def test_one_call_preserves_research_and_supports_existing_contract(self):
        source = result_for(); before = deepcopy(source)
        envelope, generator = self.call(result=source)
        self.assertIsNone(envelope['error'])
        self.assertEqual(envelope['result']['business_insight']['status'], 'ok')
        self.assertEqual(generator.call_count, 1)
        self.assertEqual(source, before)
        for field in ('summary', 'evidence'):
            self.assertEqual(envelope['result'][field], source[field])
        require_current_review(envelope['result'])
        self.assertNotIn('SECRET', json.dumps(envelope))
        self.assertIn('downstream; version: 1.2', generator.call_args.args[0])

    def test_quote_bounds_exclude_same_chunk_tail_and_audit(self):
        source = result_for(); summary = source['summary']; evidence = source['evidence']
        evidence[0]['text'] += ' SECRET_UNACCEPTED_TAIL with speculative revenue.'
        summary['held_claims'] = [{'text': 'SECRET_HELD'}]
        summary['quality_review']['original_claims'] = [{'text': 'SECRET_DRAFT'}]
        summary['claims'][0]['audit'] = 'SECRET_NESTED'
        evidence.append({**deepcopy(evidence[0]), 'chunk_id': 'p2', 'text': 'SECRET_UNRELATED'})
        clean, bounded, bounds = accepted_research(summary, evidence)
        self.assertEqual(bounds, {'p1': 'accepted_quotes'})
        self.assertNotIn('SECRET', json.dumps([clean, bounded]))
        self.assertEqual(bounded[0]['source_url'], evidence[0]['source_url'])

    def test_caveat_quotes_survive_and_interpretations_do_not(self):
        source = result_for(); summary = source['summary']; evidence = source['evidence']
        evidence.append({**deepcopy(evidence[0]), 'chunk_id': 'p2', 'text': 'The authors did not evaluate onboarding.'})
        summary['limitation_support'] = [{'text': evidence[1]['text'], 'chunk_ids': ['p2'],
            'support': [{'chunk_id': 'p2', 'quote': evidence[1]['text']}]}]
        summary['claims'].append({'text': 'SECRET_INTERPRETATION', 'kind': 'interpretation', 'chunk_ids': ['p2']})
        clean, bounded, _ = accepted_research(summary, evidence)
        self.assertEqual([p['chunk_id'] for p in bounded], ['p1', 'p2'])
        self.assertNotIn('SECRET', json.dumps(clean))
        self.assertIn('did not evaluate', clean['limitations'][-1])

    def test_invalid_quote_never_falls_back_to_whole_passage(self):
        for mutation in ('wrong_quote', 'missing_source', 'incomplete_support'):
            source = result_for()
            if mutation == 'wrong_quote': source['summary']['claims'][0]['support'][0]['quote'] = 'invented'
            elif mutation == 'missing_source': source['summary']['claims'][0]['support'][0]['chunk_id'] = 'absent'
            else: source['summary']['claims'][0]['support'] = []
            source['review_fingerprint'] = content_fingerprint(source)
            envelope, generator = self.call(result=source)
            self.assertEqual(envelope['error']['stage'], 'business')
            generator.assert_not_called()
            self.assertEqual(envelope['result']['summary'], source['summary'])

    def test_review_required_even_when_quality_check_flag_would_be_false(self):
        source = result_for(); source['summary'].pop('quality_review')
        source['review_fingerprint'] = content_fingerprint(source)
        envelope, generator = self.call(result=source)
        generator.assert_not_called()
        self.assertNotIn('business_insight', envelope['result'])

    def test_reviewed_legacy_without_quotes_records_passage_boundary(self):
        source = result_for(); source['summary']['claims'][0].pop('support')
        _, _, bounds = accepted_research(source['summary'], source['evidence'])
        self.assertEqual(bounds, {'p1': 'passage'})

    def test_integrity_and_context_errors_precede_generation(self):
        source = result_for(); source['summary']['claims'][0]['text'] = 'Edited'
        gen = Mock()
        with self.assertRaises(ValueError): translate_result(source, context=CONTEXT, generate=gen)
        with self.assertRaises(ValueError): translate_result(result_for(), context=CONTEXT, generate=gen, expected_fingerprint='stale')
        for context in ({}, {'industry': 'Banking'}, {**CONTEXT, 'workflow': ' '}, {**CONTEXT, 'secret': 'x'}):
            with self.assertRaises(ValueError): business_context(context)
        gen.assert_not_called()

    def test_insufficient_research_skips_generation(self):
        source = result_for(); source['summary'].update(status='insufficient_evidence', claims=[])
        source['review_fingerprint'] = content_fingerprint(source)
        envelope, generator = self.call(result=source)
        generator.assert_not_called()
        self.assertEqual(envelope['result']['business_insight']['status'], 'insufficient_evidence')
        self.assertNotIn('passed the evidence and advice checks',
                         ' '.join(envelope['result']['business_insight']['limitations']))
        self.assertIsNone(envelope['error'])

    def test_provider_failure_and_malformed_output_keep_research_and_are_sanitized(self):
        for gen in (Mock(side_effect=RuntimeError('SECRET')), Mock(return_value='not JSON')):
            source = result_for()
            envelope = translate_result(source, context=CONTEXT, generate=gen)
            self.assertEqual(envelope['result']['summary'], source['summary'])
            self.assertEqual(envelope['error']['stage'], 'business')
            self.assertNotIn('SECRET', json.dumps(envelope))
            self.assertEqual(gen.call_count, 1)

    def test_no_semantic_screen_publishes_structurally_valid_output_unchanged(self):
        # The validated Hydrogen configuration has no semantic publication gate.
        # Wording a regex screen used to withhold is now published as generated.
        for value in ('This may generate annual savings for onboarding.',
                      'Workflow reconstruction improved accuracy by 99% in onboarding.'):
            with self.subTest(value=value):
                envelope, _ = self.call(business(text=value))
                output = envelope['result']['business_insight']
                self.assertEqual(output['status'], 'ok')
                self.assertEqual(output['implications'][0]['text'], value)
                gate = envelope['result']['provenance']['business_translation']['publication_gate']
                self.assertEqual(gate['policy'], 'structural-only-v1')
                self.assertNotIn('screening', envelope['result']['provenance']['business_translation'])

    def test_structural_checks_still_reject_unknown_citations_and_wrong_industry(self):
        bad_citation = business(); bad_citation['implications'][0]['chunk_ids'] = ['not-accepted']
        wrong_industry = business(); wrong_industry['industry'] = 'Banking'
        extra_field = business(); extra_field['confidence'] = 0.9
        for output in (bad_citation, wrong_industry, extra_field):
            envelope, _ = self.call(output)
            self.assertEqual(envelope['error']['code'], 'business_failed')
            self.assertNotIn('business_insight', envelope['result'])

    def test_distinct_transfer_conditions_are_not_deduplicated(self):
        output = business(); other = deepcopy(output['implications'][0])
        other.update(text='Task switches could inform onboarding documentation when traces omit parallel work.',
                     assumptions=['Coverage of parallel work remains untested.'])
        output['implications'].append(other)
        envelope, _ = self.call(output)
        self.assertEqual(len(envelope['result']['business_insight']['implications']), 2)

    def test_supported_study_number_survives_conditional_transfer(self):
        evidence = 'The travel study evaluated 92 student commuters and found travel habits useful for prediction.'
        output = business(text=evidence + ' This could inform travel survey collection.',
                          action='Compare travel-habit inputs with current survey questions and document missing travel patterns.')
        envelope, _ = self.call(output, result=result_for(evidence),
            context={**CONTEXT, 'workflow': 'Travel survey collection'})
        self.assertEqual(envelope['result']['business_insight']['status'], 'ok')

    def test_observed_study_cost_is_not_an_organization_savings_projection(self):
        evidence = 'The routing study measured request cost of $2 per task in the benchmark.'
        output = business(text=evidence + ' This could inform which routing costs to compare.',
                          action='Compare routing request cost and task quality before deciding which routing checks to retain.')
        envelope, _ = self.call(output, result=result_for(evidence))
        self.assertEqual(envelope['result']['business_insight']['status'], 'ok')

    def test_missing_prompt_is_an_isolated_failure(self):
        with patch('src.business_insights.PROMPT', Path('/missing/prompt.txt')):
            envelope, gen = self.call()
        self.assertEqual(envelope['error']['stage'], 'business')
        gen.assert_not_called()

    def test_verbose_output_is_rejected_without_truncating_material_uncertainty(self):
        output = business(); output['limitations'] = ['Evidence gap: ' + 'x'*501]
        envelope, _ = self.call(output)
        self.assertEqual(envelope['error']['stage'], 'business')
        self.assertNotIn('business_insight', envelope['result'])

    def test_conditional_new_workflow_is_not_rejected_for_industry_transfer(self):
        context = {'industry': 'Education', 'workflow': 'Documenting student-support handoffs', 'decision': ''}
        output = business()
        output['industry'] = 'Education'
        output['implications'][0].update(
            text='Workflow reconstruction preserved task switches in observed traces. This could help document student-support handoffs.',
            suggested_action='Ask support staff to compare reconstructed task switches with documented student-support handoffs; record omitted steps.',
            assumptions=['Transfer to student-support work remains untested.'])
        envelope, _ = self.call(output, context=context)
        self.assertEqual(envelope['result']['business_insight']['status'], 'ok')

    def test_cli_fixture_path_marks_output_and_refuses_overwrite(self):
        import sys
        import tempfile
        from src.business_insights import main
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'source.json').write_text(json.dumps(result_for()))
            (root/'response.json').write_text(json.dumps(business()))
            argv = ['business_insights', '--input', str(root/'source.json'), '--output', str(root/'out.json'),
                    '--industry', 'Advisory', '--workflow', CONTEXT['workflow'],
                    '--fixture-response', str(root/'response.json')]
            with patch.object(sys, 'argv', argv): main()
            data = json.loads((root/'out.json').read_text())
            self.assertEqual(data['mode'], 'fixture')
            self.assertEqual(data['result']['business_insight']['status'], 'ok')
            with patch.object(sys, 'argv', argv), patch('sys.stderr'), self.assertRaises(SystemExit): main()

    def test_research_only_does_not_route_business_or_add_calls(self):
        from tests.test_indexed_research import adapter, generator
        generate = Mock(side_effect=generator)
        research = adapter(generate=generate)
        with patch('src.indexed_research.translate') as translator:
            envelope = research.execute({'query': 'Compare the studies.', 'context_id': research.context_id})
        translator.assert_not_called()
        self.assertEqual(generate.call_count, 1)  # Existing baseline; no translation.
        self.assertNotIn('business_translation', envelope['result']['provenance'])
        self.assertNotIn('business_insight', envelope['result'])

    def test_gaps_preserved_and_new_context_changes_provenance(self):
        first, _ = self.call()
        second, _ = self.call(context={**CONTEXT, 'decision': 'Review onboarding documentation'})
        info = first['result']['provenance']['business_translation']
        self.assertNotEqual(info['context_sha256'], second['result']['provenance']['business_translation']['context_sha256'])
        self.assertEqual(info['attempted_calls'], 1)
        self.assertIn('Transfer to this workflow', first['result']['business_insight']['limitations'][0])
        self.assertFalse(first['result']['approved'])

    def test_reference_aligned_fixtures_are_not_model_quality_results(self):
        cases = json.loads(FIXTURES.read_text())
        self.assertEqual(cases['execution'], 'handwritten_canned_fixtures')
        self.assertEqual(cases['split'], 'reference_aligned_development')
        self.assertEqual(len(cases['cases']), 5)
        for case in cases['cases']:
            with self.subTest(case=case['id']):
                envelope, gen = self.call(case['business'], result_for(case['evidence']), case['context'])
                self.assertIsNone(envelope['error'])
                self.assertEqual(envelope['result']['business_insight']['status'], 'ok')
                self.assertEqual(gen.call_count, 1)


if __name__ == '__main__': unittest.main()
