import os
import json,sys,time,re,math,tracemalloc,unicodedata
from pathlib import Path
from collections import Counter
import numpy as np
prefix=Path('capture_rankings.py').read_text(encoding='utf8').split('refs=json.loads')[0]
exec(prefix)
from src.experimental.retriever import tokens
original=json.loads(Path('b2-c01-c15-trace.json').read_text())
assert ident()==original['index']
folder=d/'experiments/completion-eval-v1'
cases=json.loads((folder/'questions.json').read_text(encoding='utf8'))
if isinstance(cases,dict): cases=cases['questions']
def norm(s):
 return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKC',s).lower())
def choose(a,query,mode):
 order=a['order']; e=a['self']; pool=order[:60]; ranks=a['ranklists']
 rel={k:1/math.log2(i+2) for i,k in enumerate(pool)}
 if mode=='C':
  views=[]
  for k in pool:
   indices=e.byview[k]; vd=e.index.vectors[indices]; delta=vd-a['qv']
   views.append(vd[np.argmin(np.sum(delta**2,axis=1))])
  v=np.array(views); v/=np.maximum(np.linalg.norm(v,axis=1,keepdims=True),1e-12)
  sim=v@v.T; best=np.zeros(len(pool)); chosen=[]
  for _ in range(8):
   j=max((j for j in range(len(pool)) if j not in chosen),key=lambda j:(.75*rel[pool[j]]-.25*best[j],-j))
   chosen.append(j); best=np.maximum(best,sim[j])
  return [pool[j] for j in chosen]
 papers={}
 for entity in re.findall(r'[A-Za-z][A-Za-z0-9²-]+',query):
  if sum(c.isupper() for c in entity[1:])<2 or len(norm(entity))<4: continue
  h=norm(entity)
  direct={e.byid[k]['arxiv_id'] for k in pool if h in norm(e.byid[k]['title'])}
  if not direct:
   direct={p['arxiv_id'] for p in e.parents if p['arxiv_id'] in a['docs'] and p.get('section')=='abstract' and h in norm(p['text'])}
  if len(direct)==1: papers[entity]=next(iter(direct))
 requested=set(papers.values())
 aspects=[{k:(1/math.sqrt(r[k]) if r[k]<=20 else 0) for k in pool} for r in ranks[1:]]
 if len(requested)>=2:
  aspects.extend({k:1/math.sqrt(1+sum(e.byid[j]['arxiv_id']==paper for j in pool[:i])) if e.byid[k]['arxiv_id']==paper else 0
                  for i,k in enumerate(pool)} for paper in sorted(requested))
 text={k:set(tokens(e.byid[k].get('row_label') or e.byid[k]['text'])) for k in pool}
 def overlap(x,y): return len(x&y)/max(1,len(x|y))
 chosen=[]; covered=[0.]*len(aspects)
 for _ in range(8):
  def utility(k):
   gain=max((max(0,s[k]-x) for s,x in zip(aspects,covered)),default=0)
   redundancy=max((overlap(text[k],text[j]) for j in chosen if e.byid[j]['arxiv_id']==e.byid[k]['arxiv_id']),default=0)
   return rel[k]+.35*gain-.20*redundancy
  k=max((k for k in pool if k not in chosen),key=utility)
  chosen.append(k); covered=[max(x,s[k]) for x,s in zip(covered,aspects)]
 return chosen
seen={}
def trace(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='rank_facets': seen.update(frame.f_locals)
def measures(ids,e):
 rows=[e.byid[k] for k in ids]
 terms=[set(tokens(p.get('row_label') or p['text'])) for p in rows]
 return {'ids':ids,'papers':[p['arxiv_id'] for p in rows],
 'tokens':sum(e.index.token_count(p['text']) for p in rows),
 'redundant_pairs':sum(len(x&y)/max(1,len(x|y))>=.65 for i,x in enumerate(terms) for y in terms[:i])}
output=[]
for q,previous in zip(cases,original['cases'],strict=True):
 query=q['question'] if 'question' in q else q['query']
 sys.setprofile(trace)
 try: ret(query,8)
 finally: sys.setprofile(None)
 a=seen.copy(); e=a['self']; order=a['order']; assert order[:30]==previous['top30']
 result={'id':previous['id'],'A':measures(order[:8],e),'B':measures(order[:16],e)}
 for mode in ('C','D'):
  start=time.perf_counter(); ids=choose(a,query,mode); elapsed=time.perf_counter()-start
  tracemalloc.start(); choose(a,query,mode); _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
  result[mode]={**measures(ids,e),'ms':elapsed*1000,'peak_py_bytes':peak}
 output.append(result)
 Path('b2-selection-packets.json').write_text(json.dumps(output,indent=2))
 print(previous['id'],flush=True)
