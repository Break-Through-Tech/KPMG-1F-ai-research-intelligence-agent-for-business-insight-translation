from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
import pandas as pd
from evaluation.capture_validated_retrieval import verify_validation, reconcile
from unittest.mock import Mock


class ValidatedCaptureTests(unittest.TestCase):
    def test_refuses_unpassed_report(self):
        for report in ({}, {'status':'failed','mode':'html_first'}, {'status':'passed','mode':'synthetic'}):
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
            report={'status':'passed','mode':'html_first','failures':[],
                'papers':[{'arxiv_id':'paper','status':'passed'}],'chunks':1,
                'parquet_sha256':sha256(corpus.read_bytes()).hexdigest(),'metadata_hashes':hashes}
            self.assertEqual(len(verify_validation(report,root)),1)
            with self.assertRaises(ValueError):verify_validation({**report,'chunks':2},root)
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
