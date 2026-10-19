"""Local paired development ablation, NOT reproduction of peer quality scores."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--chunks', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cases', type=Path, nargs='+', default=[
        ROOT / 'evaluation/benchmark_cases.json', ROOT / 'evaluation/intent_controls.json',
        ROOT / 'evaluation/answer_quality_probes.json', ROOT / 'evaluation/peer_cross_paper_cases.json'])
    args = p.parse_args(argv)
    if args.output.exists():
        p.error('Output must be a fresh directory')
    cases = [row for f in args.cases for row in json.loads(f.read_text())]
    if len({c['query_id'] for c in cases}) != len(cases):
        p.error('Duplicate case IDs')
    import chromadb
    import numpy as np
    import pandas as pd
    import tiktoken
    from sentence_transformers import SentenceTransformer, CrossEncoder
    from src.retrieval import citation_metadata
    from src.hybrid_retrieval import HybridRetriever
    from src.peer_retrieval import NeighborContext, fuse, cap_papers, fuse_papers
    from evaluation.peer_sources.j_query_rewriter import rewrite_query

    args.output.mkdir(parents=True)
    frame = pd.read_parquet(args.chunks)
    if frame['chunk_id'].duplicated().any() or frame['text'].isna().any():
        raise ValueError('Invalid frozen corpus')
    rows = [{'chunk_id': r['chunk_id'], 'text': r['text'], **citation_metadata(r)}
            for r in frame.to_dict('records')]
    by_id = {r['chunk_id']: r for r in rows}
    corpus_papers = {r['arxiv_id'] for r in rows}
    for case in cases:
        for obligation in case.get('required_evidence', []):
            if obligation.get('absent_from_corpus'):
                if obligation['arxiv_id'] in corpus_papers:
                    raise ValueError('Missing-source control unexpectedly present')
            else:
                row = by_id[obligation['chunk_id']]
                if row['arxiv_id'] != obligation['arxiv_id'] or obligation['quote'] not in row['text']:
                    raise ValueError('Development evidence annotation differs from corpus')
    model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    cross_name = 'cross-encoder/ms-marco-MiniLM-L6-v2'
    model = SentenceTransformer(model_name, local_files_only=True, device='cpu')
    cross = CrossEncoder(cross_name, local_files_only=True, device='cpu')
    # Separate in-memory Chroma: no reads/writes of anyone's persistent index.
    client = chromadb.EphemeralClient()
    collection = client.create_collection('peer_repro', configuration={
        'hnsw': {'space': 'l2', 'ef_construction': 200, 'ef_search': 200, 'num_threads': 1}})
    vectors = model.encode([r['text'] for r in rows], show_progress_bar=False)
    collection.add(ids=list(by_id), embeddings=vectors.tolist(),
                   documents=[r['text'] for r in rows])
    embeddings = {}
    def vector(q):
        if q not in embeddings:
            embeddings[q] = model.encode([q], show_progress_bar=False)[0]
        return embeddings[q]
    def dense(q, k):
        found = collection.query(query_embeddings=[vector(q).tolist()],
                                  n_results=min(k, len(rows)), include=['distances'])
        return [{**by_id[i], 'distance': float(d)} for i, d in
                zip(found['ids'][0], found['distances'][0])]
    score_cache = {}
    def rank(q, candidates):
        missing = [r for r in candidates if (q, r['chunk_id']) not in score_cache]
        if missing:
            scores = cross.predict([(q, r['text']) for r in missing],
                                   show_progress_bar=False, batch_size=32)
            score_cache.update({(q, r['chunk_id']): float(s) for r, s in zip(missing, scores)})
        return [score_cache[q, r['chunk_id']] for r in candidates]
    hybrid = HybridRetriever(rows, dense_search=dense)
    baseline = HybridRetriever(rows, dense_search=dense, rerank=rank)
    papers = frame.drop_duplicates('arxiv_id').sort_values('arxiv_id')
    paper_ids = papers.arxiv_id.tolist()
    paper_vectors = model.encode((papers.title + '\n' + papers.abstract).tolist(),
                                 normalize_embeddings=True, show_progress_bar=False)
    enc = tiktoken.get_encoding('cl100k_base')
    count_tokens = lambda text: len(enc.encode(text))
    context = NeighborContext(rows, count_tokens=count_tokens)
    provenance = {
        'baseline_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'chunks_sha256': digest(args.chunks), 'chunks': len(rows), 'papers': len(papers),
        'case_hashes': {str(f): digest(f) for f in args.cases},
        'implementation_hashes': {str(f.relative_to(ROOT)): digest(f) for f in [
            Path(__file__), ROOT/'src/peer_retrieval.py', ROOT/'src/hybrid_retrieval.py',
            ROOT/'evaluation/peer_sources/j_query_rewriter.py']},
        'packages': {n: importlib.metadata.version(n) for n in
                     ['chromadb','sentence-transformers','torch','numpy','pandas','tiktoken']},
        'models': {}, 'device': 'cpu', 'top_k': 5, 'candidate_pool': 25,
        'dense_index': 'fresh ephemeral Chroma L2, ef construction/search 200, one thread',
        'semantic_acceptance': 'unreviewed', 'case_status': 'development cases only, not holdout',
        'peer_sources': {
            'neighbor': '1B bc782a8ac0c8104a814d3c2ba83ba53004ac6d52',
            'rerank_diversity': '1J 78e7ba17be7014dd648efca44a1327431923ba8b',
            'paper_fusion': '1J 3b931d89d42ab1324917ecb91978c79acd9900a6',
            'query_rewriter': '1J 0ac8e869b8c84d9ff1e21fa4327e5e47a5764302'},
        'limitations': ['Adaptation to 1F, not a replication of peer corpus/metrics.',
            'No generation, independent relevance judgements, or quality win established.',
            'Same model/chunks held fixed; no database or chunker comparison.',
            'Metadata fusion returns one passage per paper and changes output policy.',
            'Text-token budget excludes prompts and citation formatting overhead.',
            'Table neighbors do not prove complete original-document continuity.']}
    from huggingface_hub import hf_hub_download
    for name in [model_name, cross_name]:
        weight = Path(hf_hub_download(name, 'model.safetensors', local_files_only=True))
        provenance['models'][name] = {'revision': weight.parent.name, 'weights_sha256': digest(weight)}
    artifact = {'provenance': provenance, 'created_at': datetime.now(timezone.utc).isoformat(), 'cases': []}
    for case in cases:
        start = time.monotonic()
        q = case['query']
        base = baseline(q, 25)
        anchors = base[:5]
        rewritten = rewrite_query(q)
        expanded = fuse({'original': hybrid(q, 25), 'expanded': hybrid(rewritten, 25)},
                         method='original-expanded-hybrid-rrf')
        # Query-fusion ablation retains the identical original-query cross-encoder.
        values = rank(q, expanded)
        for r, score in zip(expanded, values):
            r['retrieval']['rerank_score'] = score
        expanded.sort(key=lambda r: (-r['retrieval']['rerank_score'],
                                     -r['retrieval']['rrf_score'], r['chunk_id']))
        v = vector(q)
        paper_ranking = [paper_ids[i] for i in np.argsort(
            -(paper_vectors @ (v / np.linalg.norm(v))), kind='stable')]
        def evidence(paper):
            idx = [i for i,r in enumerate(rows) if r['arxiv_id'] == paper]
            best = min(idx, key=lambda i: (float(np.sum((vectors[i]-v)**2)), rows[i]['chunk_id']))
            return {**rows[best], 'distance': float(np.sum((vectors[best]-v)**2))}
        combined = fuse_papers(paper_ranking, dense(q, 100), evidence)[:5]
        neighbors, budget = context.expand(anchors)
        variants = {'dense': dense(q,5), 'hybrid_rrf': hybrid(q,5), 'baseline_cross': anchors,
                    'cross_cap2': cap_papers(base), 'query_fusion_cross': expanded[:5],
                    'paper_metadata_fusion': combined, 'baseline_neighbors': neighbors}
        summary = {}
        base_ids = {r['chunk_id'] for r in anchors}
        for name, selected in variants.items():
            counts = Counter(r['arxiv_id'] for r in selected)
            for row in selected:
                frozen = by_id[row['chunk_id']]
                if any(row.get(k) != frozen.get(k) for k in ('text','source_url','arxiv_id')):
                    raise ValueError('Selected text/citation not in frozen corpus')
            summary[name] = {'passages': len(selected), 'papers': len(counts),
                'max_per_paper': max(counts.values(),default=0),
                'text_tokens': sum(count_tokens(r['text']) for r in selected),
                'baseline_overlap': len(base_ids & {r['chunk_id'] for r in selected})}
            obligations = case.get('required_evidence', [])
            if obligations:
                paper_hits = sum(o['arxiv_id'] in counts for o in obligations)
                quote_hits = sum(any(r['arxiv_id']==o['arxiv_id'] and
                    o.get('quote') is not None and o['quote'] in r['text'] for r in selected)
                    for o in obligations)
                summary[name]['obligation_coverage'] = {'required':len(obligations),
                    'papers_found':paper_hits, 'quotes_found':quote_hits,
                    'all_papers_found':paper_hits==len(obligations),
                    'all_quotes_found':quote_hits==len(obligations),
                    'scope':'agent-authored source/quote presence only, not synthesis quality'}
        artifact['cases'].append({'case':case,'expanded_query':rewritten,'variants':variants,
                                 'context_budget':budget,'observations':summary,
                                 'seconds_all_variants':round(time.monotonic()-start,3)})
        (args.output/'run.json').write_text(json.dumps(artifact,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'case':case['query_id'],'variants':len(variants),'seconds':
                         artifact['cases'][-1]['seconds_all_variants']}),flush=True)
    summary = {name: {key: round(sum(c['observations'][name][key] for c in artifact['cases'])/len(cases),3)
                            for key in ['passages','papers','max_per_paper','text_tokens','baseline_overlap']}
               for name in variants}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
