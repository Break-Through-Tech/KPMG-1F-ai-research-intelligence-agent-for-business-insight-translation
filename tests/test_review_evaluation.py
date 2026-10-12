import copy
import unittest
from evaluation.run_benchmarks import capture
from evaluation.reviews.score_reviews import aggregate
from main import demo_retrieve,demo_summary,demo_translate
from src.research_pipeline import run_research


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.run=capture([{'query_id':'q01','query':'agents','type':'factual'}],
            research_fn=lambda r:run_research(r,retrieve=demo_retrieve,summarize_fn=demo_summary,translate_fn=demo_translate),
            context={'industry':'banking'},provenance={'execution':'synthetic_fixture'})

    def review(self,reviewer='unit-test-reviewer'):
        return {'run_id':self.run['run_id'],'query_id':'q01','reviewer':reviewer,'reviewer_kind':'human',
                'coverage':'partially_covered','passage_ratings':[{'chunk_id':p['chunk_id'],'rating':2}
                    for p in self.run['cases'][0]['result']['evidence']], 'claim_checks':[],
                'summary_scores':{'accuracy':4,'clarity':4,'completeness':4},
                'business_scores':{'actionability':4,'kpmg_relevance':4,'citation_quality':4},
                'abstention':'not_applicable','notes':'Synthetic test input, not an actual human score.'}

    def test_empty_reviews_never_invent_scores(self):
        report=aggregate(self.run,[])
        self.assertEqual(report['complete_queries'],0)
        self.assertIsNone(report['precision_at_5'])
        self.assertFalse(report['end_to_end_targets_met'])
        self.assertFalse(report['approved'])

    def test_fewer_hits_keep_denominator_five_and_fixtures_do_not_count(self):
        review=self.review();report=aggregate(self.run,[review])
        self.assertEqual(report['precision_at_5'],0.4)
        self.assertFalse(report['retrieval_target_met'])
        review['reviewer_kind']='fixture';report=aggregate(self.run,[review])
        self.assertEqual(report['fixture_review_count'],1)
        self.assertEqual(report['complete_queries'],0)

    def test_stale_unknown_and_invalid_ratings_fail(self):
        for key,value in [('run_id','stale'),('query_id','missing')]:
            review=self.review();review[key]=value
            with self.assertRaises(ValueError):aggregate(self.run,[review])
        for rating in [True,-1,3]:
            review=self.review();review['passage_ratings'][0]['rating']=rating
            with self.assertRaises(ValueError):aggregate(self.run,[review])
        edited=copy.deepcopy(self.run);edited['cases'][0]['result']['evidence'][0]['text']='changed'
        with self.assertRaises(ValueError):aggregate(edited,[self.review()])

    def test_missing_ratings_are_incomplete_and_duplicates_fail(self):
        review=self.review();review['passage_ratings']=[]
        self.assertEqual(aggregate(self.run,[review])['complete_queries'],0)
        with self.assertRaises(ValueError):aggregate(self.run,[self.review(),self.review()])

    def test_disagreement_preserved_until_explicit_adjudication(self):
        a=self.review('synthetic-a');b=self.review('synthetic-b');b['passage_ratings'][0]['rating']=0
        report=aggregate(self.run,[a,b]);self.assertEqual(report['unresolved_disagreements'],['q01'])
        self.assertEqual(len(report['reviews']),2)
        c=self.review('synthetic-resolver');c['adjudicates']=['synthetic-a','synthetic-b']
        report=aggregate(self.run,[a,b,c]);self.assertEqual(report['unresolved_disagreements'],[])
        self.assertEqual(len(report['reviews']),3)

    def test_available_dimensions_must_be_complete(self):
        review=self.review();review['summary_scores']={'accuracy':4}
        with self.assertRaises(ValueError):aggregate(self.run,[review])
        review=self.review();review['summary_scores']=None
        self.assertEqual(aggregate(self.run,[review])['summary_scored'],0)


if __name__=='__main__': unittest.main()
