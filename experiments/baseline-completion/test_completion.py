"""Offline regression tests for the opt-in completion pass, replaying saved held-out traces. No model calls."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE)]
import completion  # noqa: E402
from src.answer_quality import review_summary  # noqa: E402
from src.research_chat import synthesize  # noqa: E402

RUN = ROOT / 'data/processed/codex-heldout-v1-baseline'
DEV = ROOT / 'data/processed/codex-baseline-v1-deployed'
QUESTIONS = {q['id']: q['question'] for q in json.loads(
    (ROOT / 'experiments/heldout-v1/questions.json').read_text(encoding='utf-8'))}
C0020 = '2602.16901v1_c0020'
GPT51 = 'For example, the average ASR on GPT-5.1 exceeds about 70%'
CLAUDE = 'Notably, Claude-4.5 demonstrates strong inherent resistance to prompt injection, achieving 0% ASR under both attack strategies.'


class Replay:
    """Returns queued replies by prompt type; records every call."""
    supports_response_schema = True

    def __init__(self, synthesis=(), review=()):
        self.queues = {'synthesis': list(synthesis), 'review': list(review)}
        self.calls = []

    def __call__(self, prompt, response_schema=None):
        kind = 'synthesis' if prompt.startswith('Synthesize an answer') else 'review'
        self.calls.append(kind)
        reply = self.queues[kind].pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply if isinstance(reply, str) else json.dumps(reply)


def saved(folder, qid):
    read = lambda name: json.loads((folder / qid / name).read_text(encoding='utf-8'))
    return read('1-synthesis.evidence.json'), read('1-synthesis.reply.json')['provider_text'], \
        read('2-review.reply.json')['provider_text']


def original_answer(qid, folder=RUN, question=None):
    """The Baseline answer exactly as the live run produced it, rebuilt from its recorded replies."""
    passages, draft, review = saved(folder, qid)
    question = question or QUESTIONS[qid]
    replay = Replay([draft], [review])
    answer = review_summary(question, synthesize(question, passages, generate=replay), passages, generate=replay)
    return question, passages, answer


def finding(text, *quotes):
    return {'text': text, 'kind': 'finding', 'support': [{'chunk_id': C0020, 'quote': q} for q in quotes]}


def redraft(*claims):
    return {'status': 'ok', 'claims': list(claims), 'limitations': []}


def review_of(n, keep=None, coverage='partial'):
    keep = list(range(n)) if keep is None else keep
    return {'coverage': coverage if keep else 'none', 'gap': 'Other requested parts are answered elsewhere.' if keep else
            'No retained claims.', 'retained_claim_indices': keep, 'limitations': [],
            'decisions': [{'index': i, 'supported': i in keep, 'relevant': i in keep, 'reason': 'checked'} for i in range(n)]}


GPT51_CLAIM = finding('Long-horizon attacks were highly effective against GPT-5.1, whose average ASR exceeded about 70%.', GPT51)
CLAUDE_CLAIM = finding('Claude-4.5 resisted both attack strategies, with 0% ASR under each.', CLAUDE)


class H05(unittest.TestCase):
    """Saved H05: one drafted claim; the review reported the GPT-5.1 and Claude-4.5 results as available but omitted."""

    def setUp(self):
        self.question, self.passages, self.answer = original_answer('H05')
        self.assertTrue(completion.should_complete(self.answer))
        self.before = deepcopy(self.answer)

    def run_completion(self, synthesis, review=()):
        replay = Replay(synthesis, review)
        out, record = completion.complete(self.question, self.answer, self.passages, generate=replay)
        self.assertEqual(self.answer, self.before)  # the input is never mutated
        return out, record, replay

    def test_recovers_the_two_omitted_points_and_keeps_the_original_claim(self):
        duplicate = {k: v for k, v in deepcopy(self.answer['claims'][0]).items() if k in ('text', 'kind', 'support')}
        interpretation = {**GPT51_CLAIM, 'kind': 'interpretation', 'text': 'This suggests safety training is insufficient.'}
        out, record, replay = self.run_completion([redraft(GPT51_CLAIM, CLAUDE_CLAIM, duplicate, interpretation)],
                                                  [review_of(2)])
        self.assertEqual(replay.calls, ['synthesis', 'review'])
        self.assertEqual(out['claims'][0], self.before['claims'][0])  # published claim unchanged and first
        self.assertEqual([c['text'] for c in out['claims'][1:]], [GPT51_CLAIM['text'], CLAUDE_CLAIM['text']])
        self.assertEqual((record['added'], record['model_calls']), (2, 2))
        self.assertIn('completion pass added 2', out['answer_lead'])
        self.assertEqual(out['limitations'][1:], self.before['limitations'][1:])  # other caveats preserved

    def test_invented_quote_discards_the_whole_redraft(self):
        bad = finding('GPT-5.1 was fully compromised.', 'GPT-5.1 was compromised in every single trial we ran.')
        out, record, replay = self.run_completion([redraft(bad)])
        self.assertEqual((out, record['added'], replay.calls), (self.before, 0, ['synthesis']))
        self.assertIn('error', record)

    def test_number_absent_from_its_quote_is_dropped_before_review(self):
        wrong = finding('GPT-5.1 average ASR exceeded 90%.', GPT51)
        out, record, replay = self.run_completion([redraft(wrong)])
        self.assertEqual((out, replay.calls), (self.before, ['synthesis']))
        self.assertEqual(record['dropped'][0]['reason'], 'number absent from cited quotes')

    def test_claims_the_review_rejects_are_not_added(self):
        overreach = finding('Claude-4.5 is immune to all prompt injection.', CLAUDE)
        out, record, _ = self.run_completion([redraft(GPT51_CLAIM, overreach)], [review_of(2, keep=[0])])
        self.assertEqual([c['text'] for c in out['claims'][1:]], [GPT51_CLAIM['text']])
        self.assertEqual(record['rejected_by_review'], 1)

    def test_invalid_review_or_provider_error_returns_the_original(self):
        for synthesis, review in (([redraft(GPT51_CLAIM)], ['{"coverage": "full"}']),
                                  ([RuntimeError('provider timeout')], [])):
            with self.subTest(review=review):
                out, record, _ = self.run_completion(synthesis, review)
                self.assertEqual((out, record['added']), (self.before, 0))

    def test_insufficient_redraft_adds_nothing(self):
        abstain = {'status': 'insufficient_evidence', 'claims': [], 'limitations': [
            {'text': 'Not supported.', 'support': [{'chunk_id': C0020, 'quote': CLAUDE}]}]}
        out, record, replay = self.run_completion([abstain])
        self.assertEqual((out, record['added'], replay.calls), (self.before, 0, ['synthesis']))


class NoTrigger(unittest.TestCase):
    def test_h06_and_h10_omissions_are_invisible_to_the_existing_review(self):
        # Their reviews said "full" although points were omitted: the pass cannot help, and costs nothing.
        for qid in ('H06', 'H10'):
            with self.subTest(qid=qid):
                question, passages, answer = original_answer(qid)
                self.assertEqual(answer['quality_review']['coverage'], 'full')
                replay = Replay()
                out, record = completion.complete(question, answer, passages, generate=replay)
                self.assertEqual((out, record['triggered'], replay.calls), (answer, False, []))

    def test_missing_evidence_gap_does_not_trigger(self):
        question = json.loads((DEV / 'F02' / 'result.json').read_text(encoding='utf-8'))['question']
        _, passages, answer = original_answer('F02', DEV, question)
        self.assertIn('do not establish', answer['quality_review']['gap'])
        self.assertFalse(completion.should_complete(answer))


class Wiring(unittest.TestCase):
    def test_enable_wraps_baseline_summary_and_requires_the_review(self):
        from src.experimental.demo import create_research
        question, passages, _ = original_answer('H05')
        _, draft, review = saved(RUN, 'H05')
        replay = Replay([draft, redraft(GPT51_CLAIM, CLAUDE_CLAIM)], [review, review_of(2)])
        identity = lambda: {'collection': 'fixture', 'count': len(passages), 'indexed_records_sha256': 'fixture'}
        research = create_research((lambda q, k: deepcopy(passages)[:k], identity, 'fixture', {'method': 'fixture'}),
                                   replay, {'provider': 'replay'}, 8)
        completion.enable(research)
        envelope = research.execute({'query': question, 'context_id': research.context_id, 'interpret_context': False})
        claims = envelope['result']['summary']['claims']
        self.assertEqual(len(claims), 3)
        self.assertEqual(replay.calls, ['synthesis', 'review', 'synthesis', 'review'])  # +2 calls when triggered
        research.quality_check = False
        with self.assertRaises(ValueError):
            completion.enable(research)


if __name__ == '__main__':
    unittest.main()
