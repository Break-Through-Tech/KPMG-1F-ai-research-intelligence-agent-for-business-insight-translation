"""Presentation identity/grounding checks; not semantic acceptance."""
from copy import deepcopy
import unittest

from src.plain_language import fixture_view, plain_language_view
from src.research_demo import load_demo, saved_result_envelope


class PlainLanguageTests(unittest.TestCase):
    def test_supported_partial_and_abstention_preserve_exact_original(self):
        for scenario in ['plain-language', 'full', 'partial', 'insufficient', 'empty']:
            demo = load_demo({'query': 'Q'}, scenario)
            result = demo['result']
            before = deepcopy(result)
            view = fixture_view(result)
            self.assertEqual(view['status'], 'available')
            self.assertEqual(len(view['claims']), len(result['summary']['claims']))
            self.assertEqual(view['semantic_review'], 'pending')
            self.assertTrue(view['fixture'])
            self.assertEqual(result, before)
            self.assertFalse(result['approved'])
            self.assertEqual(saved_result_envelope(result)['plain_language']['status'], 'unavailable')

    def test_definition_only_supported_when_source_explicitly_defines_it(self):
        supported = load_demo({'query': 'Q'}, 'plain-language')['plain_language']
        self.assertEqual(supported['definitions'][0]['status'], 'supported')
        absent = load_demo({'query': 'Q'}, 'full')['plain_language']
        self.assertEqual(absent['definitions'][0]['status'], 'unavailable')

    def test_rejects_stale_result_missing_claims_and_invalid_quotes(self):
        result = load_demo({'query': 'Q'}, 'plain-language')['result']
        base = fixture_view(result)
        mutations = [
            lambda c: c.update(result_identity='stale'),
            lambda c: c['claims'].pop(),
            lambda c: c['claims'][0].update(chunk_ids=['unknown']),
            lambda c: c['claims'][0]['support'][0].update(quote='invented'),
            lambda c: c['claims'][0].update(support=[]),
            lambda c: c['claims'].reverse(),
            lambda c: c.update(semantic_review='approved'),
            lambda c: c['definitions'][0]['support'][0].update(quote='invented definition'),
            lambda c: c['definitions'][0].update(chunk_ids=['unknown']),
            lambda c: c.update(definitions=None),
        ]
        for mutation in mutations:
            candidate = deepcopy(base)
            mutation(candidate)
            self.assertEqual(plain_language_view(result, candidate)['status'], 'failed')
        changed = deepcopy(result)
        changed['summary']['limitations'].append('New limitation')
        self.assertEqual(plain_language_view(changed, base)['status'], 'failed')

    def test_unavailable_and_generation_failure_are_not_abstention(self):
        result = load_demo({'query': 'Q'}, 'full')['result']
        self.assertEqual(plain_language_view(result)['status'], 'unavailable')
        self.assertEqual(plain_language_view(result, {'status': 'failed'})['status'], 'failed')
        self.assertEqual(result['summary']['status'], 'ok')
        self.assertEqual(plain_language_view(result, [])['status'], 'failed')
