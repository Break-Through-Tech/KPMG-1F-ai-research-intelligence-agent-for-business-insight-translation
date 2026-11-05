"""Synthetic tests: no private scoring keys or held-out files."""
import json,tempfile,unittest
from pathlib import Path
from evaluation.development.validation import load_questions,aggregate_credits,citation_membership

class DevelopmentValidationTests(unittest.TestCase):
    cases=[{'id':'fixture','question':'What was measured?','category':'direct','split':'development','required_points_count':2},
           {'id':'negative','question':'What is absent?','category':'unanswerable','split':'development','required_points_count':0}]
    def review(self,ident,points,abstention='not_applicable'):
        return {'id':ident,'point_credits':points,'abstention':abstention,'notes':'Synthetic rubric review.',
                'human_confirmed':False,'confirmation_status':'pending'}
    def test_separate_abstention_and_partial_point_credit(self):
        result=aggregate_credits(self.cases,[self.review('fixture',[1,.5]),self.review('negative',[],'correct')])
        self.assertEqual(result['coverage'],.75);self.assertEqual(result['correct_abstentions'],1)
        self.assertTrue(result['complete']);self.assertFalse(result['human_confirmed'])
    def test_duplicate_unknown_and_confirmation_rejected(self):
        for reviews in [[self.review('unknown',[])],[self.review('fixture',[1,1])]*2,
                        [{**self.review('fixture',[1,1]),'human_confirmed':True}]]:
            with self.assertRaises(ValueError):aggregate_credits(self.cases,reviews)
    def test_nan_boolean_and_wrong_length_rejected(self):
        for credits in [[True,1],[float('nan'),1],[1]]:
            with self.assertRaises(ValueError):aggregate_credits(self.cases,[self.review('fixture',credits)])
    def test_loader_refuses_non_development_or_keys(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'questions.json'
            for payload in [{'split':'reserved','answer_keys_included':False,'cases':self.cases},
                            {'split':'development','answer_keys_included':True,'cases':self.cases}]:
                p.write_text(json.dumps(payload))
                with self.assertRaises(ValueError):load_questions(p)
    def test_membership_does_not_claim_entailment(self):
        result={'evidence':[{'chunk_id':'x','text':'A measured source fact.'}],
          'summary':{'claims':[{'support':[{'chunk_id':'x','quote':'source fact'},{'chunk_id':'missing','quote':'x'}]}]}}
        checks=citation_membership(result)
        self.assertTrue(checks[0]['quote_present']);self.assertFalse(checks[1]['resolved'])
        self.assertNotIn('supported',checks[0])
    def test_shared_specs_have_no_keys(self):
        cases=load_questions(Path(__file__).resolve().parents[1]/'evaluation/development/questions.json')
        self.assertEqual(len(cases),15)

if __name__=='__main__':unittest.main()
