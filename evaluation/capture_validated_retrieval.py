"""Capture real retrieval against a validated, reconciled frozen corpus.

No generation provider is invoked. Output directories refuse overwrite.
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

ROOT = Path(__file__).resolve().parents[1]


def verify_validation(report, root=ROOT):
    if report.get('status') != 'passed' or report.get('mode') != 'html_first':
        raise ValueError('A passed HTML-first validation report is required')
    if report.get('failures') or not report.get('papers') or any(
            p.get('status') != 'passed' for p in report['papers']):
        raise ValueError('Validation contains incomplete paper checks')
    corpus = root/'data/processed/chunks.parquet'
    if not corpus.is_file() or sha256(corpus.read_bytes()).hexdigest() != report.get('parquet_sha256'):
        raise ValueError('Current Parquet differs from the validated corpus')
    for relative in ('data/metadata/arxiv_csAI_25_pdf_sample.csv','data/metadata/arxiv_csAI_100_metadata.csv'):
        path = root/relative
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != report.get('metadata_hashes',{}).get(relative):
            raise ValueError('Current metadata differs from the validated snapshot')
    frame = pd.read_parquet(corpus)
    if len(frame) != report.get('chunks') or set(frame['arxiv_id']) != {p['arxiv_id'] for p in report['papers']}:
        raise ValueError('Corpus counts/IDs differ from the validation report')
    return frame


def reconcile(collection, frame):
    expected = {r['chunk_id']:r for r in frame.to_dict('records')}
    if len(expected) != len(frame): raise ValueError('Duplicate corpus chunk IDs')
    stored = collection.get(include=['documents','metadatas'])
    if set(stored['ids']) != set(expected): raise ValueError('Index/corpus ID mismatch')
    for ident,text,metadata in zip(stored['ids'],stored['documents'],stored['metadatas']):
        if text != expected[ident]['text'] or metadata != retrieval.citation_metadata(expected[ident]):
            raise ValueError('Indexed text/citation metadata differs from validated corpus')
    rows = sorted(zip(stored['ids'],stored['documents'],stored['metadatas']))
    return sha256(json.dumps(rows,sort_keys=True,allow_nan=False).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
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
    provenance.update(corpus_mode='html_first',indexed_corpus_sha256=index_hash,
        corpus_validation_sha256=sha256(args.validation.read_bytes()).hexdigest(),
        embedding_weights_sha256=sha256(weights.read_bytes()).hexdigest(),
        embedding_revision=weights.parent.name,
        capture_script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        packages={n:importlib.metadata.version(n) for n in ('sentence-transformers','chromadb','torch','pandas','pyarrow')},
        absent_stages=['summary generation not requested','business adapter not bound','actual human reviews not supplied'])
    def research(request):
        return run_research(request,retrieve=lambda q,k:retrieval.search(q,k,model=model),
            summarize_fn=lambda q,p:{'status':'insufficient_evidence','query':q,'claims':[],
                'limitations':['Generation not requested; real retrieval-only capture, not a generated answer.']})
    artifact=capture(json.loads((ROOT/'evaluation/benchmark_cases.json').read_text()),
                     research_fn=research,provenance=provenance)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'run.json').write_text(json.dumps(artifact,indent=2,allow_nan=False)+'\n')
    export_review_table(artifact,args.output/'review.csv')
    (args.output/'unscored.json').write_text(json.dumps(aggregate(artifact,[]),indent=2)+'\n')
    (args.output/'corpus-validation.json').write_bytes(args.validation.read_bytes())
    failed=sum(row['status']=='error' for row in artifact['cases'])
    print(json.dumps({'run_id':artifact['run_id'],'queries':len(artifact['cases']),'failures':failed,'chunks':len(frame)}))
    return int(failed>0)


if __name__ == '__main__': raise SystemExit(main())
