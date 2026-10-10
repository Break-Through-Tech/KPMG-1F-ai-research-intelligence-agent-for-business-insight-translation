import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
from src import retrieval


def chunks():
    return pd.DataFrame([
        dict(chunk_id="html_1", arxiv_id="paper-a", title="HTML paper", text="Agent evidence",
             source="html", page_number=None, pdf_url="https://arxiv.org/pdf/a",
             html_url="https://arxiv.org/html/a#S1", section="results", subsection="impact",
             high_value=True, authors=["Alice", "Bob"], categories=["cs.AI"]),
        dict(chunk_id="pdf_2", arxiv_id="paper-b", title="PDF paper", text="Other evidence",
             source="pdf", page_number=3, pdf_url="https://arxiv.org/pdf/b",
             html_url=None, section="methods", subsection=None, high_value=False,
             authors="Carol", categories="cs.AI")])


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        # Every Azure constructor and embedding model is mocked: never use credentials/network.
        self.azure = patch.object(retrieval, "SearchClient").start()
        self.index = patch.object(retrieval, "SearchIndexClient").start()
        self.model_class = patch.object(retrieval, "SentenceTransformer").start()
        self.addCleanup(patch.stopall)
        self.client = self.azure.return_value
        self.client.upload_documents.side_effect = lambda documents: [
            SimpleNamespace(succeeded=True) for _ in documents]
        self.model = self.model_class.return_value
        self.model.encode.return_value = np.ones(384)
        self.config = patch.multiple(retrieval, AZURE_SEARCH_ENDPOINT="https://test.search.windows.net",
                                     AZURE_SEARCH_QUERY_KEY="fake-query", AZURE_SEARCH_ADMIN_KEY=None)
        self.config.start()

    def round_trip(self):
        with patch.object(retrieval, "get_search_client", return_value=self.client):
            retrieval.store_embeddings(chunks(), np.ones((2,384)))
        docs = self.client.upload_documents.call_args.kwargs["documents"]
        self.client.search.return_value = [dict(d, **{"@search.score": 0.8}) for d in docs]
        return retrieval.search("agent", 2)

    def test_html_pdf_metadata_round_trip(self):
        html, pdf = self.round_trip()
        self.assertEqual(html["source"], "html")
        self.assertIsNone(html["page_number"])
        self.assertEqual(html["source_url"], "https://arxiv.org/html/a#S1")
        self.assertEqual((html["section"], html["subsection"], html["high_value"]),
                         ("results", "impact", True))
        self.assertEqual(html["authors"], "Alice, Bob")
        self.assertEqual(pdf["source_url"], "https://arxiv.org/pdf/b#page=3")
        self.assertEqual(pdf["page_number"], 3)
        self.assertEqual(html["chunk_id"], retrieval.make_azure_key("html_1"))

    def test_query_key_does_not_require_admin(self):
        retrieval.get_query_search_client()
        self.assertEqual(self.azure.call_args.kwargs["credential"].key, "fake-query")
        self.index.assert_not_called()

    def test_query_and_hybrid_request(self):
        self.client.search.return_value=[]
        for hybrid in (False, True):
            self.assertEqual(retrieval.search_chunks(" agent ", 3, hybrid), [])
            request=self.client.search.call_args.kwargs
            self.assertEqual(request["search_text"], "agent" if hybrid else None)
            self.assertEqual(request["top"],3)
            self.assertEqual(request["vector_queries"][0].fields,"embedding")
            self.assertIn("chunk_id",request["select"])
        self.model_class.assert_called_with("all-MiniLM-L6-v2")
        self.client.upload_documents.assert_not_called()

    def test_invalid_queries_never_call_azure(self):
        for query,k in [("",5),(None,5),("q",0),("q",True)]:
            with self.assertRaises(ValueError): retrieval.search(query,k)
        self.azure.assert_not_called()

    def test_invalid_metadata_rejected_before_upload(self):
        for field,value in [("source","unknown"),("html_url",None),("html_url","bad"),
                            ("high_value","false")]:
            df=chunks(); df[field]=df[field].astype(object); df.at[0,field]=value
            with self.assertRaises(ValueError): retrieval.store_embeddings(df,np.ones((2,384)))
        for page in [None,0,-1,1.5,True,float("inf")]:
            row=chunks().iloc[1].to_dict(); row["page_number"]=page
            with self.assertRaises(ValueError): retrieval.citation_metadata(row)
        self.azure.assert_not_called()

    def test_bad_ids_text_or_vectors_rejected(self):
        for field,value in [("chunk_id",""),("text",None),("arxiv_id","")]:
            df=chunks(); df.at[0,field]=value
            with self.assertRaises(ValueError): retrieval.store_embeddings(df,np.ones((2,384)))
        df=chunks(); df.loc[1,"chunk_id"]=df.loc[0,"chunk_id"]
        with self.assertRaises(ValueError): retrieval.store_embeddings(df,np.ones((2,384)))
        for vectors in [np.ones((2,3)),np.ones((1,384)),np.full((2,384),np.nan)]:
            with self.assertRaises(ValueError): retrieval.store_embeddings(chunks(),vectors)
        self.azure.assert_not_called()

    def test_upload_failure_is_reported(self):
        self.client.upload_documents.side_effect=None
        self.client.upload_documents.return_value=[SimpleNamespace(succeeded=False,error_message="failure")]
        with patch.object(retrieval,"get_search_client",return_value=self.client):
            with self.assertRaises(RuntimeError): retrieval.store_embeddings(chunks(),np.ones((2,384)))

    def test_batch_upload_does_not_reset_index(self):
        with patch.object(retrieval,"BATCH_SIZE",1), patch.object(retrieval,"get_search_client",return_value=self.client):
            retrieval.store_embeddings(chunks(),np.ones((2,384)))
        self.assertEqual(self.client.upload_documents.call_count,2)
        self.index.assert_not_called()

    def test_bad_search_result_raises(self):
        self.client.search.return_value=[dict(chunks().iloc[0],html_url="",**{"@search.score":1})]
        with self.assertRaises(ValueError): retrieval.search("agent")

    def test_rebuild_requires_explicit_opt_in(self):
        with self.assertRaises(ValueError): retrieval.create_index()
        self.index.assert_not_called()
        with patch.object(retrieval,"AZURE_SEARCH_ADMIN_KEY","fake-admin"):
            self.index.return_value.list_index_names.return_value=[retrieval.INDEX_NAME]
            retrieval.create_index(rebuild=True)
        self.index.return_value.delete_index.assert_called_once_with(retrieval.INDEX_NAME)
        schema=self.index.return_value.create_index.call_args.args[0]
        self.assertEqual(next(f for f in schema.fields if f.name=="embedding").vector_search_dimensions,384)

    def test_embedding_model_and_size(self):
        self.model.encode.return_value=np.ones((2,384))
        self.assertEqual(retrieval.create_embeddings(chunks()).shape,(2,384))
        self.model_class.assert_called_with("all-MiniLM-L6-v2")

if __name__ == "__main__": unittest.main()
