import unittest
import numpy as np
from experiments.retrieval_harness.packing import protect_dense,windows,pack

class PackingTests(unittest.TestCase):
    def test_protect_keeps_dense_hits_and_hybrid_tail(self):
        scores=protect_dense([5,4,3,2,1],[1,2,3,4,5],2)
        self.assertEqual(list(np.argsort(-scores)),[4,3,0,1,2])

    def test_window_selects_query_sentence_and_preserves_offsets(self):
        text='Irrelevant background fills space. Answer concerns portability. More unrelated context.'
        blocks={0:dict(text=text,source='html')}
        cs=[dict(block=0,start=0,end=len(text),text=text)]
        w=windows(cs,blocks,'portability',len,40)[0]
        self.assertEqual(w['text'],text[w['start']:w['end']])
        self.assertIn('portability',w['text'])
        self.assertLessEqual(len(w['text']),40)

    def test_atomic_unit_not_cut_to_fit(self):
        text='A'*100
        blocks={0:dict(text=text,source='tex',paper='p',location=dict(line_start=1))}
        cs=[dict(block=0,start=0,end=100,text=text)]
        self.assertEqual(windows(cs,blocks,'x',len,10),cs)
        r=pack(cs,[1],blocks,len,'x',50,compact=True)
        self.assertEqual(r['tokens'],0)
