import os
import json,sys
from pathlib import Path
ns={}
exec(Path('compare_selection.py').read_text(encoding='utf8').split('output=[]')[0],ns)
d=ns['d']; rows=json.loads((d/'experiments/measure/end-to-end-diagnostic/results.json').read_text(encoding='utf8'))['historical']
results=[]
for name in ('agreemate','CU-DPO','Willow'):
 item=next(x for x in rows if x['id']==name)
 query=item['question']; sys.setprofile(ns['trace'])
 try: ns['ret'](query,8)
 finally: sys.setprofile(None)
 a=ns['seen']; sel={'A':a['order'][:8],'B':a['order'][:16]}
 sel.update({mode:ns['choose'](a,query,mode) for mode in 'CD'})
 results.append({'id':name,'packets':sel})
Path('b2-selection-controls.json').write_text(json.dumps(results,indent=2))
