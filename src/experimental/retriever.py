"""Isolated generic retrieval experiment. No benchmark access or generation."""
from collections import Counter,defaultdict
from copy import deepcopy
import re,math
import numpy as np

STOP=set('a an the what how do does did are is of in on for to and or with before after should used use it its that as by from at be can could would which each these those our study paper research according between under get result results'.split())
def tokens(text):
    words=re.findall(r'[a-z]+[a-z0-9]*|[0-9]+(?:\.[0-9]+)*',text.lower().replace(',',''))
    result=[]
    for w in words:
        if w in STOP:continue
        if len(w)>6 and w.endswith('ing'):w=w[:-3]
        elif len(w)>5 and w.endswith('ed'):w=w[:-2]
        elif len(w)>4 and w.endswith('s') and not w.endswith('ss'):w=w[:-1]
        result.append(w)
    return result

class Lexical:
    def __init__(self,texts):
        self.counts=[Counter(tokens(t)) for t in texts];self.lengths=np.array([sum(c.values()) for c in self.counts]);self.avg=max(1,float(self.lengths.mean()))
        self.postings=defaultdict(list)
        for i,c in enumerate(self.counts):
            for term,n in c.items():self.postings[term].append((i,n))
        self.idf={term:math.log(1+(len(texts)-len(xs)+.5)/(len(xs)+.5)) for term,xs in self.postings.items()}
    def score(self,query):
        out=np.zeros(len(self.counts))
        for term in set(tokens(query)):
            for i,n in self.postings.get(term,[]):out[i]+=self.idf[term]*n*2.2/(n+1.2*(.25+.75*self.lengths[i]/self.avg))
        return out

class Retriever:
    def __init__(self,index,reranker=None):
        self.index=index;self.parents=index.parents;self.views=index.views;self.reranker=reranker
        self.byid={p['chunk_id']:p for p in self.parents};self.pidx={p['chunk_id']:i for i,p in enumerate(self.parents)}
        self.byview=defaultdict(list);self.bydoc=defaultdict(list);self.tables=defaultdict(list)
        for i,v in enumerate(self.views):self.byview[v['parent_chunk_id']].append(i)
        for p in self.parents:
            self.bydoc[p['arxiv_id']].append(p['chunk_id'])
            if p.get('table_id'):self.tables[(p['arxiv_id'],p['table_id'])].append(p['chunk_id'])
        texts=[]
        for p in self.parents:
            if p.get('table_id'):
                body='; '.join(h['text']+': '+c['text'] for h,c in zip(p['table_headers'],p['table_cells']))
                text=p['title']+' '+p.get('section','')+' '+p['caption']+' '+body
            else:text=p['title']+' '+p.get('section','')+' '+p['text']
            texts.append(text)
        self.lex=Lexical(texts)
        self.content={p['chunk_id']:set(tokens(p['row_label'] if p.get('table_id') else p['text'])) for p in self.parents}

    def rank(self,query,qv,*,with_reranker=True):
        ds=np.sum((self.index.vectors-qv)**2,axis=1);best={}
        for i,(v,d) in enumerate(zip(self.views,ds)):
            ident=v['parent_chunk_id'];key=(float(d),v['view_id'])
            if ident not in best or key<best[ident][0]:best[ident]=(key,i)
        dense=sorted(best,key=lambda i:(best[i][0][0],i));dr={i:n for n,i in enumerate(dense,1)}
        ls=self.lex.score(query);lexical=sorted((p['chunk_id'] for n,p in enumerate(self.parents) if ls[n]>0),key=lambda i:(-ls[self.pidx[i]],i));lr={i:n for n,i in enumerate(lexical,1)}
        # Score papers by their best dense and lexical evidence, avoiding a
        # sum over all rows that would favor documents with more tables.
        docscore={doc:1/(60+min(dr[i] for i in ids))+1/(60+min((lr.get(i,10**6) for i in ids))) for doc,ids in self.bydoc.items()}
        docs=sorted(docscore,key=lambda d:(-docscore[d],d))[:3]
        pool=set(dense[:60]+lexical[:60])
        for doc in docs:
            ids=self.bydoc[doc]
            pool.update(sorted(ids,key=lambda i:(-ls[self.pidx[i]],i))[:20])
            pool.update(sorted(ids,key=lambda i:(dr[i],i))[:20])
        qwords=tokens(query);bigrams=set(zip(qwords,qwords[1:]))
        def phrases(text):
            ws=tokens(text);return len(bigrams.intersection(zip(ws,ws[1:])))/max(1,len(bigrams))
        def fused(i):
            p=self.byid[i]
            return (1/(60+dr[i])+1/(60+lr.get(i,10**6))+.25*docscore[p['arxiv_id']]
                    +.006*phrases(p.get('caption',p['text'])))
        discovery=sorted(pool,key=lambda i:(-fused(i),i))
        # Expand promising tables as groups before row selection. This does not
        # combine or rewrite evidence: every returned row stays independently citable.
        groups=[]
        for i in discovery[:30]:
            p=self.byid[i];g=(p['arxiv_id'],p.get('table_id'))
            if g[1] and g not in groups:groups.append(g)
        for g in groups[:8]:pool.update(self.tables[g])
        discovery=sorted(pool,key=lambda i:(-fused(i),i))
        routes={'document_hybrid':discovery};details={'candidate_count':len(pool),'paper_candidates':docs}
        if not with_reranker or self.reranker is None:return routes,details
        candidates=discovery[:60];pairs=[];owners=[]
        for ident in candidates:
            p=self.byid[ident];choices=[best[ident][1]]
            # Include the view with best lexical query coverage when a long
            # paragraph's nearest dense view is not its decisive evidence.
            choices.append(max(self.byview[ident],key=lambda j:sum(self.lex.idf.get(w,1) for w in set(tokens(query)).intersection(tokens(self.views[j]['text'])))))
            for j in dict.fromkeys(choices):
                view=self.views[j];text='Title: '+p['title']+'\nSection: '+p.get('section','')+'\n'+view['text']
                count=len(self.reranker.tokenizer(query,text,add_special_tokens=True,truncation=False)['input_ids'])
                if count>self.reranker.max_seq_length:raise ValueError('Reranker pair would truncate')
                pairs.append((query,text));owners.append(ident)
        values=np.asarray(self.reranker.predict(pairs,batch_size=16,show_progress_bar=False)).reshape(-1)
        ce={}
        for ident,value in zip(owners,values):ce[ident]=max(ce.get(ident,-1e9),float(value))
        if not np.isfinite(values).all():raise ValueError('Invalid reranker values')
        reranked=sorted(candidates,key=lambda i:(-ce[i],-fused(i),i))
        routes['document_hybrid_ce']=reranked
        # Query-facet selection prefers complementary explicitly requested row
        # labels, rather than spending five slots on near-identical captions.
        qset=set(qwords);weight=lambda ws:sum(self.lex.idf.get(w,1) for w in ws)
        total=max(1,weight(qset));covered=set();selected=[];remaining=set(candidates)
        relevance={i:1/(1+math.exp(-max(-30,min(30,ce[i])))) for i in candidates}
        maxfusion=max(fused(i) for i in candidates)
        while remaining:
            def utility(i):
                rowmatch=weight(qset.intersection(self.content[i]))/total
                gain=weight(qset.intersection(self.content[i])-covered)/total
                return relevance[i]+.2*fused(i)/maxfusion+.2*rowmatch+.15*gain
            chosen=min(remaining,key=lambda i:(-utility(i),i));selected.append(chosen);remaining.remove(chosen)
            covered.update(qset.intersection(self.content[chosen]))
        routes['table_aware_selection']=selected
        details.update(pairs_scored=len(pairs),rerank_parent_count=len(candidates),rerank_scores=ce)
        return routes,details

    def resolve(self,order,k=20):return [deepcopy(self.byid[i]) for i in order[:k]]
