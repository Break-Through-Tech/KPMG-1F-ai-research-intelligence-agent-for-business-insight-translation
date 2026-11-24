import os
import json,math,re,statistics as s
from collections import Counter
from pathlib import Path
d=Path(os.environ['B2_RESEARCH_ROOT'])
rows=json.loads(Path('b2-adaptive-packets.json').read_text())
refs={r['id']:r['required_points'] for r in json.loads((d/'experiments/completion-eval-v1/references.json').read_text())}
cases=[r for r in rows if r['id'] in refs]
needed={k for r in rows for k in r['ids']}
bundle=Path(os.environ['B2_BUNDLE'])
parents={p['chunk_id']:p for l in (bundle/'parents.jsonl').open(encoding='utf8') if (p:=json.loads(l))['chunk_id'] in needed}
def terms(i):
 p=parents[i]; return set(re.findall(r'\w+', (p.get('row_label') or p['text']).lower()))
words={i:terms(i) for i in needed}
def p90(xs):return sorted(xs)[math.ceil(.9*len(xs))-1]
def hits(r,ids):
 ids=set(ids)
 return {p['point_id'] for p in refs[r['id']] if any(set(g)<=ids for g in p['anchors'])}
def k_budget(r,b,depth):
 k=0; total=0
 for n in r['sizes'][:depth]:
  if total+n>b:break
  k+=1;total+=n
 return k
def metrics(select,hole_budget=None):
 packets=[]
 for r in cases:
  if hole_budget is None:
   indices=list(range(select(r)))
  else:
   indices=[]; remaining=hole_budget
   for i,size in enumerate(r['sizes']):
    if size<=remaining:
     indices.append(i);remaining-=size
  packets.append(indices)
 depths=[len(v) for v in packets]
 h=[hits(r,[r['ids'][i] for i in v]) for r,v in zip(cases,packets)]
 ts=[sum(r['sizes'][i] for i in v) for r,v in zip(cases,packets)]
 more=[(r,hh) for r,k,hh in zip(cases,depths,h) if k>8]
 misses=[hits(r,r['ids'])-hh for r,hh in zip(cases,h)]
 rep=off=0
 for r,v in zip(cases,packets):
  ids=[r['ids'][i] for i in v]; papers={p['paper'] for p in refs[r['id']]}
  off+=sum(parents[i]['arxiv_id'] not in papers for i in ids)
  for j,i in enumerate(ids):
   rep+=sum(len(words[i]&words[p])/max(1,len(words[i]|words[p]))>=.65 for p in ids[:j])
 return [sum(map(len,h)),sum(len(hh)==len(refs[r['id']]) for r,hh in zip(cases,h)),round(s.mean(depths),2),max(depths),s.median(ts),p90(ts),round(1000*sum(map(len,h))/sum(ts),3),len(more),sum(hh==hits(r,r['ids'][:8]) for r,hh in more),sum(bool(m) for m in misses),sum(map(len,misses)),rep,off,sum(depths)]
print('arm | exact full mean_k max_k median_tokens p90_tokens points_per_1k expanded no_gain premature_q premature_pts near_dup off_reference slots')
for arm in ('8','16','20','30'):
 print(arm,*metrics(lambda r:r['arms'][arm]['k']))
for a in ('complexity','facet','score'):
 print(a,'passage-only',*metrics(lambda r:r['arms'][a]['intent']))
for b in (4000,6000,8000):
 print('skip-fit',b,*metrics(None,b))
 for a in ('window','complexity','facet','score'):
  print(a,b,*metrics(lambda r:k_budget(r,b,30 if a=='window' else r['arms'][a]['intent'])))
for r in rows:
 if r['id'] in refs:continue
 print('control',r['id'],{**{a:x['k'] for a,x in r['arms'].items()},**{b:k_budget(r,b,30) for b in (4000,6000,8000)}})
