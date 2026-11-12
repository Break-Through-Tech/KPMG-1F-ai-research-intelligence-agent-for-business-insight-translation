import sys,unittest,copy
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True;
import numpy as np
from src.experimental.retriever import Retriever,Lexical,tokens

class FakeReranker:
    max_seq_length=512
    def tokenizer(self,q,t,**kw):return {'input_ids':[1]*(len(q.split())+len(t.split()))}
    def predict(self,pairs,**kw):return np.array([len(set(tokens(q)).intersection(tokens(t))) for q,t in pairs],dtype=float)

def index():
    parents=[{'chunk_id':'x','arxiv_id':'doc-A','title':'Thermal sensing','section':'Measurements','text':'Thermal temperature sensing measured in laboratory.'},
             {'chunk_id':'y','arxiv_id':'doc-A','title':'Thermal sensing','section':'Measurements','text':'Sensor B temperature results','table_id':'T','row_label':'Sensor B','caption':'Temperature measurements',
              'table_headers':[{'text':'Sensor'},{'text':'Value (K)'}],'table_cells':[{'text':'Sensor B'},{'text':'12'}]},
             {'chunk_id':'z','arxiv_id':'doc-B','title':'Ocean waves','section':'Results','text':'Ocean wave heights were measured.'}]
    views=[{'parent_chunk_id':p['chunk_id'],'view_id':p['chunk_id']+'v','text':p['text']} for p in parents]
    return SimpleNamespace(parents=parents,views=views,vectors=np.array([[0,0],[1,1],[2,2]],dtype=np.float32))

class RetrievalTests(unittest.TestCase):
    def test_lexical_discovery(self):
        lex=Lexical(['thermal sensor','ocean wave'])
        self.assertGreater(lex.score('thermal')[0],lex.score('thermal')[1])
    def test_dense_and_doc_discovery_is_deterministic(self):
        r=Retriever(index());a,_=r.rank('temperature sensor',np.zeros(2),with_reranker=False)
        b,_=r.rank('temperature sensor',np.zeros(2),with_reranker=False)
        self.assertEqual(a,b);self.assertEqual(set(a['document_hybrid']),{'x','y','z'})
    def test_reranker_and_selection_preserve_source_records(self):
        idx=index();before=copy.deepcopy(idx.parents);r=Retriever(idx,FakeReranker())
        routes,debug=r.rank('temperature sensor',np.zeros(2))
        self.assertEqual(idx.parents,before)
        for order in routes.values():
            self.assertEqual(len(order),len(set(order)))
            for p in r.resolve(order):self.assertEqual(p,next(x for x in before if x['chunk_id']==p['chunk_id']))
        self.assertGreater(debug['pairs_scored'],0)
    def test_wrong_paper_identifiers_are_not_special_cased(self):
        idx=index();r=Retriever(idx);order,_=r.rank('thermal sensing',np.zeros(2),with_reranker=False)
        for p in idx.parents:p['arxiv_id']='renamed-'+p['arxiv_id']
        other,_=Retriever(idx).rank('thermal sensing',np.zeros(2),with_reranker=False)
        self.assertEqual(order,other)
    def test_oversize_pair_rejected(self):
        rr=FakeReranker();rr.max_seq_length=2
        with self.assertRaisesRegex(ValueError,'truncate'):Retriever(index(),rr).rank('thermal sensing',np.zeros(2))
    def test_nonfinite_reranking_rejected(self):
        rr=FakeReranker();rr.predict=lambda pairs,**kw:np.full(len(pairs),np.nan)
        with self.assertRaisesRegex(ValueError,'Invalid reranker'):Retriever(index(),rr).rank('thermal sensing',np.zeros(2))



import sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True;
from src.experimental.balanced_retriever import facets,FacetRetriever

import numpy as np
class FakeModel:
    def encode(self,queries,**kw):return np.zeros((len(queries),2),dtype=np.float32)
class FacetTests(unittest.TestCase):
    def test_split_multiple_parts_but_not_model_names(self):
        self.assertEqual(facets('Compare Sensor A and Sensor B.'),[])
        self.assertEqual(facets('Compare sensors, and what limitations apply?'),['what limitations apply'])
    def test_deployment_scope_is_general_not_an_industry_override(self):
        self.assertEqual(facets('Will this work in production?'),['Experimental setting and limitations on production deployment'])
    def test_records_preserved_and_repeatable(self):
        r=FacetRetriever(index(),FakeReranker(),FakeModel())
        a,d=r.rank_facets('temperature Sensor B, and what limitations apply?',np.zeros(2))
        b,_=r.rank_facets('temperature Sensor B, and what limitations apply?',np.zeros(2))
        self.assertEqual(a,b);self.assertEqual(set(a),{'x','y','z'})
        self.assertGreater(d['pairs_scored'],0)
        self.assertEqual(r.resolve(a)[0],r.byid[a[0]])
    def test_qualifier_cues_expand_candidates_without_displacing_answers(self):
        from unittest.mock import patch
        for weak_text in ['Sensor packaging may be blue.', 'Sensor accuracy was 1%.']:
            with self.subTest(text=weak_text):
                parents=[{'chunk_id':f'p{i}','arxiv_id':'doc-A','title':'Sensor measurements',
                          'text':'Direct sensor measurement answer.'} for i in range(5)]
                parents.append({**parents[0],'chunk_id':'weak','text':weak_text, 'section':'Results'})
                idx=SimpleNamespace(parents=parents,
                    views=[{'parent_chunk_id':p['chunk_id'],'text':p['text']} for p in parents],
                    vectors=np.zeros((6,2),dtype=np.float32))
                rr=FakeReranker()
                rr.predict=lambda pairs,**kw:np.array([-100 if ('packaging' in t or '1%' in t) else 100 for q,t in pairs])
                r=FacetRetriever(idx,rr,FakeModel())
                for already_discovered in (True,False):
                    hybrid=[f'p{i}' for i in range(5)]+(['weak'] if already_discovered else [])
                    with patch.object(Retriever,'rank',return_value=(
                        {'document_hybrid':hybrid}, {'paper_candidates':['doc-A']})):
                        order,debug=r.rank_facets('What fraction do sensor measurements resolve?',np.zeros(2))
                    self.assertEqual(set(order[:5]),{f'p{i}' for i in range(5)})
                    self.assertNotIn('weak',debug['balanced_prefix'])
                if weak_text:
                    self.assertIn('weak',order)
                    self.assertEqual(debug['pairs_scored'],6)

if __name__=='__main__':unittest.main()
