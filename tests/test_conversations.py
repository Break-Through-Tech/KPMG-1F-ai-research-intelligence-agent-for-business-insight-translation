"""Persistent research conversations: migration, context resolution, isolation and soft deletion (offline)."""
import json
import sqlite3
from contextlib import closing
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.brief_store import BriefStore
from src.business_demo import record_conversation_turn, research_business_flags
from src.conversation_context import RESTATE, needs_context, resolve
from src.conversation_store import ConversationStore
from tests.test_downstream_business import result_for

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'experiments/render-staging'))
import server  # noqa: E402

FIRST = 'How can AI agents improve insurance claims processing?'


def decision(kind='continue', resolved='', question='', options=()):
    return json.dumps({'decision': kind, 'resolved_query': resolved, 'question': question,
                       'options': [{'text': o, 'support': []} for o in options]})


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / 'briefs.sqlite3'
        self.briefs = BriefStore(self.path)
        self.store = ConversationStore(self.briefs)

    def tearDown(self):
        self.dir.cleanup()

    def counts(self):
        with closing(sqlite3.connect(self.path)) as db:
            return [db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ('briefs', 'brief_versions', 'reviews')]

    def save(self, question):
        return self.briefs.save({'mode': 'indexed', 'submitted_request': {'query': question}, 'result': result_for()})

    def conversation(self, *questions):
        conversation_id = self.store.create(questions[0])
        for question in questions:
            brief = self.save(question)['library']['brief']['id']
            self.store.append_turn(conversation_id, brief, original_question=question, resolved_question=question,
                                   resolution={'kind': 'standalone', 'calls': 0})
        return conversation_id


class StoreTests(Base):
    def test_migration_gives_each_existing_brief_one_turn_without_data_loss(self):
        saved = [self.save(q) for q in (FIRST, 'Which datasets measure legal hallucination?')]
        before = self.counts()
        self.assertEqual(self.store.migrate(), 2)
        self.assertEqual(self.store.migrate(), 0)  # idempotent
        conversations = self.store.list()
        self.assertEqual(len(conversations), 2)
        self.assertEqual({c['turn_count'] for c in conversations}, {1})
        loaded = self.store.load('c' + saved[0]['library']['brief']['id'])
        self.assertEqual(loaded['turns'][0]['original_question'], saved[0]['library']['brief']['original_question'])
        self.assertEqual(loaded['turns'][0]['envelope']['result'], saved[0]['result'])
        self.assertEqual(self.counts(), before)

    def test_reopening_restores_every_turn_in_order_with_its_own_answer(self):
        conversation_id = self.conversation(FIRST, 'What about the risks?', 'And the costs?')
        loaded = self.store.load(conversation_id)
        self.assertEqual([t['position'] for t in loaded['turns']], [1, 2, 3])
        self.assertEqual([t['original_question'] for t in loaded['turns']], [FIRST, 'What about the risks?', 'And the costs?'])
        self.assertTrue(all(t['envelope']['result']['evidence'] for t in loaded['turns']))
        self.assertEqual(len({t['brief_id'] for t in loaded['turns']}), 3)  # each turn is its own validated brief

    def test_history_carries_questions_and_findings_but_never_evidence(self):
        conversation_id = self.conversation(FIRST)
        history = self.store.history(conversation_id)
        text = json.dumps(history)
        self.assertEqual([m['role'] for m in history], ['user', 'assistant'])
        self.assertIn(FIRST, history[0]['content'])
        self.assertIn('not evidence', history[1]['content'])
        for passage in result_for()['evidence']:
            self.assertNotIn(passage['chunk_id'], text)  # no citations or passage identities
        for key in ('chunk_ids', 'evidence', 'support', 'passages', 'quote'):
            self.assertNotIn(f'"{key}"', text)
        self.assertLessEqual(len(history[1]['content']), 1500)

    def test_soft_delete_hides_without_touching_the_audit_trail_or_other_conversations(self):
        kept = self.conversation('Which datasets measure legal hallucination?')
        removed = self.conversation(FIRST, 'What about the risks?')
        removed_briefs = [t['brief_id'] for t in self.store.turns(removed)]
        self.store.soft_delete(removed)
        self.assertEqual([c['id'] for c in self.store.list()], [kept])
        with self.assertRaises(KeyError):
            self.store.load(removed)
        listed = {b['id'] for b in self.briefs.list()}
        self.assertFalse(set(removed_briefs) & listed)
        self.assertEqual(len(listed), 1)
        self.assertEqual(self.briefs.load(removed_briefs[0])['library']['brief']['id'], removed_briefs[0])  # retained
        with closing(sqlite3.connect(self.path)) as db:
            for table in ('brief_versions', 'conversation_turns'):
                with self.subTest(table=table), self.assertRaises(sqlite3.IntegrityError):
                    db.execute(f'DELETE FROM {table}')  # protection triggers unchanged

    def test_rename_and_archive(self):
        conversation_id = self.conversation(FIRST)
        self.assertEqual(self.store.update(conversation_id, title='Claims AI')['title'], 'Claims AI')
        self.store.update(conversation_id, archived=True)
        self.assertEqual(self.store.list(), [])
        self.assertEqual([c['id'] for c in self.store.list(archived=True)], [conversation_id])


class ResolutionTests(unittest.TestCase):
    history = [{'role': 'user', 'content': FIRST}, {'role': 'assistant', 'content': 'Earlier findings (not evidence): - x'}]

    def test_only_context_dependent_follow_ups_make_a_call(self):
        self.assertTrue(needs_context('What about the risks?', self.history))
        self.assertTrue(needs_context('Why?', self.history))
        self.assertFalse(needs_context('What about the risks?', []))
        self.assertFalse(needs_context('Which benchmark measures multi-constraint travel planning accuracy for LLM agents?', self.history))
        generate = Mock()
        self.assertEqual(resolve('Which benchmark measures multi-constraint travel planning accuracy for LLM agents?', self.history, generate)[2],
                         {'kind': 'standalone', 'calls': 0})
        generate.assert_not_called()

    def test_follow_up_is_resolved_with_the_prior_topic(self):
        resolved = 'What are the risks of using AI agents in insurance claims processing?'
        generate = Mock(return_value=decision(resolved=resolved))
        action, text, info = resolve('What about the risks?', self.history, generate)
        self.assertEqual((action, text, info['kind']), ('research', resolved, 'resolved'))
        prompt = generate.call_args.args[0]
        self.assertIn('NOT source evidence', prompt)  # existing query-clarification prompt, unchanged
        generate.assert_called_once()

    def test_topic_change_keeps_the_new_question(self):
        question = 'And how is hallucination measured in legal question answering?'
        action, text, info = resolve(question, self.history, Mock(return_value=decision(resolved=question)))
        self.assertEqual((action, text, info['kind']), ('research', question, 'unchanged'))

    def test_ambiguous_or_failed_resolution_asks_instead_of_researching(self):
        action, text, info = resolve('What about that?', self.history,
                                     Mock(return_value=decision('clarify', question='Do you mean the risks or the costs?', options=['Risks', 'Costs'])))
        self.assertEqual((action, info['kind'], info['options']), ('clarify', 'clarify', ['Risks', 'Costs']))
        for broken in (Mock(side_effect=RuntimeError('provider down')), Mock(return_value='not json'),
                       Mock(return_value=decision(resolved=''))):
            with self.subTest(generate=broken):
                self.assertEqual(resolve('What about the risks?', self.history, broken)[:2], ('clarify', RESTATE))


class WrapperTests(Base):
    def wrapped(self, *replies):
        execute = Mock(side_effect=lambda payload, **kw: {'mode': 'indexed', 'result': {'q': payload['query']}})
        generate = Mock(side_effect=list(replies))
        budget = Mock()
        return server.conversational(execute, generate, budget, self.path), execute, generate, budget

    def test_first_and_self_contained_questions_make_no_resolution_call(self):
        run, execute, generate, _ = self.wrapped()
        response = run({'query': FIRST, 'context_id': 'x'})
        self.assertEqual(execute.call_args.args[0]['query'], FIRST)
        self.assertEqual(response['conversation_turn']['resolution'], {'kind': 'first', 'calls': 0})
        conversation_id = self.conversation(FIRST)
        run({'query': 'Which benchmark measures multi-constraint travel planning accuracy for LLM agents?',
             'conversation_id': conversation_id, 'context_id': 'x'})
        generate.assert_not_called()

    def test_follow_up_researches_the_standalone_question_and_keeps_the_original(self):
        resolved = 'What are the risks of using AI agents in insurance claims processing?'
        run, execute, generate, budget = self.wrapped(decision(resolved=resolved))
        conversation_id = self.conversation(FIRST)
        response = run({'query': 'What about the risks?', 'conversation_id': conversation_id, 'context_id': 'x'})
        sent = execute.call_args.args[0]
        self.assertEqual(sent['query'], resolved)
        self.assertNotIn('conversation_id', sent)  # the research engine never sees conversation state
        self.assertNotIn('history', sent)
        turn = response['conversation_turn']
        self.assertEqual((turn['original_question'], turn['resolved_question']), ('What about the risks?', resolved))
        budget.reserve.assert_called_once()

    def test_ambiguous_follow_up_returns_a_clarification_and_runs_no_research(self):
        run, execute, generate, _ = self.wrapped(decision('clarify', question='Which risks do you mean?'),
                                                 decision(resolved='What are the operational risks of AI agents in insurance claims processing?'))
        conversation_id = self.conversation(FIRST)
        response = run({'query': 'What about that?', 'conversation_id': conversation_id, 'context_id': 'x'})
        self.assertEqual(response['scenario'], 'conversation_clarification')
        self.assertIsNone(response['result'])
        execute.assert_not_called()
        # The reply to the clarification is resolved with the clarification in context, then researched.
        response = run({'query': 'Operational ones', 'conversation_id': conversation_id, 'context_id': 'x'})
        self.assertIn('operational risks', execute.call_args.args[0]['query'])
        self.assertIn('Clarification asked: Which risks do you mean?', generate.call_args.args[0])
        self.assertEqual(response['conversation_turn']['resolution']['clarified_question'], 'What about that?')

    def test_removed_conversation_is_refused_without_research(self):
        run, execute, _, _ = self.wrapped()
        conversation_id = self.conversation(FIRST)
        self.store.soft_delete(conversation_id)
        response = run({'query': 'What about the risks?', 'conversation_id': conversation_id, 'context_id': 'x'})
        self.assertEqual(response['error']['code'], 'conversation_missing')
        execute.assert_not_called()


class RecordingTests(Base):
    def test_new_and_follow_up_turns_are_recorded_and_deleted_conversations_stay_deleted(self):
        body = {**self.save(FIRST), 'conversation_turn': {'conversation_id': None, 'original_question': FIRST,
                'resolved_question': FIRST, 'resolution': {'kind': 'first', 'calls': 0}}}
        body['library']['replayed'] = False
        recorded = record_conversation_turn(self.briefs, body)['conversation']
        self.assertEqual((recorded['position'], recorded['deleted']), (1, False))
        # Deleted while the follow-up was running: the turn is kept for audit but not shown or continued.
        release, finished = threading.Event(), {}

        def running_request():
            release.wait(5)
            follow = {**self.save('What about the risks?'), 'conversation_turn': {
                'conversation_id': recorded['id'], 'original_question': 'What about the risks?',
                'resolved_question': 'What are the risks of AI agents in insurance claims processing?',
                'resolution': {'kind': 'resolved', 'calls': 1}}}
            follow['library']['replayed'] = False
            finished['body'] = research_business_flags(record_conversation_turn(self.briefs, follow))
        worker = threading.Thread(target=running_request)
        worker.start()
        self.store.soft_delete(recorded['id'])
        release.set()
        worker.join(5)
        self.assertTrue(finished['body']['conversation']['deleted'])
        self.assertEqual(self.store.list(), [])
        self.assertEqual(self.briefs.list(), [])  # its briefs are hidden from the library too

    def test_clarification_without_a_saved_answer_is_not_recorded(self):
        conversation_id = self.conversation(FIRST)
        body = record_conversation_turn(self.briefs, {'mode': 'indexed', 'result': None, 'conversation_turn': {
            'conversation_id': conversation_id, 'original_question': 'What about that?', 'resolved_question': 'What about that?',
            'resolution': {'kind': 'clarify', 'calls': 1}}})
        self.assertTrue(body['conversation']['awaiting_clarification'])
        self.assertEqual(self.store.summary(conversation_id)['turn_count'], 1)


if __name__ == '__main__':
    unittest.main()


class InheritanceTests(Base):
    """A confirmed follow-up may inherit the previous turn's verified business context when the classifier fails."""
    RESOLVED = 'What are the risks of using AI agents in insurance claims processing?'

    def business_turn(self, conversation_id=None):
        from src.business_intent import VERSION
        body = self.save(FIRST)
        envelope = {'mode': 'indexed', 'submitted_request': {'query': FIRST}, 'result': result_for(),
                    'business_intent': {'version': VERSION, 'status': 'ok', 'value': {
                        'is_business': True, 'industry': 'insurance', 'workflow': 'insurance claims processing',
                        'decision': FIRST, 'confidence': 'high'}}}
        brief = self.briefs.save(envelope)['library']['brief']['id']
        conversation_id = conversation_id or self.store.create(FIRST)
        self.store.append_turn(conversation_id, brief, original_question=FIRST, resolved_question=FIRST,
                               resolution={'kind': 'first', 'calls': 0})
        return conversation_id

    def wrapped(self, resolved, classifier_record):
        execute = Mock(side_effect=lambda payload, **kw: {'mode': 'indexed', 'result': {'summary': {}},
                                                           'business_intent': classifier_record})
        generate = Mock(return_value=decision(resolved=resolved))
        return server.conversational(execute, generate, Mock(), self.path), generate

    def test_confirmed_follow_up_inherits_when_classifier_times_out(self):
        from src.business_insights import resolve_business_intent
        conversation_id = self.business_turn()
        run, generate = self.wrapped(self.RESOLVED, {'status': 'unavailable', 'reason': 'timeout'})
        response = run({'query': 'What about the risks?', 'conversation_id': conversation_id, 'context_id': 'x'})
        carried = response['business_context_inherited']
        self.assertEqual((carried['industry'], carried['workflow'], carried['source'], carried['from_position']),
                         ('insurance', 'insurance claims processing', 'semantic', 1))
        self.assertEqual(carried['decision'], self.RESOLVED)  # the new question, not the earlier decision
        self.assertEqual(carried['reason'], 'classifier_unavailable')
        self.assertEqual(generate.call_count, 1)  # only the resolution call; no extra model call
        resolved = resolve_business_intent(self.RESOLVED, response['business_intent'], carried)
        self.assertEqual(resolved['source'], 'inherited')
        self.assertEqual(resolved['context'], {'industry': 'insurance', 'workflow': 'insurance claims processing',
                                               'decision': self.RESOLVED})

    def test_no_inheritance_on_topic_change_or_a_usable_classifier_verdict(self):
        conversation_id = self.business_turn()
        topic = 'How do LLM agents perform on the TravelPlanner benchmark?'
        run, _ = self.wrapped(topic, {'status': 'unavailable'})
        response = run({'query': 'And what about TravelPlanner results?', 'conversation_id': conversation_id, 'context_id': 'x'})
        self.assertEqual(response['conversation_turn']['resolution']['kind'], 'resolved')
        self.assertNotIn('business_context_inherited', response)  # reworded topic change: earlier topic absent
        from src.business_intent import VERSION
        verdict = {'version': VERSION, 'status': 'ok', 'value': {'is_business': False, 'industry': 'unspecified',
                   'workflow': '', 'decision': '', 'confidence': 'high'}}
        run, _ = self.wrapped(self.RESOLVED, verdict)
        response = run({'query': 'What about the risks?', 'conversation_id': conversation_id, 'context_id': 'x'})
        self.assertNotIn('business_context_inherited', response)  # the classifier's own verdict wins
        run, _ = self.wrapped('What about the risks?', {'status': 'unavailable'})
        response = run({'query': 'What about the risks?', 'conversation_id': conversation_id, 'context_id': 'x'})
        self.assertEqual(response['conversation_turn']['resolution']['kind'], 'unchanged')
        self.assertNotIn('business_context_inherited', response)  # resolver did not confirm continuity

    def test_research_only_ambiguous_tampered_and_older_turns_never_inherit(self):
        from src.business_insights import resolve_business_intent
        carried = {'industry': 'insurance', 'workflow': 'insurance claims processing', 'source': 'semantic',
                   'decision': self.RESOLVED + ' Research only.'}
        self.assertEqual(resolve_business_intent(self.RESOLVED + ' Research only.', None, carried)['source'], 'research_only')
        for broken in ({**carried, 'decision': FIRST}, {**carried, 'source': 'guess'}, {**carried, 'industry': 'fintech'},
                       {**carried, 'workflow': ''}):
            with self.subTest(broken=broken):
                self.assertNotEqual(resolve_business_intent(self.RESOLVED, None, {**broken, **(
                    {'decision': self.RESOLVED} if broken.get('decision') != FIRST else {})})['source'], 'inherited')
        # Ambiguous follow-up: clarification, no research and therefore nothing to inherit.
        conversation_id = self.business_turn()
        execute = Mock()
        run = server.conversational(execute, Mock(return_value=decision('clarify', question='Which risks?')), Mock(), self.path)
        response = run({'query': 'What about that?', 'conversation_id': conversation_id, 'context_id': 'x'})
        self.assertNotIn('business_context_inherited', response)
        execute.assert_not_called()
        # Only the immediately previous turn counts: a non-business turn in between breaks inheritance.
        brief = self.save('How do LLM agents perform on the TravelPlanner benchmark?')['library']['brief']['id']
        self.store.append_turn(conversation_id, brief, original_question='TravelPlanner?', resolved_question='TravelPlanner?',
                               resolution={'kind': 'standalone', 'calls': 0})
        self.assertIsNone(self.store.previous_business_context(conversation_id))

    def test_continuity_requires_the_earlier_business_topic_in_the_resolved_question(self):
        from src.conversation_context import continues_business_topic
        earlier = {'industry': 'insurance', 'workflow': 'insurance claims processing'}
        self.assertTrue(continues_business_topic(self.RESOLVED, earlier))
        self.assertFalse(continues_business_topic('How do LLM agents perform on the TravelPlanner benchmark?', earlier))
        self.assertTrue(continues_business_topic('What evidence supports agents for claims processing?', earlier))

    def test_inherited_context_is_recorded_in_business_provenance(self):
        from src.business_insights import translate_result
        from tests.test_downstream_business import CONTEXT, business
        provenance = {'source': 'inherited', 'inherited_from': 'semantic', 'from_position': 1, 'reason': 'classifier_unavailable'}
        envelope = translate_result(result_for(), context=CONTEXT, generate=Mock(return_value=json.dumps(business())),
                                    metadata={'provider': 'injected_test'}, context_provenance=provenance)
        self.assertEqual(envelope['result']['provenance']['business_translation']['context_provenance'], provenance)
