"""Offline integrity preflight and explicit, separately authorized paired execution."""
import argparse, hashlib, json, os, random, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];sys.path.insert(0,str(REPO))
from src.business_handoff import accepted_research
from src.business_insights import translate_result
from src.business_translation import translate

def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=True)+'\n',encoding='utf-8',newline='\n')
def preflight():
 m=read(ROOT/'frozen/manifest.json')
 for rel,h in m['files'].items():assert sha((ROOT/rel).read_bytes())==h, 'Frozen asset changed: '+rel
 for rel,h in m['implementation_files'].items():assert sha((REPO/rel).read_bytes())==h, 'Implementation changed: '+rel
 receipts=read(ROOT/'frozen/source-verification.json')
 for r in receipts:
  assert sha(Path(r['original_pdf']).read_bytes())==r['pdf_sha256']
  assert r['dual_extractor_membership']
 cases=read(ROOT/'frozen/cases.json');assert len(cases)==12
 calls=0
 for c in cases:
  p=read(ROOT/('frozen/packets/'+c['id']+'.json'))
  s,e,_=accepted_research(p['result']['summary'],p['result']['evidence']);s['business_context']=p['context']
  assert sha(json.dumps([s,e],sort_keys=True).encode())==p['shared_input_sha256']
  calls+=2*c['expected_calls_per_arm']
 assert calls==22 and calls<=m['hard_translation_call_cap']==24
 return {'assets':'PASS','source_hashes_and_dual_membership':'PASS','cases':12,'reference_aligned':5,'new_generation_heldout':7,'scheduled_model_calls':calls,'no_call_outcomes':2,'live_calls_made':0,'live_ready':False,'pending':['approved provider/model and separate project configuration','explicit live-call approval','two independent reviewers; do not use assistant ratings as human scores']}

def execute(config_path,run_dir,approved_hash):
 preflight()
 manifest_hash=sha((ROOT/'frozen/manifest.json').read_bytes())
 if approved_hash!=manifest_hash:raise ValueError('Explicit approval must identify the frozen manifest hash.')
 cfg=read(config_path)
 assert cfg['provider'] in {'openai','gemini'} and cfg['model']
 assert cfg['independent_project_confirmed'] is True and cfg['project_label']
 assert not any(os.environ.get(k) for k in ('GOOGLE_GENAI_USE_VERTEXAI','GOOGLE_GEMINI_BASE_URL','GOOGLE_VERTEX_BASE_URL')), 'Remove alternate Gemini endpoints.'
 assert cfg['temperature']==0 and cfg['sdk_attempts']==1 and cfg['hard_cap']==24
 assert os.environ.get('BUSINESS_EVAL_API_KEY') and not any(os.environ['BUSINESS_EVAL_API_KEY']==os.environ.get(k) for k in ('GOOGLE_API_KEY','OPENAI_API_KEY','RESEARCH_API_KEY')),'Use a separately scoped business-evaluation credential.'
 run_dir=run_dir.resolve();assert REPO/'business-evaluation' in run_dir.parents,'Use the isolated business-evaluation tree.'
 lock=ROOT/'private/campaign.lock';lock.parent.mkdir(exist_ok=True)
 with lock.open('x') as f:json.dump({'manifest_sha256':manifest_hash,'run_dir':str(run_dir)},f)
 run_dir.mkdir(exist_ok=False);(run_dir/'private').mkdir();(run_dir/'blind').mkdir();(run_dir/'ledger').mkdir()
 dump(run_dir/'private/run-config.json',{**cfg,'manifest_sha256':manifest_hash,'run_config_sha256':sha(config_path.read_bytes())})
 # Load the existing provider adapter explicitly: no dotenv, fallback or campaign state.
 from src.generation_config import GenerationConfig
 from src.generation import create_generate
 generate,metadata=create_generate(GenerationConfig(cfg['provider'],cfg['model'],os.environ['BUSINESS_EVAL_API_KEY']))
 cases=read(ROOT/'frozen/cases.json');order=list(cases);random.SystemRandom().shuffle(order)
 mapping={};count=0
 for i,c in enumerate(order,1):
  label=f'Q{i:02}';mapping[label]={'case_id':c['id'],'split':c['split']}
  arms=['baseline','candidate'] if i%2 else ['candidate','baseline']
  mapping[label]['labels']={k:a for k,a in zip(('A','B'),arms)}
  dump(run_dir/'private/blind-key.json',mapping)
  packet=read(ROOT/('frozen/packets/'+c['id']+'.json'))
  s,e,_=accepted_research(packet['result']['summary'],packet['result']['evidence']);s['business_context']=packet['context']
  dump(run_dir/('blind/'+label+'-case.json'),{'question':c['question'],'context':packet['context'],'accepted_research':s,'evidence':e})
  for public,arm in mapping[label]['labels'].items():
   key=label+'-'+public;attempts=0;raw=[];audit=None;started=time.perf_counter()
   def once(prompt):
    nonlocal count,attempts
    if count>=24 or attempts:raise RuntimeError('Hard budget or no-retry gate.')
    # Reserve BEFORE dispatch. Exclusive slot files count ambiguous failures too.
    slot=run_dir/'ledger'/f'{count+1:02}.json'
    with slot.open('x') as f:json.dump({'case':label,'arm':arm,'status':'reserved','prompt_sha256':sha(prompt.encode())},f)
    count+=1;attempts+=1
    answer=generate(prompt);raw.append(answer);return answer
   try:
    if arm=='baseline':
     output=translate(s,e,industry=packet['context']['industry'],generate=once)
     error=None
    else:
     env=translate_result(packet['result'],context=packet['context'],generate=once,metadata=metadata,research_input={'kind':'source_verified_manual_packet'})
     output=env['result'].get('business_insight');error=env['error'];audit=env['result']['provenance']['business_translation']
    status='execution_failed' if error else 'skipped_no_accepted_evidence' if not attempts else output['status']
   except Exception:
    output=None;error=True;status='execution_failed'
   dump(run_dir/('private/'+key+'.json'),{'arm':arm,'case':c['id'],'raw_responses':raw,'audit':audit,'output':output,'status':status,'attempts':attempts,'elapsed_seconds':time.perf_counter()-started})
   # Identical schema and neutral failures; omit model, prompt, checks and arm identity.
   dump(run_dir/('blind/'+key+'.json'),{'case':label,'label':public,'status':status,'business_insight':output})
 dump(run_dir/'private/completion.json',{'attempted_calls':count,'hard_cap':24,'automatic_retries':0,'cases':12})

def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--config',type=Path);p.add_argument('--run-dir',type=Path);p.add_argument('--approved-manifest-sha256');a=p.parse_args()
 if a.execute:
  if not all((a.config,a.run_dir,a.approved_manifest_sha256)):p.error('Explicit config, new run-dir and approved manifest hash required.')
  execute(a.config,a.run_dir,a.approved_manifest_sha256)
 else:print(json.dumps(preflight(),indent=2))
if __name__=='__main__':main()
