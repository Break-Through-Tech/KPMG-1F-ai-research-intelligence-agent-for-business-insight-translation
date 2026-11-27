"""End-to-end DRY RUN of the controlled A/B against the ACTUAL live backend, with a fake provider. No model calls.

What is real: live_backend.py with --profile ab-agentic-1 --agentic, the demo-100 index, encoder and reranker, the
capped wrapper, the SQLite call ledger (a DISPOSABLE copy of the real ledger standing in for the canonical one via an
in-memory, test-only profile edit), the baseline pipeline, the orchestrator, validators, envelopes, ab_run.py and
ab_eval.py. What is fake: src.codex_generation (fake_provider.py), so every "model" answer is deterministic and local.
The real ledger is hashed before and after and must be unchanged.

Run from the repository root (needs the local models and corpus; ~1-2 minutes):
  py -3.14 -B experiments/agentic/test_ab_dryrun.py
(-I is not used because the retrieval models need the user site-packages.)
"""
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TE = HERE.parent / 'table-endpoint'
sys.path.insert(0, str(HERE))
import ab_eval  # noqa: E402
import ab_run  # noqa: E402

REAL_LEDGER = Path(r'D:\KPMG-demo-corpus\table-endpoint-exp\codex-authorization-40.ledger.sqlite3')
EXPORT = Path(r'D:\KPMG-demo-corpus\main-727b0b3')
BUNDLE = EXPORT / 'data/processed/demo-bundles/demo-100'
ENCODER = Path.home() / '.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
RERANKER = Path(r'C:\Users\ngkho\KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation\data\processed\model-cache'
                r'\models--cross-encoder--ms-marco-MiniLM-L6-v2\snapshots\233902d25c440f23af6f7d6e94d2946bac0bee0a')
AUDIT = Path(r'D:\KPMG-demo-corpus\table-endpoint-exp\table-audit-demo-100.json')
NEEDED = (REAL_LEDGER, BUNDLE / 'parents.jsonl', ENCODER, RERANKER, AUDIT)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@unittest.skipUnless(all(p.exists() for p in NEEDED), 'local corpus, models or ledger not present')
class DryRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_before = sha(REAL_LEDGER)
        cls.tmp = Path(tempfile.mkdtemp())
        cls.ledger = cls.tmp / 'standin-ledger.sqlite3'
        shutil.copy(REAL_LEDGER, cls.ledger)
        cls.fake_log = cls.tmp / 'fake-calls.txt'
        cls.port = free_port()
        argv = ['--export', str(EXPORT), '--bundle', str(BUNDLE), '--encoder', str(ENCODER), '--reranker', str(RERANKER),
                '--library', str(cls.tmp / 'briefs.sqlite3'), '--table-audit', str(AUDIT), '--call-log', str(cls.tmp / 'session-calls.jsonl'),
                '--port', str(cls.port), '--max-calls', '14', '--agentic', '--profile', 'ab-agentic-1',
                '--call-ledger', str(cls.ledger), '--authorized-calls', '40', '--experiment', 'ab-agentic-1', '--experiment-cap', '14']
        code = (f"import sys; sys.path.insert(0, {str(TE)!r}); sys.path.insert(0, {str(HERE)!r})\n"
                f"from pathlib import Path\nimport ab_profile\n"
                f"ab_profile.PROFILES['ab-agentic-1']['ledger_path'] = Path({str(cls.ledger)!r})  # TEST-ONLY stand-in\n"
                f"import fake_provider\nsys.modules['src.codex_generation'] = fake_provider  # TEST-ONLY provider\n"
                f"import live_backend\nlive_backend.main({argv!r})")
        env = {**os.environ, 'FAKE_CALL_LOG': str(cls.fake_log)}
        cls.server = subprocess.Popen([sys.executable, '-B', '-u', '-c', code], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, cwd=str(TE), env=env)
        cls.startup = None
        deadline = time.time() + 300
        while time.time() < deadline:
            line = cls.server.stdout.readline()
            if not line:
                break
            if '"url"' in line:
                cls.startup = json.loads(line)
                break
        if cls.startup is None:
            cls.server.kill()
            raise RuntimeError('live backend did not start')
        cls.backend = f'http://127.0.0.1:{cls.port}'
        cls.spec = ab_eval.load_questions(HERE / 'ab_questions.json')
        cls.preflight = ab_run.preflight(cls.backend, cls.spec)
        cls.run_dir = ab_run.run(cls.backend, cls.spec, cls.tmp / 'run', approval=ab_run.APPROVAL)
        report, (review, key) = ab_eval.build_report(ab_eval.load_records(cls.run_dir), cls.spec, blind=True, run_dir=cls.run_dir)
        cls.report_dir = ab_eval.write_report(cls.tmp / 'report', report, review, key)
        cls.report = report

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        try:
            cls.server.wait(timeout=20)
        except subprocess.TimeoutExpired:
            cls.server.kill()
        time.sleep(1)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_backend_is_the_pinned_corpus_and_preflight_passed(self):
        self.assertTrue(self.startup['identities_match'])
        self.assertEqual(self.startup['table_index_sha256'], self.spec['corpus']['parents_sha256'])
        self.assertTrue(self.preflight['ok'], self.preflight['problems'])
        self.assertEqual(self.preflight['model_calls'], 0)

    def test_four_records_with_actual_calls_matching_the_ledger(self):
        records = ab_eval.load_records(self.run_dir)
        self.assertEqual([(r['question_id'], r['mode']) for r in records], [tuple(s) for s in self.spec['sequence']])
        calls = [r['model_calls_actual'] for r in records]
        self.assertEqual(calls, [2, 3, 2, 3])  # fake provider: synthesis+review; plan+research+verify
        connection = sqlite3.connect(f'file:{self.ledger.as_posix()}?mode=ro', uri=True)
        rows = connection.execute("SELECT state FROM calls WHERE experiment = 'ab-agentic-1'").fetchall()
        lock = connection.execute("SELECT value FROM meta WHERE key = 'locked_experiment'").fetchone()
        connection.close()
        self.assertEqual(len(rows), sum(calls))
        self.assertTrue(all(state == 'completed' for (state,) in rows))
        self.assertEqual(lock, ('ab-agentic-1',))  # the stand-in, not the real ledger, was locked
        self.assertEqual(self.fake_log.read_text().count('UNEXPECTED'), 0)  # no business translation or other call
        self.assertEqual(len(self.fake_log.read_text().splitlines()), sum(calls))

    def test_answers_are_research_only_with_valid_citations_on_the_pinned_index(self):
        for analysis in self.report['analyses']:
            auto = analysis['automatic']
            with self.subTest(f"{analysis['question_id']}-{analysis['mode']}"):
                self.assertIn(auto['status'], ('answered', 'abstained'))
                self.assertTrue(auto['index_matches_pinned_corpus'])
                self.assertIsNot(auto['citation_ids_valid'], False)
                self.assertIsNot(auto['quotes_in_passages'], False)
                self.assertFalse(auto['business_insight_present'])
                self.assertEqual(analysis['human'], {'false_abstention': 'pending', 'overall_correct': 'pending'})
        agentic = [a for a in self.report['analyses'] if a['mode'] == 'agentic']
        self.assertTrue(all(a['automatic']['model_calls_actual'] == a['automatic']['model_calls_reported_by_agentic'] for a in agentic))
        self.assertTrue(all(a['orchestration_trace'] for a in agentic))
        routing = [e for e in agentic[0]['orchestration_trace'] if e.get('decision') == 'business_routing'][0]
        self.assertIn('Research-only', routing['reason'])

    def test_report_files_and_real_ledger_untouched(self):
        self.assertTrue((self.report_dir / 'report.md').exists() and (self.report_dir / 'review-sheet.csv').exists())
        self.assertEqual(sha(REAL_LEDGER), self.real_before)


if __name__ == '__main__':
    unittest.main(verbosity=1)
