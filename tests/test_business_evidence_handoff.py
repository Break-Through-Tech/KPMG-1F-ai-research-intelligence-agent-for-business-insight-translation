"""Business context must retain accepted caveat sources without rejected drafts."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from src.research_pipeline import run_research, require_current_review
from tests.test_indexed_research import PASSAGES, adapter


def sources():
    rows=[]
    for number,text in enumerate([
        'The controlled pilot improved the task completion score.',
        'The authors report no known real-world deployment instances.',
        'An unrelated draft comparison used a different training method.',
        'An older draft caveat describes a different experimental setting.',
    ],1):
        rows.append({**deepcopy(PASSAGES[0]),'chunk_id':f'p{number}','text':text})
    return rows


def item(text, source):
    return {'text':text,'support':[{'chunk_id':source['chunk_id'],'quote':source['text']}],
            'chunk_ids':[source['chunk_id']]}


def business():
    return {'status':'ok','industry':'banking','implications':[
        {'text':'Consider a bounded pilot; real-world transfer remains untested.',
         'chunk_ids':['p1','p2'],'suggested_action':'Compare locally before deployment.',
         'assumptions':['Controlled findings may not transfer.']}], 'risks':[], 'limitations':[]}


class BusinessEvidenceHandoffTests(unittest.TestCase):
    def test_rebuilt_limitation_source_reaches_business_without_rejected_audit(self):
        p1,p2,p3,p4=sources()
        # Retrieval order, not set order, must be retained.
        evidence=[p2,p3,p1,p4]
        def wire(text,source):return {k:v for k,v in item(text,source).items() if k!='chunk_ids'}
        raw={'status':'ok','claims':[dict(wire('The pilot improved task completion.',p1),kind='finding'),
            dict(wire('Unrelated training comparison.',p3),kind='finding')],
            'limitations':[wire('An obsolete draft caveat.',p4)]}
        review={'coverage':'full','gap':'','retained_claim_indices':[0],
                'decisions':[{'index':0,'supported':True,'relevant':True,'reason':'Answers the question.'},
                             {'index':1,'supported':True,'relevant':False,'reason':'Unrelated.'}],
                'limitations':[wire('No known real-world deployment instances.',p2)]}
        calls=[]
        def generate(prompt,**kwargs):
            calls.append(prompt)
            return json.dumps(review if prompt.startswith('ANSWER QUALITY REVIEW') else raw)
        research=adapter(generate=generate,retrieve=lambda q,k:deepcopy(evidence),quality_check=True)
        with patch('src.indexed_research.translate',return_value=business()) as translate:
            response=research.execute({'query':'What did the pilot find for banking?',
                'industry':'banking','context_id':research.context_id})
        self.assertIsNone(response['error'])
        summary,passed=translate.call_args.args
        self.assertEqual([p['chunk_id'] for p in passed],['p2','p1'])
        self.assertEqual(summary['limitation_support'][0]['chunk_ids'],['p2'])
        self.assertNotIn('quality_review',summary)
        self.assertNotIn('p3',json.dumps([summary,passed]))
        self.assertNotIn('p4',json.dumps([summary,passed]))
        final=response['result']
        self.assertEqual(len(final['evidence']),4)
        self.assertEqual(final['summary']['quality_review']['original_claims'][1]['chunk_ids'],['p3'])
        self.assertEqual(final['summary']['quality_review']['original_limitation_support'][0]['chunk_ids'],['p4'])
        self.assertFalse(final['approved'])
        require_current_review(final)
        self.assertEqual(len(calls),2)  # Existing synthesis/review only; no new model stage.

    def finish_summary(self,summary,evidence):
        research=adapter(quality_check=True)
        request={'query':'What does the research support?','top_k':5,'industry':'banking'}
        result=run_research(request,retrieve=lambda q,k:deepcopy(evidence),
            summarize_fn=lambda q,p:deepcopy(summary),provenance=research.provenance)
        return research,result,request

    def test_shared_citations_are_unique_ordered_and_inputs_remain_intact(self):
        p1,p2,p3,_=sources()
        summary={'status':'ok','query':'What does the research support?',
            'claims':[dict(item('The pilot improved task completion.',p1),kind='finding')],
            'limitations':['Deployment remains unverified.','Controlled setting only.'],
            'limitation_support':[item('Deployment remains unverified.',p2),item('Controlled setting only.',p1)],
            'answer_scope':'partial','answer_lead':'Deployment effects remain untested.',
            'quality_review':{'original_claims':[item('Rejected draft.',p3),
                              item('Rejected assertion from a shared source.',p2)]}}
        research,result,request=self.finish_summary(summary,[p2,p1,p3]);before=deepcopy(result)
        with patch('src.indexed_research.translate',return_value=business()) as translate:
            response=research.finish(result,request)
        passed_summary,passed=translate.call_args.args
        self.assertEqual([p['chunk_id'] for p in passed],['p2','p1'])
        self.assertEqual(result['summary'],before['summary'])
        self.assertEqual(result['evidence'],before['evidence'])
        self.assertNotIn('quality_review',passed_summary)
        self.assertNotIn('Rejected assertion',json.dumps(passed_summary))
        self.assertEqual(passed_summary['answer_scope'],'partial')
        self.assertEqual(passed_summary['answer_lead'],'Deployment effects remain untested.')
        self.assertIsNone(response['error'])

    def test_legacy_summary_without_limitation_citations_keeps_claim_sources(self):
        p1,p2,*_=sources()
        for support in (None,[]):
            summary={'status':'ok','query':'What does the research support?',
                'claims':[dict(item('The pilot improved task completion.',p1),kind='finding')],
                'limitations':['Legacy uncited scope note.']}
            if support is not None:summary['limitation_support']=support
            research,result,request=self.finish_summary(summary,[p2,p1])
            output=business();output['implications'][0]['chunk_ids']=['p1']
            with patch('src.indexed_research.translate',return_value=output) as translate:
                response=research.finish(result,request)
            self.assertIsNone(response['error'])
            self.assertEqual([p['chunk_id'] for p in translate.call_args.args[1]],['p1'])

    def test_missing_accepted_limitation_source_fails_before_business_generation(self):
        p1,p2,*_=sources()
        for malformed in ('unknown_id','missing_ids','null_support'):
            with self.subTest(malformed=malformed):
                limit=item('Deployment remains unverified.',p2)
                if malformed=='missing_ids':limit.pop('chunk_ids')
                summary={'status':'ok','query':'What does the research support?',
                    'claims':[dict(item('The pilot improved task completion.',p1),kind='finding')],
                    'limitations':[limit['text']],'limitation_support':[limit]}
                if malformed=='null_support':summary['limitation_support']=None
                research,result,request=self.finish_summary(summary,[p1])
                with patch('src.indexed_research.translate') as translate:
                    response=research.finish(result,request)
                translate.assert_not_called()
                self.assertEqual(response['error']['code'],'business_failed')
                self.assertEqual(response['result']['summary']['status'],'ok')
                self.assertNotIn('business_insight',response['result'])

    def test_real_translation_accepts_caveat_source_and_rejects_filtered_source(self):
        p1,p2,p3,_=sources()
        summary={'status':'ok','query':'What does the research support?',
            'claims':[dict(item('The pilot improved task completion.',p1),kind='finding')],
            'limitations':['Deployment remains unverified.'],
            'limitation_support':[item('Deployment remains unverified.',p2)],
            'quality_review':{'original_claims':[item('Rejected draft.',p3)]}}
        for citation in ('p2','p3'):
            with self.subTest(citation=citation):
                research,result,request=self.finish_summary(summary,[p1,p2,p3])
                output=business();output['implications'][0]['chunk_ids']=[citation]
                research.generate=lambda *a,**k:json.dumps(output)
                response=research.finish(result,request)
                if citation=='p2':
                    self.assertIsNone(response['error'])
                    self.assertEqual(response['result']['business_insight']['implications'][0]['chunk_ids'],['p2'])
                else:
                    self.assertEqual(response['error']['code'],'business_failed')
                    self.assertNotIn('business_insight',response['result'])

    def test_unreviewed_path_keeps_the_full_evidence_set(self):
        p1,p2,p3,p4=sources()
        summary={'status':'ok','query':'What does the research support?',
            'claims':[dict(item('The pilot improved task completion.',p1),kind='finding')],
            'limitations':[]}
        research,result,request=self.finish_summary(summary,[p2,p3,p1,p4])
        research.quality_check=False
        with patch('src.indexed_research.translate',return_value=business()) as translate:
            response=research.finish(result,request)
        self.assertIsNone(response['error'])
        self.assertEqual(translate.call_args.args[1],result['evidence'])


if __name__=='__main__':unittest.main()
