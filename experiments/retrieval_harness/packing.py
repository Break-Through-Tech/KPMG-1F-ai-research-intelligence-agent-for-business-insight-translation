"""Query-only packing ablations; source units remain atomic and traceable."""
import numpy as np
from experiments.retrieval_harness.harness import terms, source_units, context


def protect_dense(hybrid, dense, limit=3):
    """Reserve first three positions for dense hits, then retain hybrid order."""
    first=list(map(int,np.argsort(-np.asarray(dense),kind='stable')[:limit]))
    order=first+[int(i) for i in np.argsort(-np.asarray(hybrid),kind='stable') if int(i) not in first]
    scores=np.empty(len(order));scores[order]=np.arange(len(order),0,-1)
    return scores


def windows(chunks, blocks, query, count, cap=160):
    """Best query-term contiguous unit window per seed, or original if atomic.

    This is extractive lexical selection, not entailment. Never split a source
    sentence/math unit to satisfy a cap. No targets or answer labels accepted.
    """
    result=[];qt=set(terms(query))
    for c in chunks:
        if count(c['text'])<=cap:
            result.append(dict(c));continue
        text=blocks[c['block']]['text']
        spans=[(a,b) for a,b in source_units(text,blocks[c['block']]['source']=='tex') if c['start']<=a<b<=c['end']]
        candidates=[]
        for i,(a,b) in enumerate(spans):
            for _,z in spans[i:]:
                n=count(text[a:z])
                if n>cap:break
                candidates.append((len(qt & set(terms(text[a:z]))),-n,-a,a,z))
        if candidates:
            *_,a,b=max(candidates);result.append(dict(c,start=a,end=b,text=text[a:b]))
        else:result.append(dict(c))
    return result


def pack(chunks,scores,blocks,count,query,budget,*,dense=None,compact=False):
    if dense is not None:scores=protect_dense(scores,dense)
    if compact:chunks=windows(chunks,blocks,query,count)
    return context(chunks,scores,blocks,count,query,arm='deduplication',budget=budget)
