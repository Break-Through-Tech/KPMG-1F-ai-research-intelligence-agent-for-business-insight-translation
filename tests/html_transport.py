"""Disk-backed Azure-shaped test double. NOT an Azure service emulator or vector DB choice."""
import hashlib
import json
import sqlite3
from contextlib import closing
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from src import retrieval


class DeterministicModel:
    """Exact-text fingerprint vectors; cannot establish semantic relevance."""
    def encode(self, text):
        digest = hashlib.sha256(text.encode()).digest()
        vector = np.tile(np.frombuffer(digest, dtype=np.uint8).astype(float) - 127, 12)
        return vector / np.linalg.norm(vector)


class PersistentDouble:
    def __init__(self, path):
        self.path = path
        with closing(sqlite3.connect(path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, body TEXT)')

    def upload_documents(self, documents):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executemany('INSERT OR REPLACE INTO documents VALUES (?, ?)',
                           [(d['chunk_id'], json.dumps(d)) for d in documents])
        return [SimpleNamespace(succeeded=True) for _ in documents]

    def get_document_count(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            return db.execute('SELECT count(*) FROM documents').fetchone()[0]

    def documents(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            return [json.loads(row[0]) for row in db.execute('SELECT body FROM documents ORDER BY id')]

    def search(self, *, vector_queries, top, **kwargs):
        vector = np.asarray(vector_queries[0].vector)
        hits = [dict(d, **{'@search.score': float(np.dot(vector, d['embedding']))})
                for d in self.documents()]
        return sorted(hits, key=lambda d: d['@search.score'], reverse=True)[:top]

    def list_index_names(self):
        return [retrieval.INDEX_NAME]

    def delete_index(self, name):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DELETE FROM documents')

    def create_index(self, index):
        return index


def validate_transport(frame, path):
    """Exercise production serialization/search/rebuild through a disposable persistent double."""
    store = PersistentDouble(path)
    model = DeterministicModel()
    vectors = np.array([model.encode(text) for text in frame.text])
    with patch.object(retrieval, 'SearchClient', side_effect=AssertionError('Live Azure forbidden')), \
         patch.object(retrieval, 'SearchIndexClient', side_effect=AssertionError('Live Azure forbidden')), \
         patch.object(retrieval, 'get_search_client', return_value=store), \
         patch.object(retrieval, 'get_index_client', return_value=store):
        retrieval.store_embeddings(frame, vectors)
        first = store.get_document_count()
        retrieval.store_embeddings(frame, vectors)
        if store.get_document_count() != len(frame):
            raise AssertionError('Rerun duplicated records')
        # Reopen from disk, not an in-memory mock return value.
        reopened = PersistentDouble(path)
        expected = {retrieval.make_azure_key(row['chunk_id']): row for row in frame.to_dict('records')}
        for document in reopened.documents():
            row = expected[document['chunk_id']]
            if document['text'] != row['text']:
                raise AssertionError('Persisted passage changed')
            for key, value in retrieval.citation_metadata(row).items():
                if document[key] != value:
                    raise AssertionError(f'Persisted citation changed: {key}')
        queries = []
        for _, paper in frame.groupby('arxiv_id'):
            row = paper.iloc[0].to_dict()
            hits = retrieval.search_chunks(row['text'], top_k=3, client=reopened, model=model)
            if not any(hit['text'] == row['text'] for hit in hits):
                raise AssertionError('Exact-text transport probe failed')
            for hit in hits:
                original = expected[hit['chunk_id']]
                if hit['text'] != original['text']:
                    raise AssertionError('Retrieved text changed')
                for key, value in retrieval.citation_metadata(original).items():
                    if hit[key] != value:
                        raise AssertionError('Retrieved citation changed')
            queries.append({'paper': row['arxiv_id'], 'query_kind': 'exact passage text',
                            'returned_ids': [hit['chunk_id'] for hit in hits]})
        # A smaller corpus without resetting demonstrates the real upsert limitation.
        reduced = frame.iloc[:-1]
        retrieval.store_embeddings(reduced, vectors[:-1])
        stale_after_upsert = store.get_document_count() - len(reduced)
        if stale_after_upsert != 1:
            raise AssertionError('Expected stale row after upload-only operation')
        retrieval.create_index(rebuild=True)  # Patched management client: SQLite only.
        retrieval.store_embeddings(reduced, vectors[:-1])
        if len(store.documents()) != len(reduced) or retrieval.make_azure_key(frame.iloc[-1].chunk_id) in {
                d['chunk_id'] for d in store.documents()}:
            raise AssertionError('Explicit isolated rebuild retained stale row')
        return {'backend': 'SQLite-backed Azure client test double, NOT live Azure',
                'model': 'SHA256 deterministic 384-dimensional fingerprint; NOT MiniLM',
                'first_count': first, 'rerun_count': first, 'reopened_verified_records': len(expected),
                'query_probes': queries, 'stale_rows_after_upload_only': stale_after_upsert,
                'count_after_explicit_rebuild': store.get_document_count(),
                'live_azure_requests': 0, 'semantic_relevance_tested': False}
