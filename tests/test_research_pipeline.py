import copy
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import Mock, patch

from tests import research_fixtures as main
from src.research_pipeline import PipelineError, require_current_review, run_research


class WorkflowTests(unittest.TestCase):
    def run_draft(self, **kwargs):
        return run_research({'query': 'agents', 'industry': 'banking', 'jurisdiction': 'US'},
                            retrieve=main.demo_retrieve, summarize_fn=main.demo_summary, **kwargs)

    def test_whole_interface_preserves_html_pdf_and_pending_review(self):
        result = self.run_draft(translate_fn=main.demo_translate,
                               review_fn=lambda r: {'approved': True, 'jurisdiction': r['request']['jurisdiction']})
        self.assertEqual(result['evidence'], main.demo_retrieve('agents', 5))
        self.assertIsNone(result['evidence'][0]['page_number'])
        self.assertEqual(result['evidence'][1]['page_number'], 2)
        self.assertEqual(result['evidence'][0]['distance'], 0.25)
        self.assertFalse(result['approved'])
        self.assertEqual(result['human_review']['status'], 'pending')
        self.assertEqual(result['regulatory_checkpoint']['jurisdiction'], 'US')
        require_current_review(result)

    def test_summarization_adapter_preserves_exact_query(self):
        from src.summarization import summarize
        query = " agents "
        responses = [
            main.demo_summary(query, main.demo_retrieve(query, 5)),
            {'status': 'insufficient_evidence', 'claims': [], 'limitations': ['No support.']},
            {'status': 'ok', 'claims': [{'text': 'Unknown.', 'chunk_ids': ['unknown']}],
             'limitations': []},
            'not JSON',
        ]
        for response in responses:
            with self.subTest(response=response):
                raw = json.dumps(response) if isinstance(response, dict) else response
                result = run_research({'query': query}, retrieve=main.demo_retrieve,
                    summarize_fn=lambda q, p: summarize(q, p, generate=lambda prompt: raw))
                self.assertEqual(result['request']['query'], query)
                self.assertEqual(result['summary']['query'], query)
                self.assertEqual(result['summary']['status'],
                                 'ok' if response is responses[0] else 'insufficient_evidence')
                self.assertFalse(result['approved'])
                require_current_review(result)

    def test_no_hits_skips_all_generation(self):
        summary, business = Mock(), Mock()
        result = run_research({'query': 'agents', 'industry': 'banking'}, retrieve=lambda *a: [],
                              summarize_fn=summary, translate_fn=business)
        summary.assert_not_called()
        business.assert_not_called()
        self.assertEqual(result['summary']['status'], 'insufficient_evidence')
        self.assertEqual(result['business_insight']['status'], 'insufficient_evidence')

    def test_provider_failure_does_not_leak_exception_payload(self):
        def fail(*args):
            raise RuntimeError('SECRET-KEY-IN-PAYLOAD')
        with self.assertRaises(PipelineError) as cm:
            run_research({'query': 'agents'}, retrieve=main.demo_retrieve, summarize_fn=fail)
        self.assertIn('Summary failed', str(cm.exception))
        self.assertNotIn('SECRET', str(cm.exception))

    def test_unknown_citation_and_mismatched_query_fail(self):
        for key, value in [('query', 'other'), ('claims', [{'text': 'bad', 'chunk_ids': ['unknown']}])]:
            def bad(q, p):
                output = main.demo_summary(q, p)
                output[key] = value
                return output
            with self.assertRaises(ValueError):
                run_research({'query': 'agents'}, retrieve=main.demo_retrieve, summarize_fn=bad)

    def test_invalid_request(self):
        for request in [{'query': ''}, {'query': 'a', 'top_k': True}, {'query': 'a', 'top_k': 0},
                        {'query': 'a', 'jurisdiction': ''}]:
            with self.assertRaises(ValueError):
                run_research(request, retrieve=Mock(), summarize_fn=Mock())
        with self.assertRaisesRegex(ValueError, 'industry'):
            run_research({'query': 'a'}, retrieve=Mock(), summarize_fn=Mock(), translate_fn=Mock())

    def test_adapter_mutation_cannot_change_evidence_or_summary(self):
        def mutate(summary, passages, *, industry):
            output = main.demo_translate(summary, passages, industry=industry)
            summary['claims'].clear()
            passages.clear()
            return output
        result = self.run_draft(translate_fn=mutate)
        self.assertEqual(len(result['summary']['claims']), 2)
        self.assertEqual(len(result['evidence']), 2)

    def test_stale_review_after_any_material_edit(self):
        result = self.run_draft(translate_fn=main.demo_translate)
        for field in ['request', 'evidence', 'summary', 'business_insight', 'provenance', 'regulatory_checkpoint']:
            changed = copy.deepcopy(result)
            changed[field] = {'changed': True}
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'changed'):
                require_current_review(changed)
        rerun = self.run_draft()
        self.assertFalse(rerun['approved'])



if __name__ == '__main__':
    unittest.main()
