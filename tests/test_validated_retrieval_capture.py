from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
import pandas as pd
from evaluation.capture_validated_retrieval import verify_validation, reconcile, implementation_hashes
from unittest.mock import Mock


class ValidatedCaptureTests(unittest.TestCase):
    def test_refuses_unpassed_report(self):
        for report in ({}, {'status':'FAIL','mode':'HTML-first; cached sources only'},
                       {'status':'passed','mode':'html_first'}, {'status':'PASS','mode':'synthetic'}):
            with self.assertRaises(ValueError):verify_validation(report)

    def test_binds_parquet_metadata_and_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            corpus=root/'data/processed/chunks.parquet'; corpus.parent.mkdir(parents=True)
            pd.DataFrame([{'chunk_id':'c1','arxiv_id':'paper'}]).to_parquet(corpus,index=False)
            hashes={}
            for name in ('arxiv_csAI_25_pdf_sample.csv','arxiv_csAI_100_metadata.csv'):
                path=root/'data/metadata'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
                hashes[str(path.relative_to(root))]=sha256(path.read_bytes()).hexdigest()
            hashes['data/processed/chunks.parquet'] = sha256(corpus.read_bytes()).hexdigest()
            report={'status':'PASS','mode':'HTML-first; cached sources only','failures':[],
                'papers':[{'arxiv_id':'paper','failures':[],'chunks':1,'verified_passages':1}],
                'persisted_chunks':1,'locked_papers':1,'input_hashes':hashes,
                'implementation_hashes':implementation_hashes(),
                'protected_inputs_unchanged':True,'source_files_unchanged':True,
                'cached_ingestion_rerun':'PASS: persisted == regenerated == second run',
                'transport':{'first_count':1,'rerun_count':1,'reopened_verified_records':1}}
            self.assertEqual(len(verify_validation(report,root)),1)
            windows = {**report, 'input_hashes':{k.replace('/', '\\'):v for k,v in hashes.items()}}
            self.assertEqual(len(verify_validation(windows,root)),1)
            for change in ({'persisted_chunks':2}, {'implementation_hashes':{}},
                           {'protected_inputs_unchanged':False}, {'source_files_unchanged':False},
                           {'cached_ingestion_rerun':'FAIL'}, {'transport':{}},
                           {'papers':[{'arxiv_id':'paper','failures':[],'chunks':1,'verified_passages':0}]}):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    verify_validation({**report,**change},root)
            metadata = root/'data/metadata/arxiv_csAI_25_pdf_sample.csv'
            metadata.write_text('changed')
            with self.assertRaisesRegex(ValueError,'metadata'):verify_validation(report,root)
            metadata.write_text('fixture')
            corpus.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Parquet'):verify_validation(report,root)

    def test_reconciliation_rejects_stale_and_changed_metadata(self):
        frame=pd.DataFrame([{'chunk_id':'c1','arxiv_id':'paper','text':'original','title':'title',
            'pdf_url':'https://example.com/paper.pdf','source':'pdf','page_number':2}])
        client=Mock();client.get.return_value={'ids':['stale'],'documents':['original'],'metadatas':[{}]}
        with self.assertRaisesRegex(ValueError,'ID mismatch'):reconcile(client,frame)
        client.get.return_value={'ids':['c1'],'documents':['original'],'metadatas':[{}]}
        with self.assertRaisesRegex(ValueError,'metadata'):reconcile(client,frame)
        from src.retrieval import citation_metadata
        client.get.return_value['metadatas']=[citation_metadata(frame.iloc[0])]
        self.assertEqual(len(reconcile(client,frame)),64)
        client.get.return_value['documents'] = []
        with self.assertRaisesRegex(ValueError,'incomplete stored records'):reconcile(client,frame)
