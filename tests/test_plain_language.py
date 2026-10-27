"""Presentation identity/grounding checks; not semantic acceptance."""
from copy import deepcopy
import unittest
import json
from pathlib import Path

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


class GeneratedPresentationTests(unittest.TestCase):
    def setUp(self):
        self.result = json.loads((Path(__file__).parent / 'fixtures/research/normal-v1.json').read_text())

    def response(self):
        return {'claims': [dict(claim_index=i, text=c['text'], chunk_ids=c['chunk_ids'],
            support=[{'chunk_id': id, 'quote': c['text']} for id in c['chunk_ids']])
            for i, c in enumerate(self.result['summary']['claims'])], 'definitions': []}

    def test_generation_preserves_original_and_requests_schema(self):
        from src.plain_language import generate_view
        original = deepcopy(self.result)
        def generate(prompt, *, response_schema):
            self.assertIn('negation', prompt)
            self.assertEqual(response_schema['additionalProperties'], False)
            return json.dumps(self.response())
        generate.supports_response_schema = True
        view = generate_view(self.result, generate=generate)
        self.assertEqual(view['status'], 'available')
        self.assertFalse(view['fixture'])
        self.assertEqual(view['semantic_review'], 'pending')
        self.assertEqual(self.result, original)

    def test_failure_does_not_discard_original_or_use_fixture(self):
        from src.plain_language import generate_view
        before = deepcopy(self.result)
        for response in ['not json', '{"claims":[],"claims":[],"definitions":[]}',
                         json.dumps({'claims': [], 'definitions': []})]:
            self.assertEqual(generate_view(self.result, generate=lambda _: response)['status'], 'failed')
        def fail(_): raise RuntimeError('private provider error')
        self.assertEqual(generate_view(self.result, generate=fail)['status'], 'failed')
        self.assertEqual(self.result, before)
        self.assertEqual(generate_view(self.result, generate=None)['status'], 'unavailable')

    def test_abstention_never_calls_provider(self):
        from src.plain_language import generate_view
        result = json.loads((Path(__file__).parent / 'fixtures/research/insufficient-v1.json').read_text())
        def fail(_): self.fail('Abstention must not generate new claims/definitions')
        view = generate_view(result, generate=fail)
        self.assertEqual(view['status'], 'available')
        self.assertEqual(view['claims'], [])
        self.assertEqual(view['definitions'], [])

    def test_invented_support_is_rejected(self):
        from src.plain_language import generate_view
        candidate = self.response()
        candidate['claims'][0]['support'][0]['quote'] = 'Not in the source'
        self.assertEqual(generate_view(self.result, generate=lambda _: json.dumps(candidate))['status'], 'failed')


    def test_damaged_optional_replay_cannot_hide_valid_original(self):
        from tempfile import TemporaryDirectory
        from src.research_demo import replay_presentation
        original = deepcopy(self.result)
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'presentation.json'
            for raw in [b'{', b'\xff', b' ' * 120001]:
                path.write_bytes(raw)
                self.assertEqual(replay_presentation(self.result, path)['status'], 'failed')
            self.assertEqual(replay_presentation(self.result, Path(folder)/'absent.json')['status'], 'failed')
        self.assertEqual(self.result, original)
