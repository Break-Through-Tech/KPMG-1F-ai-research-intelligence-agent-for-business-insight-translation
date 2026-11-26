"""Freeze the prepared evaluation assets, never generation outputs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 target=ROOT/'frozen/manifest.json'
 if target.exists():raise SystemExit('Already frozen; create a new version for any change.')
 runtime=['src/business_checks.py','src/business_handoff.py','src/business_translation.py','src/business_insights.py','src/research_contracts.py','src/research_pipeline.py','src/research_review.py','src/generation.py','src/generation_config.py','experiments/agentic/numeric_checks.py','prompts/business_translation/baseline-v1.txt','prompts/business_translation/downstream-v1.1.txt']
 files={str(p.relative_to(ROOT)).replace('\\','/'):h(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and 'private' not in p.relative_to(ROOT).parts and p.name not in {'manifest.json','seal.json','preflight-result.json'}}
 manifest={'evaluation_id':'proofline-business-paired-v1','implementation_commit':'82702dc5436c8f5b41bdcd8df3bfa0422403ce22','status':'frozen_no_generation','hard_translation_call_cap':24,'scheduled_translation_calls':22,'no_call_case_arm_outcomes':2,'reference_cases':5,'new_generation_heldout_cases':7,'independent_human_scientific_verification':False,'files':files,'implementation_files':{p:h(REPO/p) for p in runtime}}
 target.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
 (ROOT/'frozen/seal.json').write_text(json.dumps({'manifest_sha256':h(target),'generation_started':False},indent=2)+'\n',encoding='utf-8',newline='\n')
 print(h(target))
if __name__=='__main__':main()
