"""Persistent limits on actual Gemini SDK dispatch, including automatic retries."""
from contextlib import closing
import json
import re
import sqlite3
from time import monotonic, sleep, time

PROJECT_RPM = 15
PROJECT_INPUT_TPM = 250_000
WINDOW_SECONDS = 61
CALL_LIMIT = 40
ARM_LIMIT = 20
INPUT_LIMIT = 1_200_000
OUTPUT_LIMIT = 150_000
MAX_OUTPUT = OUTPUT_LIMIT // CALL_LIMIT

# Screen the full request body, including evidence, schema metadata and review drafts.
# A clean pattern scan cannot establish redistribution rights or exclude all personal data.
RESTRICTED_PATTERN = re.compile(
    r'[\w.+%-]+@[\w.-]+\.[a-z]{2,}|'
    r'(?:\d{3}-\d{2}-\d{4}|AIza[\w-]{35}|gh[pousr]_[a-z0-9]{25,})|'
    r'-----BEGIN [A-Z ]*PRIVATE KEY-----', re.IGNORECASE,
)


class LimitReached(RuntimeError):
    pass


class Ledger:
    def __init__(self, path, *, pace=False, clock=time, wait=sleep):
        self.path = path
        self.pace, self.clock, self.wait = pace, clock, wait
        self.limit_hit = False
        self.payload_blocked = False
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS dispatch (
                id INTEGER PRIMARY KEY, arm TEXT NOT NULL, question TEXT NOT NULL,
                input_bound INTEGER NOT NULL, output_bound INTEGER NOT NULL,
                usage TEXT, blocked INTEGER NOT NULL DEFAULT 0,
                seconds REAL, outcome TEXT, sent_at REAL
            )""")

            columns = {row[1] for row in db.execute('PRAGMA table_info(dispatch)')}
            if 'sent_at' not in columns:
                db.execute('ALTER TABLE dispatch ADD COLUMN sent_at REAL')

    def reserve(self, arm, question, input_bound):
        while True:
            dispatch, delay = self._reserve(arm, question, input_bound)
            if dispatch is not None:
                return dispatch
            self.wait(delay)

    def _reserve(self, arm, question, input_bound):
        if arm not in ('S2', 'R2') or input_bound <= 0:
            raise ValueError('Invalid dispatch reservation.')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            calls, arm_calls, inputs, outputs, blocked = db.execute(
                """SELECT COUNT(*), COALESCE(SUM(arm = ?), 0),
                          COALESCE(SUM(COALESCE(json_extract(usage, '$.prompt'), input_bound)), 0),
                          COALESCE(SUM(output_bound), 0), COALESCE(MAX(blocked), 0)
                   FROM dispatch""", (arm,)).fetchone()
            if (blocked or calls >= CALL_LIMIT or arm_calls >= ARM_LIMIT or
                    inputs + input_bound > INPUT_LIMIT or outputs + MAX_OUTPUT > OUTPUT_LIMIT):
                self.limit_hit = True
                raise LimitReached('Campaign request or token budget exhausted.')
            now = self.clock()
            if self.pace:
                latest, undated = db.execute(
                    'SELECT MAX(sent_at), COUNT(*) - COUNT(sent_at) FROM dispatch'
                ).fetchone()
                if undated or (latest is not None and latest > now) or input_bound > PROJECT_INPUT_TPM:
                    self.limit_hit = True
                    raise LimitReached('Project quota cannot be safely reserved.')
                active = db.execute(
                    'SELECT sent_at, input_bound FROM dispatch WHERE sent_at > ? ORDER BY sent_at',
                    (now - WINDOW_SECONDS,),
                ).fetchall()
                if len(active) >= PROJECT_RPM or sum(bound for _, bound in active) + input_bound > PROJECT_INPUT_TPM:
                    return None, active[0][0] + WINDOW_SECONDS - now
            dispatch = db.execute(
                'INSERT INTO dispatch (arm, question, input_bound, output_bound, sent_at) VALUES (?, ?, ?, ?, ?)',
                (arm, question, input_bound, MAX_OUTPUT, now),
            ).lastrowid
            return dispatch, None

    def check_blocked(self):
        if self.payload_blocked:
            raise SystemExit('Free-tier payload screen failed. Campaign stopped before dispatch.')
        if self.limit_hit:
            raise SystemExit('Campaign dispatch limit reached.')
        with closing(sqlite3.connect(self.path)) as db:
            if db.execute('SELECT 1 FROM dispatch WHERE blocked = 1 LIMIT 1').fetchone():
                raise SystemExit('Provider usage breached or could not verify the reservation. Campaign stopped.')

    def failure(self, dispatch, seconds, error):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE dispatch SET seconds = ?, outcome = ? WHERE id = ?',
                       (seconds, type(error).__name__, dispatch))

    def record(self, dispatch, usage, seconds, *, outcome='response'):
        with closing(sqlite3.connect(self.path)) as db, db:
            input_bound, output_bound = db.execute(
                'SELECT input_bound, output_bound FROM dispatch WHERE id = ?', (dispatch,)).fetchone()
            blocked = (type(usage.get('prompt')) is not int or usage['prompt'] <= 0 or
                       type(usage.get('candidates')) is not int or usage['candidates'] < 0 or
                       type(usage.get('thoughts', 0)) is not int or usage.get('thoughts', 0) < 0 or
                       usage['prompt'] > input_bound or
                       usage['candidates'] + usage.get('thoughts', 0) > output_bound)
            db.execute('UPDATE dispatch SET usage = ?, blocked = ?, seconds = ?, outcome = ? WHERE id = ?',
                       (json.dumps(usage), blocked, seconds, outcome, dispatch))
        if blocked:
            raise LimitReached('Missing usage or provider token counts exceeded the reservation.')


class GuardedModels:
    def __init__(self, client, ledger, usage, scope):
        # Keep the SDK client alive for as long as its models can dispatch.
        self.client, self.ledger, self.usage, self.scope = client, ledger, usage, scope

    def generate_content(self, *, model, contents, config):
        from google.genai.types import ThinkingConfig

        metered = config.model_copy(update={
            'max_output_tokens': MAX_OUTPUT,
            'thinking_config': ThinkingConfig(thinking_level='MINIMAL'),
        })
        payload = json.dumps({'model': model, 'prompt': contents, 'config': metered.model_dump(mode='json')},
                             ensure_ascii=False)
        if RESTRICTED_PATTERN.search(payload):
            self.ledger.payload_blocked = True
            raise LimitReached('Payload failed the local free-tier screen.')
        # Conservative local estimate. Gemini exposes exact usage only after dispatch.
        bound = len(payload.encode()) + 1024
        arm, question = self.scope()
        dispatch = self.ledger.reserve(arm, question, bound)
        start = monotonic()
        try:
            response = self.client.models.generate_content(model=model, contents=contents, config=metered)
        except Exception as error:
            self.ledger.failure(dispatch, monotonic() - start, error)
            raise
        candidates = getattr(response, 'candidates', None)
        reason = getattr(candidates[0], 'finish_reason', None) if candidates else None
        outcome = 'MAX_TOKENS' if reason == 'MAX_TOKENS' else 'response'
        self.ledger.record(dispatch, self.usage(response), monotonic() - start, outcome=outcome)
        return response
