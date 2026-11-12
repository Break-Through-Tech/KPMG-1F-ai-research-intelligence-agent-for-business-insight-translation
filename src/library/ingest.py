"""Resumable ingestion: fetch versioned arXiv HTML, extract citable passages, store a shard.

Each paper commits independently, so an interrupted run resumes where it stopped.
Raw HTML is cached gzip-compressed to allow re-extraction without re-downloading.
"""
import gzip
from hashlib import sha256
import json
from pathlib import Path

from .arxiv_client import RateLimited
from .store import now

MIN_PASSAGES = 5


def shard_dir(root, base_id):
    return Path(root) / 'papers' / base_id.replace('/', '_')


def extract(html_bytes, record):
    from src.experimental.arxiv_fallback import html_passages
    passages = html_passages(html_bytes, {'arxiv_id': record['arxiv_id'], 'title': record['title']})
    if len(passages) < MIN_PASSAGES:
        raise ValueError(f'too little extractable text ({len(passages)} passages)')
    return passages


def fetch_html(client, cache_root, arxiv_id):
    cache = Path(cache_root) / f'{arxiv_id.replace("/", "_")}.html.gz'
    if cache.is_file():
        return 200, gzip.decompress(cache.read_bytes())
    status, body = client.get(f'https://arxiv.org/html/{arxiv_id}')
    if status == 200:
        cache.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache.with_suffix('.tmp')
        tmp.write_bytes(gzip.compress(body))
        tmp.replace(cache)
    return status, body


def ingest_one(store, client, row, *, html_cache):
    record = dict(row)
    if row['status'] == 'update_available':
        record['arxiv_id'] = f"{row['base_id']}v{row['latest_seen_version']}"
        record['version'] = row['latest_seen_version']
    try:
        status, body = fetch_html(client, html_cache, record['arxiv_id'])
    except RateLimited:
        raise
    except Exception as exc:
        store.mark(row['base_id'], 'failed', attempts=row['attempts'] + 1,
                   last_error=f'fetch: {type(exc).__name__}')
        store.event('failed', row['base_id'], f'fetch {type(exc).__name__}')
        return 'failed'
    if status != 200:
        if row['status'] == 'update_available':  # keep the indexed version; the new one has no HTML yet
            store.mark(row['base_id'], 'indexed' if row['bundle_id'] else 'extracted',
                       last_error=f'update v{record["version"]}: no HTML (HTTP {status})')
            return 'update_unavailable'
        store.mark(row['base_id'], 'skipped', last_error=f'no versioned HTML (HTTP {status})')
        store.event('skipped', row['base_id'], f'HTTP {status}')
        return 'skipped'
    try:
        passages = extract(body, record)
    except Exception as exc:
        reason = str(exc)[:200] if isinstance(exc, ValueError) else type(exc).__name__
        if row['status'] == 'update_available':
            store.mark(row['base_id'], 'indexed' if row['bundle_id'] else 'extracted',
                       last_error=f'update v{record["version"]} unreadable: {reason}')
            return 'update_unavailable'
        store.mark(row['base_id'], 'skipped', last_error=f'unreadable: {reason}')
        store.event('skipped', row['base_id'], reason)
        return 'skipped'
    folder = shard_dir(store.root, row['base_id'])
    folder.mkdir(parents=True, exist_ok=True)
    shard = folder / f"{record['arxiv_id'].replace('/', '_')}.jsonl"
    tmp = shard.with_suffix('.tmp')
    tmp.write_text('\n'.join(json.dumps(p, ensure_ascii=False, allow_nan=False) for p in passages), encoding='utf-8')
    tmp.replace(shard)
    store.mark(row['base_id'], 'extracted', arxiv_id=record['arxiv_id'], version=record['version'],
               html_sha256=sha256(body).hexdigest(), shard=str(shard.relative_to(store.root)),
               parents=len(passages), extracted_at=now(), last_error=None,
               attempts=row['attempts'] + 1)
    store.db.execute('UPDATE versions SET ingested_at=? WHERE base_id=? AND version=?',
                     (now(), row['base_id'], record['version']))
    store.event('updated' if row['status'] == 'update_available' else 'extracted', row['base_id'],
                f"{record['arxiv_id']} passages={len(passages)}")
    return 'extracted'


def ingest(store, client, *, target, html_cache, log=print, batch=25):
    """Extract papers until `target` papers are ready (extracted or indexed)."""
    results = {'extracted': 0, 'skipped': 0, 'failed': 0, 'update_unavailable': 0}
    while True:
        updates_pending = store.db.execute(
            "SELECT COUNT(*) FROM papers WHERE status='update_available'").fetchone()[0]
        if store.ready_count() - updates_pending >= target and not updates_pending:
            break
        rows = store.next_candidates(batch)
        if not rows:
            log('no more candidates; run discovery with a larger per-topic limit')
            break
        for row in rows:
            if store.ready_count() >= target and row['status'] != 'update_available':
                break
            try:
                outcome = ingest_one(store, client, row, html_cache=html_cache)
            except RateLimited:
                store.event('rate_limited', row['base_id'], 'paused; resume later')
                store.commit()
                log('arXiv rate limit persisted; stopping cleanly. Rerun to resume.')
                return results
            results[outcome] += 1
            store.commit()
            log(f"{outcome:10s} {row['base_id']} ready={store.ready_count()}/{target}")
    return results
