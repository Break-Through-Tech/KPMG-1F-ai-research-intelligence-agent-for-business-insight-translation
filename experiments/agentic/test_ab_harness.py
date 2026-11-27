"""Model-free tests for the A/B harness (ab_eval.py) and the guarded runner (ab_run.py).

Run from the repository root:  py -3.14 -I -B experiments/agentic/test_ab_harness.py
Envelopes are produced by the REAL contracts (synthesize, run_research, the orchestrator and to_envelope) with fake
providers; the runner is exercised against an in-process fake backend. No model, no network, no real ledger.
The end-to-end run against the actual live backend is in test_ab_dryrun.py.
"""
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
import ab_eval  # noqa: E402
import ab_run  # noqa: E402
import fake_provider  # noqa: E402
from agents import OrchestratorAgent  # noqa: E402
from envelope import to_envelope  # noqa: E402

SPEC = ab_eval.load_questions(HERE / 'ab_questions.json')
INDEX = SPEC['corpus']['parents_sha256']
PARENTS = Path(SPEC['corpus']['bundle']) / 'parents.jsonl'


def passage(cid, text, arxiv):
    url = f'https://arxiv.org/html/{arxiv}'
    return {'chunk_id': cid, 'text': text, 'arxiv_id': arxiv, 'title': f'Paper {arxiv}', 'pdf_url': f'https://arxiv.org/pdf/{arxiv}',
            'source': 'html', 'source_url': url, 'page_number': None, 'section': 'abstract'}


# Real corpus sentences (verbatim) so required-point coverage can be exercised.
EVIDENCE = {
    'Q2': [passage('2412.14470v2_c0000', 'Our evaluation of 16 popular LLM agents reveals a concerning result: none of the agents achieves a safety score above 60%.', '2412.14470v2'),
           passage('2402.01622v4_c0000', 'Comprehensive evaluations show that the current language agents are not yet capable of handling such complex planning tasks, even GPT-4 only achieves a success rate of 0.6 %.', '2402.01622v4')],
    'Q3': [passage('2602.00931v2_c0000', 'On mathematical reasoning benchmarks, CU- DPO improves strategy selection accuracy from 35–46% to 68–78% across seven base models.', '2602.00931v2')],
}


class FakeGenerate:
    supports_response_schema = True

    def __init__(self):
        self.calls = 0

    def __call__(self, prompt, response_schema=None):
        self.calls += 1
        return json.dumps(fake_provider.answer(prompt))


def baseline_envelope(qid):
    from src.research_chat import synthesize
    from src.answer_quality import review_summary
    from src.research_pipeline import run_research
    generate = FakeGenerate()
    evidence = EVIDENCE[qid]
    result = run_research({'query': SPEC['questions'][qid]['text'], 'top_k': 8}, retrieve=lambda q, k: evidence,
                          summarize_fn=lambda q, ps: review_summary(q, synthesize(q, ps, generate=generate), ps, generate=generate),
                          provenance={'index': {'indexed_records_sha256': INDEX}, 'timings_seconds': {'total': 1.5},
                                      'stages': {'retrieval': 'ok', 'summary': 'ok', 'business': 'not_requested'}})
    return {'mode': 'indexed', 'scenario': 'summary-only', 'result': result, 'error': None}, generate.calls


def agentic_envelope(qid):
    generate = FakeGenerate()
    evidence = EVIDENCE[qid]
    r = OrchestratorAgent(generate=generate, retrieve=lambda q, k: [dict(p) for p in evidence], top_k=8,
                          index_sha256=INDEX, research_only=True).run(SPEC['questions'][qid]['text'])
    return to_envelope(r, top_k=8, provenance={'index': {'indexed_records_sha256': INDEX}}, context_id='c'), generate.calls


def config(used, *, experiment='ab-agentic-1', cap=14, stopped=False, index=INDEX):
    return {'live': True, 'agentic_mode': True, 'context_id': 'ctx', 'index': {'indexed_records_sha256': index}, 'mode': 'indexed',
            'call_budget': {'cap': 14, 'used': used, 'remaining': 14 - used, 'stopped': stopped, 'provider': 'fake',
                            'call_timeout_seconds': 300,
                            'cumulative': {'authorized': 40, 'used': 20 + used, 'remaining': 20 - used,
                                           'experiment': {'name': experiment, 'cap': cap, 'used': used, 'remaining': cap - used}}}}


def records_for(run_dir):
    run_dir = ab_eval.new_directory(run_dir)
    used = 0
    for sequence, (qid, mode) in enumerate(SPEC['sequence'], 1):
        envelope, calls = baseline_envelope(qid) if mode == 'baseline' else agentic_envelope(qid)
        ab_eval.write_new(ab_eval.record_path(run_dir, sequence, qid, mode), ab_eval.make_record(
            run_id='test-run', sequence=sequence, question_id=qid, question=SPEC['questions'][qid]['text'], mode=mode,
            endpoint=ab_run.ENDPOINT[mode], request={}, response=envelope, http_status=200, started_at='t0', finished_at='t1',
            latency_seconds=1.0, budget_before=config(used), budget_after=config(used + calls), backend_config={'provider': 'fake'},
            source='fake'))
        used += calls
    return run_dir


class Spec(unittest.TestCase):
    @unittest.skipUnless(PARENTS.is_file(), 'pinned demo-100 bundle not present')
    def test_required_point_anchors_are_literal_text_of_their_source_chunks(self):
        import hashlib
        self.assertEqual(hashlib.sha256(PARENTS.read_bytes()).hexdigest(), INDEX)
        texts = {}
        with PARENTS.open(encoding='utf-8') as handle:
            for line in handle:
                row = json.loads(line)
                texts[row['chunk_id']] = row['text']
        for qid, question in SPEC['questions'].items():
            for point in question['required_points'] + question.get('optional_points', []):
                joined = ' '.join(texts[cid] for cid in point['source_chunks'])  # KeyError = unknown chunk
                for anchor in point['anchors']:
                    with self.subTest(point=point['id'], anchor=anchor):
                        self.assertIn(anchor, texts[point['source_chunks'][0]] if anchor in texts[point['source_chunks'][0]] else joined)

    def test_budget_plan_fits_the_cap(self):
        total = sum(SPEC['max_calls'][mode] for _q, mode in SPEC['sequence'])
        self.assertEqual(total, SPEC['max_calls']['total'])
        self.assertLessEqual(total, 14)


class Harness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__('shutil').rmtree, self.tmp, True)

    def test_report_separates_automatic_metrics_from_pending_human_review(self):
        run_dir = records_for(self.tmp / 'run')
        report, (review, key) = ab_eval.build_report(ab_eval.load_records(run_dir), SPEC, blind=True, run_dir=run_dir)
        self.assertEqual(report['records'], 4)
        self.assertEqual(report['human_review_status'], 'pending')
        q2 = {a['mode']: a for a in report['analyses'] if a['question_id'] == 'Q2'}
        for mode in ('baseline', 'agentic'):
            auto = q2[mode]['automatic']
            self.assertEqual((auto['status'], auto['index_matches_pinned_corpus'], auto['citation_ids_valid'], auto['quotes_in_passages']),
                             ('answered', True, True, True))
            # Chunk-level: the two abstracts are sources of all four Q2 points (coverage of a chunk, not of a statement).
            self.assertEqual(auto['required_points_evidence_covered'], 4)
            self.assertIn('349', next(p for p in auto['required_points'] if p['id'] == 'Q2-P1')['anchors_missing'])
            self.assertTrue(all(p['human_correct'] == 'pending' for p in auto['required_points']))
            self.assertEqual(q2[mode]['human'], {'false_abstention': 'pending', 'overall_correct': 'pending'})
        self.assertIsNotNone(q2['agentic']['orchestration_trace'])
        self.assertIsNone(q2['agentic']['baseline_stage_trace'])
        self.assertIsNotNone(q2['baseline']['baseline_stage_trace'])
        self.assertIsNone(q2['baseline']['orchestration_trace'])
        self.assertEqual(q2['baseline']['automatic']['model_calls_actual'], 2)
        self.assertEqual(q2['agentic']['automatic']['model_calls_actual'], q2['agentic']['automatic']['model_calls_reported_by_agentic'])
        # blind sheet: labels hide the mode; the key maps them back
        self.assertEqual(sorted(key), ['Q2-A', 'Q2-B', 'Q3-A', 'Q3-B'])
        self.assertEqual(sorted(key.values()), ['agentic', 'agentic', 'baseline', 'baseline'])
        self.assertTrue(all('mode' not in answer for answer in review['answers']))

    def test_outputs_are_written_once_and_never_overwritten(self):
        run_dir = records_for(self.tmp / 'run')
        report, (review, key) = ab_eval.build_report(ab_eval.load_records(run_dir), SPEC, run_dir=run_dir)
        out = ab_eval.write_report(self.tmp / 'report', report, review, key)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ['blinding-key.json', 'report.json', 'report.md', 'review-sheet.csv', 'review-sheet.json'])
        self.assertIn('Human review status: pending', (out / 'report.md').read_text(encoding='utf-8'))
        with self.assertRaises(ab_eval.HarnessError):
            ab_eval.write_report(self.tmp / 'report', report, review, key)
        with self.assertRaises(ab_eval.HarnessError):
            ab_eval.write_new(ab_eval.record_path(run_dir, 1, 'Q2', 'baseline'), {})

    def test_merge_review_marks_partial_until_every_field_is_filled(self):
        run_dir = records_for(self.tmp / 'run')
        report, (review, key) = ab_eval.build_report(ab_eval.load_records(run_dir), SPEC, run_dir=run_dir)
        out = ab_eval.write_report(self.tmp / 'report', report, review, key)
        filled = json.loads((out / 'review-sheet.json').read_text(encoding='utf-8'))
        filled['answers'][0]['overall_correct'] = True
        for claim in filled['answers'][0]['claims']:
            claim.update(semantically_correct=True, citation_entails=True, misleading_comparison=False)
        (self.tmp / 'filled.json').write_text(json.dumps(filled), encoding='utf-8')
        merged = ab_eval.merge_review(out, self.tmp / 'filled.json', self.tmp / 'merged')
        result = json.loads((merged / 'report.json').read_text(encoding='utf-8'))
        self.assertEqual(result['human_review_status'], 'partial')
        first = result['human_summary'][f"{filled['answers'][0]['question_id']}-{key[filled['answers'][0]['answer_label']]}"]
        self.assertEqual(first['claims_correct'], first['claims_total'])

    def test_citation_failures_and_wrong_index_are_detected(self):
        envelope, _ = agentic_envelope('Q3')
        envelope['result']['summary']['claims'][0]['chunk_ids'] = ['not-in-evidence']
        envelope['result']['provenance']['agentic']['index_sha256'] = 'e' * 64
        envelope['result']['provenance']['index'] = {'indexed_records_sha256': 'e' * 64}
        record = ab_eval.make_record(run_id='r', sequence=1, question_id='Q3', question='q', mode='agentic', endpoint='x', request={},
                                     response=envelope, http_status=200, started_at=None, finished_at=None, latency_seconds=1,
                                     budget_before=None, budget_after=None, backend_config=None, source='fake')
        problems = ab_run.answer_problems(record, SPEC)
        self.assertTrue(any('different index' in p for p in problems))
        self.assertTrue(any('not in its evidence' in p for p in problems))

    def test_replay_from_saved_envelopes(self):
        saved = self.tmp / 'saved'
        saved.mkdir()
        for qid, mode in SPEC['sequence']:
            envelope, _ = baseline_envelope(qid) if mode == 'baseline' else agentic_envelope(qid)
            (saved / f'{qid}-{mode}.json').write_text(json.dumps({'response': envelope, 'http_status': 200}), encoding='utf-8')
        run_dir = ab_eval.replay(SPEC, saved, self.tmp / 'replayed')
        records = ab_eval.load_records(run_dir)
        self.assertEqual([r['source'] for r in records], ['replay'] * 4)
        self.assertIsNone(records[0]['model_calls_actual'])  # no ledger snapshots in a replay: unknown, not invented


# ---------------------------------------------------------------- runner against an in-process fake backend
class FakeBackend(BaseHTTPRequestHandler):
    """Scriptable stand-in for the live backend's /api/config and research routes."""
    script, state, posts = {}, {}, []

    def log_message(self, *args):
        pass

    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.reply(200, config(FakeBackend.state['used'], **FakeBackend.script.get('config', {})))

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        FakeBackend.posts.append((self.path, body))
        step = len(FakeBackend.posts)
        action = FakeBackend.script.get('steps', {}).get(step, 'ok')
        qid = 'Q2' if 'Agent-SafetyBench' in body['query'] else 'Q3'
        if action == 'provider_error':
            FakeBackend.state['used'] += 1
            return self.reply(200, {'mode': 'indexed', 'result': None, 'error': {'kind': 'provider', 'cause': 'timeout', 'message': 'x'}})
        envelope, calls = baseline_envelope(qid) if self.path == '/api/research' else agentic_envelope(qid)
        FakeBackend.state['used'] += calls + (3 if action == 'overspend' else 0)
        if action == 'bad_citation':
            envelope['result']['summary']['claims'][0]['chunk_ids'] = ['invented-id']
        self.reply(200, envelope)


class Runner(unittest.TestCase):
    def start(self, script):
        FakeBackend.script, FakeBackend.state, FakeBackend.posts = script, {'used': 0}, []
        server = ThreadingHTTPServer(('127.0.0.1', 0), FakeBackend)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__('shutil').rmtree, tmp, True)
        return f'http://127.0.0.1:{server.server_port}', tmp

    def test_refuses_without_the_exact_approval_and_sends_nothing(self):
        backend, tmp = self.start({})
        for approval in ('', 'yes', 'ab-agentic-1'):
            with self.assertRaisesRegex(ab_run.Stop, 'approve'):
                ab_run.run(backend, SPEC, tmp / f'run-{len(approval)}', approval=approval)
        self.assertEqual(FakeBackend.posts, [])

    def test_complete_run_saves_four_records_in_order_with_actual_calls(self):
        backend, tmp = self.start({})
        run_dir = ab_run.run(backend, SPEC, tmp / 'run', approval=ab_run.APPROVAL)
        records = ab_eval.load_records(run_dir)
        self.assertEqual([(r['question_id'], r['mode']) for r in records], [tuple(s) for s in SPEC['sequence']])
        self.assertEqual([p for p, _ in FakeBackend.posts], ['/api/research', '/api/agentic-research'] * 2)
        self.assertTrue(all(body.get('interpret_context') is False for path, body in FakeBackend.posts if path == '/api/research'))
        self.assertTrue(all('industry' not in body and 'risk_assessment' not in body for _p, body in FakeBackend.posts))
        self.assertEqual(sum(r['model_calls_actual'] for r in records), FakeBackend.state['used'])
        self.assertTrue((run_dir / 'COMPLETED.json').exists())
        with self.assertRaises(ab_eval.HarnessError):
            ab_run.run(backend, SPEC, run_dir, approval=ab_run.APPROVAL)  # never reuses a run directory

    def test_stop_conditions_save_the_failing_response_and_send_nothing_more(self):
        cases = {'provider_error': (2, 'Execution error'), 'overspend': (1, 'Budget discrepancy'),
                 'bad_citation': (3, 'not in its evidence')}
        for action, (step, reason) in cases.items():
            with self.subTest(action):
                backend, tmp = self.start({'steps': {step: action}})
                with self.assertRaisesRegex(ab_run.Stop, reason):
                    ab_run.run(backend, SPEC, tmp / 'run', approval=ab_run.APPROVAL)
                self.assertEqual(len(FakeBackend.posts), step)  # no request after the failing one, no retry
                self.assertEqual(len(ab_eval.load_records(tmp / 'run')), step)  # the failing response is saved
                self.assertIn(reason.split()[0], (tmp / 'run' / 'STOPPED.json').read_text(encoding='utf-8'))

    def test_preflight_refuses_a_wrong_experiment_used_allocation_or_index(self):
        for script, reason in (({'config': {'experiment': 'other'}}, 'not running experiment'),
                               ({'config': {'index': 'e' * 64}}, 'not the pinned corpus'),
                               ({'config': {'stopped': True}}, 'stopped')):
            with self.subTest(reason):
                backend, tmp = self.start(script)
                with self.assertRaisesRegex(ab_run.Stop, reason):
                    ab_run.run(backend, SPEC, tmp / 'run', approval=ab_run.APPROVAL)
                self.assertEqual(FakeBackend.posts, [])
        backend, tmp = self.start({})
        FakeBackend.state['used'] = 3
        self.assertIn('already used', ' '.join(ab_run.preflight(backend, SPEC)['problems']))


if __name__ == '__main__':
    unittest.main(verbosity=1)
