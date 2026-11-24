import os
import json,sys,time
from pathlib import Path
d=Path(os.environ['B2_RESEARCH_ROOT']); sys.path.insert(0,str(d))
from src.experimental.b2 import open_b2
bundle=Path(os.environ['B2_BUNDLE'])
enc=Path(os.environ['B2_ENCODER'])
rer=Path(os.environ['B2_RERANKER'])
ret,ident,*_=open_b2(bundle,encoder_path=enc,reranker_path=rer)
refs=json.loads((d/'experiments/completion-eval-v1/references.json').read_text(encoding='utf8'))
seen={}; results=[]
def trace(frame,event,arg):
 if event=='call' and frame.f_code.co_name=='rank_facets': return trace
 if event=='return' and frame.f_code.co_name=='rank_facets': seen.update(frame.f_locals)
 return None
for q in refs:
 start=time.perf_counter(); sys.setprofile(trace)
 try: ret(q['question'],8)
 finally: sys.setprofile(None)
 a=seen.copy(); order=a['order']; engine=a['self']; papers=a['docs']
 saved=json.loads((Path(os.environ['B2_BASELINE_RUN'])/q['id']/'1-synthesis.evidence.json').read_text(encoding='utf8'))
 savedids=[p['chunk_id'] for p in saved]
 ids={p:i+1 for i,p in enumerate(order)}
 def rank(k,l): return l.index(k)+1 if k in l else None
 row={'id':q['id'],'reproduced':savedids==order[:8],'seconds':round(time.perf_counter()-start,2),'paper_candidates':sorted(papers),'top30':order[:30],'top8_papers':[engine.byid[k]['arxiv_id'] for k in order[:8]],'points':[]}
 for p in q['required_points']:
  data=[]
  for group in p['anchors']:
   data.append([dict(id=k,indexed=k in engine.byid,shortlisted=p['paper'] in papers,hybrid=rank(k,a['hybrid']),final=ids.get(k),ce=[r.get(k) for r in a['ranklists']],section=engine.byid.get(k,{}).get('section'),table=engine.byid.get(k,{}).get('table_id')) for k in group])
  row['points'].append(dict(id=p['point_id'],anchors=data,saved=any(set(g)<=set(savedids) for g in p['anchors'])))
 results.append(row)
 Path('b2-c01-c15-trace.json').write_text(json.dumps({'index':ident(),'cases':results},indent=2),encoding='utf8')
 print(q['id'],row['reproduced'],row['seconds'],flush=True)
