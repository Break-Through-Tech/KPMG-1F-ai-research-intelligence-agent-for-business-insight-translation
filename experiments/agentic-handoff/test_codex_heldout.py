"""Offline tests for the held-out Baseline vs Baseline+decomposition runner. Scripted model replies; no index loaded."""
import json
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

import codex_baseline
from test_codex_baseline import FakeAdapter
from test_quote_grounding import PACKET

sys.path.insert(0, str(codex_baseline.ROOT / 'experiments/baseline-decomposition'))
from decomposed_retrieval import decomposed  # noqa: E402

HELD = codex_baseline.SETS['heldout'][0]


def engine(decompose):
    from src.experimental.demo import create_research
    base = lambda q, k: [dict(p) for p in PACKET][:k]
    retrieve = decomposed(base, splitter=lambda q: ['part one', 'part two']) if decompose else base
    identity = lambda: {'collection': 'fixture', 'count': len(PACKET), 'indexed_records_sha256': 'fixture'}
    return create_research((retrieve, identity, 'fixture-index', {'method': 'fixture'}), lambda *a, **k: None,
                           {'provider': 'fake'}, 8)


def go(root, variant, adapter):
    research = engine(codex_baseline.VARIANTS[variant][2])
    return codex_baseline.run(variant, research=research, generate=adapter, receipts=adapter.receipts, out_root=root)


class HeldOut(unittest.TestCase):
    def test_variants_differ_only_in_decomposition(self):
        base, dec = codex_baseline.VARIANTS['heldout-baseline'], codex_baseline.VARIANTS['heldout-decomposed']
        self.assertEqual((base[1], base[2], base[3]), (False, False, 'heldout'))
        self.assertEqual((dec[1], dec[2], dec[3]), (False, True, 'heldout'))
        self.assertNotEqual(base[0], dec[0])
        self.assertEqual(len({v[0] for v in codex_baseline.VARIANTS.values()}), len(codex_baseline.VARIANTS))

    def test_baseline_arm_runs_the_ten_frozen_heldout_questions_at_two_calls_each(self):
        frozen = {q['id']: q['question'] for q in json.loads((HELD / 'questions.json').read_text(encoding='utf-8'))}
        with TemporaryDirectory() as temp:
            root, adapter = Path(temp), FakeAdapter()
            status = go(root, 'heldout-baseline', adapter)
            self.assertEqual(list(status), [f'H{i:02d}' for i in range(1, 11)])
            out = root / 'codex-heldout-v1-baseline'
            info = json.loads((out / 'run.json').read_text())
            self.assertEqual((info['calls_used'], info['call_cap'], info['question_decomposition']), (20, 30, False))
            saved = json.loads((out / 'H04' / 'result.json').read_text(encoding='utf-8'))
            self.assertEqual(saved['question'], frozen['H04'])
            self.assertGreaterEqual(saved['retrieval_invocations'], 1)
            rows = codex_baseline.report(out, 'heldout')
            self.assertEqual([p['point_id'] for p in rows['H01']['required_points']], ['H01.1', 'H01.2', 'H01.3'])

    def test_decomposed_arm_feeds_the_merged_packet_with_the_same_call_count(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            go(root, 'heldout-baseline', FakeAdapter())
            go(root, 'heldout-decomposed', FakeAdapter())
            sizes = {}
            for arm in ('baseline', 'decomposed'):
                out = root / f'codex-heldout-v1-{arm}'
                packet = json.loads((out / 'H01' / '1-synthesis.evidence.json').read_text(encoding='utf-8'))
                sizes[arm] = len(packet)
                self.assertEqual(json.loads((out / 'run.json').read_text())['calls_used'], 20)
            self.assertEqual(sizes['baseline'], min(8, len(PACKET)))
            self.assertGreaterEqual(sizes['decomposed'], sizes['baseline'])

    def test_resume_never_repeats_completed_heldout_questions(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            go(root, 'heldout-decomposed', FakeAdapter())
            again = FakeAdapter()
            go(root, 'heldout-decomposed', again)
            self.assertEqual(again.prompts, [])

    def test_seal_verifies_and_detects_tampering(self):
        self.assertEqual(codex_baseline.heldout_sealed(), 'verified')
        with TemporaryDirectory() as temp:
            copy = Path(temp) / 'heldout'
            shutil.copytree(HELD, copy)
            (copy / 'references.json').write_text('[]', encoding='utf-8')
            with mock.patch.dict(codex_baseline.SETS, {'heldout': (copy, codex_baseline.SETS['heldout'][1])}):
                with self.assertRaises(SystemExit):
                    codex_baseline.heldout_sealed()


if __name__ == '__main__':
    unittest.main()
