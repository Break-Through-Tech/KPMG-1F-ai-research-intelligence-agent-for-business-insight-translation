"""Paired captures must preserve adverse evidence, never replace failed cases."""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

from evaluation.compare_intent_retrieval import capture_pairs
from evaluation.run_benchmarks import artifact_id


class IntentComparisonTests(unittest.TestCase):
    def test_rejection_keeps_baseline_candidates_receipts_and_later_cases(self):
        cases = [{'query_id': str(i), 'query': str(i)} for i in range(3)]
        receipts, traces = [], []
        passage = {'chunk_id': 'source', 'text': 'An actual source passage.'}
        def intent(q, k):
            traces.append({'query': q, 'candidates': [passage]})
            receipts.append({'status': 'failed' if q == '1' else 'ok'})
            if q == '1':
                raise ValueError('Private provider detail that must not escape')
            return [passage]
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            output = Path(folder) / 'capture'
            result = capture_pairs(cases, baseline=lambda q, k: [passage], intent=intent,
                                   provenance={}, output=output, receipts=receipts, traces=traces)
            self.assertEqual([r['intent']['status'] for r in result['cases']], ['ok', 'error', 'ok'])
            self.assertIsNone(result['cases'][1]['intent']['selected'])
            self.assertEqual(result['cases'][1]['baseline']['selected'], [passage])
            self.assertEqual(result['cases'][1]['intent']['receipt_range'], [1, 2])
            self.assertEqual(result['cases'][1]['intent']['trace_range'], [1, 2])
            self.assertEqual(json.loads((output / 'traces.json').read_text())[1]['candidates'], [passage])
            self.assertEqual(len(json.loads((output / 'receipts.json').read_text())), 3)
            self.assertNotIn('Private provider', (output / 'run.json').read_text())
            self.assertEqual(result['run_id'], artifact_id(result))
            self.assertEqual(result['semantic_acceptance'], 'unreviewed')
            with self.assertRaises(FileExistsError):
                capture_pairs(cases, baseline=lambda q, k: self.fail('must not rerun'), intent=intent,
                              provenance={}, output=output, receipts=[], traces=[])

    def test_bad_case_set_rejects_before_provider_or_artifact(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'capture'
            for cases in ([], [{'query_id': 'x', 'query': ''}],
                          [{'query_id': 'x', 'query': 'a'}, {'query_id': 'x', 'query': 'b'}]):
                with self.assertRaises(ValueError):
                    capture_pairs(cases, baseline=lambda q, k: self.fail('must not run'),
                                  intent=None, provenance={}, output=output, receipts=[], traces=[])
                self.assertFalse(output.exists())

    def test_empty_and_duplicate_results_are_errors_not_successes(self):
        p = {'chunk_id': 'x', 'text': 'Source text.'}
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            result = capture_pairs([{'query_id': 'x', 'query': 'question'}],
                                   baseline=lambda q, k: [], intent=lambda q, k: [p, p],
                                   provenance={}, output=Path(folder) / 'capture', receipts=[], traces=[])
            self.assertEqual(result['cases'][0]['baseline']['status'], 'error')
            self.assertEqual(result['cases'][0]['intent']['status'], 'error')
