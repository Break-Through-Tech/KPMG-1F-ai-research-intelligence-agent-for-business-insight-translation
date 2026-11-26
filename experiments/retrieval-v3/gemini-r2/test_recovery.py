"""Offline response-boundary tests. Set PROOFLINE_REPLAY_STATE for real saved responses."""
from contextlib import closing
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from jsonschema import Draft202012Validator, ValidationError

from budget import Ledger
from recovery import COVERAGE_NOTICE, recover_response
from run import ROOT, application_generate

sys.path[:0] = [str(ROOT), str(ROOT / 'experiments/consolidated-v2')]
import env
import publication
import review
import synthesis

PASSAGE = {'chunk_id': 'paper-1', 'text': 'The encoder preserves the input image.',
           'arxiv_id': 'test', 'title': 'Synthetic paper'}
SUPPORT = [{'chunk_id': 'paper-1', 'quote': PASSAGE['text']}]
CLAIM = {'text': PASSAGE['text'], 'kind': 'finding', 'support': SUPPORT}
LIMIT = {'text': 'Uncited limitation', 'support': []}
DRAFT_SCHEMA = synthesis.synthesis_schema(['paper-1'])


def decision(index):
    return {'index': index, 'supported': True, 'relevant': True, 'quotes_entail': True,
            'reason': 'Supported by the quote.', 'supported_text': '', 'reduced_entailed': False,
            'related': False, 'added_support': [], 'flag_resolutions': []}


class RecoveryTests(unittest.TestCase):
    def test_malformed_draft_claim_and_limitation_are_withheld(self):
        draft = {'status': 'ok', 'claims': [CLAIM, {**CLAIM, 'support': 'mistyped'}],
                 'limitations': [LIMIT]}
        raw, events = recover_response(json.dumps(draft), DRAFT_SCHEMA)
        result = json.loads(raw)
        self.assertEqual(result['claims'], [CLAIM])
        self.assertEqual(result['limitations'], [])
        self.assertEqual([(e['field'], e['index']) for e in events], [('claims', 1), ('limitations', 0)])
        Draft202012Validator(DRAFT_SCHEMA).validate(result)

    def test_no_claim_survives_without_support(self):
        draft = {'status': 'ok', 'claims': [{**CLAIM, 'support': []}], 'limitations': []}
        raw, _ = recover_response(json.dumps(draft), DRAFT_SCHEMA)
        self.assertEqual(json.loads(raw)['status'], 'insufficient_evidence')

    def test_malformed_identifiable_review_items_are_withheld(self):
        schema = review.review_schema(['paper-1'], 2)[0]
        item = {**decision(1), 'quotes_entail': 'yes'}
        raw, events = recover_response(json.dumps({
            'coverage': 'full', 'gap': '', 'decisions': [decision(0), item], 'limitations': [LIMIT]
        }), schema)
        value = json.loads(raw)
        self.assertEqual(value, {'coverage': 'partial', 'gap': COVERAGE_NOTICE,
                                 'decisions': [decision(0)], 'limitations': []})
        self.assertEqual([(e['field'], e['index']) for e in events], [('decisions', 1), ('limitations', 0)])

    def test_critical_json_envelope_and_ambiguous_identity_fail(self):
        review_schema = review.review_schema(['paper-1'], 2)[0]
        for raw, schema in (
            ('{"status":"ok","status":"ok","claims":[],"limitations":[]}', DRAFT_SCHEMA),
            ('{"status":"ok","claims":[NaN],"limitations":[]}', DRAFT_SCHEMA),
            ('{"status":"ok","claims":[]}', DRAFT_SCHEMA),
            ('{"coverage":"full","gap":"","decisions":{},"limitations":[]}', review_schema),
            (json.dumps({'coverage': 'full', 'gap': '', 'decisions': [
                decision(0), {**decision(0), 'quotes_entail': 'yes'}
            ], 'limitations': []}), review_schema),
        ):
            with self.subTest(raw=raw), self.assertRaises((ValueError, ValidationError)):
                recover_response(raw, schema)

    def test_adapter_keeps_receipts_and_propagates_coverage_notice_in_both_arms(self):
        with TemporaryDirectory() as tmp:
            ledger = Ledger(Path(tmp) / 'test.sqlite3')
            responses = iter([
                {'status': 'ok', 'claims': [CLAIM, {**CLAIM, 'support': 'mistyped'}], 'limitations': []},
                {'coverage': 'full', 'gap': '', 'decisions': [decision(0)], 'limitations': []},
            ] * 2)

            def send(**_):
                return SimpleNamespace(candidates=[SimpleNamespace(finish_reason='STOP')],
                    text=json.dumps(next(responses)), usage_metadata=SimpleNamespace(
                        prompt_token_count=10, candidates_token_count=5, thoughts_token_count=0))

            for arm in ('S2', 'R2'):
                generate, _ = application_generate(ledger, lambda: (arm, 'U2'), 'fake-test-key',
                    client_factory=lambda **_: SimpleNamespace(models=SimpleNamespace(generate_content=send)))
                synthesized = generate('Synthetic draft', response_schema=DRAFT_SCHEMA)
                draft, _ = synthesis.parse(synthesized, [PASSAGE])
                checked = generate('Synthetic review', response_schema=review.review_schema(['paper-1'], 1)[0])
                accepted, _ = review.parse(checked, draft, [PASSAGE])
                result = publication.publish(draft, accepted, [PASSAGE], [],
                                             v2=env.load_v2(), gate=env.load_gate())
                self.assertEqual(len(result['claims']), 1)
                self.assertEqual(result['answer_scope'], 'partial')
                self.assertEqual(result['answer_lead'], COVERAGE_NOTICE)
                events = ledger.recovery_events(arm, 'U2')
                self.assertEqual([(e['stage'], e['field'], e['index']) for e in events], [('draft', 'claims', 1)])
            import sqlite3
            with closing(sqlite3.connect(ledger.path)) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM dispatch WHERE usage IS NOT NULL').fetchone()[0], 4)

    def test_shape_valid_but_fabricated_quote_still_fails_grounding(self):
        fabricated = {**CLAIM, 'support': [{'chunk_id': 'paper-1', 'quote': 'A fabricated quotation.'}]}
        draft = json.dumps({'status': 'ok', 'claims': [CLAIM, fabricated], 'limitations': []})
        raw, drops = recover_response(draft, DRAFT_SCHEMA)
        self.assertEqual(drops, [])
        summary, report = synthesis.parse(raw, [PASSAGE])
        self.assertEqual(len(summary['claims']), 1)
        self.assertEqual(report['dropped'][0]['reason'], 'quote not found verbatim in its cited passage')

    def test_valid_duplicate_decisions_remain_ambiguous_to_native_review(self):
        draft = synthesis.parse(json.dumps({'status': 'ok', 'claims': [CLAIM, CLAIM],
                                            'limitations': []}), [PASSAGE])[0]
        raw = json.dumps({'coverage': 'partial', 'gap': 'A decision is ambiguous.',
                          'decisions': [decision(0), decision(0)], 'limitations': []})
        self.assertEqual(recover_response(raw, review.review_schema(['paper-1'], 2)[0]), (raw, []))
        reviewed, report = review.parse(raw, draft, [PASSAGE])
        self.assertNotIn(0, reviewed['decisions'])
        self.assertEqual(report['duplicate_decisions'], [0])

    def test_incomplete_sdk_finish_is_not_salvaged(self):
        from src.generation import PipelineError
        with TemporaryDirectory() as tmp:
            ledger = Ledger(Path(tmp) / 'test.sqlite3')
            def send(**_):
                return SimpleNamespace(candidates=[SimpleNamespace(finish_reason='MAX_TOKENS')],
                    text=json.dumps({'status': 'ok', 'claims': [CLAIM], 'limitations': []}),
                    usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=5))
            generate, _ = application_generate(ledger, lambda: ('S2', 'U2'), 'fake-test-key',
                client_factory=lambda **_: SimpleNamespace(models=SimpleNamespace(generate_content=send)))
            with self.assertRaises(PipelineError):
                generate('Synthetic draft', response_schema=DRAFT_SCHEMA)
            self.assertEqual(ledger.recovery_events('S2', 'U2'), [])


@unittest.skipUnless(os.environ.get('PROOFLINE_REPLAY_STATE'), 'Requires private saved Gemini checkpoints.')
class SavedGeminiTests(unittest.TestCase):
    def stages(self, question, required):
        state = Path(os.environ['PROOFLINE_REPLAY_STATE'])
        for marker in state.glob('checkpoints/*/*/fingerprint.json'):
            stages = marker.parent / 'stages'
            if (json.loads(marker.read_bytes())['session'] == f'eval-S2-{question}'
                    and (stages / required).is_file()):
                return stages
        self.fail(f'Missing saved {question} checkpoint')

    def test_saved_u1_passes_unchanged(self):
        stages = self.stages('U1', 'review.json')
        passages = json.loads((stages / 'evidence.json').read_bytes())['passages']
        draft = json.loads((stages / 'synthesis.json').read_bytes())['summary']
        review_raw = json.loads((stages / 'review.json').read_bytes())['raw']
        self.assertEqual(recover_response(review_raw, review.review_schema(
            sorted(p['chunk_id'] for p in passages), len(draft['claims']))[0]), (review_raw, []))

    def test_saved_u2_draft_and_simulated_review_preserve_cited_findings(self):
        stages = self.stages('U2', 'synthesis.json')
        packet = json.loads((stages / 'evidence.json').read_bytes())
        draft = json.loads((stages / 'synthesis.json').read_bytes())
        ids = sorted(p['chunk_id'] for p in packet['passages'])
        self.assertEqual(recover_response(draft['raw'], synthesis.synthesis_schema(ids)), (draft['raw'], []))
        simulated_review = {'coverage': 'partial', 'gap': 'Draft did not cover MultiFinRAG.',
                            'decisions': [decision(0), decision(1), {**decision(2), 'supported': False}],
                            'limitations': [LIMIT]}
        raw, events = recover_response(json.dumps(simulated_review),
                                      review.review_schema(ids, len(draft['summary']['claims']))[0])
        self.assertEqual(events, [{'stage': 'review', 'field': 'limitations', 'index': 0}])
        parsed, _ = review.parse(raw, draft['summary'], packet['passages'])
        result = publication.publish(draft['summary'], parsed, packet['passages'], packet['notes'],
                                     v2=env.load_v2(), gate=env.load_gate())
        self.assertEqual(len(result['claims']), 2)
        self.assertEqual(len(result['held_claims']), 1)
        self.assertEqual(result['limitations'], [])
        self.assertEqual(result['answer_scope'], 'partial')
        self.assertEqual(result['answer_lead'], COVERAGE_NOTICE)


if __name__ == '__main__':
    unittest.main()
