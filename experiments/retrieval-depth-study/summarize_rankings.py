import os
import collections,json
from pathlib import Path
data=json.loads(Path('b2-c01-c15-trace.json').read_text(encoding='utf-8'))
cases=data['cases']
def hit(p,k):
 return any(all(a['final'] is not None and a['final']<=k for a in g) for g in p['anchors'])
def reason(a):
 if not a['indexed']:return 'not indexed'
 if a['final'] is None:
  if a['hybrid'] is None:return 'outside discovery, not reranked'
  return 'outside rerank pool'
 if a['final']<=8:return 'delivered'
 return 'reranked, below top 8'
rows=[]
print(len(cases),'cases;',sum(c['reproduced'] for c in cases),'exact replay packets')
print('k, points covered, complete questions')
for k in [8,12,16,20,30,1000000]:
 print(k,sum(hit(p,k) for c in cases for p in c['points']),sum(all(hit(p,k) for p in c['points']) for c in cases))
print('Identifier | Point(s) | Funnel location | Paper shortlist / top8 paper count | Initial hybrid rank | CE ranks | Final rank')
for c in cases:
 anchors={}
 for p in c['points']:
  for g in p['anchors']:
   for a in g:
    if a['final'] is not None and a['final']<=8:continue
    a, points=anchors.setdefault(a['id'],(a,[]))
    points.append(p['id'])
 for k,(a,points) in anchors.items():
  paper=k.split('_')[0]
  print(k,','.join(points),reason(a),str(a['shortlisted'])+'/'+str(c['top8_papers'].count(paper)),a['hybrid'],a['ce'],a['final'],sep=' | ')
