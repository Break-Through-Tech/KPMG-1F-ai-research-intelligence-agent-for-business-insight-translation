"""Paired retrieval-only capture; successful execution is NOT semantic acceptance.

Keeps all candidate assessments, selected passages, rejected attempts and provider
receipts. No answer generation, fallback, selective case replacement or scoring.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from evaluation.run_benchmarks import artifact_id, source_provenance, ROOT, CASES

CONTROLS = ROOT / 'evaluation/intent_controls.json'


def validate_cases(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError('A nonempty case list is required')
    ids = [c.get('query_id') for c in cases if isinstance(c, dict)]
    if (len(ids) != len(cases) or any(not isinstance(i, str) or not i.strip() for i in ids)
            or len(set(ids)) != len(ids)
            or any(not isinstance(c.get('query'), str) or not c['query'].strip() for c in cases)):
        raise ValueError('Cases require unique nonempty IDs and nonempty questions')


def capture_pairs(cases, *, baseline, intent, provenance, output, receipts, traces):
    """Both routes execute once per case; a rejection never becomes empty success."""
    validate_cases(cases)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    artifact = {'schema_version': 'intent-comparison-v1',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'provenance': deepcopy(provenance), 'top_k': 5,
                'semantic_acceptance': 'unreviewed', 'cases': []}
    for case in deepcopy(cases):
        row = {'case': case}
        for name, retrieve in [('baseline', baseline), ('intent', intent)]:
            receipt_start, trace_start = len(receipts), len(traces)
            try:
                passages = deepcopy(retrieve(case['query'], 5))
                if (not isinstance(passages, list) or not passages or len(passages) > 5
                        or any(not isinstance(p, dict) or not isinstance(p.get('chunk_id'), str)
                               or not p['chunk_id'] or not isinstance(p.get('text'), str)
                               or not p['text'].strip() for p in passages)
                        or len({p['chunk_id'] for p in passages}) != len(passages)):
                    raise ValueError('Invalid retrieval result')
                json.dumps(passages, allow_nan=False)
                row[name] = {'status': 'ok', 'selected': passages, 'error': None}
            except Exception as exc:
                row[name] = {'status': 'error', 'selected': None,
                             'error': {'type': type(exc).__name__,
                                       'message': 'Retrieval rejected; no fallback or replacement.'}}
            row[name]['receipt_range'] = [receipt_start, len(receipts)]
            row[name]['trace_range'] = [trace_start, len(traces)]
        artifact['cases'].append(row)
        artifact['run_id'] = artifact_id(artifact)
        for filename, value in [('run.json', artifact), ('receipts.json', receipts),
                                ('traces.json', traces)]:
            temporary = output / (filename + '.tmp')
            temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
            temporary.replace(output / filename)
        print(json.dumps({'query_id': case['query_id'],
                          **{name: row[name]['status'] for name in ('baseline', 'intent')}}), flush=True)
    return artifact


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True,
                        help='Frozen run binding corpus bytes AND indexed text/citations')
    parser.add_argument('--output', type=Path, required=True, help='New private artifact directory')
    parser.add_argument('--controls', type=Path, default=CONTROLS)
    parser.add_argument('--codex-bin', required=True)
    parser.add_argument('--model', required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error('Choose a new frozen output directory')
    cases = json.loads(CASES.read_text()) + json.loads(args.controls.read_text())
    validate_cases(cases)
    reference = json.loads(args.reference.read_text())
    if artifact_id(reference) != reference.get('run_id'):
        parser.error('Frozen reference hash mismatch')
    provenance = source_provenance(execution='persistent_corpus')
    for relative, digest in provenance['input_hashes'].items():
        if not digest or digest != reference['provenance']['input_hashes'].get(relative):
            parser.error('Corpus/metadata differs from the frozen reference')
    import pandas as pd
    import chromadb
    from sentence_transformers import SentenceTransformer, CrossEncoder
    from huggingface_hub import hf_hub_download
    from src import retrieval
    from src.hybrid_retrieval import HybridRetriever
    from src.intent_reranking import create_intent_rerank
    from src.codex_generation import create_codex_generate
    from evaluation.capture_validated_retrieval import reconcile

    frame = pd.read_parquet(ROOT / 'data/processed/chunks.parquet')
    client = chromadb.PersistentClient(path=str(ROOT / 'data/chroma_db'))
    index_hash = reconcile(client.get_collection(retrieval.COLLECTION_NAME), frame)
    if not index_hash or index_hash != reference['provenance'].get('indexed_corpus_sha256'):
        parser.error('Index differs from the frozen reference')
    dense_model = SentenceTransformer(retrieval.EMBEDDING_MODEL, local_files_only=True)
    cross_name = 'cross-encoder/ms-marco-MiniLM-L6-v2'
    cross = CrossEncoder(cross_name, local_files_only=True)
    passages = [{'chunk_id': r['chunk_id'], 'text': r['text'], **retrieval.citation_metadata(r)}
                for r in frame.to_dict('records')]
    def dense(query, count):
        return retrieval.search(query, count, client=client, model=dense_model)
    receipts, traces = [], []
    generate, generation = create_codex_generate(model=args.model, binary=args.codex_bin, receipts=receipts)
    def record_generate(prompt, *, response_schema):
        trace = {'prompt': prompt, 'schema': deepcopy(response_schema), 'response': None}
        traces.append(trace)
        trace['response'] = generate(prompt, response_schema=response_schema)
        return trace['response']
    record_generate.supports_response_schema = True
    rank, settings = create_intent_rerank(record_generate)
    def audited_rank(query, candidates):
        # Keep even rejected candidates; no known-answer IDs influence selection.
        trace = {'query': query, 'candidates': deepcopy(candidates), 'assessments': None}
        traces.append(trace)
        trace['assessments'] = rank(query, candidates)
        return trace['assessments']
    baseline = HybridRetriever(passages, dense_search=dense,
        rerank=lambda q, ps: cross.predict([(q, p['text']) for p in ps], show_progress_bar=False))
    intent = HybridRetriever(passages, dense_search=dense, rerank=audited_rank)
    model_files = {}
    for name in ('sentence-transformers/' + retrieval.EMBEDDING_MODEL, cross_name):
        weights = Path(hf_hub_download(name, 'model.safetensors', local_files_only=True))
        model_files[name] = {'revision': weights.parent.name,
                             'weights_sha256': sha256(weights.read_bytes()).hexdigest()}
    provenance.update(indexed_corpus_sha256=index_hash, corpus_mode='html_first', generation=generation,
        reference_run_id=reference['run_id'], reference_sha256=sha256(args.reference.read_bytes()).hexdigest(),
        cases_sha256=sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
        models=model_files, baseline_reranker=cross_name, intent_reranker=settings,
        implementation_hashes={p: sha256((ROOT / p).read_bytes()).hexdigest() for p in (
            'evaluation/compare_intent_retrieval.py', 'src/intent_reranking.py', 'src/hybrid_retrieval.py',
            'src/retrieval.py', 'src/codex_generation.py', 'src/quote_validation.py', 'src/evidence_led.py')},
        limitations=['Retrieval only; not generated-answer or business-quality acceptance.',
                     'Quote membership and model relevance scores are not independent semantic review.',
                     'No human/stakeholder approval is supplied.'])
    artifact = capture_pairs(cases, baseline=baseline, intent=intent, provenance=provenance,
                             output=args.output, receipts=receipts, traces=traces)
    return int(any(row[name]['status'] != 'ok' for row in artifact['cases']
                   for name in ('baseline', 'intent')))


if __name__ == '__main__':
    raise SystemExit(main())
