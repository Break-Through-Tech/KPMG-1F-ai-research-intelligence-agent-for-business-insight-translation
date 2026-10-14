import json
import unittest
from unittest.mock import Mock, patch

from src.intent_reranking import create_intent_rerank
from src.hybrid_retrieval import HybridRetriever
from src.research_pipeline import PipelineError


class IntentTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'chunk_id':'threat','text':'Tool execution may run malicious commands and expose credentials.'},
                   {'chunk_id':'coord','text':'Poor coordination can create redundant work and communication overhead.'}]

    def reply(self):
        return {'assessments':[{'chunk_id':'coord','score':0,'reason':'Not tool security.','quote':''},
            {'chunk_id':'threat','score':3,'reason':'Direct security result.',
             'quote':self.rows[0]['text']}]}

    def test_reorders_returned_ids_and_retains_audit_without_keyword_override(self):
        fn=Mock(return_value=json.dumps(self.reply()));rank,meta=create_intent_rerank(fn)
        h=HybridRetriever(self.rows,dense_search=lambda q,k:self.rows,rerank=rank)
        out=h('What are the security risks of multi-agent tool execution?',1)
        self.assertEqual(out[0]['chunk_id'],'threat')
        self.assertEqual(out[0]['retrieval']['rerank_assessment']['quote'],self.rows[0]['text'])
        self.assertEqual(meta['score_semantics'],'ordinal_relevance_not_confidence')
        self.assertNotIn('focus_retained',out[0]['retrieval'])

    def test_duplicate_missing_and_unknown_assessments_fail_without_fallback(self):
        for mutate in ['duplicate','missing','unknown']:
            reply=self.reply()
            if mutate=='duplicate':reply['assessments'][0]['chunk_id']='threat'
            if mutate=='missing':reply['assessments'].pop()
            if mutate=='unknown':reply['assessments'][0]['chunk_id']='invented'
            rank,_=create_intent_rerank(lambda p:json.dumps(reply))
            with self.subTest(mutate=mutate),self.assertRaises(PipelineError):rank('tool risks',self.rows)

    def test_quote_from_hidden_tail_or_another_candidate_is_rejected(self):
        for quote in [self.rows[1]['text'],'Secret hidden tail beyond the displayed text.']:
            rows=[{**self.rows[0],'text':self.rows[0]['text']+' '*100+quote},self.rows[1]]
            reply=self.reply();reply['assessments'][1]['quote']=quote
            rank,_=create_intent_rerank(lambda p:json.dumps(reply),max_passage_chars=100)
            with self.subTest(quote=quote),self.assertRaises(PipelineError):rank('tool risks',rows)

    def test_invalid_scores_and_irrelevant_support_fail_closed(self):
        for score in [True,4,-1,float('nan')]:
            reply=self.reply();reply['assessments'][1]['score']=score
            rank,_=create_intent_rerank(lambda p:json.dumps(reply))
            with self.subTest(score=score),self.assertRaises(PipelineError):rank('risks',self.rows)
        reply=self.reply();reply['assessments'][0]['quote']=self.rows[1]['text']
        rank,_=create_intent_rerank(lambda p:json.dumps(reply))
        with self.assertRaises(PipelineError):rank('risks',self.rows)

    def test_single_correction_rechecks_quotes_and_unique_ids_under_same_schema(self):
        for kind in ['case','duplicate']:
            invalid=self.reply()
            if kind=='case':invalid['assessments'][1]['quote']=self.rows[0]['text'].lower()
            else:invalid['assessments'][0]['chunk_id']='threat'
            fn=Mock(side_effect=[json.dumps(invalid),json.dumps(self.reply())])
            fn.supports_response_schema=True
            rank,_=create_intent_rerank(fn)
            with self.subTest(kind=kind):
                out=rank('tool security',self.rows)
                self.assertEqual(out[0]['assessment']['quote'],self.rows[0]['text'])
                self.assertEqual(out[0]['assessment']['validation_attempts'],2)
                self.assertEqual(fn.call_count,2)
                self.assertEqual(fn.call_args_list[0].kwargs,fn.call_args_list[1].kwargs)

    def test_second_invalid_output_still_has_no_ranking_or_provider_retry(self):
        invalid=self.reply();invalid['assessments'][1]['quote']='Not the displayed source quotation.'
        fn=Mock(return_value=json.dumps(invalid));rank,_=create_intent_rerank(fn)
        with self.assertRaises(PipelineError):rank('risks',self.rows)
        self.assertEqual(fn.call_count,2)
        fn=Mock(side_effect=RuntimeError('SECRET'));rank,_=create_intent_rerank(fn)
        with self.assertRaises(PipelineError):rank('risks',self.rows)
        self.assertEqual(fn.call_count,1)

    def test_empty_skips_generation_and_budget_is_not_silent_truncation(self):
        fn=Mock();rank,_=create_intent_rerank(fn,max_candidates=1)
        self.assertEqual(rank('risks',[]),[]);fn.assert_not_called()
        with self.assertRaisesRegex(ValueError,'budget'):rank('risks',self.rows)

    def test_schema_capability_and_provider_failure_payload_are_preserved_safely(self):
        fn=Mock(return_value=json.dumps(self.reply()));fn.supports_response_schema=True
        rank,_=create_intent_rerank(fn);rank('risks',self.rows)
        self.assertIn('response_schema',fn.call_args.kwargs)
        rank,_=create_intent_rerank(Mock(side_effect=RuntimeError('SECRET')))
        with self.assertRaises(PipelineError) as error:rank('risks',self.rows)
        self.assertNotIn('SECRET',str(error.exception))

    def test_cli_rejects_unfunded_retrieval_or_conflicting_ranking_routes(self):
        import main
        from contextlib import redirect_stderr
        import io
        for flags in [['--mode','retrieval','--retrieval-mode','hybrid'],[],
                      ['--retrieval-mode','hybrid','--reranker-model','fixture']]:
            with self.subTest(flags=flags),redirect_stderr(io.StringIO()):
                self.assertEqual(main.main(['--query','risks','--intent-rerank',*flags]),1)
