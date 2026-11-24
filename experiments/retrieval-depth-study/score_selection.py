import os
import json,statistics
from pathlib import Path
from collections import Counter
d=Path(os.environ['B2_RESEARCH_ROOT'])
refs={q['id']:q for q in json.loads((d/'experiments/completion-eval-v1/references.json').read_text(encoding='utf8'))}
rows=json.loads(Path('b2-selection-packets.json').read_text())
def hit(r,mode):
 ids=set(r[mode]['ids']); return {p['point_id'] for p in refs[r['id']]['required_points'] if any(set(g)<=ids for g in p['anchors'])}
for mode in 'ABCD':
 got=[hit(r,mode) for r in rows]
 added=[x-hit(r,'A') for x,r in zip(got,rows)]
 lost=[hit(r,'A')-x for x,r in zip(got,rows)]
 print(mode,'anchors',sum(map(len,got)),'complete',sum(len(x)==len(refs[r['id']]['required_points']) for x,r in zip(got,rows)))
 print('gain',sorted(set().union(*added)),'loss',sorted(set().union(*lost)))
 print('tokens median',statistics.median(r[mode]['tokens'] for r in rows),'offref slots',sum(sum(p not in {x['paper'] for x in refs[r['id']]['required_points']} for p in r[mode]['papers']) for r in rows),'slots',sum(len(r[mode]['ids']) for r in rows),'repeated pairs',sum(r[mode]['redundant_pairs'] for r in rows))
 if mode in 'CD': print('ms median max',statistics.median(r[mode]['ms'] for r in rows),max(r[mode]['ms'] for r in rows),'peak traced KiB',max(r[mode]['peak_py_bytes'] for r in rows)/1024)
for r in rows:
 print(r['id'],[len(hit(r,m)) for m in 'ABCD'])
 if r['id'] in ('C07','C08','C14','C15'):
  for m in 'ABCD': print(m,dict(Counter(r[m]['papers'])),sorted(hit(r,m)))
