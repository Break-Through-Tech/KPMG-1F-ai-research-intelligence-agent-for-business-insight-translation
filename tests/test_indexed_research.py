"""Offline indexed integration tests; fake adapters are not semantic acceptance."""
import json
import unittest
from copy import deepcopy
from unittest.mock import patch
from src.indexed_research import IndexedResearch, collection_identity, open_index
from src.research_pipeline import require_current_review

PASSAGES = [dict(chunk_id=f'p{i}', text=f'Paper {i} reports a bounded improvement in evaluation accuracy.',
    arxiv_id=f'2608.0000{i}v1', title=f'Paper {i}', source='pdf',
    pdf_url=f'https://arxiv.org/pdf/2608.0000{i}v1',
    source_url=f'https://arxiv.org/pdf/2608.0000{i}v1#page=2', page_number=2) for i in (1, 2)]
IDENTITY = {'count': 2, 'indexed_records_sha256': 'records', 'collection': 'papers'}


def generator(prompt, **kwargs):
    if 'PAPER PASSAGES' in prompt:
        return json.dumps({'status': 'ok', 'claims': [dict(text=p['text'], kind='finding',
            support=[{'chunk_id': p['chunk_id'], 'quote': p['text']}]) for p in PASSAGES],
            'limitations': []})
    return json.dumps({'status': 'ok', 'industry': 'banking', 'implications': [
        {'text': 'Consider a bounded evaluation pilot.', 'chunk_ids': ['p1'],
         'suggested_action': 'Evaluate locally before adoption.', 'assumptions': ['Transfer to banking is untested.']}],
        'risks': ['Experimental results may not transfer.'], 'limitations': ['Not approved.']})


def adapter(**kwargs):
    defaults = dict(retrieve=lambda q, k: deepcopy(PASSAGES), identity=lambda: deepcopy(IDENTITY),
        generate=generator, metadata={'provider': 'injected_test'}, index_path='/test/index')
    return IndexedResearch(**{**defaults, **kwargs})


class IndexedTests(unittest.TestCase):
    def run_query(self, research, **kwargs):
        return research.execute({'query': 'Compare the studies.', 'context_id': research.context_id, **kwargs})

    def test_two_paper_synthesis_and_business_preserve_sources_and_pending_review(self):
        result = self.run_query(adapter(), industry='banking')
        self.assertEqual(result['scenario'], 'full')
        self.assertEqual(len({p['arxiv_id'] for p in result['result']['evidence']}), 2)
        self.assertEqual(result['result']['summary']['claims'][0]['support'][0]['quote'], PASSAGES[0]['text'])
        self.assertEqual(result['result']['human_review']['status'], 'pending')
        self.assertFalse(result['result']['approved'])
        require_current_review(result['result'])

    def test_research_only_is_explicit_summary_only(self):
        result = self.run_query(adapter())
        self.assertEqual(result['scenario'], 'summary-only')
        self.assertNotIn('business_insight', result['result'])
        self.assertEqual(result['result']['provenance']['stages']['business'], 'not_requested')

    def test_empty_skips_provider_and_business_generation(self):
        def forbidden(*args, **kwargs):
            self.fail('Empty evidence must not call generation')
        result = self.run_query(adapter(retrieve=lambda q, k: [], generate=forbidden), industry='banking')
        self.assertEqual(result['scenario'], 'empty')
        self.assertEqual(result['result']['provenance']['stages']['business'], 'skipped')

    def test_irrelevant_and_partial_questions_can_abstain_without_fabrication(self):
        def abstain(prompt, **kwargs):
            return json.dumps({'status': 'insufficient_evidence', 'claims': [], 'limitations': [
                {'text': 'These passages describe evaluation accuracy, not this question.',
                 'support': [{'chunk_id': 'p1', 'quote': PASSAGES[0]['text']}]}]})
        for query in ['Who won the World Cup?', 'Why did the study prove immortality?',
                      'Compare accuracy and give a guaranteed stock return.']:
            with self.subTest(query=query):
                result = self.run_query(adapter(generate=abstain), query=query)
                self.assertEqual(result['scenario'], 'insufficient')
                self.assertFalse(result['result']['summary']['claims'])

    def test_provider_and_retrieval_failures_are_not_evidence_absence(self):
        def fail(*a, **kw):
            raise RuntimeError('SECRET_TOKEN provider payload')
        for key, stage in [('retrieve', 'retrieval'), ('generate', 'summary')]:
            result = self.run_query(adapter(**{key: fail}))
            self.assertEqual(result['scenario'], 'execution-error')
            self.assertEqual(result['error']['stage'], stage)
            self.assertIsNone(result['result'])
            self.assertNotIn('SECRET_TOKEN', json.dumps(result))

    def test_translation_failure_preserves_summary_without_fake_abstention(self):
        def fail_business(prompt, **kw):
            if 'PAPER PASSAGES' in prompt:
                return generator(prompt, **kw)
            raise RuntimeError('SECRET_TOKEN')
        result = self.run_query(adapter(generate=fail_business), industry='banking')
        self.assertEqual(result['scenario'], 'partial')
        self.assertEqual(result['error']['stage'], 'business')
        self.assertEqual(result['result']['provenance']['stages']['business'], 'failed')
        self.assertNotIn('business_insight', result['result'])
        require_current_review(result['result'])

    def test_bad_quotes_fail_closed(self):
        def bad(prompt, **kwargs):
            answer = json.loads(generator(prompt, **kwargs))
            answer['claims'][0]['support'][0]['quote'] = 'A fabricated quote absent from evidence.'
            return json.dumps(answer)
        self.assertIsNone(self.run_query(adapter(generate=bad))['result'])

    def test_identity_and_history_rejected_before_retrieval(self):
        research = adapter()
        with self.assertRaises(ValueError):
            research.execute({'query': 'Q', 'context_id': 'old'})
        with self.assertRaises(ValueError):
            self.run_query(research, history=[{'role': 'assistant', 'content': 'untrusted'}])
        with self.assertRaises(ValueError):
            self.run_query(research, industry='x' * 301)
        with patch.object(research, 'identity', return_value={**IDENTITY, 'count': 3}):
            with self.assertRaises(ValueError):
                self.run_query(research)

    def test_missing_index_does_not_create_directory(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / 'nonexistent'
            with self.assertRaisesRegex(ValueError, 'missing'):
                open_index(missing, 'papers')
            self.assertFalse(missing.exists())

    def test_corpus_identity_is_order_independent_but_binds_text_and_locations(self):
        class Collection:
            name, metadata = 'papers', {'embedding_model': 'local'}
            def get(self, **kwargs):
                return {'ids': ['b', 'a'], 'documents': ['B', 'A'], 'metadatas': [{'page': 2}, {'page': 1}]}
        collection = Collection()
        before = collection_identity(collection)
        with patch.object(collection, 'get', return_value={
                'ids': ['a', 'b'], 'documents': ['A', 'B'], 'metadatas': [{'page': 1}, {'page': 2}]}):
            self.assertEqual(before, collection_identity(collection))
        with patch.object(collection, 'get', return_value={
                'ids': ['b', 'a'], 'documents': ['B', 'CHANGED'], 'metadatas': [{'page': 2}, {'page': 1}]}):
            self.assertNotEqual(before, collection_identity(collection))
