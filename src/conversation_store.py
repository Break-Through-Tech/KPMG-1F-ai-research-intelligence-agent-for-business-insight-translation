"""Persistent research conversations over the immutable brief store.

A conversation is an ordered list of research turns. Every turn is a normal saved brief with its own
retrieval, citations, findings, business insight, versions and reviews; the conversation only records
order, the user's original wording and the standalone question that was actually researched. Earlier
answers are never evidence for later turns: history() returns questions and short finding text for
resolving references, and nothing from it reaches retrieval or citation validation.

Removal from history is a soft delete. The audit trail (briefs, versions, reviews, turns) is kept and the
database protection triggers are unchanged; deleted conversations disappear from lists, cannot be
reopened through the API and cannot receive new research or business work.
"""
import json
from datetime import datetime, timezone
from uuid import uuid4

from src.brief_store import BriefStore, _text

MAX_HISTORY_TURNS = 6          # validate_history accepts at most six complete turns
MAX_ANSWER_NOTE_CHARS = 1500   # short finding text per turn; never passages or citations


class ConversationDeleted(Exception):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat()


class ConversationStore:
    def __init__(self, store):
        self.store = store if isinstance(store, BriefStore) else BriefStore(store)

    # ---------- migration ----------
    def migrate(self):
        """Give every brief without a conversation its own one-turn conversation. Idempotent; no data loss."""
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('''SELECT b.* FROM briefs b WHERE NOT EXISTS
                                 (SELECT 1 FROM conversation_turns t WHERE t.brief_id=b.id) ORDER BY b.created_at''').fetchall()
            for brief in rows:
                conversation_id = 'c' + brief['id']  # deterministic: a re-run can never duplicate
                db.execute('INSERT OR IGNORE INTO conversations(id,title,created_at,updated_at,archived) VALUES(?,?,?,?,?)',
                           (conversation_id, brief['title'], brief['created_at'], brief['updated_at'], brief['archived']))
                db.execute('INSERT INTO conversation_turns VALUES(?,?,?,?,?,?,?)',
                           (conversation_id, 1, brief['id'], brief['original_question'], brief['original_question'],
                            json.dumps({'kind': 'migrated'}), brief['created_at']))
            return len(rows)

    # ---------- writes ----------
    def create(self, title):
        conversation_id, now = uuid4().hex, _now()
        with self.store.connection() as db:
            db.execute('INSERT INTO conversations(id,title,created_at,updated_at) VALUES(?,?,?,?)',
                       (conversation_id, _text(title[:200], 'Title', 200), now, now))
        return conversation_id

    def append_turn(self, conversation_id, brief_id, *, original_question, resolved_question, resolution):
        """Record a saved research turn. A conversation deleted while the request ran stays deleted."""
        now = _now()
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT deleted_at FROM conversations WHERE id=?', (conversation_id,)).fetchone()
            if row is None:
                raise KeyError('Conversation not found.')
            position = db.execute('SELECT COALESCE(MAX(position),0)+1 FROM conversation_turns WHERE conversation_id=?',
                                  (conversation_id,)).fetchone()[0]
            db.execute('INSERT INTO conversation_turns VALUES(?,?,?,?,?,?,?)',
                       (conversation_id, position, brief_id, _text(original_question, 'Question', 2000),
                        _text(resolved_question, 'Resolved question', 6000), json.dumps(resolution, sort_keys=True), now))
            if row['deleted_at'] is None:
                db.execute('UPDATE conversations SET updated_at=? WHERE id=?', (now, conversation_id))
            return {'id': conversation_id, 'position': position, 'deleted': row['deleted_at'] is not None}

    def update(self, conversation_id, *, title=None, archived=None):
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            current = self._row(db, conversation_id)
            title = current['title'] if title is None else _text(title.strip(), 'Title', 200)
            if archived is not None and type(archived) is not bool:
                raise ValueError('Archived must be true or false.')
            db.execute('UPDATE conversations SET title=?, archived=?, updated_at=? WHERE id=?',
                       (title, current['archived'] if archived is None else int(archived), _now(), conversation_id))
        return self.summary(conversation_id)

    def soft_delete(self, conversation_id):
        """Hide from history permanently. Research records stay in the audit trail."""
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self._row(db, conversation_id)
            db.execute('UPDATE conversations SET deleted_at=? WHERE id=?', (_now(), conversation_id))
        return {'id': conversation_id, 'deleted': True}

    # ---------- reads ----------
    @staticmethod
    def _row(db, conversation_id, *, include_deleted=False):
        row = db.execute('SELECT * FROM conversations WHERE id=?', (conversation_id,)).fetchone()
        if row is None or (row['deleted_at'] is not None and not include_deleted):
            raise KeyError('Conversation not found.')
        return dict(row)

    def summary(self, conversation_id):
        with self.store.connection() as db:
            row = self._row(db, conversation_id)
            count = db.execute('SELECT COUNT(*) FROM conversation_turns WHERE conversation_id=?', (conversation_id,)).fetchone()[0]
        return {**row, 'turn_count': count}

    def list(self, *, archived=False, query='', offset=0, limit=50):
        if type(archived) is not bool or not isinstance(query, str) or len(query) > 200 \
                or type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('Invalid conversation list.')
        with self.store.connection() as db:
            return [dict(row) for row in db.execute('''
                SELECT c.id, c.title, c.created_at, c.updated_at, c.archived,
                       (SELECT COUNT(*) FROM conversation_turns t WHERE t.conversation_id=c.id) AS turn_count
                FROM conversations c
                WHERE c.deleted_at IS NULL AND c.archived=? AND (instr(lower(c.title), lower(?))>0 OR EXISTS (
                      SELECT 1 FROM conversation_turns t WHERE t.conversation_id=c.id
                      AND instr(lower(t.original_question), lower(?))>0))
                ORDER BY c.updated_at DESC, c.id LIMIT ? OFFSET ?''', (int(archived), query, query, limit, offset))]

    def turns(self, conversation_id):
        with self.store.connection() as db:
            self._row(db, conversation_id)
            return [{**dict(row), 'resolution': json.loads(row['resolution_json'])} for row in db.execute(
                'SELECT conversation_id, position, brief_id, original_question, resolved_question, resolution_json, created_at '
                'FROM conversation_turns WHERE conversation_id=? ORDER BY position', (conversation_id,))]

    def load(self, conversation_id):
        """Complete conversation: every turn with its current saved brief (answers, citations, insights)."""
        summary = self.summary(conversation_id)
        turns = []
        for turn in self.turns(conversation_id):
            turn.pop('resolution_json', None)
            turns.append({**turn, 'envelope': self.store.load(turn['brief_id'])})
        return {'conversation': summary, 'turns': turns}

    def conversation_of_brief(self, brief_id):
        with self.store.connection() as db:
            row = db.execute('''SELECT c.id, c.deleted_at FROM conversation_turns t JOIN conversations c
                                ON c.id=t.conversation_id WHERE t.brief_id=?''', (brief_id,)).fetchone()
        return None if row is None else {'id': row['id'], 'deleted': row['deleted_at'] is not None}

    def history(self, conversation_id):
        """Bounded user/assistant pairs for resolving references: questions plus short finding text and the
        business context of each turn. Never passages, chunk IDs or citations."""
        messages = []
        for turn in self.turns(conversation_id)[-MAX_HISTORY_TURNS:]:
            envelope = self.store.load(turn['brief_id'])
            result = envelope.get('result') or {}
            findings = [claim.get('text', '') for claim in (result.get('summary') or {}).get('claims', [])]
            note = ' '.join(f'- {text}' for text in findings if text) or 'No supported answer was found.'
            context = (result.get('provenance') or {}).get('business_translation', {}).get('context') \
                or ((envelope.get('business_intent') or {}).get('value') or {})
            if context.get('industry') or context.get('workflow'):
                note += f" Business context: industry {context.get('industry') or 'unspecified'}; workflow {context.get('workflow') or 'unspecified'}."
            question = turn['original_question']
            if turn['resolved_question'] != question:
                question += f' (researched as: {turn["resolved_question"]})'
            messages += [{'role': 'user', 'content': question[:2000]},
                         {'role': 'assistant', 'content': ('Earlier findings (not evidence): ' + note)[:MAX_ANSWER_NOTE_CHARS]}]
        return messages

    def previous_business_context(self, conversation_id):
        """Verified business context of the immediately previous research turn, or None.

        Verified means either the context of a published (validated) business insight on that turn, or the
        turn's trusted semantic classification with a verbatim workflow. Older turns are never used, so a
        topic change in between always breaks inheritance. No model call is made.
        """
        from src.business_intent import trusted_value
        turns = self.turns(conversation_id)
        if not turns:
            return None
        last = turns[-1]
        envelope = self.store.load(last['brief_id'])
        result = envelope.get('result') or {}
        origin = {'from_position': last['position'], 'from_brief_id': last['brief_id']}
        context = (result.get('provenance') or {}).get('business_translation', {}).get('context')
        if result.get('business_insight') and isinstance(context, dict) and context.get('workflow'):
            return {'industry': context['industry'], 'workflow': context['workflow'], 'source': 'business_insight', **origin}
        question = (envelope.get('submitted_request') or {}).get('query', '')
        value = trusted_value(envelope.get('business_intent'), ' '.join(question.split()))
        if value and value['is_business'] and value['workflow'] and value['confidence'] in {'high', 'medium'}:
            industry = 'Industry unspecified' if value['industry'] == 'unspecified' else value['industry']
            return {'industry': industry, 'workflow': value['workflow'], 'source': 'semantic', **origin}
        return None
