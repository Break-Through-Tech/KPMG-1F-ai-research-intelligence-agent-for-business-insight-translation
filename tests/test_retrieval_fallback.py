import unittest
from experiments.retrieval_harness.fallback import fill

class FallbackTests(unittest.TestCase):
    def fixtures(self):
        blocks={0:dict(text='Original evidence. New evidence. Oversized sentence.',paper='p',source='tex',location=dict(source_url='source',line_start=10))}
        e=dict(block=0,start=0,end=18,text=blocks[0]['text'][:18],paper='p',source='tex',location=dict(source_url='source',line_start=10,line_end=10))
        return blocks,dict(evidence=[e],tokens=18)

    def test_addition_retains_original_and_exact_offsets(self):
        blocks,base=self.fixtures()
        r=fill(base,[dict(block=0,start=19,end=32,score=.8,rank=1)],blocks,len,32)
        self.assertEqual(r['evidence'][0]['text'],blocks[0]['text'][:32])
        self.assertEqual(base['tokens'],18)
        self.assertEqual(r['tokens'],32)

    def test_no_room_preserves_evidence_without_clipping(self):
        blocks,base=self.fixtures()
        r=fill(base,[dict(block=0,start=19,end=32,score=.8,rank=1)],blocks,len,20)
        self.assertEqual(r['evidence'],base['evidence'])
        self.assertEqual(r['fallback_additions'],0)

    def test_rejects_invalid_offsets_and_scores(self):
        blocks,base=self.fixtures()
        for a,b,score in [(-1,5,.5),(0,999,.5),(0,5,float('nan'))]:
            with self.assertRaises(ValueError):fill(base,[dict(block=0,start=a,end=b,score=score,rank=1)],blocks,len,100)
