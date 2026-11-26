r"""Regression tests: optimized S2-R2 produces byte-identical evidence with one fewer original search (0 LLM calls).

    D:\KPMG-venvs\stage-a-py314\Scripts\python.exe -X utf8 -m unittest test_s2_r2_opt
"""
import json
import tempfile
import unittest

import s3_env  # noqa: F401
from engine import CheckpointStore
from components import components
from s2_r2 import S2R2Research
from s2_r2_opt import S2R2OptResearch
from test_s2_r2 import corpus, count, NoTables


def run(cls, question, orders, default, rows, parallel=False):
    calls = []

    def ranked(q, n):
        calls.append((q, n))
        return [rows[c] for c in orders.get(q, default)[:n]]
    e = cls(retrieval_strategy='r2', ranked=ranked, count=count, tables=NoTables(), generate=None, v2=None, gate=None,
            rows=rows, parallel_search=parallel)
    pk = e.gather_evidence(question, CheckpointStore(tempfile.mkdtemp()), {})[0]
    return json.dumps(pk, sort_keys=True, default=str), calls


class Optimized(unittest.TestCase):
    def setUp(self):
        self.rows = corpus()
        self.base = [f'P1_c{i:04d}' for i in range(40)] + [f'P2_c{i:04d}' for i in range(40)]

    def check(self, q, orders, expected_saving=1):
        old, c_old = run(S2R2Research, q, orders, self.base, self.rows)
        new, c_new = run(S2R2OptResearch, q, orders, self.base, self.rows)
        self.assertEqual(old, new)                                          # byte-identical packet
        self.assertEqual(len(c_old) - len(c_new), expected_saving)          # exactly the duplicate removed
        self.assertEqual(len(set(c_new)), len(c_new))                       # no query searched twice
        return c_new

    def test_simple_question(self):
        self.check('What is FooNet?', {})

    def test_named_cross_paper(self):
        calls = self.check('How do FooNet and BarGuard compare?', {})
        self.assertEqual(len(calls), 1)                                      # B1 route: one search only

    def test_multipart_fusion(self):
        q = 'What does the forecasting study propose, how accurate was it, and what limits apply?'
        orders = {c: ['P1_c0035'] + self.base for c in components(q)}
        calls = self.check(q, orders)
        self.assertEqual(len(calls), 1 + len(components(q)))

    def test_parallel_identical(self):
        q = 'What does FooNet propose, how fast is it, and what limits apply?'
        orders = {c: list(reversed(self.base)) for c in components(q)}
        a, _ = run(S2R2OptResearch, q, orders, self.base, self.rows, parallel=False)
        b, _ = run(S2R2OptResearch, q, orders, self.base, self.rows, parallel=True)
        self.assertEqual(a, b)

    def test_no_state_across_requests(self):
        q1, q2 = 'What is FooNet?', 'What is BarGuard?'
        e_calls = []
        rows = self.rows

        def ranked(q, n):
            e_calls.append(q)
            return [rows[c] for c in self.base[:n]]
        e = S2R2OptResearch(retrieval_strategy='r2', ranked=ranked, count=count, tables=NoTables(), generate=None,
                            v2=None, gate=None, rows=rows, parallel_search=False)
        for q in (q1, q1, q2):
            e.gather_evidence(q, CheckpointStore(tempfile.mkdtemp()), {})
        self.assertEqual(e_calls, [q1, q1, q2])                              # memo is per request, not global


if __name__ == '__main__':
    unittest.main()
