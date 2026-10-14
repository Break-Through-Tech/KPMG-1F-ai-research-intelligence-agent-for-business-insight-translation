"""Offline translator contract checks; canned replies are not model findings."""
from copy import deepcopy
from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import main
from src.business_translation import PROMPT_PATH, prompt_provenance, translate
from src.research_pipeline import PipelineError, run_research


class BusinessTranslationTests(unittest.TestCase):
    def setUp(self):
        self.fixtures = json.loads((PROMPT_PATH.parent / 'fixtures.json').read_text())
        self.fixture = deepcopy(self.fixtures[0])

    def call(self, *, output=None, fixture=None, generate=None):
        fixture = fixture or self.fixture
        generator = generate if generate is not None else Mock(
            return_value=json.dumps(fixture['expected'] if output is None else output))
        return translate(fixture['summary'], fixture['evidence'],
                         industry=fixture['industry'], generate=generator)

    def test_bounded_fixture_preserves_inputs_and_versioned_prompt(self):
        before = deepcopy(self.fixture)
        generator = Mock(return_value=json.dumps(self.fixture['expected']))
        self.assertEqual(self.call(generate=generator), self.fixture['expected'])
        self.assertEqual(before, self.fixture)
        prompt = generator.call_args.args[0]
        self.assertIn('Prompt ID: business-translation/baseline; version: 1.1', prompt)
        self.assertIn(json.dumps(self.fixture['summary']), prompt)
        self.assertIn(json.dumps(self.fixture['evidence']), prompt)
        self.assertEqual(generator.call_count, 1)

    def test_conflicting_fixture_retains_both_sides_and_citations(self):
        fixture = self.fixtures[2]
        generator = Mock(return_value=json.dumps(fixture['expected']))
        output = self.call(fixture=fixture, generate=generator)
        self.assertEqual(output, fixture['expected'])
        self.assertEqual(output['implications'][0]['chunk_ids'],
                         [p['chunk_id'] for p in fixture['evidence']])
        for passage in fixture['evidence']:
            self.assertIn(passage['text'], generator.call_args.args[0])

    def test_insufficient_summary_and_empty_evidence_skip_generation(self):
        for fixture in (self.fixtures[1], {**self.fixture, 'evidence': []}):
            with self.subTest(industry=fixture['industry']):
                generator = Mock(side_effect=AssertionError('must not generate'))
                output = self.call(fixture=fixture, generate=generator)
                self.assertEqual(output['status'], 'insufficient_evidence')
                self.assertEqual(output['implications'], [])
                self.assertTrue(output['limitations'])
                self.assertEqual(output['industry'], fixture['industry'])
                generator.assert_not_called()
        output = self.call(fixture=self.fixtures[1])
        self.assertIn('No evaluated retail outcome.', output['limitations'])

    def test_missing_industry_and_noncallable_generator_are_rejected(self):
        for industry in (None, '', ' ', 42):
            with self.subTest(industry=industry), self.assertRaisesRegex(ValueError, 'industry'):
                translate(self.fixture['summary'], self.fixture['evidence'],
                          industry=industry, generate=Mock())
        with self.assertRaisesRegex(ValueError, 'callable'):
            self.call(generate=42)

    def test_original_industry_and_dollar_data_are_not_retemplated(self):
        self.fixture['industry'] = ' Insurance $summary_json '
        self.fixture['expected']['industry'] = self.fixture['industry']
        self.fixture['evidence'][0]['text'] += ' $industry ${evidence_json}'
        generator = Mock(return_value=json.dumps(self.fixture['expected']))
        output = self.call(generate=generator)
        self.assertEqual(output['industry'], self.fixture['industry'])
        self.assertIn('$industry ${evidence_json}', generator.call_args.args[0])
        bad = deepcopy(output)
        bad['industry'] = 'Insurance'
        with self.assertRaisesRegex(ValueError, 'industry'):
            self.call(output=bad)

    def test_invalid_evidence_and_summary_are_rejected_before_generation(self):
        bad_inputs = []
        for change in (None, {}, [{'chunk_id': 'a', 'text': ' '}],
                       self.fixture['evidence'] * 2):
            bad_inputs.append({**self.fixture, 'evidence': change})
        for summary in (None, {}, {**self.fixture['summary'], 'claims': []},
                        {**self.fixture['summary'], 'status': []},
                        {**self.fixture['summary'], 'limitations': [' ']},
                        {**self.fixture['summary'], 'status': 'insufficient_evidence'}):
            bad_inputs.append({**self.fixture, 'summary': summary})
        for fixture in bad_inputs:
            generator = Mock()
            with self.subTest(fixture=fixture), self.assertRaises(ValueError):
                self.call(fixture=fixture, generate=generator)
            generator.assert_not_called()

    def test_summary_and_business_reject_unknown_or_duplicate_citations(self):
        for citations in (['invented'], [], ['synthetic-benefit-1'] * 2, [{}]):
            with self.subTest(citations=citations):
                fixture = deepcopy(self.fixture)
                fixture['summary']['claims'][0]['chunk_ids'] = citations
                with self.assertRaisesRegex(ValueError, 'Citations'):
                    self.call(fixture=fixture)
                output = deepcopy(self.fixture['expected'])
                output['implications'][0]['chunk_ids'] = citations
                with self.assertRaises(ValueError):
                    self.call(output=output)

    def test_exact_response_contract_rejects_missing_and_extra_fields(self):
        for field in self.fixture['expected']:
            output = deepcopy(self.fixture['expected'])
            del output[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                self.call(output=output)
        for field in ('confidence', 'approved', 'reviewer'):
            output = {**self.fixture['expected'], field: True}
            with self.subTest(extra=field), self.assertRaises(ValueError):
                self.call(output=output)
            output = deepcopy(self.fixture['expected'])
            output['implications'][0][field] = True
            with self.subTest(implication_extra=field), self.assertRaises(ValueError):
                self.call(output=output)

    def test_invalid_implication_and_list_fields_are_rejected(self):
        for field, value in [('text', ' '), ('suggested_action', 42),
                             ('assumptions', 'not a list'), ('assumptions', [' '])]:
            output = deepcopy(self.fixture['expected'])
            output['implications'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.call(output=output)
        for field, value in [('risks', None), ('limitations', [42]),
                             ('risks', [' ']), ('implications', []), ('status', [])]:
            output = {**self.fixture['expected'], field: value}
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.call(output=output)

    def test_provider_abstention_requires_empty_implications_and_gaps(self):
        output = {'status': 'insufficient_evidence', 'industry': self.fixture['industry'],
                  'implications': [], 'risks': [], 'limitations': ['No transferable outcome.']}
        self.assertEqual(self.call(output=output), output)
        for change in ({'implications': self.fixture['expected']['implications']},
                       {'limitations': []}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.call(output={**output, **change})

    def test_provider_failure_is_sanitized_even_for_pipeline_errors(self):
        for error in (RuntimeError('SECRET-provider-payload'),
                      PipelineError('SECRET-provider-payload')):
            with self.subTest(error=type(error).__name__), self.assertRaises(PipelineError) as caught:
                self.call(generate=Mock(side_effect=error))
            self.assertNotIn('SECRET', str(caught.exception))
            self.assertTrue(caught.exception.__suppress_context__)

    def test_strict_json_rejects_fences_duplicates_nonfinite_and_nonobjects(self):
        for raw in ('not JSON', '```json\n{}\n```', '{"status":"ok","status":"ok"}',
                    '{"value":NaN}', '{"value":Infinity}', '[]', 'null', '"text"', '', None, {}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.call(generate=Mock(return_value=raw))

    def test_nonfinite_input_and_missing_prompt_fail_before_generation(self):
        self.fixture['evidence'][0]['distance'] = float('nan')
        generator = Mock()
        with self.assertRaisesRegex(ValueError, 'finite'):
            self.call(generate=generator)
        generator.assert_not_called()
        self.fixture['evidence'][0]['distance'] = None
        with patch('src.business_translation.PROMPT_PATH', Path('/missing/business-prompt')):
            with self.assertRaisesRegex(PipelineError, 'prompt unavailable'):
                self.call(generate=generator)
            with self.assertRaises(PipelineError):
                prompt_provenance()
        generator.assert_not_called()

    def test_prompt_provenance_binds_selected_artifact(self):
        self.assertEqual(prompt_provenance(), {
            'prompt_id': 'business-translation/baseline', 'prompt_version': '1.1',
            'template_sha256': sha256(PROMPT_PATH.read_bytes()).hexdigest()})

    def test_pipeline_integration_preserves_citations_and_pending_review(self):
        fixture = self.fixture
        before = deepcopy(fixture)
        result = run_research({'query': fixture['summary']['query'], 'industry': fixture['industry']},
            retrieve=lambda q, k: fixture['evidence'],
            summarize_fn=lambda q, p: fixture['summary'],
            translate_fn=lambda s, p, *, industry: translate(s, p, industry=industry,
                generate=lambda prompt: json.dumps(fixture['expected'])))
        self.assertEqual(result['business_insight'], fixture['expected'])
        self.assertEqual(result['evidence'], fixture['evidence'])
        self.assertEqual(result['human_review']['status'], 'pending')
        self.assertFalse(result['approved'])
        self.assertEqual(fixture, before)

    def test_existing_cli_loads_translator_without_shared_file_changes(self):
        fixture = self.fixture
        generate = Mock(side_effect=[json.dumps(fixture['summary']), json.dumps(fixture['expected'])])
        with patch.object(main, 'persistent_retrieve', return_value=fixture['evidence']), \
                patch.object(main, 'create_generate', return_value=(generate, {'provider': 'fixture'})), \
                redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main.main(['--query', fixture['summary']['query'], '--mode', 'business',
                '--industry', fixture['industry'],
                '--translation-adapter', 'src.business_translation:translate']), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result['business_insight'], fixture['expected'])
        self.assertFalse(result['approved'])

    def test_import_is_lazy_without_model_or_provider_modules(self):
        result = subprocess.run([sys.executable, '-c',
            'import src.business_translation, sys; '
            'assert "google.genai" not in sys.modules; '
            'assert "chromadb" not in sys.modules; '
            'assert "sentence_transformers" not in sys.modules'],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
