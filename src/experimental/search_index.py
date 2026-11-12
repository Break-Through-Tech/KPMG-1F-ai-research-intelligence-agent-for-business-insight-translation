"""Read-only experimental retrieval over bounded views and complete source parents."""
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from .search_chunks import collapse_to_parents
from src.research_contracts import validate_evidence


ARTIFACTS = {'parents.jsonl', 'views.json', 'vectors.npy'}


def load_artifacts(path):
    """Require a complete, explicitly selected bundle; never build or download it."""
    import numpy as np
    path = Path(path).resolve()
    raw = (path / 'manifest.json').read_bytes()
    manifest = json.loads(raw)
    if (not isinstance(manifest, dict) or manifest.get('kind') != 'bounded_search_views_v1'
            or manifest.get('status') != 'complete'
            or not isinstance(manifest.get('artifact_sha256'), dict)
            or set(manifest.get('artifact_sha256', {})) != ARTIFACTS
            or manifest.get('embedding_model') != 'all-MiniLM-L6-v2'
            or manifest.get('distance') != 'squared_l2'
            or manifest.get('human_acceptance') != 'pending'
            or manifest.get('strategy') not in {'token224_parent', 'semantic95_token224_parent'}):
        raise ValueError('Select a complete, compatible experimental search-view bundle.')
    artifacts = {}
    for name, expected in manifest['artifact_sha256'].items():
        artifacts[name] = (path / name).read_bytes()
        if sha256(artifacts[name]).hexdigest() != expected:
            raise ValueError('Search-view artifact changed: ' + name)
    parents = [json.loads(line) for line in artifacts['parents.jsonl'].decode('utf-8').splitlines()]
    views = json.loads(artifacts['views.json'])
    vectors = np.load(BytesIO(artifacts['vectors.npy']), allow_pickle=False)
    validate_evidence(parents)
    if (vectors.dtype != np.float32 or vectors.ndim != 2
            or vectors.shape != (len(views), 384) or not np.isfinite(vectors).all()
            or len(parents) != manifest.get('parent_count')
            or len(views) != manifest.get('view_count') or not views):
        raise ValueError('Incomplete or incompatible search-view embeddings.')
    # Also checks complete parent hashes, exact view offsets and unique view IDs.
    collapse_to_parents(views, [0.0] * len(views), parents, top_k=len(parents))
    represented = {v['parent_chunk_id'] for v in views}
    if represented != {p['chunk_id'] for p in parents}:
        raise ValueError('Some source parents have no searchable view.')
    by_parent = {}
    for v in views:  # group once: the per-parent scan was quadratic at library scale
        by_parent.setdefault(v['parent_chunk_id'], []).append((v['char_start'], v['char_end']))
    for parent in parents:
        intervals = sorted(by_parent.get(parent['chunk_id'], ()))
        end = 0
        for start, stop in intervals:
            if start > end and parent['text'][end:start].strip():
                raise ValueError('Search views leave source text uncovered.')
            end = max(end, stop)
        if parent['text'][end:].strip():
            raise ValueError('Search views omit the source ending.')
    return manifest, parents, views, vectors, sha256(raw).hexdigest()


class SearchViewIndex:
    def __init__(self, path, *, model=None):
        self.path = Path(path).resolve()
        manifest, parents, views, vectors, manifest_hash = load_artifacts(self.path)
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(manifest['embedding_model'], local_files_only=True)
        self.model, self.manifest = model, manifest
        self.parents, self.views, self.vectors = parents, views, vectors
        self.manifest_hash = manifest_hash
        if model.max_seq_length < 224:
            raise ValueError('The cached embedding model cannot accept the declared views.')
        for view in views:
            count = self.token_count(view['text'])
            if count != view['text_tokens'] or count > 224:
                raise ValueError('Search input violates its actual tokenizer limit.')
        self._identity = {
            'collection': 'experimental_complete_parent_search', 'count': len(parents),
            'metadata': {'embedding_model': manifest['embedding_model'], 'strategy': manifest['strategy'],
                         'search_views': len(views), 'human_acceptance': 'pending'},
            'indexed_records_sha256': manifest['artifact_sha256']['parents.jsonl'],
            'embedding_bytes_sha256': manifest['artifact_sha256']['vectors.npy'],
            'identity_limits': 'Local artifact integrity; source certification and human acceptance remain pending.'}

    def token_count(self, text):
        return len(self.model.tokenizer(text, add_special_tokens=True, truncation=False,
                                        verbose=False)['input_ids'])

    def identity(self):
        if sha256((self.path / 'manifest.json').read_bytes()).hexdigest() != self.manifest_hash:
            raise ValueError('Search-view selection changed; restart the host.')
        for name, expected in self.manifest['artifact_sha256'].items():
            if sha256((self.path / name).read_bytes()).hexdigest() != expected:
                raise ValueError('Search-view source changed; restart the host.')
        return deepcopy(self._identity)

    def retrieve(self, query, top_k=5):
        import numpy as np
        self.identity()
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ValueError('top_k must be an integer from 1 to 20.')
        if not isinstance(query, str) or not query.strip():
            raise ValueError('Enter a nonempty search question.')
        if self.token_count(query) > self.model.max_seq_length:
            raise ValueError('Shorten the question to fit the search encoder; it was not silently truncated.')
        query_vector = np.asarray(self.model.encode([query], show_progress_bar=False), dtype=np.float32)
        if query_vector.shape != (1, 384) or not np.isfinite(query_vector).all():
            raise ValueError('Invalid query embedding.')
        distances = np.sum((self.vectors - query_vector[0]) ** 2, axis=1)
        hits = collapse_to_parents(self.views, distances, self.parents, top_k=top_k)
        for hit in hits:
            # Ranking/debug fields are not evidence or model instructions. Keep
            # the supplied source representation identical to the frozen test.
            for key in ('distance', 'retrieval', 'text_tokens', 'exceeds_embedding_limit',
                        'normalized_text_in_single_frozen_chunk', 'same_text_in_baseline'):
                hit.pop(key, None)
        validate_evidence(hits)
        return hits
