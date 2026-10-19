"""Offline opt-in retrieval/context boundary tests."""
from copy import deepcopy
import unittest
from src.peer_retrieval import NeighborContext, fuse, cap_papers, fuse_papers

def passage(i, paper='2601.00001v1',section='results',page=1):
    return dict(chunk_id=i,arxiv_id=paper,section=section,subsection='',source='pdf',
                text='word '*5,pdf_url='https://arxiv.org/pdf/'+paper,
                source_url=f'https://arxiv.org/pdf/{paper}#page={page}',page_number=page)


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.rows = [passage('z',page=1),passage('a',page=2),passage('q',page=3),
                     passage('x',section='limitations'),passage('b',paper='2601.00002v1')]
        self.context = NeighborContext(self.rows,count_tokens=lambda s:len(s.split()))

    def test_expansion_preserves_neighbor_page_and_has_no_fake_score(self):
        original = deepcopy(self.rows)
        anchor = {**self.rows[1],'distance':0.2,'retrieval':{'score':1}}
        selected, stats = self.context.expand([anchor],token_budget=20)
        self.assertEqual({r['chunk_id'] for r in selected},{'z','a','q'})
        neighbors = [r for r in selected if r['context']['role']=='neighbor']
        self.assertEqual({r['page_number'] for r in neighbors},{1,3})
        self.assertTrue(all('distance' not in r and 'retrieval' not in r for r in neighbors))
        self.assertEqual(stats['text_tokens'],15)
        self.assertEqual(self.rows,original)

    def test_budget_dedup_and_foreign_anchor(self):
        selected, stats = self.context.expand(self.rows[:2],token_budget=10)
        self.assertEqual(len(selected),2)
        self.assertEqual(stats['skipped_for_budget'],['q'])
        with self.assertRaises(ValueError):
            self.context.expand(self.rows[:2],token_budget=9)
        with self.assertRaises(ValueError):
            self.context.expand([{**self.rows[0],'source_url':'wrong'}])

    def test_fusion_rejects_conflicting_citations(self):
        with self.assertRaises(ValueError):
            fuse({'a':[self.rows[0]],'b':[{**self.rows[0],'source_url':'wrong'}]},method='test')
        self.assertEqual(len(cap_papers(self.rows,per_paper=2)),3)

    def test_metadata_only_paper_gets_its_own_evidence(self):
        extra = self.rows[-1]
        result = fuse_papers([extra['arxiv_id']],self.rows[:1],lambda p:next(r for r in self.rows if r['arxiv_id']==p))
        self.assertIn(extra['chunk_id'],[r['chunk_id'] for r in result])

    def test_repeated_section_label_does_not_jump_across_boundary(self):
        rows = [passage('a'), passage('b',section='methods'), passage('c')]
        ctx = NeighborContext(rows,count_tokens=lambda s:len(s.split()))
        selected,_ = ctx.expand([rows[0]],window=2)
        self.assertEqual([r['chunk_id'] for r in selected],['a'])


if __name__ == '__main__':
    unittest.main()
