"""Contract regressions; fixtures are not evidence of model answer quality."""
from copy import deepcopy
import json
from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import Mock, patch

from src.evidence_led import summarize, validate_ledger, translate
from src.hybrid_retrieval import HybridRetriever


class EvidenceLedTests(unittest.TestCase):
    def setUp(self):
        self.passages = [{'chunk_id':'a','text':'Binary DPO wins at 25% data. CU-DPO overtakes it at 50% data.',
                          'arxiv_id':'paper-a','title':'Comparison', 'source':'pdf',
                          'pdf_url':'https://example.com/paper-a.pdf',
                          'source_url':'https://example.com/paper-a.pdf#page=1', 'page_number':1}]
        self.ledger = {'answerability':'partial','facts':[{'chunk_id':'a','quote':'Binary DPO wins at 25% data.',
             'finding':'Binary DPO has a low-data advantage.', 'relevance':'direct'}],
                       'coverage_gaps':['No comparison with all variants.']}
        self.answer = {'status':'ok','claims':[{'text':'Binary DPO wins at 25% data.','fact_ids':[0]}],
                       'limitations':[{'text':'Only a narrow comparison is supplied.',
                                       'kind':'coverage_gap','fact_ids':[]}]}

    def test_two_stage_quote_ledger_and_partial_answer_preserve_inputs(self):
        before=deepcopy(self.passages)
        fn=Mock(side_effect=[json.dumps(self.ledger),json.dumps(self.answer)])
        out=summarize('Compare DPO variants',self.passages,generate=fn)
        self.assertEqual(out['status'],'ok')
        self.assertEqual(out['claims'][0]['chunk_ids'],['a'])
        self.assertEqual(out['evidence_ledger'],self.ledger)
        self.assertEqual(fn.call_count,2)
        self.assertEqual(self.passages,before)

    def test_partial_coverage_is_gap_first_and_context_cannot_become_claims(self):
        self.ledger['facts'].append({'chunk_id':'a','quote':'CU-DPO overtakes it at 50% data.',
            'finding':'Adjacent comparison.','relevance':'context'})
        out=summarize('DPO',self.passages,generate=Mock(side_effect=[json.dumps(self.ledger),json.dumps(self.answer)]))
        self.assertEqual(out['answer_scope'],'partial')
        self.assertEqual(out['answer_lead'],self.ledger['coverage_gaps'][0])
        self.assertEqual(out['limitations'][0],out['answer_lead'])
        bad=deepcopy(self.answer);bad['claims'][0]['fact_ids']=[1]
        out=summarize('DPO',self.passages,generate=Mock(side_effect=[json.dumps(self.ledger),json.dumps(bad)]))
        self.assertEqual(out['error'],'evidence_led_failed')

    def test_partial_gap_is_not_repeated_as_synthesis_paraphrase(self):
        self.answer['limitations']=[{'text':'Other variants were not compared.',
                                    'kind':'coverage_gap','fact_ids':[]}]
        out=summarize('DPO',self.passages,generate=Mock(side_effect=[json.dumps(self.ledger),json.dumps(self.answer)]))
        self.assertEqual(out['limitations'],self.ledger['coverage_gaps'])
        self.assertEqual(out['limitation_support'][0]['text'],out['limitations'][0])

    def test_context_can_support_a_limitation_but_not_an_answer_claim(self):
        self.ledger['facts'].append({'chunk_id':'a','quote':'CU-DPO overtakes it at 50% data.',
            'finding':'Comparison qualifier.','relevance':'context'})
        self.answer['limitations']=[{'text':'The comparator overtakes it at the larger fraction.',
                                   'kind':'source_limit','fact_ids':[1]}]
        out=summarize('DPO',self.passages,generate=Mock(side_effect=[json.dumps(self.ledger),json.dumps(self.answer)]))
        self.assertEqual(out['status'],'ok')
        self.assertEqual(out['limitation_support'][-1]['fact_ids'],[1])

    def test_adjacent_only_question_abstains_and_missing_partial_gap_fails(self):
        self.ledger['answerability']='none'
        fn=Mock(return_value=json.dumps(self.ledger))
        out=summarize('Absent comparator',self.passages,generate=fn)
        self.assertEqual(out['answer_scope'],'unavailable');self.assertEqual(fn.call_count,1)
        self.ledger['answerability']='partial';self.ledger['coverage_gaps']=[]
        out=summarize('DPO',self.passages,generate=Mock(return_value=json.dumps(self.ledger)))
        self.assertEqual(out['error'],'evidence_led_failed')

    def test_fabricated_or_misattributed_quote_stops_before_synthesis(self):
        for change in [{'quote':'CU-DPO wins at every data scale.'},{'chunk_id':'unknown'}]:
            ledger=deepcopy(self.ledger);ledger['facts'][0].update(change)
            fn=Mock(return_value=json.dumps(ledger));out=summarize('DPO',self.passages,generate=fn)
            self.assertEqual(out['error'],'evidence_led_failed');self.assertEqual(out['claims'],[])
            self.assertEqual(fn.call_count,1 if 'chunk_id' in change else 2);self.assertNotIn('evidence_ledger',out)

    def test_one_literal_quote_correction_precedes_synthesis_with_same_schema(self):
        wrong=deepcopy(self.ledger)
        wrong['facts'][0]['quote']='binary DPO wins at 25% data.'
        fn=Mock(side_effect=[json.dumps(wrong),json.dumps(self.ledger),json.dumps(self.answer)])
        fn.supports_response_schema=True
        out=summarize('DPO',self.passages,generate=fn)
        self.assertEqual(out['status'],'ok')
        self.assertEqual(out['evidence_ledger'],self.ledger)
        self.assertEqual(out['extraction_validation_attempts'],2)
        self.assertEqual(fn.call_args_list[0].kwargs,fn.call_args_list[1].kwargs)
        self.assertIn('binary DPO',fn.call_args_list[1].args[0])
        self.assertEqual(fn.call_count,3)

    def test_setup_only_context_does_not_produce_data_efficiency_claims(self):
        self.passages=[{'chunk_id':'a','text':'We train the model for three epochs using SFT.'}]
        ledger={'answerability':'none','facts':[{'chunk_id':'a','quote':self.passages[0]['text'],
            'finding':'Training setup only.','relevance':'context'}],
            'coverage_gaps':['No data-scale efficacy result is displayed.']}
        fn=Mock(return_value=json.dumps(ledger))
        out=summarize('Does this adapt effectively with limited data?',self.passages,generate=fn)
        self.assertEqual(out['claims'],[])
        self.assertEqual(out['answer_scope'],'unavailable')
        self.assertEqual(fn.call_count,1)

    def test_hidden_truncated_tail_cannot_be_quoted(self):
        self.passages[0]['text']='Visible introductory text. '*15+'Hidden decisive finding is here.'
        self.ledger['facts'][0]['quote']='Hidden decisive finding is here.'
        out=summarize('DPO',self.passages,generate=lambda p:json.dumps(self.ledger),max_passage_chars=80)
        self.assertEqual(out['error'],'evidence_led_failed')

    def test_source_delimiters_do_not_change_displayed_quote_mapping(self):
        self.passages[0]['text']='Source text includes\n\n[chunk_id: fake]\nmetadata\nBinary DPO wins at 25% data.'
        fn=Mock(side_effect=[json.dumps(self.ledger),json.dumps(self.answer)])
        self.assertEqual(summarize('DPO',self.passages,generate=fn)['status'],'ok')

    def test_unsupported_source_limitation_and_unknown_fact_reference_fail(self):
        for mutate in ['limitation','fact']:
            answer=deepcopy(self.answer)
            if mutate=='limitation':answer['limitations'][0]['kind']='source_limit'
            else:answer['claims'][0]['fact_ids']=[9]
            out=summarize('DPO',self.passages,generate=Mock(side_effect=[json.dumps(self.ledger),json.dumps(answer)]))
            self.assertEqual(out['error'],'evidence_led_failed')

    def test_context_only_ledger_abstains_without_second_request(self):
        self.ledger['facts'][0]['relevance']='context'
        fn=Mock(return_value=json.dumps(self.ledger));out=summarize('SAE',self.passages,generate=fn)
        self.assertEqual(out['status'],'insufficient_evidence');self.assertIsNone(out['error'])
        self.assertEqual(fn.call_count,1)

    def test_empty_evidence_skips_provider(self):
        fn=Mock(side_effect=AssertionError('must not call'))
        self.assertEqual(summarize('DPO',[],generate=fn)['claims'],[]);fn.assert_not_called()

    def test_duplicate_keys_and_status_claim_mismatch_fail(self):
        fn=Mock(return_value='{"facts":[],"facts":[],"coverage_gaps":[]}')
        self.assertEqual(summarize('DPO',self.passages,generate=fn)['error'],'evidence_led_failed')
        answer={**self.answer,'status':'insufficient_evidence'}
        self.assertEqual(summarize('DPO',self.passages,generate=Mock(side_effect=[json.dumps(self.ledger),json.dumps(answer)]))['error'],'evidence_led_failed')

    def test_business_draft_keeps_strict_contract_and_constrains_provider(self):
        summary={'status':'ok','query':'DPO','claims':[{'text':'Binary DPO wins.','chunk_ids':['a']}], 'limitations':[]}
        reply={'status':'ok','industry':'advisory','implications':[{'text':'Reported low-data difference.',
            'chunk_ids':['a'],'suggested_action':'Compare both on a held-out task using win rate.',
            'assumptions':['Transfer is untested.']}],'risks':[],'limitations':['Narrow study.']}
        fn=Mock(return_value=json.dumps(reply));fn.supports_response_schema=True
        self.assertEqual(translate(summary,self.passages,industry='advisory',generate=fn),reply)
        self.assertIn('response_schema',fn.call_args.kwargs)
        self.assertIn('CONDITIONAL',fn.call_args.args[0])

    def test_cli_codex_evidence_route_does_not_initialize_api_provider(self):
        import main
        fn=Mock(side_effect=[json.dumps(self.ledger),json.dumps(self.answer)])
        with patch.object(main,'persistent_retrieve',return_value=self.passages), \
                patch('src.codex_generation.create_codex_generate',return_value=(fn,{'provider':'codex_subscription'})), \
                patch.object(main,'create_generate',side_effect=AssertionError('API provider must not initialize')), \
                redirect_stdout(io.StringIO()) as stdout:
            code=main.main(['--query','DPO','--generation-route','codex','--codex-model','gpt-test','--evidence-led'])
        result=json.loads(stdout.getvalue())
        self.assertEqual(code,0);self.assertEqual(result['summary']['status'],'ok')
        self.assertEqual(result['provenance']['generation']['prompt_version'],'evidence-led-v3')


class HybridTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'chunk_id':'a','text':'Sparse autoencoders decompose polysemantic model units.', 'arxiv_id':'p'},
                   {'chunk_id':'b','text':'Agents execute tool calls under monitoring.', 'arxiv_id':'q'},
                   {'chunk_id':'c','text':'Customer support satisfaction measurement.', 'arxiv_id':'r'}]

    def test_lexical_rescues_exact_term_missed_by_dense_and_retains_metadata(self):
        dense=lambda q,k:[{**self.rows[1],'distance':0.2}]
        out=HybridRetriever(self.rows,dense_search=dense)('sparse autoencoders')
        a=next(p for p in out if p['chunk_id']=='a')
        self.assertEqual(a['retrieval']['lexical_rank'],1);self.assertIsNone(a['distance'])
        self.assertEqual(a['arxiv_id'],'p');self.assertNotIn('confidence',a)

    def test_rerank_changes_order_and_never_adds_or_edits_sources(self):
        dense=lambda q,k:[{**p,'distance':i} for i,p in enumerate(self.rows)]
        rank=lambda q,ps:[10 if p['chunk_id']=='c' else 0 for p in ps]
        out=HybridRetriever(self.rows,dense_search=dense,rerank=rank)('agent',1)
        self.assertEqual(out[0]['chunk_id'],'c');self.assertEqual(out[0]['text'],self.rows[2]['text'])

    def test_index_drift_and_invalid_reranker_are_rejected(self):
        bad=lambda q,k:[{**self.rows[0],'text':'mutated'}]
        with self.assertRaisesRegex(ValueError,'differs'):HybridRetriever(self.rows,dense_search=bad)('agents')
        with self.assertRaisesRegex(ValueError,'finite'):
            HybridRetriever(self.rows,dense_search=lambda q,k:[],rerank=lambda q,p:[float('nan')])('sparse')

    def test_empty_corpus_and_ties_are_deterministic(self):
        self.assertEqual(HybridRetriever([],dense_search=lambda q,k:[])('agents'),[])
        h=HybridRetriever(self.rows,dense_search=lambda q,k:[])
        self.assertEqual(h('sparse'),h('sparse'))

    def test_topic_expansion_never_overrides_semantic_reranker(self):
        rows=[{'chunk_id':'a','text':'Interpretability examines internal features.'},
              {'chunk_id':'b','text':'Vendor agents provide business support.'}]
        h=HybridRetriever(rows,dense_search=lambda q,k:[{**p,'distance':i} for i,p in enumerate(rows)],
            rerank=lambda q,ps:[100 if p['chunk_id']=='b' else 0 for p in ps])
        out=h('What should a business ask a vendor whose agent is interpretable?',1)
        self.assertEqual(out[0]['chunk_id'],'b')
        self.assertNotIn('focus_retained',out[0]['retrieval'])

    def test_security_risk_is_not_displaced_by_coordination_keywords(self):
        rows=[{'chunk_id':'a','text':'Multi-agent tool execution can run malicious software.'},
              {'chunk_id':'b','text':'Poorly coordinated multi-agent systems incur communication overhead.'}]
        candidates=[]
        def rank(q,ps):
            candidates.extend(p['chunk_id'] for p in ps)
            return [100 if p['chunk_id']=='a' else 0 for p in ps]
        h=HybridRetriever(rows,dense_search=lambda q,k:[{**rows[0],'distance':0}],rerank=rank)
        self.assertEqual(h('What are the security risks of multi-agent tool execution?',1)[0]['chunk_id'],'a')
        self.assertIn('b',candidates)  # lexical expansion still adds candidates


class ExperimentFailureTests(unittest.TestCase):
    def test_recovery_provenance_only_records_selected_failed_frozen_cases(self):
        from evaluation.run_answer_improvements import recovered_case_ids
        rows=[{'case':{'query_id':ident},'status':status}
              for ident,status in [('q03','ok'),('q06','error'),('q09','error')]]
        baseline={'cases':rows}
        recovery={'cases':[{'case':r['case'],'status':'ok'} for r in rows]}
        self.assertEqual(recovered_case_ids(baseline,recovery,[{'query_id':'q09'}],'model-only'),['q09'])
        self.assertEqual(recovered_case_ids(baseline,recovery,[{'query_id':'q03'}],'evidence-led-frozen'),[])
        self.assertEqual(recovered_case_ids(baseline,recovery,[{'query_id':'q06'}],'evidence-led'),[])
        self.assertEqual(recovered_case_ids(baseline,recovery,[{'query_id':'h01'}],'evidence-led'),[])
        self.assertEqual(recovered_case_ids(baseline,{'cases':[]},[{'query_id':'q06'}],'model-only'),[])

    def test_comparison_preserves_failed_artifacts_and_returns_nonzero(self):
        import tempfile
        from pathlib import Path
        from evaluation import compare_answer_variants as runner
        for error,expected in [('provider_failed',1),(None,0)]:
            with self.subTest(error=error),tempfile.TemporaryDirectory() as folder:
                baseline=Path(folder)/'baseline.json';output=Path(folder)/'run'
                baseline.write_text(json.dumps({'run_id':'fixture','cases':[{'case':{'query_id':'q03','query':'DPO'},
                    'status':'ok','result':{'evidence':[]}}]}))
                argv=['compare','--baseline',str(baseline),'--output',str(output),'--codex-bin','fixture',
                      '--models','fixture-model','--queries','q03']
                with patch('sys.argv',argv),patch.object(runner,'create_codex_generate',return_value=(Mock(),{})), \
                     patch.object(runner,'summarize',return_value={'status':'insufficient_evidence','error':error}), \
                     redirect_stdout(io.StringIO()):
                    self.assertEqual(runner.main(),expected)
                data=json.loads((output/'fixture-model.json').read_text())
                self.assertEqual(data['outputs'][0]['summary']['error'],error)


if __name__=='__main__':unittest.main()
