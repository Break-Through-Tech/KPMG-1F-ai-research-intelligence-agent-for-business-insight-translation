"""Offline retrieval-only experiments. Never reads relevance labels or writes indexes."""
import re
from functools import lru_cache
import numpy as np
from experiments.semantic_calibration.policies import merge_intervals
from experiments.semantic_calibration.policies import units

STOP = set('a an the of in on to for and or is are does do how what why which can with by from it its that this as be when'.split())
ARMS = ['baseline', 'selective_expansion', 'budget_allocation', 'deduplication',
        'hybrid_search', 'reranking', 'question_aware', 'evidence_gap', 'source_aware', 'combined']


@lru_cache(maxsize=100000)
def source_units(text, tex):
    return units(text, tex=tex)


def terms(text):
    return [t for t in re.findall(r'[\w-]+', text.lower()) if t not in STOP and len(t)>1]


def lexical_scores(texts, query):
    """BM25 with fixed k1=1.2, b=.75; no corpus relevance labels."""
    from collections import Counter
    docs = [Counter(terms(t)) for t in texts]
    lengths = np.array([sum(d.values()) for d in docs])
    avg = max(float(lengths.mean()), 1)
    result = np.zeros(len(docs))
    for term in set(terms(query)):
        tf = np.array([d[term] for d in docs])
        df = np.count_nonzero(tf)
        result += np.log(1+(len(docs)-df+.5)/(df+.5))*tf*2.2/(tf+1.2*(.25+.75*lengths/avg))
    return result


def fuse(dense, sparse):
    out = np.zeros(len(dense))
    for scores in (dense, sparse):
        order = np.argsort(-scores, kind='stable')
        out[order] += 1/(60+np.arange(1,len(order)+1))
    return out


def context(chunks, scores, blocks, count, query, *, arm, budget=1600, vectors=None):
    if arm not in ARMS or budget <= 0:
        raise ValueError('Invalid arm or budget')
    if len(scores)!=len(chunks) or not np.isfinite(scores).all():
        raise ValueError('Invalid retrieval scores')
    if any(not 0 <= c['start'] < c['end'] <= len(blocks[c['block']]['text']) for c in chunks):
        raise ValueError('Invalid source offsets')
    enabled = lambda name: arm in (name, 'combined')
    order = list(map(int,np.argsort(-np.asarray(scores),kind='stable')[:200]))
    selected, raw, accepted, skipped = {}, [], [], 0
    seen_terms = set()
    # A simple MMR allocator balances query rank with novel evidence, not labels.
    if enabled('budget_allocation') and vectors is None:
        raise ValueError('MMR requires vectors')
    while order:
        if enabled('budget_allocation') and accepted:
            scale = max(float(np.max(np.abs(scores))), 1e-12)
            relevance = {idx:float(scores[idx])/scale for idx in order}
            idx = max(order,key=lambda j: .7*relevance[j]-.3*max(float(vectors[j]@vectors[k]) for k in accepted))
            order.remove(idx)
        elif enabled('evidence_gap') and len(accepted)==3:
            # One bounded second pass: residual QUERY terms, never gold anchors.
            missing = set(terms(query))-seen_terms
            order.sort(key=lambda j: -len(missing & set(terms(chunks[j]['text']))))
            idx = order.pop(0)
        else:
            idx = order.pop(0)
        c=chunks[idx]; key=c['block']; text=blocks[key]['text']
        a,b=c['start'],c['end']
        if enabled('selective_expansion') or enabled('source_aware'):
            spans=source_units(text,blocks[key]['source']=='tex')
            intersect=[(x,y) for x,y in spans if x<b and y>a]
            if enabled('source_aware') and intersect:
                # Whole source sentences / atomic TeX math, never fabricate offsets.
                a,b=min(a,intersect[0][0]),max(b,intersect[-1][1])
            if enabled('selective_expansion'):
                neighbors=[(x,y) for x,y in spans if y<=a][-1:]+[(x,y) for x,y in spans if x>=b][:1]
                for x,y in neighbors:
                    # Deterministic query-term affinity; no claim of entailment.
                    if set(terms(query)) & set(terms(text[x:y])) and count(text[min(a,x):max(b,y)])<=400:
                        a,b=min(a,x),max(b,y)
        candidate={k:list(v) for k,v in selected.items()}
        candidate[key]=merge_intervals(candidate.get(key,[])+[(a,b)],text)
        trial=raw+[(key,a,b)]
        dedup=enabled('deduplication')
        evidence=[(k,x,y) for k,intervals in candidate.items() for x,y in intervals] if dedup else trial
        cost=sum(count(blocks[k]['text'][x:y]) for k,x,y in evidence)
        if cost>budget:
            skipped+=1
            continue
        if dedup and candidate==selected:
            continue
        selected=candidate;raw=trial;accepted.append(idx)
        seen_terms.update(terms(text[a:b]))
    evidence=[(k,a,b) for k,intervals in selected.items() for a,b in intervals] if enabled('deduplication') else raw
    receipts=[]
    for k,a,b in evidence:
        block=blocks[k];loc=dict(block['location']);body=block['text'][a:b]
        if block['source']=='tex':
            loc['line_start']+=block['text'].count('\n',0,a)
            loc['line_end']=loc['line_start']+body.count('\n')
        receipts.append(dict(block=k,start=a,end=b,text=body,paper=block['paper'],source=block['source'],location=loc))
    assert sum(count(e['text']) for e in receipts)<=budget
    return dict(evidence=receipts,tokens=sum(count(e['text']) for e in receipts),seeds=len(accepted),skipped=skipped)
