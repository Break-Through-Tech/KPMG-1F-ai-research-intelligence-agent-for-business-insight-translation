"""Reproducible offline ablations. No generation API, downloads, or index writes."""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import time
import unicodedata

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

from experiments.semantic_calibration.policies import POLICIES, Policy, choose_policy, semantic_intervals, select_context, units
from src.data_ingestion.tex_chunking import split_tex
from src.semantic_chunking_adapter import EmbeddingAdapter

MODELS = {
    'minilm': ('sentence-transformers/all-MiniLM-L6-v2', '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'),
    'bge': ('BAAI/bge-small-en-v1.5', '5c38ec7c405ec4b44b94cc5a9bb96e735b38267a'),
    'e5': ('intfloat/e5-small-v2', 'ffb93f3bd4047442299a41ebb6fa998a38507c52'),
}
MODES = [('top5', None, 5, 0), ('tokens800',800,None,0),
         ('tokens1600',1600,None,0), ('tokens1600_neighbors',1600,None,1)]


@lru_cache(maxsize=200000)
def norm(text):
    """Matching aid, not TeX rendering or semantic judgment. Never embed this."""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\\(?:cite\w*|label|ref|eqref)\*?(?:\[[^\]]*\])*\{[^{}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\*?', '', text)
    return ''.join(c for c in text.casefold() if c.isalnum())


def evaluate(qs, chunks, vectors, queries, blocks, counter, availability):
    scores = queries @ vectors.T
    output = {}
    for mode, budget, k, neighbors in MODES:
        rows = []
        for q, similarities in zip(qs, scores):
            context = select_context(chunks, similarities, blocks, counter,
                                     budget=budget, top_k=k, neighbors=neighbors)
            texts = [(blocks[e['block']]['paper'], norm(e['text'])) for e in context['evidence']]
            found = [any(paper==q['paper'] and norm(a) in t for paper,t in texts) for a in q['anchors']]
            available = availability[q['id']]
            receipts = []
            for e in context.pop('evidence'):
                block = blocks[e['block']]
                location = dict(block['location'])
                if block['source']=='tex':
                    location['line_start'] += block['text'].count('\n',0,e['start'])
                    location['line_end'] = location['line_start']+e['text'].count('\n')
                receipts.append({**e, 'paper':block['paper'], 'source':block['source'], 'location':location})
            rows.append(dict(id=q['id'],paper=q['paper'],split=q['split'],found=found,
                             complete=all(found),source_available=all(available),**context,evidence=receipts))
        output[mode]=rows
    return output


def summarize(rows):
    present = [r for r in rows if r['source_available']]
    return dict(questions=len(rows), complete=sum(r['complete'] for r in rows),
                source_available=len(present), complete_when_available=sum(r['complete'] for r in present),
                mean_tokens=round(float(np.mean([r['tokens'] for r in rows])),2) if rows else 0)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--corpus',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--device',default='cpu',choices=['cpu','mps'])
    ap.add_argument('--models',nargs='+',default=list(MODELS),choices=MODELS)
    ap.add_argument('--sources',nargs='+',default=['pdf','html','tex'],choices=['pdf','html','tex'])
    args=ap.parse_args()
    os.environ['HF_HUB_OFFLINE']='1'
    os.environ['TOKENIZERS_PARALLELISM']='false'
    import torch
    torch.set_num_threads(4)
    from sentence_transformers import SentenceTransformer
    corpus=json.loads(args.corpus.read_text())
    args.output.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(args.corpus.read_bytes()).hexdigest()
    protocol=dict(corpus_sha256=digest,policies=[p.__dict__ for p in POLICIES],models=MODELS,
                  modes=MODES,candidate_limit=200,common_papers=corpus['common_papers'],split=corpus['split'],
                  selection='Per source/model, tuning-only complete-span count at 1600 tokens; choose policy and neighbor setting. Ties: fewer mean tokens then name. Baseline/token-only excluded.',
                  limitations=corpus['notes'],device=args.device,
                  budget='Exact tokenizer length with passage prefix and special tokens for each emitted interval; no generation prompt framing. Never truncate context to fill budget.')
    protocol_file=args.output/'protocol.json'
    if protocol_file.exists() and json.loads(protocol_file.read_text()) != json.loads(json.dumps(protocol)):
        raise ValueError('Output belongs to a different protocol; use a new output directory')
    protocol_file.write_text(json.dumps(protocol,indent=2))
    common=set(corpus['common_papers'])
    qs=[dict(q,split=corpus['split'][q['paper']]) for q in corpus['questions'] if q['paper'] in common]
    (args.output/'questions.json').write_text(json.dumps(qs,indent=2))
    for short in args.models:
        name,revision=MODELS[short]
        modelpath=Path.home()/'.cache/huggingface/hub'/('models--'+name.replace('/','--'))/'snapshots'/revision
        encoder=SentenceTransformer(str(modelpath),local_files_only=True,device=args.device)
        adapter=EmbeddingAdapter(encoder,name)
        @lru_cache(maxsize=250000)
        def count(text):
            return len(encoder.tokenizer.encode(adapter.passage_prefix+text,add_special_tokens=True,truncation=False))
        qvectors=adapter.encode_queries([q['query'] for q in qs],batch_size=32,show_progress_bar=False)
        for source in args.sources:
            out=args.output/short/source
            out.mkdir(parents=True,exist_ok=True)
            if (out/'report.json').exists():
                print('CACHED',short,source,flush=True)
                continue
            started=time.monotonic()
            blocks={b['id']:b for b in corpus['blocks'] if b['source']==source and b['paper'] in common}
            availability={q['id']:[any(norm(a) in norm(b['text']) for b in blocks.values() if b['paper']==q['paper']) for a in q['anchors']] for q in qs}
            specs={}
            for k,b in blocks.items():
                try:
                    spans=units(b['text'],tex=source=='tex')
                except ValueError as error:
                    raise ValueError(f'Cannot safely split {source} block {k}: {error}') from error
                specs[k]=spans
            # Encode unique sentence/atomic units once per source/model, NOT per arm.
            sentence_texts=list(dict.fromkeys(b['text'][a:z].strip() for k,b in blocks.items() for a,z in specs[k]))
            print('UNITS',short,source,len(blocks),len(sentence_texts),flush=True)
            sentences=adapter.encode(sentence_texts,batch_size=32,show_progress_bar=False,convert_to_numpy=True)
            lookup={s:i for i,s in enumerate(sentence_texts)}
            variants={p.name:[] for p in POLICIES}
            variants['baseline']=[]
            variants['token_only240_overlap32']=[]
            splitter=RecursiveCharacterTextSplitter(chunk_size=1800,chunk_overlap=250,add_start_index=True,
                                                  separators=['\n\n','\n','. ',' ',''])
            for k,b in blocks.items():
                text=b['text']
                spans=specs[k]
                v=[sentences[lookup[text[a:z].strip()]] for a,z in spans]
                for policy in POLICIES+[Policy('token_only240_overlap32',threshold=-1,max_tokens=240,overlap_tokens=32)]:
                    for a,z in semantic_intervals(text,spans,v,count,policy):
                        variants[policy.name].append(dict(block=k,start=a,end=z,text=text[a:z]))
                if source=='tex':
                    pieces=[(p['start_index'],p['start_index']+len(p['text'])) for p in split_tex(text)]
                else:
                    pieces=[(d.metadata['start_index'],d.metadata['start_index']+len(d.page_content))
                            for d in splitter.create_documents([text])]
                for a,z in pieces:
                    assert 0 <= a < z <= len(text)
                    variants['baseline'].append(dict(block=k,start=a,end=z,text=text[a:z]))
            texts=list(dict.fromkeys(c['text'] for cs in variants.values() for c in cs))
            print('EMBED',short,source,len(texts),'unique chunks',flush=True)
            vectors=adapter.encode_passages(texts,batch_size=32,show_progress_bar=False,convert_to_numpy=True)
            index={t:i for i,t in enumerate(texts)}
            np.save(out/'chunk-vectors.npy',vectors)
            np.save(out/'query-vectors.npy',qvectors)
            (out/'chunk-texts.json').write_text(json.dumps(texts,ensure_ascii=False))
            report=dict(model=name,revision=revision,source=source,papers=len(common),variants={},
                        corpus_sha256=digest,max_seq_length=encoder.max_seq_length)
            for label,chunks in variants.items():
                v=vectors[[index[c['text']] for c in chunks]]
                rows=evaluate(qs,chunks,v,qvectors,blocks,count,availability)
                summaries={mode:{split:summarize([r for r in values if r['split']==split])
                                 for split in ('tuning','validation')} for mode,values in rows.items()}
                report['variants'][label]=dict(chunks=len(chunks),mean_chars=round(float(np.mean([len(c['text']) for c in chunks])),2),
                                              over_model_limit=sum(count(c['text'])>encoder.max_seq_length for c in chunks),
                                              summaries=summaries,queries=rows)
                print('RESULT',short,source,label,json.dumps(summaries['tokens1600']),flush=True)
            label,mode=choose_policy(report["variants"])
            report['selected']=dict(policy=label,mode=mode,tuning=report['variants'][label]['summaries'][mode]['tuning'],
                                    validation=report['variants'][label]['summaries'][mode]['validation'])
            report['elapsed_seconds']=round(time.monotonic()-started,2)
            (out/'report.json').write_text(json.dumps(report,ensure_ascii=False))
            (out/'variants.json').write_text(json.dumps(variants,ensure_ascii=False))
            print('FINISHED',short,source,json.dumps(report['selected']),report['elapsed_seconds'],flush=True)
        del encoder


if __name__=='__main__':
    main()
