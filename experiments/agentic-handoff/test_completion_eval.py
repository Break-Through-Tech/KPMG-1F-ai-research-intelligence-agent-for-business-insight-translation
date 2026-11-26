"""Offline tests for completion-eval-v1 (arm A on C01-C15, arm B = frozen completion on saved A answers). No model calls."""
import hashlib
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

import apply_completion
import codex_baseline
import fake_provider
from test_codex_heldout import engine
from test_quote_grounding import PACKET

QUESTIONS = {q['id']: q['question'] for q in json.loads(
    (codex_baseline.SETS['completion'][0] / 'questions.json').read_text(encoding='utf-8'))}
GAP = 'The second requested result is available in the passages but omitted from the retained claims.'


class Adapter:
    """Baseline-shaped replies. Reviews report an available-but-omitted gap for the questions in `gap_for`."""
    supports_response_schema = True

    def __init__(self, gap_for=(), redraft_quote=None, fail_on=None):
        self.receipts, self.prompts, self.gap_for = [], [], set(gap_for)
        self.redraft_quote, self.fail_on, self.question = redraft_quote, fail_on or {}, None

    def __call__(self, prompt, *, response_schema=None):
        self.prompts.append(prompt[:60])
        record = {'status': 'started'}
        self.receipts.append(record)
        failure = self.fail_on.get(len(self.prompts))
        if failure:
            record.update(status='failed', diagnostic=failure)
            error = RuntimeError('Codex generation failed')
            error.codex_diagnostic = failure
            raise error
        record['status'] = 'ok'
        if prompt.startswith('Synthesize an answer') and 'COMPLETION REQUEST' in prompt:
            passage = PACKET[1]
            return json.dumps({'status': 'ok', 'limitations': [], 'claims': [{'text': 'Arxiv used a time-based split.',
                    'kind': 'finding', 'support': [{'chunk_id': passage['chunk_id'], 'quote': self.redraft_quote}]}]})
        answer = fake_provider.answer(prompt)
        if prompt.startswith('ANSWER QUALITY REVIEW') and any(QUESTIONS[q] in prompt for q in self.gap_for):
            answer.update(coverage='partial', gap=GAP)
        return json.dumps(answer)


def arm_a(root, adapter):
    research = engine(False)
    return codex_baseline.run('completion-eval-baseline', research=research, generate=adapter,
                              receipts=adapter.receipts, out_root=root)


def tree_hash(folder):
    h = hashlib.sha256()
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            h.update(str(path.relative_to(folder)).encode() + path.read_bytes())
    return h.hexdigest()


class Setup(unittest.TestCase):
    def test_arm_a_is_unchanged_baseline_on_the_fifteen_frozen_questions_with_a_hard_cap_of_30(self):
        self.assertEqual(codex_baseline.VARIANTS['completion-eval-baseline'][1:], (False, False, 'completion'))
        with TemporaryDirectory() as temp:
            root, adapter = Path(temp), Adapter()
            status = arm_a(root, adapter)
            self.assertEqual(list(status), [f'C{i:02d}' for i in range(1, 16)])
            info = json.loads((root / 'codex-completion-v1-baseline' / 'run.json').read_text())
            self.assertEqual((info['calls_used'], info['call_cap']), (30, 30))

    def test_seal_covers_the_frozen_completion_code(self):
        self.assertEqual(codex_baseline.set_sealed('completion'), 'verified')
        with TemporaryDirectory() as temp:
            copy = Path(temp) / 'set'
            shutil.copytree(codex_baseline.SETS['completion'][0], copy)
            seal = json.loads((copy / 'seal.json').read_text())
            seal['completion_py_sha256'] = '0' * 64
            (copy / 'seal.json').write_text(json.dumps(seal))
            with mock.patch.dict(codex_baseline.SETS, {'completion': (copy, codex_baseline.SETS['completion'][1])}):
                with self.assertRaises(SystemExit):
                    codex_baseline.set_sealed('completion')


class ArmB(unittest.TestCase):
    def prepared(self, root, gap_for=('C03',)):
        arm_a(root, Adapter(gap_for=gap_for))
        return tree_hash(root / 'codex-completion-v1-baseline')

    def test_only_triggered_questions_spend_calls_and_saved_a_answers_are_untouched(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            before = self.prepared(root)
            quote = ' '.join(PACKET[1]['text'].split())[-40:]
            adapter = Adapter(redraft_quote=quote)
            status = apply_completion.run(generate=adapter, receipts=adapter.receipts, out_root=root)
            self.assertEqual(tree_hash(root / 'codex-completion-v1-baseline'), before)  # A never regenerated
            triggered = [q for q, v in status.items() if v.get('triggered')]
            self.assertEqual(triggered, ['C03'])
            self.assertEqual(len(adapter.prompts), 2)  # re-draft + review, only for C03
            saved = json.loads((root / 'codex-completion-v1-completed' / 'C03' / 'result.json').read_text(encoding='utf-8'))
            original = json.loads((root / 'codex-completion-v1-baseline' / 'C03' / 'result.json').read_text(encoding='utf-8'))
            a_claims = original['envelope']['result']['summary']['claims']
            self.assertEqual(saved['summary']['claims'][:len(a_claims)], a_claims)  # every A claim kept, in order
            self.assertEqual(saved['record']['added'], 1)

    def test_resume_never_repeats_and_cap_is_30(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepared(root, gap_for=())
            first = Adapter()
            apply_completion.run(generate=first, receipts=first.receipts, out_root=root)
            again = Adapter()
            apply_completion.run(generate=again, receipts=again.receipts, out_root=root)
            self.assertEqual((first.prompts, again.prompts), ([], []))  # nothing triggered, nothing repeated
            info = json.loads((root / 'codex-completion-v1-completed' / 'run.json').read_text())
            self.assertEqual(info['call_cap'], 30)

    def test_quota_error_stops_arm_b(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            self.prepared(root, gap_for=('C01', 'C02'))
            adapter = Adapter(fail_on={1: {'category': 'cli_exit', 'provider_code': 'insufficient_quota'}})
            status = apply_completion.run(generate=adapter, receipts=adapter.receipts, out_root=root)
            self.assertEqual(status['C01']['state'], 'stopped')
            self.assertNotIn('C02', status)


if __name__ == '__main__':
    unittest.main()
