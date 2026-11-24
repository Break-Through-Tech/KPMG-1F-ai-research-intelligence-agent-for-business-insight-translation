import os
import json,time
from pathlib import Path
from transformers import AutoTokenizer
root=Path(os.environ['B2_ENCODER'])
tok=AutoTokenizer.from_pretrained(root,local_files_only=True)
cases=json.loads(Path('b2-c01-c15-trace.json').read_text())['cases']
needed={i for case in cases for i in case['top30']}
data=(Path(os.environ['B2_BUNDLE']) / 'parents.jsonl')
parents={p['chunk_id']:p['text'] for line in data.open(encoding='utf8') if (p:=json.loads(line))['chunk_id'] in needed}
result=[]
for c in cases:
 start=time.perf_counter();sizes=[len(tok(parents[k],add_special_tokens=True,truncation=False,verbose=False)['input_ids']) for k in c['top30']]
 result.append({'id':c['id'],'ids':c['top30'],'sizes':sizes,'ms':(time.perf_counter()-start)*1000})
Path('b2-token-lengths.json').write_text(json.dumps(result,indent=2))
