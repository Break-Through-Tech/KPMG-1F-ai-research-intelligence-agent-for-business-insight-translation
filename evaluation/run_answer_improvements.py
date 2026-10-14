"""Controlled model-only or hybrid/evidence-led experiment on frozen sources."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from evaluation.run_benchmarks import capture, artifact_id, source_provenance
from src.codex_generation import create_codex_generate
from src.research_pipeline import run_research

ROOT = Path(__file__).resolve().parents[1]


def recovered_case_ids(baseline, recovery, cases, variant):
    """Only selected failed integrated cases served from frozen recovery evidence."""
    if variant not in {'model-only', 'evidence-led-frozen'}:
        return []
    selected = {c['query_id'] for c in cases}
    available = {c['case']['query_id'] for c in recovery['cases'] if c['status'] == 'ok'}
    return [c['case']['query_id'] for c in baseline['cases']
            if c['status'] != 'ok' and c['case']['query_id'] in selected & available]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--retrieval-baseline',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--codex-bin',required=True)
    parser.add_argument('--model',required=True)
    parser.add_argument('--variant',choices=['model-only','evidence-led','evidence-led-frozen'],required=True)
    parser.add_argument('--queries',nargs='+')
    parser.add_argument('--intent-rerank',action='store_true',help='Quote-checked model relevance instead of the local cross-encoder')
    parser.add_argument('--cases-file',type=Path,help='New-question probes over the same frozen corpus; hybrid evidence-led only')
    parser.add_argument('--reranker-model',default='cross-encoder/ms-marco-MiniLM-L6-v2')
    args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new frozen output directory')
    baseline=json.loads(args.baseline.read_text())
    retrieval_baseline=json.loads(args.retrieval_baseline.read_text())
    for artifact in (baseline,retrieval_baseline):
        if artifact_id(artifact)!=artifact['run_id']:
            parser.error('Frozen input artifact hash mismatch')
    if args.intent_rerank and args.variant!='evidence-led':
        parser.error('Intent reranking requires hybrid evidence-led mode')
    if args.cases_file and args.variant!='evidence-led':
        parser.error('New questions require hybrid retrieval, not frozen query results')
    source_cases=json.loads(args.cases_file.read_text()) if args.cases_file else [c['case'] for c in baseline['cases']]
    cases=[c for c in source_cases if not args.queries or c['query_id'] in args.queries]
    if not cases:parser.error('No matching queries')
    evidence={c['case']['query']:c['result']['evidence'] for c in retrieval_baseline['cases'] if c['status']=='ok'}
    for case in baseline['cases']:
        if case['status']=='ok' and case['result']['evidence']!=evidence[case['case']['query']]:
            parser.error('Integrated and retrieval baseline evidence differ')
    provenance=source_provenance(execution='persistent_corpus')
    provenance.update(experiment_variant=args.variant,
        baseline_run_id=baseline['run_id'],baseline_sha256=sha256(args.baseline.read_bytes()).hexdigest(),
        recovery_retrieval_run_id=retrieval_baseline['run_id'],
        baseline_failure_recovered_from_frozen_retrieval=recovered_case_ids(
            baseline, retrieval_baseline, cases, args.variant),
        implementation_hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest()
            for p in [ROOT/'src/codex_generation.py',ROOT/'src/evidence_led.py',ROOT/'src/hybrid_retrieval.py',ROOT/'src/intent_reranking.py',Path(__file__)]})
    if args.cases_file:
        provenance['new_question_probes_sha256']=sha256(args.cases_file.read_bytes()).hexdigest()
    if provenance['input_hashes']['data/processed/chunks.parquet']!=baseline['provenance']['input_hashes']['data/processed/chunks.parquet']:
        parser.error('Corpus differs from the frozen baseline')
    receipts=[]
    generate,metadata=create_codex_generate(model=args.model,binary=args.codex_bin,receipts=receipts)
    if args.variant in {'model-only','evidence-led-frozen'}:
        if args.variant=='model-only':
            from src.summarization import summarize,prompt_provenance
            from src.business_translation import translate,prompt_provenance as bp
            provenance['generation']={**metadata,**prompt_provenance(),'business_translation':bp()}
        else:
            from src.evidence_led import summarize,translate,prompt_provenance
            provenance['generation']={**metadata,**prompt_provenance(),'business_translation':'evidence-led-business-v1'}
        retrieve=lambda q,k:evidence[q][:k]
        provenance['retrieval']={'method':'frozen_dense_baseline'}
    else:
        import pandas as pd
        import chromadb
        from sentence_transformers import SentenceTransformer,CrossEncoder
        from src import retrieval
        from src.hybrid_retrieval import HybridRetriever
        from src.evidence_led import summarize,translate,prompt_provenance
        from evaluation.capture_validated_retrieval import reconcile
        frame=pd.read_parquet(ROOT/'data/processed/chunks.parquet')
        client=chromadb.PersistentClient(path=str(ROOT/'data/chroma_db'))
        index_hash=reconcile(client.get_collection(retrieval.COLLECTION_NAME),frame)
        if index_hash!=baseline['provenance']['indexed_corpus_sha256']:
            parser.error('Index differs from the frozen baseline')
        dense_model=SentenceTransformer(retrieval.EMBEDDING_MODEL)
        intent_settings=None
        if args.intent_rerank:
            from src.intent_reranking import create_intent_rerank
            rank,intent_settings=create_intent_rerank(generate)
        else:
            reranker=CrossEncoder(args.reranker_model)
            def rank(q,ps):return reranker.predict([(q,p['text']) for p in ps],show_progress_bar=False)
        passages=[{'chunk_id':r['chunk_id'],'text':r['text'],**retrieval.citation_metadata(r),
                   'page_number':retrieval.citation_metadata(r).get('page_number')}
                  for r in frame.to_dict('records')]
        hybrid=HybridRetriever(passages,dense_search=lambda q,k:retrieval.search(q,k,client=client,model=dense_model),rerank=rank)
        evidence={case['query']:hybrid(case['query'],5) for case in cases}
        retrieve=lambda q,k:evidence[q][:k]
        provenance.update(indexed_corpus_sha256=index_hash,corpus_mode='html_first')
        provenance['generation']={**metadata,**prompt_provenance(),'business_translation':'evidence-led-business-v1'}
        provenance['retrieval']={'method':'hybrid-bm25-rrf-v2','candidate_pool':25,
                                 'reranker':intent_settings or args.reranker_model,'reranker_local':not args.intent_rerank}
    args.output.mkdir(parents=True)
    (args.output/'retrieval.json').write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
    artifact={'schema_version':'1.0','created_at':datetime.now(timezone.utc).isoformat(),
              'provenance':provenance,'top_k':5,'cases':[]}
    for case in cases:
        def research(request):
            return run_research(request,retrieve=retrieve,
                summarize_fn=lambda q,p:summarize(q,p,generate=generate),
                translate_fn=lambda s,p,*,industry:translate(s,p,industry=industry,generate=generate),
                provenance=provenance)
        row=capture([case],research_fn=research,provenance=provenance,context={'industry':'professional services'})['cases'][0]
        artifact['cases'].append(row);artifact['run_id']=artifact_id(artifact)
        (args.output/'run.json').write_text(json.dumps(artifact,indent=2,allow_nan=False)+'\n')
        (args.output/'receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
        result=row['result'] or {}
        print(json.dumps({'query':case['query_id'],'status':row['status'],
            'summary':result.get('summary',{}).get('status'),'summary_error':result.get('summary',{}).get('error'),
            'business':result.get('business_insight',{}).get('status')}),flush=True)
    return int(any(c['status']=='error' or (c['result'] or {}).get('summary',{}).get('error') for c in artifact['cases']))


if __name__=='__main__':raise SystemExit(main())
