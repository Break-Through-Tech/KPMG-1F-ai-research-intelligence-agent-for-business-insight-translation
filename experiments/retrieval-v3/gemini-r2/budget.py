"""Persistent limits on actual Gemini SDK dispatch, including automatic retries."""
from contextlib import closing
import json
import sqlite3
from time import monotonic

CALL_LIMIT = 40
ARM_LIMIT = 20
INPUT_LIMIT = 1_200_000
OUTPUT_LIMIT = 150_000
MAX_OUTPUT = OUTPUT_LIMIT // CALL_LIMIT


class LimitReached(RuntimeError):
    pass


class Ledger:
    def __init__(self, path):
        self.path = path
        self.limit_hit = False
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS dispatch (
                id INTEGER PRIMARY KEY, arm TEXT NOT NULL, question TEXT NOT NULL,
                input_bound INTEGER NOT NULL, output_bound INTEGER NOT NULL,
                usage TEXT, blocked INTEGER NOT NULL DEFAULT 0,
                seconds REAL, outcome TEXT
            )""")

    def reserve(self, arm, question, input_bound):
        if arm not in ('S2', 'R2') or input_bound <= 0:
            raise ValueError('Invalid dispatch reservation.')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            calls, arm_calls, inputs, outputs, blocked = db.execute(
                """SELECT COUNT(*), COALESCE(SUM(arm = ?), 0),
                          COALESCE(SUM(input_bound), 0), COALESCE(SUM(output_bound), 0), COALESCE(MAX(blocked), 0)
                   FROM dispatch""", (arm,)).fetchone()
            if (blocked or calls >= CALL_LIMIT or arm_calls >= ARM_LIMIT or
                    inputs + input_bound > INPUT_LIMIT or outputs + MAX_OUTPUT > OUTPUT_LIMIT):
                self.limit_hit = True
                raise LimitReached('Campaign request or token budget exhausted.')
            return db.execute(
                'INSERT INTO dispatch (arm, question, input_bound, output_bound) VALUES (?, ?, ?, ?)',
                (arm, question, input_bound, MAX_OUTPUT),
            ).lastrowid

    def check_blocked(self):
        if self.limit_hit:
            raise SystemExit('Campaign dispatch limit reached.')
        with closing(sqlite3.connect(self.path)) as db:
            if db.execute('SELECT 1 FROM dispatch WHERE blocked = 1 LIMIT 1').fetchone():
                raise SystemExit('Provider usage breached or could not verify the reservation. Campaign stopped.')

    def failure(self, dispatch, seconds, error):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE dispatch SET seconds = ?, outcome = ? WHERE id = ?',
                       (seconds, type(error).__name__, dispatch))

    def record(self, dispatch, usage, seconds):
        with closing(sqlite3.connect(self.path)) as db, db:
            input_bound, output_bound = db.execute(
                'SELECT input_bound, output_bound FROM dispatch WHERE id = ?', (dispatch,)).fetchone()
            blocked = (usage.get('prompt') is None or usage.get('candidates') is None or
                       usage['prompt'] > input_bound or
                       usage['candidates'] + usage.get('thoughts', 0) > output_bound)
            db.execute('UPDATE dispatch SET usage = ?, blocked = ?, seconds = ?, outcome = ? WHERE id = ?',
                       (json.dumps(usage), blocked, seconds, 'response', dispatch))
        if blocked:
            raise LimitReached('Missing usage or provider token counts exceeded the reservation.')


class GuardedModels:
    def __init__(self, models, ledger, usage, scope):
        self.models, self.ledger, self.usage, self.scope = models, ledger, usage, scope

    def generate_content(self, *, model, contents, config):
        from google.genai.types import ThinkingConfig

        metered = config.model_copy(update={
            'max_output_tokens': MAX_OUTPUT,
            'thinking_config': ThinkingConfig(thinking_level='MINIMAL'),
        })
        payload = json.dumps({'prompt': contents, 'config': metered.model_dump(mode='json')},
                             ensure_ascii=False).encode()
        # Conservative local estimate. Gemini exposes exact usage only after dispatch.
        bound = len(payload) + 1024
        arm, question = self.scope()
        dispatch = self.ledger.reserve(arm, question, bound)
        start = monotonic()
        try:
            response = self.models.generate_content(model=model, contents=contents, config=metered)
        except Exception as error:
            self.ledger.failure(dispatch, monotonic() - start, error)
            raise
        self.ledger.record(dispatch, self.usage(response), monotonic() - start)
        return response
