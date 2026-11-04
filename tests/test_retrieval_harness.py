import unittest
import numpy as np
from experiments.retrieval_harness.harness import ARMS,context,fuse,lexical_scores

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.text='Alpha evidence. Beta explanation. Gamma conclusion.'
        self.blocks={0:dict(text=self.text,paper='p',source='html',location=dict(source_url='https://example/#a'))}
        self.chunks=[dict(block=0,start=0,end=31,text=self.text[:31]),dict(block=0,start=16,end=len(self.text),text=self.text[16:])]
        self.v=np.array([[1.,0.],[.8,.6]])
    def test_all_arms_preserve_source_and_budget(self):
        for arm in ARMS:
            r=context(self.chunks,[1,.9],self.blocks,len,'Beta explanation',arm=arm,budget=55,vectors=self.v)
            self.assertLessEqual(r['tokens'],55)
            for e in r['evidence']:
                self.assertEqual(e['text'],self.text[e['start']:e['end']])
                self.assertEqual(e['location']['source_url'],'https://example/#a')
    def test_dedup_reclaims_overlap(self):
        base=context(self.chunks,[1,.9],self.blocks,len,'Alpha',arm='baseline',budget=55)
        dedup=context(self.chunks,[1,.9],self.blocks,len,'Alpha',arm='deduplication',budget=55)
        self.assertEqual(len(base['evidence']),1)
        self.assertEqual(dedup['evidence'][0]['text'],self.text)
    def test_never_merge_different_sources(self):
        self.blocks[1]={**self.blocks[0],'paper':'other'}
        chunks=[self.chunks[0],{**self.chunks[0],'block':1}]
        r=context(chunks,[1,.9],self.blocks,len,'Alpha',arm='deduplication',budget=100)
        self.assertEqual({e['paper'] for e in r['evidence']},{'p','other'})
    def test_tex_lines_recomputed(self):
        self.blocks[0].update(source='tex',text='First.\nSecond.',location=dict(line_start=10,line_end=11,source_file='main.tex'))
        c=dict(block=0,start=7,end=14,text='Second.')
        r=context([c],[1],self.blocks,len,'Second',arm='baseline',budget=20)
        self.assertEqual(r['evidence'][0]['location']['line_start'],11)
    def test_invalid_offsets_fail(self):
        with self.assertRaises(ValueError):context([{**self.chunks[0],'start':-1}],[1],self.blocks,len,'q',arm='baseline')
    def test_oversized_seed_not_truncated(self):
        r=context(self.chunks,[1,.9],self.blocks,len,'q',arm='baseline',budget=2)
        self.assertEqual(r['evidence'],[])
    def test_bm25_exact_term_and_rank_fusion(self):
        scores=lexical_scores(['unrelated topic','specific enzyme enzyme'],'enzyme')
        self.assertGreater(scores[1],scores[0])
        self.assertEqual(int(np.argmax(fuse(np.array([.1,.9]),scores))),1)

if __name__=='__main__':unittest.main()

class MechanismTests(unittest.TestCase):
    def test_selective_expansion_adds_only_relevant_neighbor(self):
        text='Seed result. Relevant detail. Unrelated tail.'
        blocks={0:dict(text=text,paper='p',source='html',location={})}
        c=dict(block=0,start=0,end=12,text=text[:12])
        r=context([c],[1],blocks,len,'Relevant',arm='selective_expansion',budget=100)
        self.assertIn('Relevant detail.',r['evidence'][0]['text'])
        self.assertNotIn('Unrelated tail.',r['evidence'][0]['text'])
    def test_mmr_changes_budgeted_choice(self):
        blocks={i:dict(text='x'*10,paper=str(i),source='pdf',location={}) for i in range(3)}
        cs=[dict(block=i,start=0,end=10,text='x'*10) for i in range(3)]
        vectors=np.array([[1.,0.],[1.,0.],[0.,1.]])
        r=context(cs,[1,.9,.8],blocks,len,'x',arm='budget_allocation',budget=20,vectors=vectors)
        self.assertEqual([e['block'] for e in r['evidence']],[0,2])
    def test_gap_pass_uses_residual_query_terms(self):
        texts=['alpha','bravo','charlie','other','missing']
        blocks={i:dict(text=t,paper=str(i),source='html',location={}) for i,t in enumerate(texts)}
        cs=[dict(block=i,start=0,end=len(t),text=t) for i,t in enumerate(texts)]
        r=context(cs,[1,.9,.8,.7,.6],blocks,len,'alpha missing',arm='evidence_gap',budget=24)
        self.assertIn(4,[e['block'] for e in r['evidence']])
    def test_source_aware_expands_atomic_math(self):
        text='Intro. $a + b = c$ End.'
        blocks={0:dict(text=text,paper='p',source='tex',location=dict(line_start=1,source_file='m.tex'))}
        c=dict(block=0,start=9,end=12,text=text[9:12])
        r=context([c],[1],blocks,len,'a',arm='source_aware',budget=100)
        self.assertIn('$a + b = c$',r['evidence'][0]['text'])
