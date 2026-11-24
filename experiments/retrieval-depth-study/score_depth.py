import os
import json, math, statistics as s
from pathlib import Path
data=json.loads(Path('b2-adaptive-packets.json').read_text())
refs={r['id']:r['required_points'] for r in json.loads((Path(os.environ['B2_RESEARCH_ROOT']) / 'experiments/completion-eval-v1/references.json').read_text(encoding='utf8'))}
cases=[r for r in data if r['id'] in refs]
def points(r,k):
 ids=set(r['ids'][:k])
 return {p['point_id'] for p in refs[r['id']] if any(set(g)<=ids for g in p['anchors'])}
def p90(xs): return sorted(xs)[math.ceil(.9*len(xs))-1]
print('cases',len(cases),'shared retrieval seconds med/p90',s.median(r['seconds'] for r in cases),p90([r['seconds'] for r in cases]))
print('mode | points | full | avg/max k | tokens med/p90 | expansions/no gain | premature (queries/points) | rule ms med/p90')
for arm in cases[0]['arms']:
 a=[r['arms'][arm] for r in cases]; hits=[points(r,x['k']) for r,x in zip(cases,a)]
 expanded=[(r,x,h) for r,x,h in zip(cases,a,hits) if x['k']>8]
 missed=[points(r,30)-h for r,h in zip(cases,hits)]
 print(arm,sum(map(len,hits)),sum(len(h)==len(refs[r['id']]) for r,h in zip(cases,hits)),
 round(s.mean(x['k'] for x in a),2),max(x['k'] for x in a),s.median(x['tokens'] for x in a),p90([x['tokens'] for x in a]),
 len(expanded),sum(h==points(r,8) for r,x,h in expanded),sum(bool(m) for m in missed),sum(map(len,missed)),
 round(s.median(x['ms'] for x in a),4),round(p90([x['ms'] for x in a]),4))
for r in data:
 if r['id'] in refs:
  print(r['id'],r['facets'],{m:(x['k'],len(points(r,x['k']))) for m,x in r['arms'].items()})
 else:print(r['id'],{m:(x['k'],x['tokens']) for m,x in r['arms'].items()})
print('over token cap (fixed 30)',[r['id'] for r in cases if r['arms']['30']['tokens']>8000])
print('adaptive trims',[(r['id'],m,x['intent'],x['k']) for r in cases for m,x in r['arms'].items() if x['k']<x['intent']])
