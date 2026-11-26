"""Model-free integration tests: agentic envelope, saved briefs and reviews, the HTTP route logic,
the chart tool without a table audit, and the cumulative call ledger across restarts.

Run from the repository root:  py -3.14 -I -B experiments/agentic/test_integration.py
No model is loaded and no provider is called. The real shared contracts (run_research,
validate_result, BriefStore, record_human_decision) are used.
"""
import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'experiments' / 'table-endpoint'))
import route  # noqa: E402
from agents import OrchestratorAgent, chart_status  # noqa: E402
from envelope import to_envelope  # noqa: E402
from test_agentic import (Business, Provider, Retriever, TargetedRetrieval, X, Y, claim, draft, plan,  # noqa: E402
                          verdicts)

PROVENANCE = {'execution': 'persistent_index_ui', 'index': {'indexed_records_sha256': 'f' * 64}}


class Research:
    """Stands in for IndexedResearch: context check and provenance only."""
    provenance, context_id = PROVENANCE, 'ctx-1'

    def check_context(self, context_id):
        if context_id != self.context_id:
            raise ValueError('Indexed context changed. Restart the server and reload the page; no stale context was used.')


def orchestrated(provider, retriever, question='How accurate is Model X after fine-tuning?', **kwargs):
    industry = kwargs.pop('industry', None)
    return OrchestratorAgent(generate=provider, retrieve=retriever, top_k=4, **kwargs).run(question, industry=industry)


def envelope_for(provider, retriever, **kwargs):
    return to_envelope(orchestrated(provider, retriever, **kwargs), top_k=4, provenance=PROVENANCE, context_id='ctx-1')


class Envelope(unittest.TestCase):
    def test_agentic_answer_uses_the_shared_validated_result_contract(self):
        from src.research_contracts import validate_result
        from src.research_pipeline import require_current_review
        env = envelope_for(Provider(plan=[plan()], research=[draft(X, Y)],
                                    verify=[verdicts(('supported', []), ('contradicted', ['contradiction']), coverage='partial')]),
                           Retriever({'Model X': ['A1', 'A2']}))
        result = env['result']
        validate_result(result)
        require_current_review(result)
        self.assertEqual(env['mode'], 'indexed')
        self.assertEqual([c['text'] for c in result['summary']['claims']], [X['text']])
        self.assertEqual(result['human_review'], {'status': 'pending', 'reviewer': None, 'notes': None})
        self.assertIs(result['approved'], False)
        agentic = result['provenance']['agentic']
        self.assertEqual(agentic['agents_run'], ['orchestrator', 'research_agent', 'verification_agent'])
        self.assertEqual(agentic['model_calls']['used'], 3)
        self.assertEqual(agentic['held_claims'][0]['verification']['automated']['verdict'], 'contradicted')

    def test_business_insight_passes_through_the_shared_contract(self):
        env = envelope_for(Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))],
                                    business=[Business.BUSINESS]), Retriever({'Model X': ['A1']}), industry='Healthcare')
        self.assertEqual(env['scenario'], 'full')
        self.assertEqual(env['result']['business_insight']['implications'][0]['chunk_ids'], ['A1'])
        self.assertEqual(env['result']['request']['industry'], 'Healthcare')

    def test_failed_business_keeps_the_verified_answer_as_partial(self):
        bad = {**Business.BUSINESS, 'implications': [{**Business.BUSINESS['implications'][0], 'chunk_ids': ['A2']}]}
        env = envelope_for(Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))], business=[bad]),
                           Retriever({'Model X': ['A1', 'A2']}), industry='Healthcare')
        self.assertEqual(env['scenario'], 'partial')
        self.assertEqual(env['error']['stage'], 'business')
        self.assertNotIn('business_insight', env['result'])
        self.assertEqual(env['result']['summary']['status'], 'ok')

    def test_abstention_has_no_claims_and_explains_why(self):
        env = envelope_for(Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('unsupported', ['missing_support']), coverage='none')]),
                           Retriever({'Model X': ['A1']}))
        self.assertEqual(env['scenario'], 'insufficient')
        self.assertEqual(env['result']['summary']['claims'], [])
        self.assertTrue(any('did not pass verification' in text for text in env['result']['summary']['limitations']))

    def test_no_business_when_nothing_is_verified_uses_the_standard_skip(self):
        env = envelope_for(Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('unsupported', ['missing_support']), coverage='none')]),
                           Retriever({'Model X': ['A1']}), industry='Healthcare')
        self.assertEqual(env['result']['business_insight']['status'], 'insufficient_evidence')

    def test_execution_error_returns_no_result_and_a_cause(self):
        env = envelope_for(Provider(plan=[plan()], research=[RuntimeError('request timed out')]), Retriever({'Model X': ['A1']}))
        self.assertIsNone(env['result'])
        self.assertEqual((env['error']['stage'], env['error']['cause']), ('research_agent', 'timeout'))
        self.assertEqual(env['agentic']['model_calls']['used'], 2)

    def test_verifier_cli_diagnostic_survives_error_envelope(self):
        from src.research_pipeline import PipelineError
        error = PipelineError('Private provider error text')
        details = {'category': 'invalid_json_schema', 'exit_code': 1, 'http_status': 400,
                   'provider_code': 'invalid_json_schema', 'schema_keyword': 'uniqueItems'}
        error.codex_diagnostic = details
        provider = Provider(plan=[plan()], research=[draft(X)], verify=[error])
        env = envelope_for(provider, Retriever({'Model X': ['A1']}))
        self.assertIsNone(env['result'])
        self.assertEqual(env['error']['stage'], 'verification_agent')
        self.assertEqual(env['error']['cause'], 'invalid_json_schema')
        self.assertEqual(env['error']['diagnostic'], details)
        self.assertNotIn('Private provider error text', json.dumps(env))
        self.assertEqual(provider.calls, ['plan', 'research', 'verify'])

    def test_targeted_retry_rounds_are_recorded(self):
        env = envelope_for(Provider(plan=[plan()], research=[draft(X), draft(X, Y)],
                                    verify=[verdicts(('supported', []), coverage='partial', request=TargetedRetrieval.REQUEST),
                                            verdicts(('supported', []), ('supported', []))]),
                           Retriever({'Model Y': ['A2'], 'Model X': ['A1']}))
        rounds = env['result']['provenance']['agentic']['rounds']
        self.assertEqual([r['round'] for r in rounds], [1, 2])
        self.assertEqual(len(env['result']['summary']['claims']), 2)


class SavedBriefs(unittest.TestCase):
    def setUp(self):
        from src.brief_store import BriefStore
        self.tmp = tempfile.TemporaryDirectory()
        self.store = BriefStore(Path(self.tmp.name) / 'briefs.sqlite3')
        self.env = envelope_for(Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))]),
                                Retriever({'Model X': ['A1']}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_agentic_brief_saves_reopens_and_keeps_its_trace_and_citations(self):
        saved = self.store.save(self.env, title='Agentic brief')
        loaded = self.store.load(saved['library']['brief']['id'])
        self.assertEqual(loaded['result']['provenance']['agentic']['trace'], self.env['result']['provenance']['agentic']['trace'])
        self.assertEqual(loaded['result']['summary']['claims'][0]['support'], X['support'])
        self.assertEqual(loaded['result']['evidence'][0]['chunk_id'], 'A1')

    def test_human_review_records_against_the_exact_snapshot(self):
        saved = self.store.save(self.env, title='Agentic brief')
        version = saved['library']['version']
        reviewed = self.store.review(saved['library']['brief']['id'], version_id=version['id'], fingerprint=version['fingerprint'],
                                     reviewer='QA reviewer', decision='approve', notes='Checked A1.')
        self.assertEqual(reviewed['library']['reviews'][-1]['decision'], 'approve')
        with self.assertRaises(Exception):
            self.store.review(saved['library']['brief']['id'], version_id=version['id'], fingerprint='0' * 64,
                              reviewer='QA reviewer', decision='approve')

    def test_a_tampered_trace_cannot_be_saved_as_the_reviewed_snapshot(self):
        tampered = json.loads(json.dumps(self.env))
        tampered['result']['provenance']['agentic']['model_calls']['used'] = 1
        with self.assertRaises(ValueError):
            self.store.save(tampered, title='Tampered')


class RouteLogic(unittest.TestCase):
    def usage(self, remaining=40, stopped=False):
        return lambda: {'cap': 40, 'used': 40 - remaining, 'remaining': remaining, 'stopped': stopped}

    def orchestrator(self, provider):
        return OrchestratorAgent(generate=provider, retrieve=Retriever({'Model X': ['A1']}), top_k=4)

    def handle(self, payload, provider=None, **kwargs):
        provider = provider or Provider(plan=[plan()], research=[draft(X)], verify=[verdicts(('supported', []))])
        options = {'orchestrator': self.orchestrator(provider), 'research': Research(), 'usage': self.usage(), 'top_k': 4, **kwargs}
        return route.handle(payload, **options), provider

    def test_disabled_backend_answers_404(self):
        (status, body), _ = self.handle({'query': 'q'}, orchestrator=None)
        self.assertEqual((status, body['code']), (404, 'agentic_disabled'))

    def test_success_returns_a_baseline_compatible_envelope(self):
        (status, body), provider = self.handle({'query': 'How accurate is Model X?', 'context_id': 'ctx-1'})
        self.assertEqual(status, 200)
        self.assertEqual(body['mode'], 'indexed')
        self.assertEqual(provider.calls, ['plan', 'research', 'verify'])

    def test_requests_are_validated_before_any_model_call(self):
        cases = [(None, 400), ({'query': ''}, 400), ({'query': 'x' * 2001}, 400), ({'query': 'q', 'industry': 5}, 400),
                 ({'query': 'q', 'history': [{'role': 'user'}]}, 400), ({'query': 'q', 'risk_assessment': True, 'context_id': 'ctx-1'}, 400),
                 ({'query': 'q', 'context_id': 'stale'}, 409)]
        for payload, expected in cases:
            (status, _), provider = self.handle(payload)
            self.assertEqual(status, expected, payload)
            self.assertEqual(provider.calls, [], payload)

    def test_budget_below_three_calls_is_refused_before_any_call(self):
        (status, body), provider = self.handle({'query': 'q', 'context_id': 'ctx-1'}, usage=self.usage(remaining=2))
        self.assertEqual((status, body['code']), (429, 'call_budget'))
        self.assertEqual(provider.calls, [])
        (status, body), provider = self.handle({'query': 'q', 'context_id': 'ctx-1'}, usage=self.usage(stopped=True))
        self.assertEqual(status, 429)
        self.assertIn('stopped after a provider error', body['error'])

    def test_only_one_agentic_request_runs_at_a_time(self):
        route._lock.acquire()
        try:
            (status, body), provider = self.handle({'query': 'q', 'context_id': 'ctx-1'})
        finally:
            route._lock.release()
        self.assertEqual((status, body['code']), (409, 'busy'))
        self.assertEqual(provider.calls, [])


class ChartsWithoutAudit(unittest.TestCase):
    class Tables:
        audit_problem = 'No extractor audit was loaded, so completeness cannot be established.'
        index_sha256 = 'f' * 64

    def test_missing_audit_reports_unavailable_without_attempting_a_chart(self):
        called = []
        tool = route.chart_tool_for(self.Tables(), lambda *args: called.append(args))
        charts = chart_status(tool('Show a bar chart of Model X accuracy', []))
        self.assertEqual(charts['status'], 'unavailable')
        self.assertIn('Text answers are unaffected', charts['reason'])
        self.assertEqual(called, [])

    def test_supported_text_answer_survives_unavailable_charts(self):
        tool = route.chart_tool_for(self.Tables(), lambda *args: self.fail('preview must not run'))
        provider = Provider(plan=[plan(chart=True)], research=[draft(X)], verify=[verdicts(('supported', []))])
        env = to_envelope(orchestrated(provider, Retriever({'Model X': ['A1']}), chart_tool=tool),
                          top_k=4, provenance=PROVENANCE, context_id='ctx-1')
        self.assertEqual(env['result']['summary']['status'], 'ok')
        self.assertEqual(env['agentic_charts']['status'], 'unavailable')
        self.assertEqual(env['result']['provenance']['agentic']['charts']['status'], 'unavailable')

    def test_refused_tables_are_reported_not_charted(self):
        charts = chart_status({'tables': [{'key': 'x#t', 'status': 'refused', 'reason': 'The extractor audit has no record of this table.'}]})
        self.assertEqual((charts['status'], charts['reason']), ('no_verified_table', 'The extractor audit has no record of this table.'))

    @unittest.skipUnless(Path(r'D:\KPMG-demo-corpus\main-727b0b3\data\processed\demo-bundles\demo-25\parents.jsonl').is_file(),
                         'local demo-25 bundle not present')
    def test_real_table_index_without_audit_fails_closed(self):
        from evidence_tables import TableIndex
        tables = TableIndex(Path(r'D:\KPMG-demo-corpus\main-727b0b3\data\processed\demo-bundles\demo-25\parents.jsonl'), None)
        self.assertTrue(tables.audit_problem)
        charts = chart_status(route.chart_tool_for(tables, lambda *a: self.fail('preview must not run'))('chart', []))
        self.assertEqual(charts['status'], 'unavailable')


class CumulativeLedger(unittest.TestCase):
    """capped_codex_ui with a fake provider module and the SQLite ledger: counts survive a backend restart.
    Cross-process races and crashes are covered in experiments/table-endpoint/test_call_ledger.py."""

    def setUp(self):
        self.calls, self.opened = [], []
        fake = types.ModuleType('src.codex_generation')

        def create_codex_generate(**kwargs):
            def inner(prompt, response_schema=None):
                self.calls.append(prompt)
                if prompt == 'fail':
                    from src.research_pipeline import PipelineError
                    raise PipelineError('provider down')
                return '{}'
            return inner, {'provider': 'fake'}
        fake.create_codex_generate = create_codex_generate
        self.saved_module = sys.modules.get('src.codex_generation')
        sys.modules['src.codex_generation'] = fake
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self.tmp.name) / 'ledger.sqlite3'
        self.log = Path(self.tmp.name) / 'session.jsonl'

    def tearDown(self):
        for module in self.opened:
            if module.LEDGER is not None:
                module.LEDGER.close()
        if self.saved_module is None:
            sys.modules.pop('src.codex_generation', None)
        else:
            sys.modules['src.codex_generation'] = self.saved_module
        self.tmp.cleanup()

    def seed(self, count, authorized):
        import call_ledger
        seed = Path(self.tmp.name) / 'seed.jsonl'
        seed.write_text(''.join(json.dumps({'call': i, 'at': f'2026-11-17T00:00:{i:02d}', 'outcome': 'ok'}) + chr(10)
                                for i in range(count)), encoding='utf-8')
        call_ledger.init(self.ledger, authorized=authorized, seed=seed)

    def start_backend(self, cap=40, authorized=5):
        """A fresh import is a backend restart: in-memory counters start at zero."""
        sys.modules.pop('capped_codex_ui', None)
        module = importlib.import_module('capped_codex_ui')
        module.configure(cap, self.log, ledger=self.ledger, authorized=authorized)
        self.opened.append(module)
        return module, module.create()[0]

    def test_ledger_counts_earlier_calls_and_survives_restart(self):
        self.seed(3, 5)
        module, generate = self.start_backend()
        self.assertEqual(module.usage()['remaining'], 2)
        generate('a'); generate('b')
        with self.assertRaisesRegex(RuntimeError, 'Cumulative authorized cap of 5'):
            generate('c')
        module.LEDGER.close()
        module, generate = self.start_backend()  # restart: still exhausted
        cumulative = module.usage()['cumulative']
        self.assertEqual((cumulative['authorized'], cumulative['used'], cumulative['remaining']), (5, 5, 0))
        self.assertEqual(cumulative['states']['completed'], 5)
        with self.assertRaises(RuntimeError):
            generate('d')
        self.assertEqual(self.calls, ['a', 'b'])

    def test_failed_calls_still_count(self):
        self.seed(0, 3)
        module, generate = self.start_backend(authorized=3)
        with self.assertRaises(Exception):
            generate('fail')
        cumulative = module.usage()['cumulative']
        self.assertEqual((cumulative['used'], cumulative['states']['failed']), (1, 1))

    def test_per_run_cap_is_still_enforced_under_the_ledger(self):
        self.seed(0, 40)
        module, generate = self.start_backend(cap=1, authorized=40)
        generate('a')
        with self.assertRaisesRegex(RuntimeError, 'Approved cap of 1'):
            generate('b')
        self.assertEqual(module.usage()['remaining'], 0)

    def test_missing_ledger_is_refused_rather_than_starting_at_zero(self):
        sys.modules.pop('capped_codex_ui', None)
        module = importlib.import_module('capped_codex_ui')
        with self.assertRaises(ValueError):
            module.configure(40, self.log, ledger=self.ledger, authorized=40)
        with self.assertRaises(ValueError):
            module.configure(40, self.log, ledger=self.ledger)
        self.assertFalse(self.ledger.exists())

    def test_without_a_ledger_the_original_behaviour_is_unchanged(self):
        sys.modules.pop('capped_codex_ui', None)
        module = importlib.import_module('capped_codex_ui')
        module.configure(2, self.log)
        generate = module.create()[0]
        generate('a'); generate('b')
        with self.assertRaises(RuntimeError):
            generate('c')
        self.assertNotIn('cumulative', module.usage())


if __name__ == '__main__':
    unittest.main(verbosity=1)
