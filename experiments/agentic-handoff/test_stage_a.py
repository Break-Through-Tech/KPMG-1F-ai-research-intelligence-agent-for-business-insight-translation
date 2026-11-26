"""Stage A wiring at the HTTP boundary, offline: grounded paired run through the real runner, then the report.

Scripted model replies only; nothing here is a live or accuracy result.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import unittest.mock

import httpx

from agents import VERIFIER_PROMPT
from gemini_paired import GeminiRun, replay_pair
from gemini_quota import GeminiQuota
from stage_a_report import report
from test_agentic import Provider, claim, plan, verdicts
from test_quote_grounding import NODES, PACKET, SPLIT, reply

INVENTED = claim('Arxiv used a random split.', 'arxiv', 'Splitting: Random for Arxiv as well')
WRONG_NUMBER = claim('Cora has 2,522 nodes.', 'cora', 'Dataset: Cora ( Yang et al., 2016 ; Chen et al., 2023 ); # Nodes: 2,708')


def run_pair(root, *, timeout_arm=None, grounding=True, scope=None, policy=False):
    calls, arm = [], {'name': None, 'synth': 0}

    def handler(request):
        calls.append(request.url.path)
        if request.url.path.endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens': 120})
        prompt = json.loads(request.content)['contents'][0]['parts'][0]['text']
        role = Provider.role(prompt)
        if role == 'research':
            arm['synth'] += 1
            if timeout_arm is not None and arm['synth'] == 2:
                raise httpx.ReadTimeout('fixture timeout', request=request)
            text = reply(NODES, SPLIT, INVENTED, WRONG_NUMBER)
        elif role == 'verify':
            body = prompt[len(VERIFIER_PROMPT):]
            body = body[body.index('{"question"'):]  # skip the scope instructions when present
            judged = json.loads(body)['claims']
            review = verdicts(*[('supported', [])] * len(judged))
            if scope is not None:
                for verdict, item in zip(review['verdicts'], judged):
                    verdict.update(scope(item))
            text = json.dumps(review)
        else:
            text = json.dumps(plan())
        return httpx.Response(200, json={'modelVersion': 'fixture-fixed', 'usageMetadata': {'promptTokenCount': 120},
                                         'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}]})

    now = [1000]
    quota = GeminiQuota(root / 'attempts.sqlite3', clock=lambda: now[0])
    quota.observe(minute_requests=0, minute_input_tokens=0, day_requests=0, valid_until=5000, exclusive=True)
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        live = GeminiRun(http, quota, root, pause=lambda s: now.__setitem__(0, now[0] + s))
        folder = root / 'F03'
        folder.mkdir()
        try:
            replay_pair(folder, 'For Cora and Arxiv, how many nodes, and which used a random split?',
                        lambda q, k: [dict(p) for p in PACKET], lambda: {'indexed_records_sha256': 'fixture'},
                        live, ('current', 'handoff'), quote_grounding=grounding, scope_review=scope is not None,
                        withhold_interpretations=policy)
        except RuntimeError:
            pass
    return calls


class StageA(unittest.TestCase):
    def test_grounded_pair_reports_final_publication_per_claim(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            calls = run_pair(root)
            self.assertEqual(sum(c.endswith(':generateContent') for c in calls), 5)  # shared plan + 2 x (draft, verify)
            arms = {a['arm']: a for a in report(root)['questions']['F03']}
            for name in ('current', 'handoff'):
                arm = arms[name]
                self.assertEqual(arm['final_status'], 'ok')
                rows = {r['text']: r for r in arm['claims'] if r['field'] == 'claims'}
                self.assertEqual(rows[NODES['text']]['outcome'], 'published')
                split = rows[SPLIT['text']]
                self.assertEqual(split['outcome'], 'published')
                self.assertEqual(split['verifier']['verdict'], 'supported')
                support = split['support'][0]
                self.assertTrue(support['original_quote'].endswith('... Splitting: Random'))
                self.assertIn('# Nodes: 2,708; # Edges: 5,429', support['recovered_quote'])
                self.assertIn(support['recovered_quote'], ' '.join(support['cited_passage'].split()))
                self.assertEqual(rows[INVENTED['text']]['outcome'], 'dropped before verification')
                # Exact quote, wrong number: the permissive scripted verifier is overridden by the number check.
                self.assertEqual(rows[WRONG_NUMBER['text']]['outcome'], 'held')
                self.assertIn('numbers_and_qualifiers', rows[WRONG_NUMBER['text']]['held_reason'])

    def test_without_grounding_the_same_draft_abstains(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            run_pair(root, grounding=False)
            arms = {a['arm']: a for a in report(root)['questions']['F03']}
            self.assertEqual({a['abstention'] for a in arms.values()}, {'synthesis_rejected'})
            self.assertTrue(all(r['outcome'].startswith('not verified') for a in arms.values() for r in a['claims']
                                if r['field'] == 'claims'))

    def test_provider_timeout_is_an_execution_failure_not_a_grounding_result(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            run_pair(root, timeout_arm='handoff')
            out = report(root)
            self.assertEqual([(f['question'], f['arm']) for f in out['execution_failures']], [('F03', 'handoff')])
            current = next(a for a in out['questions']['F03'] if a['arm'] == 'current')
            self.assertEqual(current['final_status'], 'ok')


SPLIT_SENTENCE = 'Dataset: Cora ( Yang et al., 2016 ; Chen et al., 2023 ); # Nodes: 2,708'


def model_scope(item):
    """What a verifier might return; deliberately not source-corrected for the split claim."""
    if item['text'] == SPLIT['text']:
        return {'claim_scope': 'Cora and Arxiv', 'evidence_sentence': 'Splitting: Random',
                'evidence_scope': 'Cora row', 'scope_match': 'different'}
    return {'claim_scope': 'Cora', 'evidence_sentence': SPLIT_SENTENCE, 'evidence_scope': 'Cora row', 'scope_match': 'same'}


class ScopedStageA(unittest.TestCase):
    def test_scope_fields_travel_through_the_gemini_adapter_and_withhold(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            calls = run_pair(root, scope=model_scope)
            self.assertEqual(sum(c.endswith(':generateContent') for c in calls), 5)  # no extra call
            for arm in report(root)['questions']['F03']:
                rows = {r['text']: r for r in arm['claims'] if r['field'] == 'claims'}
                self.assertEqual(rows[NODES['text']]['outcome'], 'published')
                self.assertEqual(rows[NODES['text']]['scope_review']['scope_match'], 'same')
                self.assertEqual(rows[SPLIT['text']]['outcome'], 'held')
                self.assertIn('overgeneralization', rows[SPLIT['text']]['held_reason'])
                self.assertEqual(arm['scope_fields'], [{'round': 1, 'claims_judged': 3, 'scope_records': 3}])
                self.assertEqual(arm['verifier_rejections'], [])

    def test_reply_missing_scope_fields_is_an_execution_failure_that_publishes_nothing(self):
        # The Gemini adapter validates against the extended schema, so the run stops like any invalid output.
        with TemporaryDirectory() as temp:
            root = Path(temp)
            run_pair(root, scope=lambda item: {})
            out = report(root)
            self.assertEqual([(f['question'], f['arm']) for f in out['execution_failures']], [('F03', 'current')])
            self.assertEqual(out['execution_failures'][0]['execution_failure']['error_files'], ['verification-1.error.json'])
            self.assertFalse((root / 'F03' / 'handoff').exists())  # the paired run stopped


class PolicyStageA(unittest.TestCase):
    def test_policy_mode_holds_interpretations_through_the_gemini_adapter(self):
        from test_scope_review import MISATTRIBUTED
        import test_stage_a
        with TemporaryDirectory() as temp, unittest.mock.patch.object(
                test_stage_a, 'WRONG_NUMBER', {**MISATTRIBUTED, 'support': [{'chunk_id': 'prose', 'quote':
                'This improvement underscores the MultiFinRAG framework�s ability to retrieve relevant trunks'}]}):
            root = Path(temp)
            calls = run_pair(root, policy=True)
            self.assertEqual(sum(c.endswith(':generateContent') for c in calls), 5)  # no extra call
            for arm in report(root)['questions']['F03']:
                rows = {r['text']: r for r in arm['claims'] if r['field'] == 'claims'}
                self.assertEqual(rows[MISATTRIBUTED['text']]['outcome'], 'held')
                self.assertIn('withheld by policy', rows[MISATTRIBUTED['text']]['held_reason'])
                self.assertEqual(rows[NODES['text']]['outcome'], 'published')
                self.assertEqual(rows[SPLIT['text']]['outcome'], 'published')


class StageBWiring(unittest.TestCase):
    def test_stage_b_mode_is_f04_to_f10_with_grounding_and_policy_only(self):
        from gemini_paired import ROOT, STAGED
        name, questions, scoped, withhold = STAGED['policy_stage_b']
        self.assertEqual(questions, tuple(f'F{i:02d}' for i in range(4, 11)))
        self.assertEqual((scoped, withhold), (False, True))
        self.assertEqual(len(questions) * 9, 63)  # generation cap
        names = [entry[0] for entry in STAGED.values()]
        self.assertEqual(len(names), len(set(names)))  # every mode writes its own one-shot directory
        frozen = json.loads((ROOT / 'experiments/measure/fresh-diagnostic-v1/questions.json').read_text(encoding='utf-8'))
        self.assertTrue(set(questions) <= {q['id'] for q in frozen})

    def test_relabelled_explanation_is_flagged_for_review_not_silently_published(self):
        import test_stage_a
        relabelled = {**WRONG_NUMBER, 'text': 'The random split indicates that Cora results are less time-sensitive.',
                      'support': [{'chunk_id': 'cora', 'quote': 'Splitting: Random'}]}
        with TemporaryDirectory() as temp, unittest.mock.patch.object(test_stage_a, 'WRONG_NUMBER', relabelled):
            root = Path(temp)
            run_pair(root, policy=True)
            for arm in report(root)['questions']['F03']:
                flagged = {f['text']: f['wording'] for f in arm['findings_with_explanatory_wording']}
                self.assertEqual(flagged, {relabelled['text']: ['indicates']})  # measured, for manual review
                self.assertIsNotNone(arm['seconds'])
            self.assertIn('median', report(root)['latency_seconds'])


if __name__ == '__main__':
    unittest.main()
