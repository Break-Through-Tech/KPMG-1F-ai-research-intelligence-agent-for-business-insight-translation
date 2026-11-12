"""Prove papers are searchable, not merely stored.

1. Integrity: the current bundle loads through the research engine's own validator,
   and every indexed paper row has at least one searchable view in it.
2. Known-item search over ALL papers: each paper's title (which is not part of any
   indexed passage text) is used as a query; the paper must appear in the top-k.
3. Engine sample: the full B2 retrieval path (hybrid + reranker) on a stratified
   sample, with latency.
"""
import json
import random
import time

import numpy as np


def known_item(bundle_parents, views, vectors, encoder, papers, *, k=10, chunk=64):
    owner = {p['chunk_id']: p['arxiv_id'] for p in bundle_parents}
    view_paper = np.array([owner[v['parent_chunk_id']] for v in views])
    titles = [p['title'] for p in papers]
    q = np.asarray(encoder.encode(titles, batch_size=64, show_progress_bar=False), dtype=np.float32)
    v2 = np.sum(vectors ** 2, axis=1)
    ranks = []
    for s in range(0, len(papers), chunk):
        block = q[s:s + chunk]
        d = v2[None, :] - 2 * block @ vectors.T + np.sum(block ** 2, axis=1)[:, None]
        for row, paper in zip(d, papers[s:s + chunk]):
            order = np.argsort(row)
            seen, rank = [], None
            for i in order:
                pid = view_paper[i]
                if pid not in seen:
                    seen.append(pid)
                    if pid == paper['arxiv_id']:
                        rank = len(seen)
                        break
                    if len(seen) >= k:
                        break
            ranks.append(rank)
    return ranks


def verify(store, encoder, bundle, *, k=10, engine_sample=60, reranker_path=None, encoder_path=None, seed=7):
    from src.experimental.search_index import load_artifacts
    t0 = time.perf_counter()
    manifest, parents, views, vectors, _ = load_artifacts(bundle)
    load_s = round(time.perf_counter() - t0, 1)
    in_bundle = {p['arxiv_id'] for p in parents}
    rows = store.db.execute("SELECT base_id, arxiv_id, title, topic, topics, source FROM papers "
                            "WHERE status IN ('indexed','update_available')").fetchall()
    papers = [dict(r) for r in rows]
    missing = [p['arxiv_id'] for p in papers if p['arxiv_id'] not in in_bundle]
    bases = [p['base_id'] for p in papers]
    t1 = time.perf_counter()
    ranks = known_item(parents, views, vectors, encoder, papers, k=k)
    known_s = round(time.perf_counter() - t1, 1)
    hit1 = sum(r == 1 for r in ranks)
    hitk = sum(r is not None for r in ranks)
    by_topic = {}
    for paper, rank in zip(papers, ranks):
        t = by_topic.setdefault(paper['topic'], [0, 0])
        t[0] += rank is not None
        t[1] += 1
    report = {'bundle': str(bundle), 'papers_indexed': len(papers), 'unique_base_ids': len(set(bases)),
              'unique_versioned_ids_in_bundle': len(in_bundle), 'parents': len(parents), 'views': len(views),
              'missing_from_bundle': missing, 'bundle_load_seconds': load_s,
              'known_item': {'query': 'paper title (not in indexed passage text)', 'k': k,
                             'hit_at_1': hit1, f'hit_at_{k}': hitk, 'total': len(papers),
                             'seconds': known_s, 'by_topic': {t: f'{a}/{b}' for t, (a, b) in by_topic.items()},
                             'not_found': [p['arxiv_id'] for p, r in zip(papers, ranks) if r is None][:50]}}
    if engine_sample and reranker_path and encoder_path:
        from src.experimental.b2 import open_b2
        retrieve = open_b2(bundle, encoder_path=encoder_path, reranker_path=reranker_path, encoder=encoder)[0]
        sample = random.Random(seed).sample(papers, min(engine_sample, len(papers)))
        hits, times = 0, []
        for paper in sample:
            s = time.perf_counter()
            result = retrieve(paper['title'], 8)
            times.append(time.perf_counter() - s)
            hits += any(r['arxiv_id'] == paper['arxiv_id'] for r in result)
        report['engine_sample'] = {'method': 'full B2 retrieval (hybrid + facets + cross-encoder), top 8',
                                   'hits': hits, 'total': len(sample),
                                   'median_seconds': round(float(np.median(times)), 2),
                                   'p90_seconds': round(float(np.percentile(times, 90)), 2)}
    return report
