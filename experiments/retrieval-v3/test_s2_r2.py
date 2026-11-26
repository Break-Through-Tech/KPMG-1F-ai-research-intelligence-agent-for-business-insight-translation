r"""Regression tests for S2-R2 (0 model calls).

    D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -X utf8 -m unittest test_s2_r2   (from this folder)
"""
import json
import tempfile
import unittest
from pathlib import Path

import s3_env
import evidence as ev
from engine import CheckpointStore, ConsolidatedResearch
from components import components
from s2_r2 import S2R2Research

HERE = Path(__file__).resolve().parent
TITLES = {'P1': 'FooNet: fast forecasting', 'P2': 'BarGuard 2.0 for safety', 'P3': 'Unrelated survey'}


def corpus():
    rows = {}
    for p, t in TITLES.items():
        for i in range(40):
            rows[f'{p}_c{i:04d}'] = {'chunk_id': f'{p}_c{i:04d}', 'arxiv_id': p, 'title': t, 'text': 'w ' * 300,
                                     'section': 'results'}
    return rows


def count(p):
    return len(p['text'].split())


class NoTables:
    tables = {}

    def siblings(self, _c):
        return []


def ranked_from(rows, orders, default):
    def ranked(q, n):
        return [rows[c] for c in orders.get(q, default)[:n]]
    return ranked


def engine(strategy, ranked, rows):
    return S2R2Research(retrieval_strategy=strategy, ranked=ranked, count=count, tables=NoTables(), generate=None,
                        v2=None, gate=None, rows=rows, parallel_search=False)


def ids(packet):
    return [p['chunk_id'] for p in packet['passages']]


def gather(e, q):
    return e.gather_evidence(q, CheckpointStore(tempfile.mkdtemp()), {})[0]


class R2(unittest.TestCase):
    def setUp(self):
        self.rows = corpus()
        self.base = [f'P1_c{i:04d}' for i in range(40)] + [f'P2_c{i:04d}' for i in range(40)]

    def test_default_is_s2_and_matches_frozen(self):
        q = 'What does FooNet report, and what limits apply?'
        rk = ranked_from(self.rows, {}, self.base)
        e = S2R2Research(ranked=rk, count=count, tables=NoTables(), generate=None, v2=None, gate=None, rows=self.rows)
        frozen = ConsolidatedResearch('standard', ranked=rk, count=count, tables=NoTables(), generate=None, v2=None,
                                      gate=None)
        self.assertEqual(e.strategy, 's2')
        self.assertEqual(ids(gather(e, q)), ids(gather(frozen, q)))

    def test_invalid_strategy_rejected(self):
        with self.assertRaises(ValueError):
            S2R2Research(retrieval_strategy='x', ranked=None, count=count, tables=NoTables(), generate=None, v2=None,
                         gate=None)

    def test_simple_question_single_ask_equals_s2(self):
        q = 'What is FooNet?'
        self.assertEqual(components(q), [])
        rk = ranked_from(self.rows, {}, self.base)
        pk = gather(engine('r2', rk, self.rows), q)
        self.assertEqual(pk['r2']['route'], 's2-window (single ask)')
        self.assertEqual(ids(pk), ids(gather(engine('s2', rk, self.rows), q)))

    def test_named_cross_paper_routes_to_b1(self):
        q = 'How do FooNet and BarGuard compare?'
        rk = ranked_from(self.rows, {}, self.base)
        pk = gather(engine('r2', rk, self.rows), q)
        self.assertEqual(pk['r2']['route'], 'b1')
        self.assertTrue(any(i.startswith('P2_') for i in ids(pk)))

    def test_unnamed_multipart_routes_to_fusion_and_promotes_component_evidence(self):
        q = 'What does the forecasting study propose, how accurate was it, and what limits apply?'
        comps = components(q)
        orders = {c: ['P1_c0035'] + self.base for c in comps}
        rk = ranked_from(self.rows, orders, self.base)
        pk = gather(engine('r2', rk, self.rows), q)
        self.assertEqual(pk['r2']['route'], 'fusion')
        self.assertIn('P1_c0035', ids(pk))                       # rank 36 originally, top in every component
        self.assertNotIn('P1_c0035', ids(gather(engine('s2', rk, self.rows), q)))

    def test_single_paper_multipart_keeps_budget_and_head(self):
        q = 'What does FooNet propose, how fast is it, and what limits apply?'
        rk = ranked_from(self.rows, {c: list(reversed(self.base)) for c in components(q)}, self.base)
        pk = gather(engine('r2', rk, self.rows), q)
        self.assertLessEqual(pk['base_tokens'], ev.STANDARD_TOKENS)
        self.assertLessEqual(pk['conclusion_tokens'], ev.CONCLUSION_TOKENS)
        self.assertLessEqual(len(pk['passages']), ev.MAX_PASSAGES)
        self.assertEqual(ids(pk)[:4], self.base[:4])              # original top-4 always first

    def test_deterministic_ordering(self):
        q = 'What does FooNet propose, how fast is it, and what limits apply?'
        rk = ranked_from(self.rows, {c: list(reversed(self.base)) for c in components(q)}, self.base)
        a = [ids(gather(engine('r2', rk, self.rows), q)) for _ in range(3)]
        p = S2R2Research(retrieval_strategy='r2', ranked=rk, count=count, tables=NoTables(), generate=None, v2=None,
                         gate=None, rows=self.rows, parallel_search=True)
        self.assertTrue(a[0] == a[1] == a[2] == ids(gather(p, q)))


class ReproducesOffline(unittest.TestCase):
    def test_fresh_v4_through_engine_wrapper(self):
        """fresh-v4 subset of the 236-point comparison: S2 36, B1 40, R2 42 (full table in r2-offline.json)."""
        from eval_paper_balance import load_rows, VAL
        from transformers import AutoTokenizer
        from prepare import ENCODER
        tok = AutoTokenizer.from_pretrained(str(ENCODER))
        memo = {}

        def tcount(p):
            if p['chunk_id'] not in memo:
                memo[p['chunk_id']] = len(tok(p['text'], add_special_tokens=True, truncation=False, verbose=False)['input_ids'])
            return memo[p['chunk_id']]
        rows = load_rows(VAL)
        cache = json.loads((HERE / 'cache/fresh-v4-rankings.json').read_text(encoding='utf-8'))
        rk = lambda q, n: [rows[c] for c in cache[q]['order'][:n]]  # noqa: E731
        tables = ev.TableIndex(rows.values())
        refs = json.loads((HERE / 'fresh-v4/references.json').read_text(encoding='utf-8'))
        got = {}
        for s in ('s2', 'b1', 'r2'):
            e = S2R2Research(retrieval_strategy=s, ranked=rk, count=tcount, tables=tables, generate=None, v2=None,
                             gate=None, rows=rows, parallel_search=False)
            total = 0
            for ref in refs:
                pk = gather(e, ref['question'])
                have = {p['chunk_id'] for p in pk['passages']}
                total += sum(any(g and all(c in have for c in g) for g in p['anchors']) for p in ref['required_points'])
            got[s] = total
        self.assertEqual(got, {'s2': 36, 'b1': 40, 'r2': 42})


if __name__ == '__main__':
    unittest.main()
