"""Query-only packing ablations; source units remain atomic and traceable."""
import numpy as np
from functools import lru_cache
from experiments.retrieval_harness.harness import terms, source_units, context


def protect_dense(hybrid, dense, limit=3):
    """Reserve first three positions for dense hits, then retain hybrid order."""
    first=list(map(int,np.argsort(-np.asarray(dense),kind='stable')[:limit]))
    order=first+[int(i) for i in np.argsort(-np.asarray(hybrid),kind='stable') if int(i) not in first]
    scores=np.empty(len(order));scores[order]=np.arange(len(order),0,-1)
    return scores


@lru_cache(maxsize=12000)
def _candidates(text,start,end,tex,count,cap):
    spans=[(a,b) for a,b in source_units(text,tex) if start<=a<b<=end]
    candidates=[]
    for i,(a,b) in enumerate(spans):
        for _,z in spans[i:]:
            n=count(text[a:z])
            if n>cap:break
            candidates.append((frozenset(terms(text[a:z])),n,a,z))
    return candidates


def windows(chunks, blocks, query, count, cap=160):
    """Choose a query-term window; cache query-independent unit candidates.

    Never split source sentences/math to satisfy the cap. This is extractive
    lexical matching, not entailment. No targets or answer labels accepted.
    """
    result=[];qt=set(terms(query))
    for c in chunks:
        if count(c['text'])<=cap:
            result.append(dict(c));continue
        text=blocks[c['block']]['text']
        candidates=_candidates(text,c['start'],c['end'],blocks[c['block']]['source']=='tex',count,cap)
        if candidates:
            # Prefer earlier offsets on equal coverage and cost.
            _,_,_,a,b=max((len(qt & ts),-n,-a,a,z) for ts,n,a,z in candidates)
            result.append(dict(c,start=a,end=b,text=text[a:b]))
        else:result.append(dict(c))
    return result


def pack(chunks,scores,blocks,count,query,budget,*,dense=None,compact=False):
    if dense is not None:scores=protect_dense(scores,dense)
    if compact:chunks=windows(chunks,blocks,query,count)
    return context(chunks,scores,blocks,count,query,arm='deduplication',budget=budget)
