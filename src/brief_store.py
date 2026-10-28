"""Local saved-work library. Standard-library SQLite; never calls retrieval or a model."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from src.plain_language import plain_language_view
from src.research_contracts import validate_request, validate_result
from src.research_review import make_review_packet, record_human_decision, require_current_review


class BriefConflict(ValueError):
    """The caller's version is no longer the current version."""


def _text(value, name, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{name} must be nonempty text, at most {limit} characters.')
    return value.strip()


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def snapshot(envelope):
    """Keep the complete envelope, including fixture identity and source provenance."""
    if not isinstance(envelope, dict) or envelope.get('mode') not in {
            'fixture', 'saved-real-result', 'live-synthesis', 'indexed'}:
        raise ValueError('A research response envelope is required.')
    value = deepcopy(envelope)
    value.pop('library', None)
    value.pop('library_error', None)
    result = value.get('result')
    validate_result(result)
    if result.get('review_fingerprint') is not None:
        require_current_review(result)
    if 'plain_language' in value:
        candidate = value['plain_language']
        view = (plain_language_view(result) if isinstance(candidate, dict) and candidate.get('status') == 'unavailable'
                else plain_language_view(result, candidate))
        value['plain_language'] = (plain_language_view(result, {'status': 'failed'})
                                   if view['status'] == 'failed' else view)
    # Recompute display state from stage outcomes, not imported UI labels.
    business_failed = (isinstance(value.get('error'), dict)
                       and value['error'].get('stage') == 'business')
    value['scenario'] = ('empty' if not result['evidence'] else
                         'insufficient' if result['summary']['status'] != 'ok' else
                         'partial' if business_failed or result.get('business_insight', {}).get('status') == 'insufficient_evidence' else
                         'full' if result.get('business_insight') else 'summary-only')
    value.setdefault('submitted_request', result['request'])
    validate_request(value['submitted_request'])
    value.setdefault('error', None)
    if value['error'] is not None:
        if not isinstance(value['error'], dict) or not isinstance(value['error'].get('message'), str):
            raise ValueError('Invalid stage error in saved response.')
    encoded = _json(value)
    if len(encoded.encode()) > 8_000_000:
        raise ValueError('Saved snapshot exceeds 8 MB.')
    return value, encoded, sha256(encoded.encode()).hexdigest()


class BriefStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise ValueError('Unsupported brief-library schema; use a compatible app.')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS briefs (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, original_question TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)),
                    current_version TEXT,
                    FOREIGN KEY(id, current_version) REFERENCES brief_versions(brief_id, id)
                        DEFERRABLE INITIALLY DEFERRED
                );
                CREATE TABLE IF NOT EXISTS brief_versions (
                    id TEXT PRIMARY KEY, brief_id TEXT NOT NULL REFERENCES briefs(id),
                    number INTEGER NOT NULL, created_at TEXT NOT NULL, audience TEXT NOT NULL,
                    envelope_json TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    UNIQUE(brief_id, number), UNIQUE(brief_id, id)
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY, version_id TEXT NOT NULL REFERENCES brief_versions(id),
                    created_at TEXT NOT NULL, reviewer TEXT NOT NULL,
                    decision TEXT NOT NULL CHECK(decision IN ('approve','revise','reject')),
                    notes TEXT, fingerprint TEXT NOT NULL, reviewed_result_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS brief_order ON briefs(archived, updated_at DESC);
                CREATE INDEX IF NOT EXISTS review_version ON reviews(version_id, id DESC);
                CREATE TRIGGER IF NOT EXISTS versions_immutable_update BEFORE UPDATE ON brief_versions
                    BEGIN SELECT RAISE(ABORT, 'Versions are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS versions_immutable_delete BEFORE DELETE ON brief_versions
                    BEGIN SELECT RAISE(ABORT, 'Versions are immutable'); END;
                CREATE TRIGGER IF NOT EXISTS reviews_immutable_update BEFORE UPDATE ON reviews
                    BEGIN SELECT RAISE(ABORT, 'Reviews are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS reviews_immutable_delete BEFORE DELETE ON reviews
                    BEGIN SELECT RAISE(ABORT, 'Reviews are append-only'); END;
                PRAGMA user_version = 1;
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _brief(db, brief_id):
        row = db.execute('SELECT * FROM briefs WHERE id=?', (brief_id,)).fetchone()
        if row is None:
            raise KeyError('Brief not found.')
        return dict(row)

    @staticmethod
    def _current(brief, expected_version):
        if brief['archived'] or not expected_version or expected_version != brief['current_version']:
            raise BriefConflict('Brief changed or was archived. Reopen its current version before continuing.')

    def check_current(self, brief_id, expected_version):
        with self.connection() as db:
            self._current(self._brief(db, brief_id), expected_version)

    def save(self, envelope, *, brief_id=None, expected_version=None, title=None,
             audience='original', reuse=False):
        value, encoded, fingerprint = snapshot(envelope)
        audience = _text(audience, 'Audience', 80)
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if brief_id:
                brief = self._brief(db, brief_id)
                self._current(brief, expected_version)
                number = db.execute('SELECT MAX(number)+1 FROM brief_versions WHERE brief_id=?',
                                    (brief_id,)).fetchone()[0]
            else:
                if reuse:
                    found = db.execute('SELECT brief_id, id FROM brief_versions WHERE fingerprint=? LIMIT 1',
                                       (fingerprint,)).fetchone()
                    if found:
                        return self._load(db, found['brief_id'], found['id'])
                brief_id = uuid4().hex
                question = value['result']['request']['query']
                title = _text(title if title is not None else question[:160], 'Title', 200)
                db.execute('INSERT INTO briefs(id,title,original_question,created_at,updated_at) VALUES(?,?,?,?,?)',
                           (brief_id, title, question, now, now))
                number = 1
            version_id = uuid4().hex
            db.execute('INSERT INTO brief_versions VALUES(?,?,?,?,?,?,?)',
                       (version_id, brief_id, number, now, audience, encoded, fingerprint))
            db.execute('UPDATE briefs SET current_version=?, updated_at=? WHERE id=?',
                       (version_id, now, brief_id))
            return self._load(db, brief_id, version_id)

    def _load(self, db, brief_id, version_id=None):
        brief = self._brief(db, brief_id)
        row = db.execute('SELECT * FROM brief_versions WHERE brief_id=? AND id=?',
                         (brief_id, version_id or brief['current_version'])).fetchone()
        if row is None:
            raise KeyError('Version not found.')
        version = dict(row)
        envelope = json.loads(version.pop('envelope_json'))
        # Verify the bytes' canonical content before applying current display
        # normalization; older snapshots may contain a now-corrected UI label.
        fingerprint = sha256(_json(envelope).encode()).hexdigest()
        if fingerprint != version['fingerprint']:
            raise ValueError('Saved snapshot integrity check failed.')
        envelope, _, _ = snapshot(envelope)
        reviews = [dict(row) for row in db.execute(
            'SELECT * FROM reviews WHERE version_id=? ORDER BY id', (version['id'],))]
        for review in reviews:
            reviewed = json.loads(review.pop('reviewed_result_json'))
            require_current_review(reviewed)
            if (review['fingerprint'] != fingerprint or
                    make_review_packet(reviewed) != make_review_packet(envelope['result']) or
                    reviewed['human_review'] != {key: review[key] for key in ('reviewer', 'notes')} | {'status': review['decision']}):
                raise ValueError('Saved review integrity check failed.')
        versions = [dict(row) for row in db.execute(
            'SELECT id,number,created_at,audience FROM brief_versions WHERE brief_id=? ORDER BY number DESC',
            (brief_id,))]
        envelope['library'] = {'brief': brief, 'version': version, 'versions': versions,
                               'reviews': reviews, 'replayed': True}
        return envelope

    def load(self, brief_id, version_id=None):
        with self.connection() as db:
            return self._load(db, brief_id, version_id)

    def list(self, *, query='', archived=False, offset=0, limit=30):
        if not isinstance(query, str) or len(query) > 200 or type(offset) is not int or offset < 0:
            raise ValueError('Invalid library search.')
        if type(limit) is not int or not 1 <= limit <= 100 or type(archived) is not bool:
            raise ValueError('Invalid library page.')
        with self.connection() as db:
            return [dict(row) for row in db.execute('''
                SELECT b.*, v.number, v.audience,
                    json_extract(v.envelope_json, '$.mode') AS mode,
                    COALESCE((SELECT decision FROM reviews WHERE version_id=v.id ORDER BY id DESC LIMIT 1), 'pending') AS review_status
                FROM briefs b JOIN brief_versions v ON v.id=b.current_version
                WHERE b.archived=? AND (instr(lower(b.title),lower(?))>0 OR instr(lower(b.original_question),lower(?))>0)
                ORDER BY b.updated_at DESC, b.id LIMIT ? OFFSET ?
            ''', (int(archived), query, query, limit, offset))]

    def update(self, brief_id, *, expected_version, title=None, archived=None):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            brief = self._brief(db, brief_id)
            # Archived briefs may be restored, but stale version writes still fail.
            if brief['current_version'] != expected_version:
                raise BriefConflict('Brief changed. Reopen it before continuing.')
            if title is not None:
                brief['title'] = _text(title, 'Title', 200)
            if archived is not None:
                if type(archived) is not bool:
                    raise ValueError('Archived must be true or false.')
                brief['archived'] = int(archived)
            db.execute('UPDATE briefs SET title=?,archived=?,updated_at=? WHERE id=?',
                       (brief['title'], brief['archived'], datetime.now(timezone.utc).isoformat(), brief_id))
            return self._load(db, brief_id)

    def review(self, brief_id, *, version_id, fingerprint, reviewer, decision, notes=None):
        reviewer = _text(reviewer, 'Reviewer', 120)
        decision = _text(decision, 'Decision', 10).lower()
        if decision not in {'approve', 'revise', 'reject'}:
            raise ValueError('Unknown review decision.')
        if notes is not None and (not isinstance(notes, str) or len(notes) > 4000):
            raise ValueError('Review notes must be text, at most 4000 characters.')
        if decision == 'revise' and (not notes or not notes.strip()):
            raise ValueError('Describe the requested changes in review notes.')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self._current(self._brief(db, brief_id), version_id)
            envelope = self._load(db, brief_id, version_id)
            if fingerprint != envelope['library']['version']['fingerprint']:
                raise BriefConflict('Snapshot changed. Reopen before reviewing.')
            reviewed = record_human_decision(make_review_packet(envelope['result']),
                reviewer=reviewer, decision=decision, notes=notes)
            db.execute('INSERT INTO reviews(version_id,created_at,reviewer,decision,notes,fingerprint,reviewed_result_json) VALUES(?,?,?,?,?,?,?)',
                       (version_id, datetime.now(timezone.utc).isoformat(), reviewer,
                        decision, notes, fingerprint, _json(reviewed)))
            return self._load(db, brief_id, version_id)
