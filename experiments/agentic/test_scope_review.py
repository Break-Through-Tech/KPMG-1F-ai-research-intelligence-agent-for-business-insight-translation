"""Offline development cases for scope review. Scripted verifier replies only; nothing here measures Gemini.

Passages are verbatim from the saved Stage A packets (MultiFinRAG 2506.20821v1 c0016/c0017, Topo-RAG 2405.17602v1
Table 1). They are separate from the frozen F01-F10 references. Positive cases are valid interpretations that must
still be published.
"""
import json
import sys
import unittest
import unittest.mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE), str(HERE.parent / 'agentic-handoff')]
import scope_review  # noqa: E402
from agents import OrchestratorAgent, VERIFIER_PROMPT  # noqa: E402
from contracts import verification_schema  # noqa: E402
from test_agentic import CORPUS, Provider, Retriever, claim, passage, plan  # noqa: E402
from test_quote_grounding import ARXIV, CORA  # noqa: E402

C16 = passage('c0016', 'The accuracy difference for image-based questions between the Baseline framework and MultiFinRAG '
              'demonstrates that the Baseline framework cannot effectively extract details from images, as anticipated. '
              'This limitation arises because the Baseline framework only truncates and embeds text for retrieving '
              'answers, resulting in weaker performance for both Baseline with Llama-3.2-11B-Vision-Instruct and Baseline '
              'with Gemma 3 in this question type.', '2506.20821v1')
C17 = passage('c0017', 'Moreover, when applying different LLMs to describe tables, Gemma 3 provides significantly better '
              'descriptions than Llama-3.2-11B-Vision-Instruct. Table 1 illustrates that the accuracy for questions '
              'requiring both text and image/table analysis varies significantly between MultiFinRAG with '
              'Llama-3.2-11B-Vision-Instruct and MultiFinRAG with Gemma 3. Additionally, the transition from the Baseline '
              'to the MultiFinRAG framework notably improves the accuracy rate. For instance, accuracy increases from 0% '
              'with the Baseline framework using Gemma 3 to 40% with MultiFinRAG using Gemma 3. This improvement '
              'underscores the MultiFinRAG framework’s ability to retrieve relevant trunks and integrate information '
              'effectively to generate accurate final answers.', '2506.20821v1')
ATTRIBUTION = ('This improvement underscores the MultiFinRAG framework’s ability to retrieve relevant trunks and '
               'integrate information effectively to generate accurate final answers.')
PACKET = [C16, C17, CORA, ARXIV]

# The Stage A F01 interpretation: a combined-category attribution applied to image and table questions.
MISATTRIBUTED = claim('The significant performance gap between the Baseline and MultiFinRAG frameworks on these question '
                      'types indicates that the MultiFinRAG framework is more effective at retrieving relevant information '
                      'and integrating it to generate accurate answers.', 'c0017', ATTRIBUTION, kind='interpretation')
# Valid interpretations from the same paper: the explanation is stated for the same category.
IMAGE_CAUSE = claim("The Baseline's weak image-based accuracy reflects that it only embeds text, so it cannot use details "
                    'in images.', 'c0016', 'This limitation arises because the Baseline framework only truncates and embeds '
                    'text for retrieving answers', kind='interpretation')
TABLE_CAUSE = claim("Gemma 3's better table descriptions help explain MultiFinRAG's stronger table-based accuracy with Gemma "
                    'than with Llama.', 'c0017', 'Gemma 3 provides significantly better descriptions than '
                    'Llama-3.2-11B-Vision-Instruct', kind='interpretation')
SPLIT = claim('Cora uses a random split.', 'cora', 'Splitting: Random')


def scope(claim_scope, sentence, evidence_scope, match):
    return {'claim_scope': claim_scope, 'evidence_sentence': sentence, 'evidence_scope': evidence_scope, 'scope_match': match}


def payload(*claims):
    return {'question': 'q', 'claims': [{'index': i, 'kind': c['kind'], 'text': c['text'], 'support': c['support']}
                                        for i, c in enumerate(claims)], 'passages': PACKET}


def review(claims_and_scopes, coverage='full'):
    claims = [c for c, _ in claims_and_scopes]
    raw = json.dumps({'verdicts': [{'index': i, **s, 'verdict': 'supported', 'issues': [], 'reason': 'matches'}
                                   for i, (_, s) in enumerate(claims_and_scopes)],
                      'coverage': coverage, 'missing_aspects': [],
                      'retrieval_request': {'needed': False, 'query': '', 'reason': 'enough'}})
    out, records = scope_review.review(raw, payload(*claims))
    return json.loads(out), records


class Decisions(unittest.TestCase):
    def test_f01_misattribution_is_withheld(self):
        reply, records = review([(MISATTRIBUTED, scope('image-based and table-based questions', ATTRIBUTION,
                                                       'questions requiring both text and image/table analysis', 'different'))])
        self.assertEqual((reply['verdicts'][0]['verdict'], reply['verdicts'][0]['issues']),
                         ('partially_supported', ['overgeneralization']))
        self.assertTrue(records[0]['evidence_sentence_found_in_cited_passage'])
        self.assertNotIn('scope_match', reply['verdicts'][0])  # stripped before the existing schema check
        self.assertEqual(reply['coverage'], 'none')

    def test_valid_interpretations_with_matching_scope_are_kept(self):
        reply, records = review([
            (IMAGE_CAUSE, scope('image-based questions, Baseline', C16['text'].split('. ')[1], 'image-based questions', 'same')),
            (TABLE_CAUSE, scope('table-based questions, MultiFinRAG Gemma vs Llama',
                                'Moreover, when applying different LLMs to describe tables, Gemma 3 provides significantly '
                                'better descriptions than Llama-3.2-11B-Vision-Instruct.', 'table descriptions by LLM', 'same'))])
        self.assertEqual([v['verdict'] for v in reply['verdicts']], ['supported', 'supported'])
        self.assertEqual({r['outcome'] for r in records}, {'unchanged'})

    def test_interpretation_needs_a_stated_sentence_in_a_cited_passage(self):
        for sentence, reason in (('', 'no cited sentence'),
                                 ('This limitation arises because the Baseline framework only truncates and embeds text '
                                  'for retrieving answers', 'no cited sentence'),  # real, but from uncited c0016
                                 ('MultiFinRAG retrieves better on every question type.', 'no cited sentence')):
            with self.subTest(sentence=sentence[:30]):
                reply, records = review([(MISATTRIBUTED, scope('image and table questions', sentence, 'same', 'same'))])
                self.assertEqual(reply['verdicts'][0]['verdict'], 'partially_supported')
                self.assertIn(reason, records[0]['outcome'])

    def test_interpretation_with_unclear_or_narrower_scope_is_withheld(self):
        for match in ('unclear', 'narrower'):
            reply, _ = review([(MISATTRIBUTED, scope('image and table', ATTRIBUTION, 'all question types', match))])
            self.assertEqual(reply['verdicts'][0]['verdict'], 'partially_supported', match)

    def test_findings_are_not_held_for_unclear_or_narrower_scope(self):
        for match, sentence in (('unclear', ''), ('narrower', 'Splitting: Random')):
            reply, _ = review([(SPLIT, scope('Cora', sentence, 'Table 1 Cora row', match))])
            self.assertEqual(reply['verdicts'][0]['verdict'], 'supported', match)

    def test_finding_moved_to_another_dataset_is_withheld(self):
        # Generic dataset-transfer case: the cited row is about one dataset, the claim about another.
        wrong = claim('Arxiv uses a random split.', 'cora', 'Splitting: Random')
        reply, _ = review([(wrong, scope('Arxiv', 'Splitting: Random', 'Cora (Table 1 row)', 'different'))])
        self.assertEqual(reply['verdicts'][0]['issues'], ['overgeneralization'])

    def test_withholding_never_upgrades_a_verifier_rejection(self):
        raw = json.dumps({'verdicts': [{'index': 0, **scope('x', '', 'y', 'same'), 'verdict': 'unsupported',
                                        'issues': ['missing_support'], 'reason': 'no'}], 'coverage': 'none',
                          'missing_aspects': [], 'retrieval_request': {'needed': False, 'query': '', 'reason': 'r'}})
        reply, _ = json.loads(scope_review.review(raw, payload(SPLIT))[0]), None
        self.assertEqual(reply['verdicts'][0]['verdict'], 'unsupported')

    def test_reply_without_scope_fields_raises_and_non_json_passes_to_existing_checks(self):
        raw = json.dumps({'verdicts': [{'index': 0, 'verdict': 'supported', 'issues': [], 'reason': 'r'}]})
        with self.assertRaisesRegex(ValueError, 'scope check'):
            scope_review.review(raw, payload(SPLIT))
        self.assertEqual(scope_review.review('not json', payload(SPLIT)), ('not json', []))

    def test_known_gap_a_verifier_that_mislabels_scope_is_not_caught(self):
        # Code cannot tell a correct "same" from a wrong one when the sentence is real. Needs live measurement.
        reply, _ = review([(MISATTRIBUTED, scope('MultiFinRAG vs Baseline', ATTRIBUTION, 'MultiFinRAG vs Baseline', 'same'))])
        self.assertEqual(reply['verdicts'][0]['verdict'], 'supported')

    def test_wire_schema_puts_scope_fields_before_the_verdict(self):
        wire = scope_review.wire_schema(verification_schema(2))
        item = wire['properties']['verdicts']['items']
        self.assertEqual(list(item['properties'])[:6], ['index', *scope_review.FIELDS, 'verdict'])
        self.assertTrue(set(scope_review.FIELDS) <= set(item['required']))


class EndToEnd(unittest.TestCase):
    """Real verifier agent, gate and summary; scripted replies that include the scope fields."""

    def run_with(self, claims, scopes, *, enabled=True):
        class Scoped(Provider):
            def __call__(self, prompt, response_schema=None):
                if self.role(prompt) == 'verify':
                    self.schemas = getattr(self, 'schemas', []) + [response_schema]
                return super().__call__(prompt, response_schema)
        verdicts = [{'index': i, **(s if enabled else {}), 'verdict': 'supported', 'issues': [], 'reason': 'matches'}
                    for i, s in enumerate(scopes)]
        p = Scoped(plan=[plan()], research=[{'status': 'ok', 'claims': claims, 'limitations': []}],
                   verify=[{'verdicts': verdicts, 'coverage': 'full', 'missing_aspects': [],
                            'retrieval_request': {'needed': False, 'query': '', 'reason': 'enough'}}])
        corpus = {x['chunk_id']: x for x in PACKET}
        with unittest.mock.patch.dict(CORPUS, corpus):
            engine = OrchestratorAgent(generate=p, retrieve=Retriever({'Why': list(corpus)}), top_k=8, research_only=True)
            r = (scope_review.enable(engine) if enabled else engine).run('Why did MultiFinRAG beat the Baseline?')
        return r, p

    def test_misattribution_held_and_valid_interpretation_published(self):
        r, p = self.run_with([MISATTRIBUTED, IMAGE_CAUSE], [
            scope('image and table questions', ATTRIBUTION, 'questions requiring both text and image/table', 'different'),
            scope('image-based questions', C16['text'].split('. ')[1], 'image-based questions', 'same')])
        self.assertEqual([c['text'] for c in r['summary']['claims']], [IMAGE_CAUSE['text']])
        self.assertIn('overgeneralization', r['summary']['held_claims'][0]['verification']['held_reason'])
        self.assertIn('scope_match', json.dumps(p.schemas[0]))
        verify_prompt = next(prompt for role, prompt in p.prompts if role == 'verify')
        self.assertTrue(verify_prompt.startswith(VERIFIER_PROMPT + scope_review.INSTRUCTIONS))

    def test_all_claims_withheld_is_a_clean_abstention_not_an_error(self):
        r, _ = self.run_with([MISATTRIBUTED], [scope('image and table', '', '', 'unclear')])
        self.assertEqual((r['status'], r['summary']['claims']), ('insufficient_evidence', []))
        self.assertEqual(r['summary']['held_claims'][0]['verification']['decision'], 'held')

    def test_reply_missing_scope_fields_fails_closed(self):
        class Plain(Provider):
            pass
        p = Plain(plan=[plan()], research=[{'status': 'ok', 'claims': [IMAGE_CAUSE], 'limitations': []}],
                  verify=[{'verdicts': [{'index': 0, 'verdict': 'supported', 'issues': [], 'reason': 'r'}],
                           'coverage': 'full', 'missing_aspects': [],
                           'retrieval_request': {'needed': False, 'query': '', 'reason': 'r'}}])
        corpus = {x['chunk_id']: x for x in PACKET}
        with unittest.mock.patch.dict(CORPUS, corpus):
            engine = OrchestratorAgent(generate=p, retrieve=Retriever({'Why': list(corpus)}), top_k=8, research_only=True)
            r = scope_review.enable(engine).run('Why did the Baseline do badly on images?')
        self.assertEqual(r['summary']['claims'], [])
        self.assertIn('scope check', r['verification'][0]['verification']['rejection'])


class StageAReplay(unittest.TestCase):
    def test_saved_stage_a_before_and_after(self):
        from replay_scope_review import RUN, compare
        if not RUN.exists():
            self.skipTest('Stage A run not present')
        rows = {r['case']: r for r in compare()}
        for case, count in (('F01/current', 4), ('F01/handoff', 4), ('F03/current', 2), ('F03/handoff', 2)):
            self.assertEqual(len(rows[case]['before']['published']), count)  # replay reproduces the live result
        for case in ('F01/current', 'F01/handoff'):
            after = rows[case]['after']
            self.assertEqual(len(after['published']), 3)  # all three findings, both required points
            self.assertTrue(all(not t.startswith('The significant performance gap') for t in after['published']))
        for case in ('F03/current', 'F03/handoff'):
            self.assertEqual(rows[case]['after']['published'], rows[case]['before']['published'])


if __name__ == '__main__':
    unittest.main()
