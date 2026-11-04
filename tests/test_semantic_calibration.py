"""Contract tests for the experiment, with deterministic vectors and token costs."""
import copy
import unittest

import numpy as np

from experiments.semantic_calibration.policies import (
    Policy, choose_policy, merge_intervals, select_context, semantic_intervals, units,
)


def words(text):
    return len(text.split())


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.text = 'First result is useful. Another result is useful. Different topic needs context.'
        self.spans = units(self.text)
        self.vectors = [[1, 0], [1, 0], [0, 1]]

    def test_low_threshold_and_minimum_prevent_fragmentation(self):
        strict = semantic_intervals(self.text,self.spans,self.vectors,words,Policy('strict', .9))
        loose = semantic_intervals(self.text,self.spans,self.vectors,words,Policy('loose', -.1))
        minimum = semantic_intervals(self.text,self.spans,self.vectors,words,Policy('min', .9, 20))
        self.assertEqual(len(strict),2)
        self.assertEqual(len(loose),1)
        self.assertEqual(len(minimum),1)

    def test_size_ceiling_overrides_minimum_and_all_text_survives(self):
        spans=semantic_intervals(self.text,self.spans,self.vectors,words,Policy('small',-1,99,9))
        self.assertGreater(len(spans),1)
        for a,b in spans:
            self.assertLessEqual(words(self.text[a:b]),9)
        for a,b in self.spans:
            self.assertTrue(any(x<=a and b<=y for x,y in spans))

    def test_overlap_advances_without_losing_tail(self):
        text='One short sentence. Two short sentences. Three short sentences. Four short sentences.'
        spans=units(text)
        result=semantic_intervals(text,spans,[[1,0]]*len(spans),words,Policy('overlap',-1,0,7,3))
        self.assertTrue(any(a2<b1 for (a1,b1),(a2,b2) in zip(result,result[1:])))
        self.assertEqual(result[-1][1],len(text))
        self.assertEqual(sorted(set(result)),result)

    def test_math_and_tex_literals_are_atomic(self):
        text=r'Before. \[x = 1.2 + y.\] After. \verb|x. y.| End.'
        spans=units(text,tex=True)
        for protected in (r'\[x = 1.2 + y.\]',r'\verb|x. y.|'):
            self.assertTrue(any(text[a:b]==protected for a,b in spans))
        result=semantic_intervals(text,spans,[[1,0]]*len(spans),words,Policy('tiny',-1,0,2))
        for protected in (r'\[x = 1.2 + y.\]',r'\verb|x. y.|'):
            self.assertTrue(any(protected in text[a:b] for a,b in result))

    def test_bad_math_fails_closed(self):
        with self.assertRaises(ValueError):
            units(r'Incomplete \[ math',tex=True)

    def test_bad_vectors_rejected(self):
        for vector in ([[0,0]]*3, [[float('nan'),1]]*3, [[1,0]]):
            with self.assertRaises(ValueError):
                semantic_intervals(self.text,self.spans,vector,words,Policy('invalid'))

    def test_merge_does_not_bridge_gaps(self):
        self.assertEqual(merge_intervals([(4,8),(0,3),(2,4),(10,12)]),[(0,8),(10,12)])

    def test_context_budget_deduplication_and_source_boundaries(self):
        blocks={0:{'text':'aa bb cc dd'},1:{'text':'ee ff gg hh'}}
        chunks=[{'block':0,'start':0,'end':5},{'block':0,'start':6,'end':11},
                {'block':1,'start':0,'end':5}]
        original=copy.deepcopy(chunks)
        result=select_context(chunks,np.array([3,2,1]),blocks,words,budget=4,neighbors=1)
        self.assertEqual(result['tokens'],4)
        self.assertEqual(len(result['evidence']),1) # join only original whitespace between adjacent chunks
        self.assertEqual({e['block'] for e in result['evidence']},{0})
        self.assertEqual(chunks,original)

    def test_oversize_window_skipped_not_truncated(self):
        blocks={0:{'text':'a b c'},1:{'text':'d'}}
        chunks=[dict(block=0,start=0,end=5),dict(block=1,start=0,end=1)]
        result=select_context(chunks,np.array([2,1]),blocks,words,budget=1)
        self.assertEqual(result['evidence'][0]['block'],1)
        self.assertEqual(result['skipped_over_budget'],1)

    def test_source_neighbors_never_cross_pages(self):
        blocks={0:{'text':'page one'},1:{'text':'page two'}}
        chunks=[dict(block=k,start=0,end=8) for k in blocks]
        result=select_context(chunks,np.array([2,1]),blocks,words,top_k=1,neighbors=1)
        self.assertEqual(len(result['evidence']),1)
        self.assertEqual(result['evidence'][0]['block'],0)

    def test_selection_ignores_validation_scores(self):
        def arm(tune,val):
            return {'summaries':{mode:{'tuning':dict(complete=tune,mean_tokens=100),
                                      'validation':dict(complete=val,mean_tokens=100)}
                                 for mode in ('tokens1600','tokens1600_neighbors')}}
        variants={'first':arm(3,0),'second':arm(2,100)}
        before=choose_policy(variants)
        variants['second']['summaries']['tokens1600']['validation']['complete']=999
        self.assertEqual(choose_policy(variants),before)
        self.assertEqual(before[0],'first')

    def test_percentile_handles_single_unit_and_cancelled_centroid(self):
        result=semantic_intervals(self.text,self.spans,[[1,0],[-1,0],[0,1]],words,Policy('local',percentile=20))
        self.assertEqual(result[-1][1],len(self.text))
        one=semantic_intervals('One.',[(0,4)],[[1,0]],words,Policy('one',percentile=20))
        self.assertEqual(one,[(0,4)])


if __name__=='__main__':
    unittest.main()
