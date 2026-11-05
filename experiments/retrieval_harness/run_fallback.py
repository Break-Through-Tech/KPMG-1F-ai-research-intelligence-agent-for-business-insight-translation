"""Retrospective fixed semantic fallback experiment, no policy tuning."""
import argparse,json,hashlib,os
from pathlib import Path
from functools import lru_cache
import numpy as np
from experiments.retrieval_harness.harness import context,fuse,lexical_scores,source_units
from experiments.retrieval_harness.fallback import fill
from experiments.semantic_calibration.run import MODELS,norm
from src.semantic_chunking_adapter import EmbeddingAdapter


def main():
    p=argparse.ArgumentParser()
    for arg in ('corpus','cache','output'):p.add_argument('--'+arg,type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
    import torch
    torch.set_num_threads(4)
    from sentence_transformers import SentenceTransformer
    name,rev=MODELS['e5'];model=SentenceTransformer(str(Path.home()/'.cache/huggingface/hub'/('models--'+name.replace('/','--'))/'snapshots'/rev),local_files_only=True,device='mps');adapter=EmbeddingAdapter(model,name)
    @lru_cache(maxsize=200000)
    def count(t):return len(model.tokenizer.encode('passage: '+t,add_special_tokens=True,truncation=False))
    corpus=json.loads(args.corpus.read_text());digest=hashlib.sha256(args.corpus.read_bytes()).hexdigest()
    qs=[q for q in corpus['questions'] if q['paper'] in corpus['common_papers']];summary=[];outcomes=[];intervals=0
    for source in ('html','tex','pdf'):
        cache=args.cache/'e5'/source;receipt=json.loads((cache/'report.json').read_text());assert receipt['corpus_sha256']==digest and receipt['revision']==rev
        chunks=json.loads((cache/'variants.json').read_text())['original'];texts=json.loads((cache/'chunk-texts.json').read_text());lookup={t:i for i,t in enumerate(texts)}
        v=np.load(cache/'chunk-vectors.npy')[[lookup[c['text']] for c in chunks]];qv=np.load(cache/'query-vectors.npy')
        assert [q['id'] for q in qs]==[q['id'] for q in receipt['variants']['original']['queries']['tokens1600']]
        blocks={b['id']:b for b in corpus['blocks'] if b['source']==source and b['paper'] in corpus['common_papers']}
        rankings=[];unitmaps=[];alltexts={}
        for qi,q in enumerate(qs):
            scores=fuse(qv[qi]@v.T,lexical_scores([c['text'] for c in chunks],q['query']));rankings.append(scores);candidates=[]
            for rank,idx in enumerate(np.argsort(-scores,kind='stable')[:40],1):
                c=chunks[int(idx)];text=blocks[c['block']]['text']
                for a,b in source_units(text,source=='tex'):
                    if c['start']<=a<b<=c['end'] and count(text[a:b])<=160:
                        candidates.append(dict(block=c['block'],start=a,end=b,rank=rank));alltexts[text[a:b]]=None
            unitmaps.append(candidates)
        unique=list(alltexts);sv=adapter.encode_passages(unique,batch_size=32,show_progress_bar=False);si={t:i for i,t in enumerate(unique)};rows=[]
        for qi,q in enumerate(qs):
            candidates=[dict(c,score=float(sv[si[blocks[c['block']]['text'][c['start']:c['end']]]]@qv[qi])) for c in unitmaps[qi]]
            for budget in (800,1600):
                base=context(chunks,rankings[qi],blocks,count,q['query'],arm='deduplication',budget=budget)
                fallback=fill(base,candidates,blocks,count,budget)
                for e in base['evidence']:
                    assert any(f['block']==e['block'] and f['start']<=e['start'] and f['end']>=e['end'] for f in fallback['evidence'])
                for arm,r in (('hybrid',base),('semantic_fallback',fallback)):
                    assert r['tokens']==sum(count(e['text']) for e in r['evidence'])<=budget
                    for e in r['evidence']:
                        b=blocks[e['block']];assert e['text']==b['text'][e['start']:e['end']]
                        loc=dict(b['location'])
                        if source=='tex':loc['line_start']+=b['text'].count('\n',0,e['start']);loc['line_end']=loc['line_start']+e['text'].count('\n')
                        assert e['location']==loc;intervals+=1
                    found=[any(e['paper']==q['paper'] and norm(a) in norm(e['text']) for e in r['evidence']) for a in q['anchors']]
                    rows.append(dict(id=q['id'],split=corpus['split'][q['paper']],arm=arm,budget=budget,found=found,complete=all(found),**r))
        (args.output/(source+'-contexts.json')).write_text(json.dumps(rows))
        for arm in ('hybrid','semantic_fallback'):
            for budget in (800,1600):
                for split in ('tuning','validation'):
                    rr=[r for r in rows if (r['arm'],r['budget'],r['split'])==(arm,budget,split)]
                    summary.append(dict(source=source,arm=arm,budget=budget,split=split,questions=len(rr),complete=sum(r['complete'] for r in rr),mean_tokens=round(float(np.mean([r['tokens'] for r in rr])),2)))
        outcomes.extend(dict(source=source,**{k:v for k,v in r.items() if k!='evidence'}) for r in rows);print('FINISHED',source,flush=True)
    for filename,data in [('summary.json',summary),('outcomes.json',outcomes),('verification.json',dict(status='passed',contexts=len(outcomes),intervals=intervals,checks=['incumbent evidence retained','exact source and locator parity','token caps','scores recomputed'])) ,('protocol.json',dict(corpus_sha256=digest,model=name,revision=rev,candidate_pool=40,unit_token_cap=160,budgets=[800,1600],policy='Preserve full hybrid packing, then append whole units by query cosine; no eviction or gold labels.',limits=['Inspected development data; not blind or answer accuracy.','Extra semantic encoding cost; latency not benchmarked.','Atomic oversized units excluded; no minimum cosine threshold.']))]:
        (args.output/filename).write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps([s for s in summary if s['split']=='validation']))
if __name__=='__main__':main()
