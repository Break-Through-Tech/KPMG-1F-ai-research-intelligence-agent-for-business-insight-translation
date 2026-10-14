"""Capture real retrieval against a validated, reconciled frozen corpus.

Retrieval mode invokes no generation provider. Summary/business modes use the
explicit generation configuration. Output directories refuse overwrite.
"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path

import pandas as pd
from src import retrieval
from evaluation.run_benchmarks import capture, export_review_table, source_provenance
from evaluation.reviews.score_reviews import aggregate
from src.research_pipeline import run_research
from tests.html_transport import implementation_hashes

ROOT = Path(__file__).resolve().parents[1]


def verify_validation(report, root=ROOT):
    if report.get('status') != 'PASS' or report.get('mode') != 'HTML-first; cached sources only':
        raise ValueError('A passed HTML-first validation report is required')
    if report.get('failures') or not report.get('papers') or any(
            p.get('failures') != [] for p in report['papers']):
        raise ValueError('Validation contains incomplete paper checks')
    if (report.get('protected_inputs_unchanged') is not True or
            report.get('source_files_unchanged') is not True or
            not str(report.get('cached_ingestion_rerun', '')).startswith('PASS:')):
        raise ValueError('Validation did not preserve its inputs or verify the ingestion rerun')
    if report.get('implementation_hashes') != implementation_hashes():
        raise ValueError('Validation implementation changed; regenerate the audit report')
    hashes = {key.replace('\\', '/'): value for key, value in report.get('input_hashes', {}).items()}
    corpus = root/'data/processed/chunks.parquet'
    if not corpus.is_file() or sha256(corpus.read_bytes()).hexdigest() != hashes.get('data/processed/chunks.parquet'):
        raise ValueError('Current Parquet differs from the validated corpus')
    for relative in ('data/metadata/arxiv_csAI_25_pdf_sample.csv','data/metadata/arxiv_csAI_100_metadata.csv'):
        path = root/relative
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != hashes.get(relative):
            raise ValueError('Current metadata differs from the validated snapshot')
    frame = pd.read_parquet(corpus)
    papers = {p['arxiv_id']: p for p in report['papers']}
    if (len(papers) != len(report['papers']) or len(frame) != report.get('persisted_chunks') or
            set(frame['arxiv_id']) != set(papers) or len(papers) != report.get('locked_papers')):
        raise ValueError('Corpus counts/IDs differ from the validation report')
    for aid, rows in frame.groupby('arxiv_id'):
        paper = papers[aid]
        if paper.get('chunks') != len(rows) or paper.get('verified_passages') != len(rows):
            raise ValueError('Validation contains incomplete passage checks')
    transport = report.get('transport', {})
    if any(transport.get(key) != len(frame) for key in ('first_count', 'rerun_count', 'reopened_verified_records')):
        raise ValueError('Validation contains incomplete persistent transport checks')
    return frame


def reconcile(collection, frame):
    expected = {r['chunk_id']:r for r in frame.to_dict('records')}
    if len(expected) != len(frame): raise ValueError('Duplicate corpus chunk IDs')
    stored = collection.get(include=['documents','metadatas'])
    if (set(stored['ids']) != set(expected) or
            any(len(stored[key]) != len(expected) for key in ('ids', 'documents', 'metadatas'))):
        raise ValueError('Index/corpus ID mismatch or incomplete stored records')
    for ident,text,metadata in zip(stored['ids'],stored['documents'],stored['metadatas']):
        if text != expected[ident]['text'] or metadata != retrieval.citation_metadata(expected[ident]):
            raise ValueError('Indexed text/citation metadata differs from validated corpus')
    rows = sorted(zip(stored['ids'],stored['documents'],stored['metadatas']))
    return sha256(json.dumps(rows,sort_keys=True,allow_nan=False).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode', choices=('retrieval', 'summary', 'business'), default='retrieval')
    parser.add_argument('--industry', help='Explicit industry for business mode')
    args=parser.parse_args()
    if args.mode == 'business' and not args.industry:
        parser.error('Business mode requires --industry')
    if args.output.exists(): parser.error('Choose a new frozen output directory')
    report=json.loads(args.validation.read_text())
    frame=verify_validation(report)
    from sentence_transformers import SentenceTransformer
    from huggingface_hub import hf_hub_download
    model=SentenceTransformer(retrieval.EMBEDDING_MODEL)
    vectors=model.encode(frame['text'].tolist(),show_progress_bar=True)
    collection=retrieval.store_embeddings(frame,vectors)
    index_hash=reconcile(collection,frame)
    weights=Path(hf_hub_download('sentence-transformers/'+retrieval.EMBEDDING_MODEL,
                               'model.safetensors',local_files_only=True))
    provenance=source_provenance(execution='persistent_corpus')
    generate = None
    translate_fn = None
    if args.mode != 'retrieval':
        from src.generation import create_generate
        from src.summarization import summarize, prompt_provenance
        generate, generation = create_generate()
        provenance['generation'] = {**generation, **prompt_provenance()}
        if args.mode == 'business':
            from src.business_translation import translate, prompt_provenance as business_provenance
            provenance['generation']['business_translation'] = business_provenance()
            translate_fn = lambda summary, passages, *, industry: translate(
                summary, passages, industry=industry, generate=generate)
    provenance.update(corpus_mode='html_first',indexed_corpus_sha256=index_hash,
        corpus_validation_sha256=sha256(args.validation.read_bytes()).hexdigest(),
        embedding_weights_sha256=sha256(weights.read_bytes()).hexdigest(),
        embedding_revision=weights.parent.name,
        capture_script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        packages={n:importlib.metadata.version(n) for n in ('sentence-transformers','chromadb','torch','pandas','pyarrow')},
        absent_stages=([ 'summary generation not requested'] if args.mode == 'retrieval' else []) +
            (['business adapter not bound'] if args.mode != 'business' else []) +
            ['actual human reviews not supplied'])
    def research(request):
        return run_research(request,retrieve=lambda q,k:retrieval.search(q,k,model=model),
            summarize_fn=(lambda q,p: summarize(q,p,generate=generate)) if generate else
                (lambda q,p:{'status':'insufficient_evidence','query':q,'claims':[],
                    'limitations':['Generation not requested; real retrieval-only capture, not a generated answer.']}),
            translate_fn=translate_fn, provenance=provenance)
    artifact=capture(json.loads((ROOT/'evaluation/benchmark_cases.json').read_text()),
                     research_fn=research,provenance=provenance,
                     context={'industry':args.industry} if args.mode == 'business' else None)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'run.json').write_text(json.dumps(artifact,indent=2,allow_nan=False)+'\n')
    export_review_table(artifact,args.output/'review.csv')
    (args.output/'unscored.json').write_text(json.dumps(aggregate(artifact,[]),indent=2)+'\n')
    (args.output/'corpus-validation.json').write_bytes(args.validation.read_bytes())
    failed=sum(row['status']=='error' for row in artifact['cases'])
    summary_failed=sum(bool((row['result'] or {}).get('summary', {}).get('error'))
                       for row in artifact['cases'])
    print(json.dumps({'run_id':artifact['run_id'],'queries':len(artifact['cases']),
                     'failures':failed,'summary_failures':summary_failed,'chunks':len(frame)}))
    return int(bool(failed or summary_failed))


if __name__ == '__main__': raise SystemExit(main())
