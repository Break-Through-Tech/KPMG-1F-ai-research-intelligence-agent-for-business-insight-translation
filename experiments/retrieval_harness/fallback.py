"""Additive, query-only semantic fallback; never evicts incumbent evidence."""
from copy import deepcopy
import numpy as np
from experiments.semantic_calibration.policies import merge_intervals


def fill(base, candidates, blocks, count, budget):
    """Candidates contain source-unit offsets and query cosine, never labels.

    Preserve full incumbent passages; fill only remaining space. Whole units,
    including atomic TeX math, are never clipped. No minimum relevance claim.
    """
    result=deepcopy(base)
    selected={}
    for e in base['evidence']:
        selected.setdefault(e['block'], []).append((e['start'],e['end']))
    added=0
    for c in sorted(candidates,key=lambda c:(-c['score'],c['rank'],c['start'])):
        k,a,b=c['block'],c['start'],c['end']
        text=blocks[k]['text']
        if not 0<=a<b<=len(text) or not np.isfinite(c['score']):
            raise ValueError('Invalid fallback candidate')
        trial={key:list(spans) for key,spans in selected.items()}
        trial[k]=merge_intervals(trial.get(k,[])+[(a,b)],text)
        cost=sum(count(blocks[key]['text'][x:y]) for key,spans in trial.items() for x,y in spans)
        if trial!=selected and cost<=budget:
            selected=trial;added+=1
    evidence=[]
    for k,spans in selected.items():
        block=blocks[k]
        for a,b in spans:
            body=block['text'][a:b];loc=dict(block['location'])
            if block['source']=='tex':
                loc['line_start']+=block['text'].count('\n',0,a)
                loc['line_end']=loc['line_start']+body.count('\n')
            evidence.append(dict(block=k,start=a,end=b,text=body,paper=block['paper'],source=block['source'],location=loc))
    result.update(evidence=evidence,tokens=sum(count(e['text']) for e in evidence),fallback_additions=added)
    assert result['tokens']<=budget
    return result
