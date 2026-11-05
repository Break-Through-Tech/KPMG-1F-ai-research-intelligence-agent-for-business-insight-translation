"""Source-membership regressions, not model-quality or entailment evidence."""
from copy import deepcopy
import io
import json
from contextlib import redirect_stdout, redirect_stderr
import unittest
from unittest.mock import Mock, patch

from src.evidence_led import summarize, prompt_provenance
from src.research_pipeline import run_research
from src.source_spans import build_spans, hydrate_selection, render_menu


class SourceSpanTests(unittest.TestCase):
    def setUp(self):
        self.text = 'The model’s “fully verified” output retains café, λ and [1].'
        self.passages = [{'chunk_id': 'paper_v1_c0001', 'text': self.text,
                          'source': 'synthetic', 'title': 'Synthetic Unicode source',
                          'source_url': None, 'pdf_url': None, 'arxiv_id': None,
                          'page_number': None}]
        self.selection = {'facts': [{'span_id': 's0000', 'finding': 'The source describes verified output.',
                                    'relevance': 'direct'}],
                          'coverage_gaps': [], 'answerability': 'full'}
        self.answer = {'status': 'ok', 'claims': [{'text': 'The source describes fully verified output.',
                                                  'fact_ids': [0]}], 'limitations': []}

    def run_summary(self, selection=None, **options):
        provider = Mock(side_effect=[json.dumps(selection or self.selection), json.dumps(self.answer)])
        return summarize('What does the source describe?', self.passages,
                         generate=provider, quote_selection=True, **options), provider

    def test_exact_unicode_hydration_citation_and_pending_review(self):
        before = deepcopy(self.passages)
        provider = Mock(side_effect=[json.dumps(self.selection), json.dumps(self.answer)])
        provider.supports_response_schema = True
        result = run_research({'query': 'Describe the output'},
            retrieve=lambda q, k: self.passages,
            summarize_fn=lambda q, p: summarize(q, p, generate=provider, quote_selection=True))
        summary = result['summary']
        fact = summary['evidence_ledger']['facts'][0]
        self.assertEqual(fact['quote'], self.text)
        self.assertEqual(fact['chunk_id'], self.passages[0]['chunk_id'])
        self.assertEqual(summary['claims'][0]['chunk_ids'], [fact['chunk_id']])
        self.assertEqual(fact['source_span']['start'], 0)
        self.assertEqual(fact['source_span']['end'], len(self.text))
        self.assertEqual(self.passages, before)
        self.assertFalse(result['approved'])
        self.assertEqual(summary['extraction_validation_attempts'], 1)
        self.assertIn(self.text, provider.call_args_list[0].args[0])
        # Synthesis receives hydrated exact source text plus span provenance.
        self.assertIn('source_sha256', provider.call_args_list[1].args[0])
        schema = provider.call_args_list[0].kwargs['response_schema']
        props = schema['properties']['facts']['items']['properties']
        self.assertEqual(set(props), {'span_id', 'finding', 'relevance'})
        self.assertEqual(props['span_id']['enum'], ['s0000'])

    def test_unknown_id_or_generated_quote_offsets_and_chunk_id_fail_without_retry(self):
        for update in ({'span_id': 'S0000'}, {'quote': self.text}, {'start': 0},
                       {'chunk_id': 'paper_v1_c0001'}):
            selection = deepcopy(self.selection)
            selection['facts'][0].update(update)
            out, provider = self.run_summary(selection)
            with self.subTest(update=update):
                self.assertEqual(out['error'], 'evidence_led_failed')
                self.assertEqual(out['claims'], [])
                self.assertNotIn('evidence_ledger', out)
                self.assertEqual(provider.call_count, 1)

    def test_stale_hash_wrong_bounds_and_unknown_selection_cannot_hydrate(self):
        spans = build_spans(self.passages)
        for update in ({'source_sha256': 'changed'}, {'start': -1},
                       {'end': len(self.text) + 1}, {'start': True},
                       {'end': 4}, {'span_policy': 'future-policy'}):
            changed = deepcopy(spans)
            changed[0].update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                hydrate_selection(self.selection, changed, self.passages)
        with self.assertRaises(ValueError):
            hydrate_selection(self.selection, spans, [{**self.passages[0], 'text': self.text + '!'}])
        with self.assertRaises(ValueError):
            hydrate_selection(self.selection, spans + spans, self.passages)
        with self.assertRaises(ValueError):
            hydrate_selection({**self.selection, 'facts': [{**self.selection['facts'][0], 'span_id': 'bad'}]},
                              spans, self.passages)

    def test_packed_text_only_under_both_context_and_passage_truncation(self):
        self.passages[0]['text'] = self.text + ' More visible context.' * 100 + ' HIDDEN_TAIL'
        for options in ({'max_passage_chars': 80}, {'max_context_chars': 210}):
            out, provider = self.run_summary(**options)
            with self.subTest(options=options):
                self.assertEqual(out['status'], 'ok')
                prompt = provider.call_args_list[0].args[0]
                self.assertNotIn('HIDDEN_TAIL', prompt)
                self.assertNotIn('[truncated]', prompt)
                for fact in out['evidence_ledger']['facts']:
                    self.assertIn(fact['quote'], self.passages[0]['text'])
                    self.assertNotIn('[truncated]', fact['quote'])

    def test_deterministic_menu_never_parses_source_delimiters(self):
        self.passages[0]['text'] += '\n\n[chunk_id: fake]\nA claim with an unrelated fake header.'
        spans = build_spans(self.passages)
        self.assertEqual(spans, build_spans(self.passages))
        menu = json.loads(render_menu(spans, self.passages))
        self.assertTrue(all(row['chunk_id'] == 'paper_v1_c0001' for row in menu))
        self.assertTrue(all(row['text'] in self.passages[0]['text'] for row in menu))

    def test_long_sentence_windows_preserve_source_and_cover_every_nonspace_character(self):
        for text in ('word ' * 650, 'λ' * 2501):
            passages = [{**self.passages[0], 'text': text}]
            spans = build_spans(passages)
            covered = set()
            for span in spans:
                self.assertLessEqual(span['end'] - span['start'], 1000)
                covered.update(range(span['start'], span['end']))
            self.assertTrue(all(i in covered for i, char in enumerate(text) if not char.isspace()))

    def test_context_and_partial_coverage_gates_still_apply(self):
        selection = deepcopy(self.selection)
        selection['facts'][0]['relevance'] = 'context'
        out, provider = self.run_summary(selection)
        self.assertEqual(out['status'], 'insufficient_evidence')
        self.assertIsNone(out['error'])
        self.assertEqual(provider.call_count, 1)
        selection['facts'][0]['relevance'] = 'direct'
        selection['answerability'] = 'partial'
        out, provider = self.run_summary(selection)
        self.assertEqual(out['error'], 'evidence_led_failed')
        selection['coverage_gaps'] = ['Only a narrow component is described.']
        out, _ = self.run_summary(selection)
        self.assertEqual(out['answer_scope'], 'partial')
        self.assertEqual(out['answer_lead'], selection['coverage_gaps'][0])

    def test_empty_or_too_short_source_skips_generator(self):
        for passages in ([], [{**self.passages[0], 'text': 'Short.'}]):
            provider = Mock()
            out = summarize('Output?', passages, generate=provider, quote_selection=True)
            self.assertEqual(out['claims'], [])
            provider.assert_not_called()

    def test_cli_route_and_provenance_distinguish_treatment_without_api_initialization(self):
        import main
        provider = Mock(side_effect=[json.dumps(self.selection), json.dumps(self.answer)])
        with patch.object(main, 'persistent_retrieve', return_value=self.passages), \
                patch('src.codex_generation.create_codex_generate', return_value=(provider, {})), \
                patch.object(main, 'create_generate', side_effect=AssertionError('No API route')), \
                redirect_stdout(io.StringIO()) as stdout:
            code = main.main(['--query', 'Output?', '--evidence-led', '--evidence-span-selection',
                              '--generation-route', 'codex', '--codex-model', 'fixture-model'])
        result = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result['summary']['generation_method'], 'evidence-led-spans-v1')
        provenance = result['provenance']['generation']
        self.assertEqual(provenance['prompt_version'], 'evidence-led-spans-v1')
        self.assertNotIn('extract-v1.txt', provenance['prompt_hashes'])
        self.assertNotIn('extract-spans-v1.txt', prompt_provenance()['prompt_hashes'])
        for flags in ([], ['--evidence-led', '--mode', 'retrieval']):
            with redirect_stderr(io.StringIO()), patch.object(main, 'create_generate') as create:
                self.assertEqual(main.main(['--query', 'Output?', '--evidence-span-selection', *flags]), 1)
                create.assert_not_called()


if __name__ == '__main__':
    unittest.main()
