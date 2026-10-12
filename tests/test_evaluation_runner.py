import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest
from evaluation.run_benchmarks import capture, artifact_id, export_review_table
from main import demo_retrieve, demo_summary
from src.research_pipeline import run_research


class CaptureTests(unittest.TestCase):
    def cases(self):
        return [{'query_id':'q01','query':'agents','coverage':'not_checked'}]

    def research(self, request):
        return run_research(request, retrieve=demo_retrieve, summarize_fn=demo_summary)

    def test_complete_json_and_blank_review_export_preserve_evidence(self):
        artifact = capture(self.cases(), research_fn=self.research,
                           provenance={'execution':'synthetic_fixture'},top_k=2)
        result=artifact['cases'][0]['result']
        self.assertEqual(result['evidence'][0]['page_number'],None)
        self.assertEqual(result['evidence'][1]['page_number'],2)
        self.assertFalse(result['approved'])
        self.assertEqual(artifact['run_id'],artifact_id(artifact))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'review.csv';export_review_table(artifact,path)
            with path.open() as file:
                rows=list(csv.DictReader(file))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0]['passage_rating'],'')
            self.assertEqual(rows[0]['source_url'],result['evidence'][0]['source_url'])

    def test_failed_query_is_not_dropped_or_leaked(self):
        def fail(request): raise RuntimeError('SECRET')
        artifact=capture(self.cases(),research_fn=fail,provenance={})
        self.assertEqual(len(artifact['cases']),1)
        self.assertEqual(artifact['cases'][0]['status'],'error')
        self.assertNotIn('SECRET',json.dumps(artifact))

    def test_no_hits_and_missing_stages_are_explicit(self):
        def empty(request):
            return run_research(request,retrieve=lambda *a:[],summarize_fn=lambda *a:self.fail())
        artifact=capture(self.cases(),research_fn=empty,provenance={})
        self.assertEqual(artifact['cases'][0]['result']['summary']['status'],'insufficient_evidence')
        self.assertNotIn('business_insight',artifact['cases'][0]['result'])

    def test_unknown_or_mutated_query_and_non_json_are_failures(self):
        for value in [{'request':{},'evidence':[]},{'request':{'query':'agents','top_k':5},'evidence':[], 'bad':float('nan')}]:
            artifact=capture(self.cases(),research_fn=lambda r:value,provenance={})
            self.assertEqual(artifact['cases'][0]['status'],'error')
        artifact=capture(self.cases(),research_fn=self.research,provenance={})
        changed=copy.deepcopy(artifact);changed['cases'][0]['request']['query']='edited'
        self.assertNotEqual(artifact_id(changed),artifact['run_id'])

    def test_original_ten_questions_and_unique_ids(self):
        cases=json.loads(Path('evaluation/benchmark_cases.json').read_text())
        self.assertEqual(len(cases),10)
        self.assertEqual(cases[-1]['query_id'],'q10')
        with self.assertRaises(ValueError):capture(cases+cases,research_fn=self.research,provenance={})
        for k in [False,0]:
            with self.assertRaises(ValueError):capture(cases,research_fn=self.research,provenance={},top_k=k)


if __name__ == '__main__': unittest.main()
