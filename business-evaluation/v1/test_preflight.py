"""Offline preflight tests: capture prompts with canned invalid JSON, never models."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path[:0]=[str(ROOT),str(ROOT.parents[1])]
import run
from src.business_handoff import accepted_research
from src.business_translation import translate
from src.business_insights import translate_result
class PreflightTests(unittest.TestCase):
 def test_integrity_sources_and_budget(self):self.assertEqual(run.preflight()['scheduled_model_calls'],22)
 def test_paired_input_payloads_and_skip(self):
  calls=0
  for case in run.read(ROOT/'frozen/cases.json'):
   p=run.read(ROOT/('frozen/packets/'+case['id']+'.json'));s,e,_=accepted_research(p['result']['summary'],p['result']['evidence']);s['business_context']=p['context']
   prompts=[]
   def capture(prompt):prompts.append(prompt);return '{}'
   try:translate(s,e,industry=p['context']['industry'],generate=capture)
   except ValueError:pass
   translate_result(p['result'],context=p['context'],generate=capture)
   self.assertEqual(len(prompts),2*case['expected_calls_per_arm'])
   for prompt in prompts:
    self.assertIn(json.dumps(s,allow_nan=False),prompt);self.assertIn(json.dumps(e,allow_nan=False),prompt)
   calls+=len(prompts)
  self.assertEqual(calls,22) # Canned invocations, zero external calls.
 def test_no_live_approval_no_dispatch(self):
  with self.assertRaises(ValueError):run.execute(ROOT/'provider-config.example.json',ROOT/'never-created','unapproved')
  self.assertFalse((ROOT/'never-created').exists())
if __name__=='__main__':unittest.main()
