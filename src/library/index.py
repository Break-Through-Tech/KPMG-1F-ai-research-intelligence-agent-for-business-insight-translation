"""Incremental bundle builds: embed only new or changed papers, reuse cached vectors.

Each paper keeps its own view/vector cache keyed by the hash of its passages,
model and view settings. A build assembles all ready papers into a NEW standard
B2 bundle (parents.jsonl, views.json, vectors.npy, manifest.json), validates it
with the same loader the research engine uses, then switches the CURRENT pointer.
Earlier bundles stay available for rollback.
"""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import time

import numpy as np

from .store import now

MODEL = 'all-MiniLM-L6-v2'
BUDGET, OVERLAP = 224, 32


def _parents_hash(parents):
    return sha256(json.dumps(parents, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _cache_paths(store, row):
    shard = store.root / row['shard']
    stem = shard.with_suffix('')
    return shard, stem.with_name(stem.name + '.views.json'), stem.with_name(stem.name + '.vectors.npy'), \
        stem.with_name(stem.name + '.cache.json')


def seed_from_bundle(store, bundle):
    """Import an existing B2 bundle's papers as library papers, reusing its exact vectors."""
    bundle = Path(bundle)
    parents = [json.loads(l) for l in (bundle / 'parents.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    views = json.loads((bundle / 'views.json').read_text(encoding='utf-8'))
    vectors = np.load(bundle / 'vectors.npy', allow_pickle=False)
    manifest = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('strategy') != 'token224_parent' or manifest.get('embedding_model') != MODEL:
        raise ValueError('Seed bundle must use the same view strategy and embedding model.')
    by_paper = {}
    for p in parents:
        by_paper.setdefault(p['arxiv_id'], []).append(p)
    owner = {p['chunk_id']: p['arxiv_id'] for p in parents}
    rows = {}
    for i, v in enumerate(views):
        rows.setdefault(owner[v['parent_chunk_id']], []).append(i)
    from src.arxiv_collection import identity
    added = 0
    for arxiv_id, papers in by_paper.items():
        base, version = identity(arxiv_id)
        if store.db.execute('SELECT 1 FROM papers WHERE base_id=?', (base,)).fetchone():
            continue
        folder = store.root / 'papers' / base
        folder.mkdir(parents=True, exist_ok=True)
        shard = folder / f'{arxiv_id}.jsonl'
        shard.write_text('\n'.join(json.dumps(p, ensure_ascii=False) for p in papers), encoding='utf-8')
        idx = rows[arxiv_id]
        stem = shard.with_suffix('')
        stem.with_name(stem.name + '.views.json').write_text(json.dumps([views[i] for i in idx], ensure_ascii=False), encoding='utf-8')
        np.save(stem.with_name(stem.name + '.vectors.npy'), vectors[idx], allow_pickle=False)
        stem.with_name(stem.name + '.cache.json').write_text(json.dumps(
            {'parents_sha256': _parents_hash(papers), 'model': MODEL, 'budget': BUDGET, 'overlap': OVERLAP,
             'origin': str(bundle)}), encoding='utf-8')
        store.db.execute(
            'INSERT INTO papers(base_id, arxiv_id, version, title, categories, topics, topic, topic_rank, source,'
            ' status, latest_seen_version, shard, parents, discovered_at, extracted_at) '
            'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (base, arxiv_id, version, papers[0]['title'], '', json.dumps(['existing-library']), 'existing-library',
             -1, 'seed', 'extracted', version, str(shard.relative_to(store.root)), len(papers), now(), now()))
        store.db.execute('INSERT OR IGNORE INTO versions(base_id, version, arxiv_id, first_seen, ingested_at) '
                         'VALUES (?,?,?,?,?)', (base, version, arxiv_id, now(), now()))
        added += 1
    store.event('seeded', None, f'{added} papers from {bundle}')
    store.commit()
    return added


def build(store, encoder, *, log=print, keep=2, batch_size=64):
    """Assemble every extracted/indexed paper into a new bundle; embed only what changed."""
    from src.experimental.search_chunks import make_search_views
    from src.experimental.search_index import SearchViewIndex
    started = time.perf_counter()
    rows = store.db.execute("SELECT * FROM papers WHERE status IN ('extracted','indexed','update_available') "
                            "AND shard IS NOT NULL ORDER BY base_id").fetchall()
    papers, pending, reused = [], [], 0
    for row in rows:
        shard, views_path, vectors_path, meta_path = _cache_paths(store, row)
        parents = [json.loads(l) for l in shard.read_text(encoding='utf-8').splitlines() if l.strip()]
        key = {'parents_sha256': _parents_hash(parents), 'model': MODEL, 'budget': BUDGET, 'overlap': OVERLAP}
        cached = json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.is_file() else {}
        if all(cached.get(k) == v for k, v in key.items()) and views_path.is_file() and vectors_path.is_file():
            views = json.loads(views_path.read_text(encoding='utf-8'))
            vectors = np.load(vectors_path, allow_pickle=False)
            reused += 1
        else:
            views = make_search_views(parents, encoder.tokenizer, budget=BUDGET, overlap=OVERLAP)
            vectors = None
            pending.append(len(papers))
        papers.append({'row': row, 'parents': parents, 'views': views, 'vectors': vectors,
                       'paths': (views_path, vectors_path, meta_path), 'key': key})
    if pending:
        texts = [v['text'] for i in pending for v in papers[i]['views']]
        log(f'embedding {len(texts)} views for {len(pending)} new or changed papers (reusing {reused})')
        encoded = np.asarray(encoder.encode(texts, batch_size=batch_size, show_progress_bar=False), dtype=np.float32)
        offset = 0
        for i in pending:
            n = len(papers[i]['views'])
            vectors = encoded[offset:offset + n]
            offset += n
            views_path, vectors_path, meta_path = papers[i]['paths']
            views_path.write_text(json.dumps(papers[i]['views'], ensure_ascii=False), encoding='utf-8')
            np.save(vectors_path, vectors, allow_pickle=False)
            meta_path.write_text(json.dumps(papers[i]['key']), encoding='utf-8')
            papers[i]['vectors'] = vectors
    all_parents = [p for paper in papers for p in paper['parents']]
    all_views = [v for paper in papers for v in paper['views']]
    all_vectors = np.concatenate([paper['vectors'] for paper in papers]).astype(np.float32)
    if all_vectors.shape != (len(all_views), 384) or not np.isfinite(all_vectors).all():
        raise ValueError('Assembled vectors do not match the views.')
    stamp_id = time.strftime('%Y%m%dT%H%M%S')
    bundle_id, n = stamp_id, 1
    while (store.root / 'bundles' / bundle_id).exists():  # never overwrite an earlier bundle
        n += 1
        bundle_id = f'{stamp_id}-{n}'
    out = store.root / 'bundles' / bundle_id
    out.mkdir(parents=True, exist_ok=False)
    (out / 'parents.jsonl').write_text('\n'.join(json.dumps(p, ensure_ascii=False, allow_nan=False)
                                                for p in all_parents), encoding='utf-8')
    (out / 'views.json').write_text(json.dumps(all_views, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    np.save(out / 'vectors.npy', all_vectors, allow_pickle=False)
    manifest = {'kind': 'bounded_search_views_v1', 'status': 'complete', 'strategy': 'token224_parent',
                'embedding_model': MODEL, 'distance': 'squared_l2', 'human_acceptance': 'pending',
                'parent_count': len(all_parents), 'view_count': len(all_views),
                'paper_count': len(papers),
                'artifact_sha256': {n: sha256((out / n).read_bytes()).hexdigest()
                                    for n in ['parents.jsonl', 'views.json', 'vectors.npy']}}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    log('validating bundle with the research engine loader')
    try:
        SearchViewIndex(out, model=encoder)
    except Exception:
        manifest['status'] = 'invalid'
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        raise
    tmp = store.root / 'CURRENT.tmp'
    tmp.write_text(bundle_id, encoding='utf-8')
    tmp.replace(store.root / 'CURRENT')
    stamp = now()
    for paper in papers:
        row = paper['row']
        store.mark(row['base_id'], 'indexed' if row['status'] != 'update_available' else 'update_available',
                   bundle_id=bundle_id, indexed_at=row['indexed_at'] or stamp)
    seconds = round(time.perf_counter() - started, 1)
    size = sum(f.stat().st_size for f in out.iterdir())
    store.db.execute('INSERT INTO bundles VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                     (bundle_id, stamp, len(papers), len(all_parents), len(all_views), len(pending), reused,
                      seconds, size, str(out), 'current'))
    store.db.execute("UPDATE bundles SET status='previous' WHERE bundle_id<>?", (bundle_id,))
    store.event('bundle_built', None, f'{bundle_id}: {len(papers)} papers, embedded {len(pending)}, reused {reused}')
    store.commit()
    old = sorted(p.name for p in (store.root / 'bundles').iterdir() if p.is_dir() and p.name != bundle_id)
    for name in old[:-max(0, keep - 1)] if keep > 1 else old:
        shutil.rmtree(store.root / 'bundles' / name)
        store.db.execute("UPDATE bundles SET status='pruned' WHERE bundle_id=?", (name,))
    store.commit()
    return {'bundle_id': bundle_id, 'path': str(out), 'papers': len(papers), 'parents': len(all_parents),
            'views': len(all_views), 'embedded_papers': len(pending), 'reused_papers': reused,
            'seconds': seconds, 'bytes': size}


def current_bundle(root):
    pointer = Path(root) / 'CURRENT'
    return Path(root) / 'bundles' / pointer.read_text(encoding='utf-8').strip() if pointer.is_file() else None
