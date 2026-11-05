"""Isolated development experiment: split frozen indexed text, never re-ingest sources."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from time import perf_counter


def split_passage(text, tokenizer, budget, overlap=32):
    """Exact character slices; prefer sentence ends, hard-split long sentences."""
    if budget <= overlap + 4:
        raise ValueError('Budget must leave room for overlap and special tokens.')
    reserve = tokenizer.num_special_tokens_to_add(pair=False)
    start = 0
    while start < len(text):
        rest = text[start:]
        tokens = tokenizer(rest, add_special_tokens=False, truncation=False,
                           return_offsets_mapping=True)['offset_mapping']
        if not tokens:
            break
        if len(tokens) + reserve <= budget:
            end = len(text)
        else:
            end = start + tokens[budget - reserve - 1][1]
            boundaries = [start + m.end() for m in re.finditer(r'(?<=[.!?])\s+|\n+', rest[:end-start])]
            candidates = [b for b in boundaries if b >= start + (end-start)//2]
            if candidates:
                end = candidates[-1]
        piece = text[start:end]
        offsets = tokenizer(piece, add_special_tokens=False, truncation=False,
                            return_offsets_mapping=True)['offset_mapping']
        # A new boundary can change tokenization. Never silently truncate.
        while len(offsets) + reserve > budget:
            end = start + offsets[budget-reserve-1][0]
            piece = text[start:end]
            offsets = tokenizer(piece, add_special_tokens=False, truncation=False,
                                return_offsets_mapping=True)['offset_mapping']
        if not piece.strip() or end <= start:
            raise ValueError('Chunker failed to advance.')
        yield start, end, piece
        if end == len(text):
            break
        next_start = start + offsets[max(1, len(offsets)-overlap)][0] if overlap and len(offsets)>1 else end
        start = next_start if next_start > start else end


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    baseline_path = (root/'data/chroma_db').resolve()
    output_path = args.output.resolve()
    if output_path == baseline_path or baseline_path in output_path.parents or output_path in baseline_path.parents:
        raise ValueError('Experimental output must be separate from the demo index.')
    args.output.mkdir(parents=True, exist_ok=False)
    import chromadb
    import numpy as np
    from sentence_transformers import SentenceTransformer
    original = chromadb.PersistentClient(path=str(root/'data/chroma_db')).get_collection('arxiv_papers')
    def snapshot():
        data = original.get(include=['documents','metadatas','embeddings'])
        return sorted([{'id': i, 'text': t, 'metadata': m, 'embedding': list(map(float,e))}
                       for i,t,m,e in zip(data['ids'],data['documents'],data['metadatas'],data['embeddings'])], key=lambda r:r['id'])
    rows = snapshot()
    frozen_hash = digest(rows)
    def save(name, value):
        (args.output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    save('frozen-source.json', rows)
    model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
    weight_hash = sha256()
    for name, tensor in model.state_dict().items():
        weight_hash.update(name.encode())
        weight_hash.update(tensor.detach().cpu().numpy().tobytes())
    tokenizer = model.tokenizer
    count = lambda text: len(tokenizer(text, add_special_tokens=True, truncation=False)['input_ids'])
    source = {r['id']:r for r in rows}
    # These source-informed probes are development labels, NOT independent gold answers.
    probes = [
        ('trip-numbers','What overall accuracy did the trip-planning system and its single-agent and workflow multi-agent baselines achieve?',
         '2605.00276v1_c0004','77.4% overall accuracy compared to 30.4% for single-agent and 23.6% for workflow-based multi-agent baselines'),
        ('trip-controller','What does the orchestration agent do to coordinate trip-planning agents?',
         '2605.00276v1_c0022','The Orchestration Agent in our architecture acts as a central meta-controller that manages sub-task decomposition, enforces consistency of the reasoning, and triggers re-thinking when necessary.'),
        ('rmu-resistance','How does RMU compare with GA and NPO in resisting recovery of forgotten knowledge through dialogue?',
         '2603.00823v2_c0018','RMU demonstrates comparatively stable robustness under interaction.'),
        ('dialogue-utility','How can dialogue containing forget-set content affect RMU generation quality and interactive capability?',
         '2603.00823v2_c0004','for RMU, exposure to forget-set content can substantially impair'),
        ('dpo-lowdata','Which method has an advantage at 25% training data, binary DPO or CU-DPO?',
         '2602.00931v2_c0022','Under data scarcity (25%), binary DPO holds a slight advantage'),
        ('dpo-crossover','At what training-data fraction does CU-DPO overtake binary DPO?',
         '2602.00931v2_c0022','CU- DPO overtakes binary DPO at 50% data')]
    cases=[]
    for ident,q,parent,quote in probes:
        if quote not in source[parent]['text']:
            raise ValueError('Development source span absent: '+ident)
        cases.append({'query_id':ident,'query':q,'source_parent':parent,'source_quote':quote,
                      'arxiv_id':source[parent]['metadata']['arxiv_id'],'label_kind':'assistant_source_inspection_development'})
    for filename in ('benchmark_cases.json','baseline_alesha_v1.json'):
        for case in json.loads((root/'evaluation'/filename).read_text(encoding='utf-8')):
            cases.append({'query_id':filename+':'+case['query_id'],'query':case['query'],'label_kind':'unscored_existing_development'})
    save('cases.json',cases)  # Frozen before any experimental retrieval.
    lengths=[count(r['text']) for r in rows]
    manifest={'kind':'development_retrieval_only_no_generation','source_sha256':frozen_hash,
              'encoder_limit':model.max_seq_length,'original_count':len(rows),
              'original_over_limit':sum(n>model.max_seq_length for n in lengths),
              'implementation_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
              'cases_sha256':digest(cases),'variants':{},'model_weights_sha256':weight_hash.hexdigest(),
              'original_hnsw_configuration':original.configuration.get('hnsw')}
    if (original.configuration.get('hnsw') or {}).get('space','l2') != 'l2':
        raise ValueError('Experiment requires the current L2 baseline metric.')
    save('manifest.json',manifest)
    query_vectors=model.encode([c['query'] for c in cases],show_progress_bar=False)
    variants=[('stored-original',rows,np.asarray([r['embedding'] for r in rows],dtype='float32'))]
    client=chromadb.PersistentClient(path=str(args.output/'experimental-index'))
    for name,budget in [('fresh-original',None),('tokens-192',192),('tokens-224',224)]:
        start=perf_counter()
        variant=[]
        for row in rows:
            pieces=[(0,len(row['text']),row['text'])] if budget is None else list(split_passage(row['text'],tokenizer,budget))
            covered=0
            for number,(a,b,text) in enumerate(pieces):
                if a>covered and row['text'][covered:a].strip():
                    raise ValueError('Non-whitespace source text lost.')
                covered=max(covered,b)
                if budget and count(text)>budget:
                    raise ValueError('Embedding budget exceeded.')
                variant.append({'id':row['id'] if budget is None else row['id']+f'__t{budget}_{number}',
                    'text':text,'metadata':{**row['metadata'],'parent_chunk_id':row['id'],
                                          'parent_char_start':a,'parent_char_end':b}})
            if row['text'][covered:].strip():
                raise ValueError('Source tail lost.')
        vectors=model.encode([r['text'] for r in variant],batch_size=32,show_progress_bar=False)
        collection=client.create_collection(name=name,metadata={'embedding_model':'all-MiniLM-L6-v2','hnsw:space':'l2'})
        for i in range(0,len(variant),128):
            batch=variant[i:i+128]
            collection.add(ids=[r['id'] for r in batch],documents=[r['text'] for r in batch],
                           metadatas=[r['metadata'] for r in batch],embeddings=vectors[i:i+128].tolist())
        manifest['variants'][name]={'chunks':len(variant),'over_limit':sum(count(r['text'])>model.max_seq_length for r in variant),
                                    'build_seconds':round(perf_counter()-start,3)}
        variants.append((name,variant,vectors))
        save('manifest.json',manifest)
        print('Built',name,len(variant),flush=True)
    # Use exact same L2 scorer for primary comparison, avoiding ANN/index-build noise.
    results={}
    for name,variant,vectors in variants:
        outputs=[]
        for case,qv in zip(cases,query_vectors):
            distances=np.sum((vectors-qv)**2,axis=1)
            order=np.argsort(distances,kind='stable')[:20]
            hits=[{**{k:v for k,v in variant[int(i)].items() if k!='embedding'},'distance':float(distances[int(i)]),
                   'tokens':count(variant[int(i)]['text'])} for i in order]
            row={'query_id':case['query_id'],'query':case['query'],'hits':hits}
            if 'source_quote' in case:
                match=lambda h: h['metadata']['arxiv_id']==case['arxiv_id'] and case['source_quote'] in h['text']
                row['span_rank']=next((n for n,h in enumerate(hits,1) if match(h)),None)
                row['span_at_5']=any(match(h) for h in hits[:5])
                row['span_at_20']=any(match(h) for h in hits)
                # Whole passages only; same generator context budget for every route.
                packed=[];used=0
                for h in hits:
                    if used+h['tokens']<=1280:
                        packed.append(h);used+=h['tokens']
                row['span_in_1280_tokens']=any(match(h) for h in packed)
            outputs.append(row)
        results[name]=outputs
    save('retrievals.json',results)
    metrics={name:{'span_probes':len(probes),**{key:sum(r.get(key,False) for r in outputs)
             for key in ('span_at_5','span_at_20','span_in_1280_tokens')}} for name,outputs in results.items()}
    original_unchanged=digest(snapshot())==frozen_hash
    save('metrics.json',{'metrics':metrics,'original_index_records_and_vectors_unchanged':original_unchanged,
                         'limitations':'Six source-informed span probes are not independent relevance/answer accuracy labels. Splitting existing chunks does not recover parser omissions or remove original overlap.'})
    if not original_unchanged:
        raise ValueError('Original index changed during experiment.')
    print(json.dumps(metrics,indent=2),flush=True)


if __name__=='__main__':
    main()
