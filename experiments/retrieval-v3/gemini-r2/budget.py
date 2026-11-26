"""Persistent limits on actual Gemini SDK dispatch, including automatic retries."""
from contextlib import closing
import json
import re
import sqlite3
import sys
from time import monotonic, sleep, time
from types import SimpleNamespace

from recovery import recover_response

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


# Only fixed labels can leave the adapter. Google error messages and arbitrary
# field paths can contain submitted values, so never log them verbatim.
SAFE_ERROR_REASONS = {'API_KEY_INVALID', 'API_KEY_SERVICE_BLOCKED', 'SERVICE_DISABLED',
                      'API_KEY_HTTP_REFERRER_BLOCKED', 'API_KEY_IP_ADDRESS_BLOCKED'}
SAFE_FIELDS = {
    'model': 'model',
    'contents': 'contents',
    'generationconfig': 'generation_config',
    'generationconfig.temperature': 'temperature',
    'generationconfig.maxoutputtokens': 'max_output_tokens',
    'generationconfig.thinkingconfig': 'thinking_config',
    'generationconfig.thinkingconfig.thinkinglevel': 'thinking_level',
    'generationconfig.responsemimetype': 'response_mime_type',
    'generationconfig.responsejsonschema': 'response_json_schema',
    'generationconfig.responseschema': 'response_schema',
}


def provider_diagnostic(error):
    from google.genai.errors import APIError

    if not isinstance(error, APIError):
        return ''
    body = error.details if isinstance(error.details, dict) else {}
    envelope = body.get('error', body)
    if not isinstance(envelope, dict):
        return ''
    details = envelope.get('details', [])
    tags = set()
    for detail in details if isinstance(details, list) else []:
        if not isinstance(detail, dict):
            continue
        reason = detail.get('reason')
        if detail.get('@type') == 'type.googleapis.com/google.rpc.ErrorInfo' and isinstance(reason, str):
            if reason in SAFE_ERROR_REASONS:
                tags.add(reason)
        if detail.get('@type') == 'type.googleapis.com/google.rpc.BadRequest':
            violations = detail.get('fieldViolations', [])
            for violation in violations if isinstance(violations, list) else []:
                path = violation.get('field') if isinstance(violation, dict) else None
                if isinstance(path, str):
                    normalized = path.lower().replace('_', '')
                    label = SAFE_FIELDS.get(normalized)
                    if label is None:
                        label = next((label for key, label in SAFE_FIELDS.items()
                                      if key in ('contents', 'generationconfig.responsejsonschema',
                                                 'generationconfig.responseschema')
                                      and normalized.startswith((key + '.', key + '['))), None)
                    if label:
                        tags.add(label)
    return ' '.join(sorted(tags)) or 'no_allowlisted_provider_detail'


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

            db.execute('''CREATE TABLE IF NOT EXISTS response_recovery (
                dispatch_id INTEGER NOT NULL, stage TEXT NOT NULL, field TEXT NOT NULL, item_index INTEGER NOT NULL
            )''')
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

    def record_recovery(self, dispatch, events):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executemany('INSERT INTO response_recovery VALUES (?, ?, ?, ?)',
                           [(dispatch, event['stage'], event['field'], event['index']) for event in events])

    def recovery_events(self, arm, question):
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(
                """SELECT dispatch_id, stage, field, item_index FROM response_recovery
                   JOIN dispatch ON dispatch.id = dispatch_id WHERE arm = ? AND question = ?
                   ORDER BY dispatch_id, field, item_index""", (arm, question))
            return [dict(zip(('dispatch', 'stage', 'field', 'index'), row)) for row in rows]

    def check_blocked(self):
        if self.payload_blocked:
            raise SystemExit('Free-tier payload screen failed. Campaign stopped before dispatch.')
        if self.limit_hit:
            raise SystemExit('Campaign dispatch limit reached.')
        with closing(sqlite3.connect(self.path)) as db:
            if db.execute('SELECT 1 FROM dispatch WHERE blocked = 1 LIMIT 1').fetchone():
                raise SystemExit('Provider usage breached or could not verify the reservation. Campaign stopped.')

    def failure(self, dispatch, seconds, error):
        diagnostic = provider_diagnostic(error)
        outcome = type(error).__name__
        if diagnostic:
            code = error.code if type(error.code) is int else 0
            outcome = f'{outcome} HTTP {code} {diagnostic}'
            print(f'evaluation-provider-rejection {outcome}', file=sys.stderr, flush=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('UPDATE dispatch SET seconds = ?, outcome = ? WHERE id = ?',
                       (seconds, outcome, dispatch))

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
    def __init__(self, client, ledger, usage, scope, schema):
        # Keep the SDK client alive for as long as its models can dispatch.
        self.client, self.ledger, self.usage, self.scope = client, ledger, usage, scope
        self.schema = schema

    def generate_content(self, *, model, contents, config):
        # Match the deployed adapter's provider-default thinking behavior.
        metered = config.model_copy(update={'max_output_tokens': MAX_OUTPUT})
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
        schema = self.schema.get()
        if schema is not None and reason == 'STOP' and isinstance(response.text, str):
            draft_recovered = (schema.get('properties', {}).get('decisions') is not None and
                               any(event['stage'] == 'draft' for event in self.ledger.recovery_events(arm, question)))
            text, events = recover_response(response.text, schema, draft_was_recovered=draft_recovered)
            if events:
                self.ledger.record_recovery(dispatch, events)
            if text != response.text:
                return SimpleNamespace(candidates=candidates, text=text)
        return response
