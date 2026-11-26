r"""Regression tests for the opt-in S2 paper-balanced selector (B1). 0 model calls.

    D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -X utf8 -m unittest test_s2_paper_balance   (from this folder)
"""
import json
import tempfile
import unittest
from pathlib import Path

import s3_env
import evidence as ev
import paper_balance as pb
from s2_paper_balance import S2Research
from engine import ConsolidatedResearch

HERE = Path(__file__).resolve().parent


def row(cid, title, words=200, section='results'):
    return {'chunk_id': cid, 'arxiv_id': cid.split('_')[0], 'title': title, 'text': 'w ' * words, 'section': section}


def count(p):
    return len(p['text'].split())


class NoTables:
    tables = {}

    def siblings(self, _c):
        return []


TITLES = {'P1': 'FooNet: fast forecasting', 'P2': 'FooNet-2: a successor', 'P3': 'BarGuard 2.0 for safety',
          'P4': 'A study of GPT-4o in clinics', 'P5': 'Unrelated survey'}


def corpus():
    rows = {}
    for p, t in TITLES.items():
        for i in range(30):
            rows[f'{p}_c{i:04d}'] = row(f'{p}_c{i:04d}', t)
    return rows


class PaperResolution(unittest.TestCase):
    def test_two_named_papers(self):
        ids = ['P1_c0000', 'P3_c0000', 'P5_c0000']
        self.assertEqual(pb.requested_papers('How do FooNet and BarGuard compare?', ids, TITLES), ['P1', 'P3'])

    def test_overlapping_titles_whole_word_only(self):
        ids = ['P1_c0000', 'P2_c0000']
        self.assertEqual(pb.requested_papers('What does FooNet report, and why?', ids, TITLES), ['P1'])
        self.assertEqual(pb.requested_papers('Compare FooNet and FooNet-2.', ids, TITLES), ['P1', 'P2'])

    def test_model_names_do_not_resolve_papers(self):
        ids = ['P1_c0000', 'P4_c0000']
        self.assertEqual(pb.requested_papers('How does FooNet compare with GPT-4o?', ids, TITLES), ['P1'])

    def test_missing_paper_not_requested(self):
        ids = ['P1_c0000', 'P5_c0000']  # BarGuard not in the candidate pool
        self.assertEqual(pb.requested_papers('Compare FooNet and BarGuard.', ids, TITLES), ['P1'])

    def test_unnamed_question(self):
        self.assertEqual(pb.requested_papers('What does the forecasting study show?', ['P1_c0000'], TITLES), [])


class Selection(unittest.TestCase):
    def setUp(self):
        self.rows = corpus()
        self.order = [f'P1_c{i:04d}' for i in range(30)] + [f'P3_c{i:04d}' for i in range(30)]

    def test_single_paper_identical_to_s2(self):
        q = 'What does FooNet report, and what limits apply?'
        b1, papers = pb.packet(q, self.order, self.rows, count, NoTables(), TITLES, mode='B1')
        s2, _ = pb.packet(q, self.order, self.rows, count, NoTables(), TITLES, mode='S2')
        self.assertEqual(papers, ['P1'])
        self.assertEqual([p['chunk_id'] for p in b1['passages']], [p['chunk_id'] for p in s2['passages']])

    def test_two_papers_balanced_and_budget_held(self):
        q = 'How do FooNet and BarGuard compare?'
        pk, papers = pb.packet(q, self.order, self.rows, count, NoTables(), TITLES, mode='B1')
        ids = [p['chunk_id'] for p in pk['passages']]
        self.assertEqual(papers, ['P1', 'P3'])
        self.assertTrue(any(i.startswith('P3_') for i in ids))          # starved paper recovered
        self.assertEqual(ids[:2], ['P1_c0000', 'P3_c0000'])              # round-robin in S2's own order
        self.assertLessEqual(pk['base_tokens'], ev.STANDARD_TOKENS)
        self.assertLessEqual(len(ids), ev.MAX_PASSAGES)

    def test_table_group_handling_unchanged(self):
        rows = self.rows
        for i in range(1, 4):
            rows[f'P3_table_ab_{i}'] = row(f'P3_table_ab_{i}', TITLES['P3'], words=50)
        tables = ev.TableIndex(rows.values())
        order = ['P1_c0000', 'P3_table_ab_2'] + self.order
        pk, _ = pb.packet('How do FooNet and BarGuard compare?', order, rows, count, tables, TITLES, mode='B1')
        ids = [p['chunk_id'] for p in pk['passages']]
        self.assertTrue({'P3_table_ab_1', 'P3_table_ab_2', 'P3_table_ab_3'} <= set(ids))  # whole group kept


def fake_engine(cls, data, order, **kw):
    ranked = lambda q, n: [data[c] for c in order[:n]]  # noqa: E731
    return cls(ranked=ranked, count=count, tables=NoTables(), generate=None, v2=None, gate=None, **kw)


class EngineFlag(unittest.TestCase):
    def test_flag_off_reproduces_frozen_s2(self):
        rows = corpus()
        order = [f'P1_c{i:04d}' for i in range(30)] + [f'P3_c{i:04d}' for i in range(30)]
        q = 'How do FooNet and BarGuard compare?'
        a = fake_engine(S2Research, rows, order, paper_balance=False, rows=rows)
        frozen = ConsolidatedResearch('standard', ranked=lambda q, n: [rows[c] for c in order[:n]], count=count,
                                      tables=NoTables(), generate=None, v2=None, gate=None)
        times = {}
        pa, _, _ = a.gather_evidence(q, __import__('engine').CheckpointStore(tempfile.mkdtemp()), times)
        pf, _, _ = frozen.gather_evidence(q, __import__('engine').CheckpointStore(tempfile.mkdtemp()), times)
        self.assertEqual([p['chunk_id'] for p in pa['passages']], [p['chunk_id'] for p in pf['passages']])

    def test_flag_on_records_and_applies(self):
        rows = corpus()
        order = [f'P1_c{i:04d}' for i in range(30)] + [f'P3_c{i:04d}' for i in range(30)]
        e = fake_engine(S2Research, rows, order, paper_balance=True, rows=rows)
        pk, _, _ = e.gather_evidence('How do FooNet and BarGuard compare?',
                                     __import__('engine').CheckpointStore(tempfile.mkdtemp()), {})
        self.assertTrue(pk['paper_balance']['applied'])
        self.assertTrue(any(p['chunk_id'].startswith('P3_') for p in pk['passages']))


class ReproducesOffline(unittest.TestCase):
    def test_engine_matches_offline_b1_on_all_triggered_questions(self):
        from eval_paper_balance import load_rows, DEMO, VAL
        from transformers import AutoTokenizer
        from prepare import ENCODER
        tok = AutoTokenizer.from_pretrained(str(ENCODER))
        memo = {}

        def tcount(p):
            if p['chunk_id'] not in memo:
                memo[p['chunk_id']] = len(tok(p['text'], add_special_tokens=True, truncation=False, verbose=False)['input_ids'])
            return memo[p['chunk_id']]
        result = json.loads((HERE / 'paper-balance.json').read_text(encoding='utf-8'))
        triggered = [o for o in result['questions'] if len(o['resolved']) >= 2]
        self.assertEqual(len(triggered), 6)
        refs = {}
        for name, path in [('consolidated/fresh-v2', HERE.parent / 'consolidated/fresh-v2/references.json'),
                           ('consolidated-v2/fresh-v3', HERE.parent / 'consolidated-v2/fresh-v3/references.json'),
                           ('fresh-v4', HERE / 'fresh-v4/references.json')]:
            for r in json.loads(path.read_text(encoding='utf-8')):
                refs[(name, r['id'])] = r
        bundles = {'fresh-v4': (load_rows(VAL), HERE / 'cache/fresh-v4-rankings.json')}
        demo = (load_rows(DEMO), HERE / 'cache/rankings.json')
        for o in triggered:
            rows, cache_path = bundles.get(o['set'], demo)
            cache = json.loads(cache_path.read_text(encoding='utf-8'))
            ref = refs[(o['set'], o['q'])]
            order = cache[ref['question']]['order']
            e = S2Research(ranked=lambda q, n, o_=order, r_=rows: [r_[c] for c in o_[:n]], count=tcount,
                           tables=ev.TableIndex(rows.values()), generate=None, v2=None, gate=None,
                           paper_balance=True, rows=rows)
            ids = {p['chunk_id'] for p in e.balanced_packet(ref['question'])['passages']}
            cov = sum(any(g and all(c in ids for c in g) for g in p['anchors']) for p in ref['required_points'])
            self.assertEqual(cov, o['B1'], (o['set'], o['q']))


if __name__ == '__main__':
    unittest.main()
