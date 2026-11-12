"""Portable opt-in adapter for the balanced evidence retrieval candidate."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import numpy as np
from .balanced_retriever import FacetRetriever
from .search_index import SearchViewIndex

METHOD = 'document-table-balanced-facets-v1'

def open_b2(index_path, *, encoder_path, reranker_path, encoder=None, reranker=None):
    """Require explicitly selected local artifacts; never fall back or download."""
    model_paths = [Path(encoder_path).resolve(), Path(reranker_path).resolve()]
    if any(not p.is_dir() for p in model_paths):
        raise ValueError('Specify existing local encoder and reranker directories; no download attempted.')
    if encoder is None or reranker is None:
        from sentence_transformers import SentenceTransformer, CrossEncoder
        if encoder is None:
            encoder = SentenceTransformer(str(model_paths[0]), local_files_only=True, device='cpu')
        if reranker is None:
            reranker = CrossEncoder(str(model_paths[1]), local_files_only=True, device='cpu')
    index = SearchViewIndex(index_path, model=encoder)
    if index.manifest['strategy'] not in {'token224_parent', 'semantic95_token224_parent'}:
        raise ValueError('B2 requires the bounded token224_parent bundle; no alternate strategy selected.')
    engine = FacetRetriever(index, reranker, encoder)
    here = Path(__file__).resolve().parent
    names = ('b2.py','retriever.py','balanced_retriever.py','evidence_coverage.py','search_index.py','search_chunks.py','semantic_views.py')
    hashes = {name: sha256((here/name).read_bytes()).hexdigest() for name in names}
    if index.manifest['strategy'] == 'semantic95_token224_parent':
        import src.semantic_chunking_adapter as adapter
        import src.semantic_chunking as chunking
        dependencies = {Path(m.__file__): sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (adapter, chunking)}
    else:
        dependencies = {}
    hashes.update({str(path.relative_to(here.parent)): digest for path, digest in dependencies.items()})
    def identity():
        for path, digest in dependencies.items():
            if sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError('Semantic implementation changed; restart before querying.')
        for name, digest in hashes.items():
            if sha256((here/name if name in names else here.parent/name).read_bytes()).hexdigest() != digest:
                raise ValueError('Retrieval implementation changed; restart before querying.')
        return {**index.identity(), 'candidate_algorithm': METHOD, 'algorithm_sha256': deepcopy(hashes)}
    def retrieve(query, top_k=5):
        identity()
        if not isinstance(query,str) or not query.strip():
            raise ValueError('Nonempty question required.')
        if isinstance(top_k,bool) or not isinstance(top_k,int) or not 1 <= top_k <= 20:
            raise ValueError('top_k must be 1..20.')
        if index.token_count(query) > encoder.max_seq_length:
            raise ValueError('Query would truncate; shorten it before retrying.')
        vector = np.asarray(encoder.encode([query],show_progress_bar=False),dtype=np.float32)
        if vector.shape != (1,384) or not np.isfinite(vector).all():
            raise ValueError('Invalid query embedding.')
        order, _ = engine.rank_facets(query,vector[0])
        return engine.resolve(order,top_k)
    return retrieve, identity, str(index.path), {
        'method':METHOD,'strategy':index.manifest['strategy'],'experimental':True,'human_acceptance':'pending',
        'generation_calls':0,'document_index_rebuilt':False,
        'embedding_model':'all-MiniLM-L6-v2','reranker':str(model_paths[1]),
        'algorithm_sha256':hashes}
