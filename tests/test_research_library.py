"""Offline tests for the persistent research library. No network; scripted arXiv responses."""
import json
from pathlib import Path
import tempfile
import unittest

from src.library.arxiv_client import ArxivClient, RateLimited
from src.library.discovery import discover, topic_query
from src.library.ingest import ingest
from src.library.store import Store

ENCODER = Path.home() / '.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41'


def feed(entries, total=None):
    body = ''.join(
        f'<entry><id>http://arxiv.org/abs/{i}</id><title>{t}</title><summary>Abstract of {t}.</summary>'
        f'<author><name>A. Author</name></author><category term="{c}"/>'
        f'<published>2025-01-01T00:00:00Z</published><updated>2025-02-01T00:00:00Z</updated></entry>'
        for i, t, c in entries)
    return (f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">'
            f'<opensearch:totalResults>{len(entries) if total is None else total}</opensearch:totalResults>'
            f'{body}</feed>').encode()


def html(arxiv_id, sections=6):
    parts = ''.join(
        f'<section class="ltx_section" id="S{n}"><h2 class="ltx_title">Section {n}</h2>'
        f'<p class="ltx_para">Paper {arxiv_id} section {n} reports that the evaluated agents completed '
        f'{40 + n} percent of benchmark tasks under fixed conditions with a held-out test split.</p></section>'
        for n in range(1, sections + 1))
    return f'<html><body><div>arXiv:{arxiv_id}</div>{parts}</body></html>'.encode()


class Response:
    def __init__(self, status, content=b'', headers=None):
        self.status_code, self.content, self.headers = status, content, headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(response=self)


class Session:
    """Routes API queries and HTML downloads to scripted responses and records calls."""
    def __init__(self, api=None, pages=None):
        self.api, self.pages, self.calls = api or {}, pages or {}, []

    def get(self, url, params=None, timeout=None, allow_redirects=None):
        self.calls.append((url, dict(params or {})))
        if params:
            item = self.api.get((params['search_query'], params['start']), Response(200, feed([], 0)))
        else:
            item = self.pages.get(url.rsplit('/', 1)[-1], Response(404))
        if isinstance(item, list):
            return item.pop(0)
        return item


def client(session):
    return ArxivClient(session=session, sleep=lambda s: None, delay=0)


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'library'
        self.cache = Path(self.tmp.name) / 'cache'
        self.store = Store(self.root)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_rate_limit_backs_off_then_succeeds_and_persistent_limit_stops_cleanly(self):
        waits = []
        s = Session(pages={'2501.00001v1': [Response(429, headers={'Retry-After': '7'}), Response(200, b'ok')]})
        c = ArxivClient(session=s, sleep=waits.append, delay=0)
        self.assertEqual(c.get('https://arxiv.org/html/2501.00001v1'), (200, b'ok'))
        self.assertIn(7, waits)
        s = Session(pages={'x': [Response(429)] * 5})
        with self.assertRaises(RateLimited):
            ArxivClient(session=s, sleep=lambda _: None, delay=0).get('https://arxiv.org/html/x')

    def test_discovery_deduplicates_across_topics_and_resumes_without_refetching(self):
        q_llm, q_rag = topic_query('llm'), topic_query('rag')
        s = Session(api={(q_llm, 0): Response(200, feed([('2501.00001v1', 'Paper One', 'cs.CL'),
                                                          ('2501.00002v1', 'Paper Two', 'cs.CL')])),
                         (q_rag, 0): Response(200, feed([('2501.00001v1', 'Paper One', 'cs.CL'),
                                                          ('2501.00003v1', 'Bio Paper', 'q-bio.GN'),
                                                          ('2501.00004v1', 'Physics', 'physics.optics')]))})
        summary = discover(self.store, client(s), per_topic=100, topics=['llm', 'rag'], log=lambda *_: None)
        self.assertEqual(summary['rag']['seen'], 1)
        self.assertEqual(summary['rag']['irrelevant'], 1)
        papers = self.store.db.execute('SELECT base_id, topics FROM papers ORDER BY base_id').fetchall()
        self.assertEqual([p['base_id'] for p in papers], ['2501.00001', '2501.00002', '2501.00003'])
        self.assertEqual(json.loads(papers[0]['topics']), ['llm', 'rag'])
        calls = len(s.calls)
        discover(self.store, client(s), per_topic=100, topics=['llm', 'rag'], log=lambda *_: None)
        self.assertEqual(len(s.calls), calls, 'completed pages must not be fetched again')

    def test_ingest_is_resumable_and_records_skips(self):
        q = topic_query('agents')
        s = Session(api={(q, 0): Response(200, feed([('2501.00011v1', 'Agents A', 'cs.AI'),
                                                      ('2501.00012v1', 'Agents B', 'cs.AI'),
                                                      ('2501.00013v2', 'Agents C', 'cs.AI')]))},
                    pages={'2501.00011v1': Response(200, html('2501.00011v1')),
                           '2501.00013v2': Response(200, html('2501.00013v2'))})
        discover(self.store, client(s), topics=['agents'], log=lambda *_: None)
        result = ingest(self.store, client(s), target=1, html_cache=self.cache, log=lambda *_: None)
        self.assertEqual(result['extracted'], 1)
        result = ingest(self.store, client(s), target=3, html_cache=self.cache, log=lambda *_: None)
        rows = {r['base_id']: r for r in self.store.db.execute('SELECT * FROM papers')}
        self.assertEqual(rows['2501.00011']['status'], 'extracted')
        self.assertEqual(rows['2501.00012']['status'], 'skipped')
        self.assertIn('no versioned HTML', rows['2501.00012']['last_error'])
        self.assertEqual(rows['2501.00013']['status'], 'extracted')
        downloads = [u for u, p in s.calls if not p]
        self.assertEqual(downloads.count('https://arxiv.org/html/2501.00011v1'), 1, 'extracted papers are not refetched')
        shard = self.root / rows['2501.00013']['shard']
        passages = [json.loads(l) for l in shard.read_text(encoding='utf-8').splitlines()]
        self.assertTrue(all(p['arxiv_id'] == '2501.00013v2' for p in passages))

    def test_newer_version_is_tracked_and_replaces_the_shard(self):
        q = topic_query('llm')
        s = Session(api={(q, 0): Response(200, feed([('2501.00021v1', 'Versioned', 'cs.CL')]))},
                    pages={'2501.00021v1': Response(200, html('2501.00021v1')),
                           '2501.00021v2': Response(200, html('2501.00021v2', sections=7))})
        discover(self.store, client(s), topics=['llm'], log=lambda *_: None)
        ingest(self.store, client(s), target=1, html_cache=self.cache, log=lambda *_: None)
        self.store.mark('2501.00021', 'indexed', bundle_id='b1')
        outcome = self.store.upsert_candidate({'base_id': '2501.00021', 'version': 2, 'arxiv_id': '2501.00021v2',
                                               'title': 'Versioned', 'abstract': 'x', 'categories': 'cs.CL',
                                               'published': '', 'updated': ''}, 'llm', 0)
        self.assertEqual(outcome, 'newer_version')
        ingest(self.store, client(s), target=1, html_cache=self.cache, log=lambda *_: None)
        row = self.store.db.execute("SELECT * FROM papers WHERE base_id='2501.00021'").fetchone()
        self.assertEqual((row['status'], row['arxiv_id'], row['version']), ('extracted', '2501.00021v2', 2))
        versions = self.store.db.execute("SELECT version FROM versions WHERE base_id='2501.00021'").fetchall()
        self.assertEqual(sorted(v[0] for v in versions), [1, 2])

    @unittest.skipUnless(ENCODER.is_dir(), 'local MiniLM encoder not cached')
    def test_index_build_is_incremental_and_loads_in_the_research_engine(self):
        from sentence_transformers import SentenceTransformer
        from src.experimental.search_index import SearchViewIndex
        from src.library.index import build
        encoder = SentenceTransformer(str(ENCODER), local_files_only=True, device='cpu')
        q = topic_query('rag')
        ids = ['2501.00031v1', '2501.00032v1', '2501.00033v1']
        s = Session(api={(q, 0): Response(200, feed([(i, f'RAG {i}', 'cs.CL') for i in ids]))},
                    pages={i: Response(200, html(i)) for i in ids})
        discover(self.store, client(s), topics=['rag'], log=lambda *_: None)
        ingest(self.store, client(s), target=2, html_cache=self.cache, log=lambda *_: None)
        first = build(self.store, encoder, log=lambda *_: None)
        self.assertEqual((first['papers'], first['embedded_papers'], first['reused_papers']), (2, 2, 0))
        ingest(self.store, client(s), target=3, html_cache=self.cache, log=lambda *_: None)
        second = build(self.store, encoder, log=lambda *_: None)
        self.assertEqual((second['papers'], second['embedded_papers'], second['reused_papers']), (3, 1, 2))
        index = SearchViewIndex(second['path'], model=encoder)
        self.assertEqual({p['arxiv_id'] for p in index.parents}, set(ids))
        hits = index.retrieve('section 3 of paper 2501.00033v1 agents completed percent of tasks', 3)
        self.assertTrue(hits)
        self.assertEqual((self.root / 'CURRENT').read_text(), second['bundle_id'])


if __name__ == '__main__':
    unittest.main()
