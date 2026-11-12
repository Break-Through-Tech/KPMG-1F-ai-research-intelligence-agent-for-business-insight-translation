"""SQLite state for the research library. One row per arXiv paper (base ID).

Statuses:
  discovered       candidate from arXiv search, not yet fetched
  extracted        text extracted and validated; waiting for the next index build
  indexed          searchable in the current bundle
  update_available a newer arXiv version was seen for an indexed/extracted paper
  failed           transient failure (network, rate limit); retried later
  skipped          permanent: no versioned HTML, unreadable or too little text
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
  base_id TEXT PRIMARY KEY, arxiv_id TEXT NOT NULL, version INTEGER NOT NULL,
  title TEXT, abstract TEXT, categories TEXT, published TEXT, updated TEXT,
  topics TEXT NOT NULL DEFAULT '[]', topic TEXT, topic_rank INTEGER,
  source TEXT NOT NULL DEFAULT 'arxiv', status TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0, last_error TEXT,
  latest_seen_version INTEGER, html_sha256 TEXT, shard TEXT, parents INTEGER,
  discovered_at TEXT, extracted_at TEXT, indexed_at TEXT, bundle_id TEXT);
CREATE TABLE IF NOT EXISTS versions (
  base_id TEXT NOT NULL, version INTEGER NOT NULL, arxiv_id TEXT NOT NULL,
  first_seen TEXT NOT NULL, ingested_at TEXT, PRIMARY KEY (base_id, version));
CREATE TABLE IF NOT EXISTS discovery_pages (
  topic TEXT NOT NULL, start INTEGER NOT NULL, query TEXT NOT NULL,
  fetched_at TEXT NOT NULL, results INTEGER NOT NULL, total INTEGER,
  PRIMARY KEY (topic, start));
CREATE TABLE IF NOT EXISTS bundles (
  bundle_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, papers INTEGER, parents INTEGER,
  views INTEGER, embedded_papers INTEGER, reused_papers INTEGER, seconds REAL,
  bytes INTEGER, path TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, kind TEXT NOT NULL,
  base_id TEXT, detail TEXT);
CREATE INDEX IF NOT EXISTS papers_status ON papers(status);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Store:
    def __init__(self, root, *, readonly=False):
        self.root = Path(root).resolve()
        if readonly:
            path = self.root / 'library.sqlite3'
            self.db = sqlite3.connect(f'file:{path.as_posix()}?mode=ro', uri=True, check_same_thread=False)
        else:
            self.root.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(self.root / 'library.sqlite3', check_same_thread=False)
            self.db.execute('PRAGMA journal_mode=WAL')
            self.db.executescript(SCHEMA)
        self.db.row_factory = sqlite3.Row

    # ---- events
    def event(self, kind, base_id=None, detail=None):
        self.db.execute('INSERT INTO events(at, kind, base_id, detail) VALUES (?,?,?,?)',
                        (now(), kind, base_id, None if detail is None else str(detail)[:500]))

    # ---- discovery with deduplication and version tracking
    def upsert_candidate(self, record, topic, rank):
        """Insert a new paper or merge a re-discovery. Returns 'new', 'seen' or 'newer_version'."""
        base, version = record['base_id'], record['version']
        row = self.db.execute('SELECT * FROM papers WHERE base_id=?', (base,)).fetchone()
        self.db.execute('INSERT OR IGNORE INTO versions(base_id, version, arxiv_id, first_seen) VALUES (?,?,?,?)',
                        (base, version, record['arxiv_id'], now()))
        if row is None:
            self.db.execute(
                'INSERT INTO papers(base_id, arxiv_id, version, title, abstract, categories, published, updated,'
                ' topics, topic, topic_rank, status, latest_seen_version, discovered_at) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (base, record['arxiv_id'], version, record['title'], record['abstract'], record['categories'],
                 record['published'], record['updated'], json.dumps([topic]), topic, rank, 'discovered',
                 version, now()))
            return 'new'
        topics = json.loads(row['topics'])
        if topic not in topics:
            topics.append(topic)
            self.db.execute('UPDATE papers SET topics=? WHERE base_id=?', (json.dumps(topics), base))
        if version > (row['latest_seen_version'] or row['version']):
            self.db.execute('UPDATE papers SET latest_seen_version=? WHERE base_id=?', (version, base))
            if row['status'] in ('indexed', 'extracted'):
                self.db.execute("UPDATE papers SET status='update_available' WHERE base_id=?", (base,))
                self.event('version_seen', base, f'v{row["version"]} -> v{version}')
                return 'newer_version'
            if row['status'] in ('discovered', 'failed', 'skipped'):
                self.db.execute('UPDATE papers SET arxiv_id=?, version=?, status=?, attempts=0 WHERE base_id=?',
                                (record['arxiv_id'], version,
                                 'discovered' if row['status'] != 'skipped' else 'discovered', base))
        return 'seen'

    def page_done(self, topic, start):
        return self.db.execute('SELECT 1 FROM discovery_pages WHERE topic=? AND start=?',
                               (topic, start)).fetchone() is not None

    def record_page(self, topic, start, query, results, total):
        self.db.execute('INSERT OR REPLACE INTO discovery_pages VALUES (?,?,?,?,?,?)',
                        (topic, start, query, now(), results, total))

    # ---- ingestion queue
    def ready_count(self):
        return self.db.execute(
            "SELECT COUNT(*) FROM papers WHERE status IN ('extracted','indexed','update_available')").fetchone()[0]

    def next_candidates(self, limit, *, max_attempts=4):
        """Interleave topics so every area fills evenly; updates first, then new papers, then retries."""
        return self.db.execute(
            "SELECT * FROM papers WHERE status='update_available' OR status='discovered' "
            "OR (status='failed' AND attempts < ?) "
            "ORDER BY CASE status WHEN 'update_available' THEN 0 WHEN 'discovered' THEN 1 ELSE 2 END, "
            "topic_rank, topic, base_id LIMIT ?", (max_attempts, limit)).fetchall()

    def mark(self, base_id, status, **fields):
        fields['status'] = status
        sets = ', '.join(f'{k}=?' for k in fields)
        self.db.execute(f'UPDATE papers SET {sets} WHERE base_id=?', (*fields.values(), base_id))

    def commit(self):
        self.db.commit()

    def close(self):
        self.db.commit()
        self.db.close()
