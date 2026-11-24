import os
import json,sys,time,re,math
from pathlib import Path
import numpy as np
from collections import Counter
exec(Path('capture_rankings.py').read_text(encoding='utf8').split('refs=json.loads')[0])
from src.experimental.balanced_retriever import facets
old=json.loads(Path('b2-c01-c15-trace.json').read_text(encoding='utf-8'))
assert ident()==old['index']
qs=json.loads((d/'experiments/completion-eval-v1/questions.json').read_text(encoding='utf-8'))
history=json.loads((d/'experiments/measure/end-to-end-diagnostic/results.json').read_text(encoding='utf8'))['historical']
qs += [{'id':n,'question':next(x['question'] for x in history if x['id']==n)} for n in ('agreemate','CU-DPO','Willow')]
seen={}
def trace(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='rank_facets': seen.update(frame.f_locals)
def cmp(q):
 return bool(re.search(r'\b(?:each|both|versus|vs|compar\w*|trade[- ]?off)\b',q,re.I))
def complexity(q):
 count=len(facets(q))
 return 30 if count>=2 or (count and cmp(q)) else 16 if count or cmp(q) else 8
def covered(q,a,ids):
 e=a['self']; pools=a['ranklists'][1:]
 covered_facets=all(any(r[i]<=3 for i in ids) for r in pools)
 if not cmp(q): return covered_facets
 diversity={e.byid[i]['arxiv_id'] for i in ids if e.byid[i]['arxiv_id'] in a['docs']}
 return covered_facets and len(diversity)>=2
def facet_depth(q,a,order):
 return next((k for k in (8,16,20,30) if covered(q,a,order[:k])),30)
def score_depth(a,order):
 # Single-pass largest adjacent raw CE gap in a monotone relevance list.
 # Map its qualifying IDs back to the original B2 prefix.
 seen=sorted(order[:60],key=lambda i:(-a['scores'][0][i],i))
 if len(seen)<9:return 8
 cut=max(range(8,min(30,len(seen)-1)+1),key=lambda k:a['scores'][0][seen[k-1]]-a['scores'][0][seen[k]])
 return min(30,max(8,max(order.index(i)+1 for i in seen[:cut])))
results=json.loads(Path('b2-adaptive-packets.json').read_text(encoding='utf-8')) if '--resume' in sys.argv else []
for q in qs:
 if any(x['id']==q['id'] for x in results):continue
 start=time.perf_counter(); sys.setprofile(trace)
 try:ret(q['question'],8)
 finally:sys.setprofile(None)
 retr=time.perf_counter()-start
 a=seen.copy(); e=a['self']; order=a['order'][:30]
 if q['id'].startswith('C') and q['id'][1:].isdigit():assert order==next(x['top30'] for x in old['cases'] if x['id']==q['id'])
 sizes=[e.index.token_count(e.byid[i]['text']) for i in order]
 arms={}
 for name,calc in [('8',lambda:8),('16',lambda:16),('20',lambda:20),('30',lambda:30),('complexity',lambda:complexity(q['question'])),('facet',lambda:facet_depth(q['question'],a,order)),('score',lambda:score_depth(a,a['order']))]:
  begin=time.perf_counter(); depth=calc()
  k=min(depth,len(order))
  if not name.isdigit():
   while k and sum(sizes[:k])>8000:k-=1
  cost=time.perf_counter()-begin
  arms[name]={'k':k,'intent':depth,'tokens':sum(sizes[:k]),'ms':cost*1000}
 results.append({'id':q['id'],'ids':order,'sizes':sizes,'seconds':retr,'arms':arms,'facets':len(a['ranklists'])-1})
 Path('b2-adaptive-packets.json').write_text(json.dumps(results,indent=2))
 print(q['id'],flush=True)
