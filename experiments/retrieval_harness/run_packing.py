"""Fixed follow-up to inspected misses; not held-out policy selection."""
import argparse,json,hashlib
from pathlib import Path
from functools import lru_cache
import numpy as np
from transformers import AutoTokenizer
from experiments.retrieval_harness.harness import fuse,lexical_scores
from experiments.retrieval_harness.packing import pack,windows
from experiments.semantic_calibration.run import norm,MODELS

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--corpus',type=Path,required=True);ap.add_argument('--cache',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    corpus=json.loads(args.corpus.read_text());digest=hashlib.sha256(args.corpus.read_bytes()).hexdigest()
    qs=[q for q in corpus['questions'] if q['paper'] in corpus['common_papers']]
    name,rev=MODELS['e5'];tok=AutoTokenizer.from_pretrained(str(Path.home()/'.cache/huggingface/hub'/('models--'+name.replace('/','--'))/'snapshots'/rev),local_files_only=True)
    @lru_cache(maxsize=100000)
    def count(t):return len(tok.encode('passage: '+t,add_special_tokens=True,truncation=False))
    summary=[];outcomes=[]
    for source in ('html','tex','pdf'):
        cache=args.cache/'e5'/source;receipt=json.loads((cache/'report.json').read_text());assert receipt['corpus_sha256']==digest and receipt['revision']==rev
        chunks=json.loads((cache/'variants.json').read_text())['original'];texts=json.loads((cache/'chunk-texts.json').read_text());lookup={t:i for i,t in enumerate(texts)}
        v=np.load(cache/'chunk-vectors.npy')[[lookup[c['text']] for c in chunks]];qv=np.load(cache/'query-vectors.npy');assert len(qv)==len(qs)
        blocks={b['id']:b for b in corpus['blocks'] if b['source']==source and b['paper'] in corpus['common_papers']};rows=[]
        for qi,q in enumerate(qs):
            dense=qv[qi]@v.T;hybrid=fuse(dense,lexical_scores([c['text'] for c in chunks],q['query']))
            compact_chunks=windows(chunks,blocks,q['query'],count)
            for arm,protect,compact in [('hybrid',False,False),('protected',True,False),('compact',False,True),('protected_compact',True,True)]:
                for budget in (800,1600):
                    r=pack(compact_chunks if compact else chunks,hybrid,blocks,count,q['query'],budget,dense=dense if protect else None)
                    for e in r['evidence']:
                        assert e['text']==blocks[e['block']]['text'][e['start']:e['end']]
                        assert e['location']['source_url']==blocks[e['block']]['location']['source_url']
                    assert r['tokens']<=budget
                    found=[any(e['paper']==q['paper'] and norm(a) in norm(e['text']) for e in r['evidence']) for a in q['anchors']]
                    rows.append(dict(id=q['id'],split=corpus['split'][q['paper']],arm=arm,budget=budget,found=found,complete=all(found),**r))
        (args.output/(source+'-contexts.json')).write_text(json.dumps(rows))
        for arm in ('hybrid','protected','compact','protected_compact'):
            for budget in (800,1600):
                for split in ('tuning','validation'):
                    rr=[r for r in rows if (r['arm'],r['budget'],r['split'])==(arm,budget,split)]
                    summary.append(dict(source=source,arm=arm,budget=budget,split=split,questions=len(rr),complete=sum(r['complete'] for r in rr),mean_tokens=round(float(np.mean([r['tokens'] for r in rr])),2)))
        outcomes.extend(dict(source=source,**{k:v for k,v in r.items() if k!='evidence'}) for r in rows)
        print('FINISHED',source,flush=True)
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2));(args.output/'outcomes.json').write_text(json.dumps(outcomes))
    protocol=dict(corpus_sha256=digest,model=name,revision=rev,protected_dense_hits=3,window_token_cap=160,budgets=[800,1600],candidate_limit=200,notes=['Retrospective development follow-up; no blind testing or generated-answer scoring.','Extractive lexical windows; whole atomic units only; all arms deduplicate intervals.','Compact windows chosen upfront for all oversize seeds, not only after budget exhaustion.','No relevance targets or anchors available to packing.'])
    (args.output/'protocol.json').write_text(json.dumps(protocol,indent=2))
    print(json.dumps([r for r in summary if r['split']=='validation'],indent=2))
if __name__=='__main__':main()
