"""Second development ablation: clause facets and explicit source-role coverage."""
import re,math
import numpy as np
from .retriever import Retriever,tokens
from .evidence_coverage import coverage_candidates

def facets(query):
    parts=re.split(r',\s*and\s+(?=(?:what|how|why|whether)\b)|;\s*',query,flags=re.I)
    result=[p.strip(' ,?') for p in parts[1:] if len(tokens(p))>=2]
    if re.search(r'\bproduction\b|deploy|real[- ]world',query,re.I):
        result.append('Experimental setting and limitations on production deployment')
    return list(dict.fromkeys(result))[:2]

class FacetRetriever(Retriever):
    def __init__(self,index,reranker,model):super().__init__(index,reranker);self.model=model
    def rank_facets(self,query,qv):
        routes,debug=super().rank(query,qv,with_reranker=False)
        hybrid=routes['document_hybrid'];fqs=facets(query);docs=set(debug['paper_candidates'])
        pool=set(hybrid[:60])
        if fqs:
            fvs=self.model.encode(fqs,show_progress_bar=False)
            for fq,fv in zip(fqs,fvs):
                fr,_=super().rank(fq,fv,with_reranker=False)
                pool.update(i for i in fr['document_hybrid'][:30] if self.byid[i]['arxiv_id'] in docs)
            # A paper's conclusion/limitation paragraphs are candidate evidence,
            # not automatically selected or treated as findings.
            for p in self.parents:
                if p['arxiv_id'] in docs and not p.get('table_id') and re.search(r'conclusion|limitation|discussion',p.get('section',''),re.I):pool.add(p['chunk_id'])
        # Qualifier cues expand the pool only. They do not establish relevance
        # or reserve a slot in the bounded evidence sent to synthesis.
        if re.search(r'trade.?off|limitation|imply|measure|production|deploy|risk|mean|conclude',query,re.I):
            query_terms=set(tokens(query))
            pool.update(p['chunk_id'] for p in self.parents
                if p['arxiv_id'] in docs and not p.get('table_id')
                and len(p['text'].split())<=120
                and re.search(r'\bnot\b|however|although|\bwhile\b|limitation|\bcost\b|\bmay\b|rather',p['text'],re.I)
                and set(tokens(p['text'])).intersection(query_terms))
        pool.update(coverage_candidates(query, self.parents, docs))
        candidates=sorted(pool);questions=[query]+fqs;ranklists=[];scores=[];pairs_total=0
        for question in questions:
            terms=set(tokens(question));pairs=[];owners=[]
            for ident in candidates:
                views=self.byview[ident]
                choices=sorted(views,key=lambda j:-sum(self.lex.idf.get(w,1) for w in terms.intersection(tokens(self.views[j]['text']))))[:2]
                for j in choices:
                    p=self.byid[ident];text='Title: '+p['title']+'\nSection: '+p.get('section','')+'\n'+self.views[j]['text']
                    if len(self.reranker.tokenizer(question,text,add_special_tokens=True,truncation=False)['input_ids'])>self.reranker.max_seq_length:raise ValueError('Reranker pair would truncate')
                    pairs.append((question,text));owners.append(ident)
            vs=np.asarray(self.reranker.predict(pairs,batch_size=16,show_progress_bar=False)).reshape(-1)
            if not np.isfinite(vs).all():raise ValueError('Invalid reranker values')
            ce={}
            for ident,v in zip(owners,vs):ce[ident]=max(ce.get(ident,-1e9),float(v))
            order=sorted(candidates,key=lambda i:(-ce[i],i));ranklists.append({i:r for r,i in enumerate(order,1)});scores.append(ce);pairs_total+=len(pairs)
        hr={i:r for r,i in enumerate(hybrid,1)};qset=set(tokens(query))
        def score(i):
            value=.5/(20+hr.get(i,10**6))+1/(20+ranklists[0][i])
            if fqs:value+=sum(1/(20+rs[i]) for rs in ranklists[1:])/len(fqs)
            p=self.byid[i]
            if p.get('table_id'):
                row=set(tokens(p['row_label']))
                # Complete named or numeric row labels explicitly present in
                # the request; never expected answer values or row positions.
                if row and row.issubset(qset) and (len(row)>=2 or any(w[0].isdigit() for w in row)):value+=.025
            return value
        order=sorted(candidates,key=lambda i:(-score(i),i))
        # Keep a lexical/dense anchor and one piece of evidence per explicit
        # question clause. This prevents a fluent relevance model from spending
        # all slots on the first half of a multi-part request.
        selected=[order[0]]
        for ranks in ranklists[1:]:
            best=min(candidates,key=lambda i:(ranks[i],i))
            if best not in selected:selected.append(best)
        if hybrid[0] not in selected:selected.append(hybrid[0])
        order=selected+[i for i in order if i not in selected]
        return order,{'facets':fqs,'candidate_count':len(candidates),'pairs_scored':pairs_total,'paper_candidates':debug['paper_candidates'],'balanced_prefix':selected}
