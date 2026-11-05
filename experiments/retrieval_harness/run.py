"""Run fixed, predeclared retrieval policies on cached E5 vectors."""
import argparse
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import time
import numpy as np
from experiments.retrieval_harness.harness import ARMS,context,fuse,lexical_scores,terms
from experiments.semantic_calibration.run import MODELS,norm
from experiments.semantic_calibration.policies import units
from src.semantic_chunking_adapter import EmbeddingAdapter


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--corpus',type=Path,required=True)
    ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
    from sentence_transformers import SentenceTransformer
    name,rev=MODELS['e5']
    encoder=SentenceTransformer(str(Path.home()/'.cache/huggingface/hub'/('models--'+name.replace('/','--'))/'snapshots'/rev),local_files_only=True,device='mps')
    model=EmbeddingAdapter(encoder,name)
    @lru_cache(maxsize=200000)
    def count(t):
        return len(encoder.tokenizer.encode(model.passage_prefix+t,add_special_tokens=True,truncation=False))
    corpus=json.loads(args.corpus.read_text());common=set(corpus['common_papers'])
    qs=[dict(q,split=corpus['split'][q['paper']]) for q in corpus['questions'] if q['paper'] in common]
    protocol=dict(model=name,revision=rev,arms=ARMS,budgets=[800,1600],candidate_limit=200,rerank_candidates=40,
                  corpus_sha256=hashlib.sha256(args.corpus.read_bytes()).hexdigest(),chunk_policy='original',
                  notes=['Already inspected development questions. No blind evaluation or answer-quality claim.',
                         'Reranker is E5 sentence-max late interaction, NOT a cross-encoder.',
                         'Query decomposition is deterministic clause splitting; gap search uses residual query terms.',
                         'Source-aware arm snaps to sentences/atomic TeX spans within original source blocks.',
                         'Isolated arms modify baseline independently. Combined composes all eight. No selection or tuning.'])
    (args.output/'protocol.json').write_text(json.dumps(protocol,indent=2))
    summary=[]
    for source in ('html','tex','pdf'):
        start=time.monotonic();cache=args.cache/'e5'/source
        previous=json.loads((cache/'report.json').read_text())
        assert previous['revision']==rev and previous['corpus_sha256']==protocol['corpus_sha256']
        chunks=json.loads((cache/'variants.json').read_text())['original']
        texts=json.loads((cache/'chunk-texts.json').read_text());lookup={t:i for i,t in enumerate(texts)}
        vectors=np.load(cache/'chunk-vectors.npy')[[lookup[c['text']] for c in chunks]]
        qvectors=np.load(cache/'query-vectors.npy');assert len(qvectors)==len(qs)
        blocks={b['id']:b for b in corpus['blocks'] if b['source']==source and b['paper'] in common}
        dense=qvectors@vectors.T
        # Encode sentences for bounded candidate-pool reranking, once per format.
        pool=set(int(i) for row in dense for i in np.argsort(-row,kind='stable')[:40])
        sentence_map={i:[chunks[i]['text'][a:b] for a,b in units(chunks[i]['text'],tex=source=='tex')] for i in pool}
        sentence_texts=list(dict.fromkeys(t for ss in sentence_map.values() for t in ss))
        sv=model.encode_passages(sentence_texts,batch_size=32,show_progress_bar=False)
        si={t:i for i,t in enumerate(sentence_texts)}
        clause_texts=[];clause_indexes=[]
        for q in qs:
            clauses=[c.strip() for c in re.split(r'\band\b|\bor\b|[,;?]',q['query']) if len(terms(c))>=2] or [q['query']]
            clause_indexes.append(list(range(len(clause_texts),len(clause_texts)+len(clauses))));clause_texts+=clauses
        cv=model.encode_queries(clause_texts,batch_size=32,show_progress_bar=False)
        rows=[]
        for qi,q in enumerate(qs):
            sparse=lexical_scores([c['text'] for c in chunks],q['query']);hybrid=fuse(dense[qi],sparse)
            rerank=dense[qi].copy()-10
            for i in np.argsort(-dense[qi],kind='stable')[:40]:
                rerank[i]=.5*dense[qi,i]+.5*max(float(sv[si[t]]@qvectors[qi]) for t in sentence_map[int(i)])
            question_scores=np.max(cv[clause_indexes[qi]]@vectors.T,axis=0)
            heading=lexical_scores([' '.join(str(v) for k,v in blocks[c['block']]['location'].items() if k in ('section','subsection','source_file')) for c in chunks],q['query'])
            available=all(any(norm(a) in norm(b['text']) for b in blocks.values() if b['paper']==q['paper']) for a in q['anchors'])
            for arm in ARMS:
                scores={'hybrid_search':hybrid,'reranking':rerank,'question_aware':question_scores,
                        'source_aware':fuse(dense[qi],heading) if heading.max()>0 else dense[qi],
                        'combined':fuse(fuse(fuse(hybrid,rerank),question_scores),heading) if heading.max()>0 else fuse(fuse(hybrid,rerank),question_scores)}.get(arm,dense[qi])
                for budget in (800,1600):
                    result=context(chunks,scores,blocks,count,q['query'],arm=arm,budget=budget,vectors=vectors)
                    found=[any(e['paper']==q['paper'] and norm(a) in norm(e['text']) for e in result['evidence']) for a in q['anchors']]
                    rows.append(dict(id=q['id'],split=q['split'],arm=arm,budget=budget,found=found,complete=all(found),available=available,**result))
        (args.output/(source+'-contexts.json')).write_text(json.dumps(rows,ensure_ascii=False))
        for arm in ARMS:
            for budget in (800,1600):
                for split in ('tuning','validation'):
                    rr=[r for r in rows if (r['arm'],r['budget'],r['split'])==(arm,budget,split)]
                    summary.append(dict(source=source,arm=arm,budget=budget,split=split,questions=len(rr),complete=sum(r['complete'] for r in rr),available=sum(r['available'] for r in rr),mean_tokens=round(np.mean([r['tokens'] for r in rr]),2)))
        print('FINISHED',source,round(time.monotonic()-start,1),flush=True)
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
    lines=['# Retrieval harness: eight isolated experiments','', 'Fixed E5, original semantic chunks, 19 matched papers / 38 previously inspected development questions. Counts are exact designated-span coverage, not answer accuracy. No tuning or winner selection.','', '| Arm | HTML 800 / 1600 | TeX 800 / 1600 | PDF 800 / 1600 |','| --- | --- | --- | --- |']
    for arm in ARMS:
        cells=[]
        for source in ('html','tex','pdf'):
            cells.append(' / '.join(str(next(r['complete'] for r in summary if (r['arm'],r['source'],r['budget'],r['split'])==(arm,source,b,'validation'))) for b in (800,1600)))
        lines.append('| '+arm+' | '+' | '.join(cells)+' |')
    lines+=['','Each score is out of 18 validation questions. PDF has designated anchors available for only 16; HTML/TeX for all 18. Retrieval never reads paper targets, anchors, or split labels. Full source-backed contexts retained outside Git; summaries and hashes committed.']
    (args.output/'SUMMARY.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
