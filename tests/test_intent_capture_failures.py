"""A model-ranking rejection must survive the shipped capture boundary."""
import io
import json
from pathlib import Path
import tempfile
from contextlib import redirect_stdout
from unittest.mock import Mock, patch
import unittest

from evaluation import run_answer_improvements as runner
from evaluation.run_benchmarks import artifact_id
from src.research_pipeline import PipelineError


class CaptureRankingFailures(unittest.TestCase):
    def test_middle_failure_is_checkpointed_with_receipts_and_later_cases_continue(self):
        cases=[{'query_id':f'q{i:02}','query':f'question {i}','type':'factual',
                'coverage':'not_checked'} for i in range(1,4)]
        rows=[{'case':c,'status':'ok','result':{'evidence':[]}} for c in cases]
        baseline={'cases':rows,'provenance':{'input_hashes':{'data/processed/chunks.parquet':'fixture'},
                   'indexed_corpus_sha256':'index'}}
        baseline['run_id']=artifact_id(baseline)
        receipts=[]
        def factory(**kwargs):
            nonlocal receipts
            receipts=kwargs['receipts']
            return Mock(),{'provider':'fixture'}
        passage={'chunk_id':'fixture','text':'A sourced finding.',
                 'arxiv_id':'fixture','title':'Synthetic fixture','pdf_url':'https://example.com/p.pdf',
                 'source':'html','html_url':'https://example.com/p#results',
                 'source_url':'https://example.com/p#results','page_number':None}
        def hybrid(q,k):
            receipts.append({'query':q,'status':'fixture_received'})
            if q=='question 2':raise PipelineError('Fixture ranking validation failure')
            return [passage]
        summary=lambda q,p,**kw:{'status':'ok','query':q,'claims':[{'text':'A sourced finding.',
                                     'chunk_ids':['fixture']}],'limitations':[]}
        business=lambda s,p,*,industry,**kw:{'status':'ok','industry':industry,
             'implications':[{'text':'Conditional check.','chunk_ids':['fixture'],
                               'suggested_action':'Compare fixtures.','assumptions':[]}],
             'risks':[],'limitations':[]}
        import pandas as pd
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)/'base.json';base.write_text(json.dumps(baseline));out=Path(folder)/'new'
            argv=['capture','--baseline',str(base),'--retrieval-baseline',str(base),
                  '--output',str(out),'--codex-bin','fixture','--model','fixture',
                  '--variant','evidence-led','--intent-rerank']
            provenance={'input_hashes':{'data/processed/chunks.parquet':'fixture'}}
            with patch('sys.argv',argv),patch.object(runner,'source_provenance',return_value=provenance), \
                 patch.object(runner,'create_codex_generate',side_effect=factory), \
                 patch('pandas.read_parquet',return_value=pd.DataFrame([passage])), \
                 patch('chromadb.PersistentClient'),patch('sentence_transformers.SentenceTransformer'), \
                 patch('evaluation.capture_validated_retrieval.reconcile',return_value='index'), \
                 patch('src.hybrid_retrieval.HybridRetriever',return_value=hybrid), \
                 patch('src.intent_reranking.create_intent_rerank',return_value=(Mock(),{'method':'fixture'})), \
                 patch('src.evidence_led.summarize',side_effect=summary), \
                 patch('src.evidence_led.translate',side_effect=business),redirect_stdout(io.StringIO()):
                code=runner.main()
            result=json.loads((out/'run.json').read_text())
            self.assertEqual(code,1)
            self.assertEqual([c['status'] for c in result['cases']],['ok','error','ok'])
            self.assertIsNone(result['cases'][1]['result'])
            self.assertEqual(result['cases'][1]['error']['type'],'PipelineError')
            self.assertEqual(result['run_id'],artifact_id(result))
            self.assertEqual(len(json.loads((out/'receipts.json').read_text())),3)
            captured=json.loads((out/'retrieval.json').read_text())
            self.assertEqual(set(captured),{'question 1','question 3'})
            self.assertNotIn('question 2',captured)
