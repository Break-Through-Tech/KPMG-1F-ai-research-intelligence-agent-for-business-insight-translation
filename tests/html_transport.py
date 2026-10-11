"""Real isolated Chroma persistence with deterministic vectors, not semantic evaluation."""
import hashlib
import json
import subprocess
import sys
import math
from pathlib import Path
from unittest.mock import patch

import chromadb
import numpy as np
from src import retrieval


class DeterministicModel:
    """Exact-text fingerprint vectors; never presented as MiniLM relevance."""
    def encode(self, texts, **kwargs):
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vector = np.tile(np.frombuffer(digest, dtype=np.uint8).astype(float) - 127, 12)
            vectors.append(vector / np.linalg.norm(vector))
        return np.array(vectors)


def validate_transport(frame, path):
    """Use a child process so native Chroma handles close before temp cleanup."""
    path = Path(path)
    input_path = path.with_suffix('.parquet')
    output_path = path.with_suffix('.json')
    frame.to_parquet(input_path, index=False)
    subprocess.run([sys.executable, '-m', 'tests.html_transport', str(input_path),
                    str(path), str(output_path)], check=True, timeout=240)
    return json.loads(output_path.read_text(encoding='utf-8'))


def run_transport(frame, path):
    model = DeterministicModel()
    vectors = model.encode(frame.text.tolist())
    with patch.object(retrieval, 'CHROMA_DIR', Path(path)):
        collection = retrieval.store_embeddings(frame, vectors)
        first = collection.count()
        retrieval.store_embeddings(frame, vectors)
        rerun = collection.count()
        assert rerun == len(frame), 'Rerun duplicated rows'
        # Read in a fresh OS process to verify real on-disk persistence.
        snapshot = Path(path).with_suffix('.snapshot.json')
        subprocess.run([sys.executable, '-c',
            'import chromadb,json,sys; c=chromadb.PersistentClient(path=sys.argv[1]).get_collection(sys.argv[2]); '
            'open(sys.argv[3],"w",encoding="utf-8").write(json.dumps(c.get(include=["documents","metadatas"])))',
            str(path), retrieval.COLLECTION_NAME, str(snapshot)], check=True, timeout=90)
        stored = json.loads(snapshot.read_text(encoding='utf-8'))
        expected = {row['chunk_id']: row for row in frame.to_dict('records')}
        assert set(stored['ids']) == set(expected), 'Original IDs changed'
        for cid, text, metadata in zip(stored['ids'], stored['documents'], stored['metadatas']):
            assert text == expected[cid]['text'], 'Persisted passage changed'
            assert metadata == retrieval.citation_metadata(expected[cid]), 'Persisted citation changed'
        client = chromadb.PersistentClient(path=str(path))
        probes=[]
        for _, paper in frame.groupby('arxiv_id'):
            row=paper.iloc[0].to_dict()
            hits=retrieval.search(row['text'], top_k=3, client=client, model=model)
            assert any(hit['text']==row['text'] for hit in hits), 'Exact-text retrieval failed'
            for hit in hits:
                required = {'chunk_id','text','distance','arxiv_id','title','pdf_url','source','source_url','page_number'}
                assert required <= hit.keys(), 'Public search contract changed'
                assert 'score' not in hit and math.isfinite(hit['distance'])
                original=expected[hit['chunk_id']]
                assert hit['text']==original['text']
                for key,value in retrieval.citation_metadata(original).items():
                    assert hit[key]==value, f'Retrieved citation differs: {key}'
                if hit['source']=='html':
                    assert hit['page_number'] is None
                else:
                    assert hit['source_url'].endswith(f"#page={hit['page_number']}")
            probes.append({'paper':row['arxiv_id'], 'query_kind':'exact passage text',
                           'returned_ids':[hit['chunk_id'] for hit in hits]})
        updated=frame.copy()
        updated.loc[updated.index[0],'title']='Updated title for isolated validation'
        retrieval.store_embeddings(updated,vectors)
        assert collection.get(ids=[str(frame.iloc[0].chunk_id)])['metadatas'][0]['title']==updated.iloc[0].title
        reduced=updated.iloc[:-1].copy()
        baseline=collection.get(include=['documents','metadatas'])
        # Failure before an upsert starts must leave existing records unchanged.
        with patch.object(type(collection), 'upsert', side_effect=RuntimeError('injected before upsert')):
            try:
                retrieval.store_embeddings(reduced,vectors[:-1])
            except RuntimeError:
                pass
            else:
                raise AssertionError('Injected upsert failure was not propagated')
        assert collection.get(include=['documents','metadatas']) == baseline
        # Failure AFTER upsert but BEFORE stale deletion does not provide rollback.
        partial=reduced.copy()
        partial.loc[partial.index[0],'title']='Partial update before stale-delete failure'
        with patch.object(type(collection), 'delete', side_effect=RuntimeError('injected stale-delete failure')):
            try:
                retrieval.store_embeddings(partial,vectors[:-1])
            except RuntimeError:
                pass
            else:
                raise AssertionError('Injected delete failure was not propagated')
        assert collection.count()==len(frame), 'Expected stale row to remain after failed deletion'
        assert collection.get(ids=[str(frame.iloc[0].chunk_id)])['metadatas'][0]['title']==partial.iloc[0].title
        assert retrieval.search(partial.iloc[0].text,client=client,model=model)
        # A successful retry repairs this demonstrated partial-update state.
        retrieval.store_embeddings(reduced,vectors[:-1])
        assert collection.count()==len(reduced)
        assert str(frame.iloc[-1].chunk_id) not in collection.get()['ids']
        baseline=collection.get(include=['documents','metadatas'])
        bad=reduced.copy()
        bad['source']='pdf'
        bad['page_number']=None
        try:
            retrieval.store_embeddings(bad,vectors[:-1])
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid citations were accepted')
        assert collection.get(include=['documents','metadatas'])==baseline, 'Invalid input changed usable data'
        assert retrieval.search(reduced.iloc[0].text,client=client,model=model), 'Data no longer searchable'
        return {'backend':'Real temporary Chroma PersistentClient', 'chroma_version':chromadb.__version__,
                'model':'SHA256 deterministic 384-dimensional fingerprint; NOT MiniLM',
                'first_count':first, 'rerun_count':rerun, 'reopened_verified_records':len(expected),
                'reopened_in_fresh_process':True, 'original_ids_preserved':True,
                'query_probes':probes, 'updated_record_verified':True,
                'stale_rows_removed':1, 'count_after_corpus_rerun':collection.count(),
                'invalid_input_preserved_usable_data':True, 'semantic_relevance_tested':False, 'public_contract_verified':True,
                'pre_upsert_failure_preserved_data':True,
                'post_upsert_delete_failure':{'stale_record_remained':True, 'updated_metadata_visible':True,
                    'searchable':True, 'retry_repaired':True, 'full_corpus_rollback':False}}



# Expected papers and evidence are fixed BEFORE embedding or querying.
SEMANTIC_PROBES = [
    ('How can we evaluate agents using realistic multi-step workflows across external tool servers?',
     '2602.00933v3', 'MCP-Atlas'),
    ('How can point clouds and action information improve three-dimensional robotic manipulation pretraining?',
     '2602.00937v3', 'CLAMP'),
    ('Can Fourier transforms replace attention to reduce the cost of processing long sequences?',
     '2605.00292v2', 'Fourier'),
]


def implementation_hashes():
    root = Path(__file__).resolve().parents[1]
    paths = [Path(__file__), Path(__file__).with_name('validate_html_sample.py'),
             root/'src/retrieval.py', *sorted((root/'src/data_ingestion').glob('*.py'))]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run_semantic(frame, path, *, corpus_path):
    """Offline bounded relevance smoke test, never downloads a model or uses a shared DB."""
    provenance = implementation_hashes()
    corpus_hash = hashlib.sha256(Path(corpus_path).read_bytes()).hexdigest()
    import os
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    import torch
    torch.set_num_threads(2)
    expected = []
    for query, aid, marker in SEMANTIC_PROBES:
        candidates = frame[(frame.arxiv_id == aid) & frame.text.str.contains(marker, regex=False)]
        if candidates.empty:
            raise ValueError(f'Expected source evidence not found before search: {aid} / {marker}')
        expected.append({'query': query, 'expected_paper': aid,
                         'expected_evidence_ids': candidates.chunk_id.tolist(),
                         'expected_evidence_excerpt': candidates.iloc[0].text[:350]})
    model = retrieval.SentenceTransformer(retrieval.EMBEDDING_MODEL, local_files_only=True, device='cpu')
    # Exercise the production embedding entrypoint with the cached actual model.
    with patch.object(retrieval, 'SentenceTransformer', return_value=model), \
         patch.object(retrieval, 'CHROMA_DIR', Path(path)):
        vectors = retrieval.create_embeddings(frame)
        assert vectors.shape == (len(frame), 384)
        collection = retrieval.store_embeddings(frame, vectors)
        client = chromadb.PersistentClient(path=str(path))
        records = {r['chunk_id']: r for r in frame.to_dict('records')}
        for probe in expected:
            hits = retrieval.search(probe['query'], top_k=5, client=client, model=model)
            for hit in hits:
                row = records[hit['chunk_id']]
                assert hit['text'] == row['text']
                assert retrieval.citation_metadata(row) == retrieval.citation_metadata(hit)
                assert hit['page_number'] is None
                assert math.isfinite(hit['distance']) and 'score' not in hit
            probe['expected_paper_in_top_5'] = any(h['arxiv_id'] == probe['expected_paper'] for h in hits)
            probe['hits'] = hits
        assert implementation_hashes() == provenance, 'Implementation changed during semantic run'
        assert hashlib.sha256(Path(corpus_path).read_bytes()).hexdigest() == corpus_hash, 'Corpus changed during semantic run'
        return {'status':'COMPLETED', 'source':'cached original corpus',
                'run_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'corpus_sha256': corpus_hash, 'implementation_hashes': provenance,
                'command': 'python -m tests.html_transport ' + ' '.join(sys.argv[1:]),
                'model':retrieval.EMBEDDING_MODEL,'local_files_only':True,'device':'cpu',
                'dimensions':384,'indexed_count':collection.count(), 'citation_checks':'PASS',
                'probes':expected, 'expected_paper_hits':sum(p['expected_paper_in_top_5'] for p in expected),
                'limitation':'Three content-informed questions, no held-out benchmark or calibrated relevance scores.'}


if __name__=='__main__':
    import pandas as pd
    runner = run_semantic if '--semantic' in sys.argv[4:] else run_transport
    kwargs = {'corpus_path': Path(sys.argv[1])} if runner is run_semantic else {}
    result=runner(pd.read_parquet(sys.argv[1]),sys.argv[2], **kwargs)
    Path(sys.argv[3]).write_text(json.dumps(result,indent=2),encoding='utf-8')
