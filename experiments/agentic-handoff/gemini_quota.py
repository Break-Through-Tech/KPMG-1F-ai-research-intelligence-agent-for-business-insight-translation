"""Fail-closed local reservations for the isolated Gemini comparison."""
from contextlib import closing
import sqlite3
import time


class QuotaRefused(RuntimeError):
    pass


class GeminiQuota:
    # Inclusive of observable other project usage. These are intentionally
    # below the published 15 RPM, 250k input TPM and 500 RPD.
    RPM = 10
    TPM = 200_000
    RPD = 400
    GENERATION_CAP = 90

    def __init__(self, database, *, clock=time.time):
        self.database = database
        self.clock = clock
        with closing(sqlite3.connect(database)) as store, store:
            store.execute("PRAGMA synchronous=FULL")
            store.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY,
                    at REAL NOT NULL,
                    kind TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL
                )
            """)
            store.execute("""
                CREATE TABLE IF NOT EXISTS observation (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    valid_until REAL NOT NULL,
                    minute_requests INTEGER NOT NULL,
                    minute_input_tokens INTEGER NOT NULL,
                    day_requests INTEGER NOT NULL
                )
            """)

    def observe(self, *, minute_requests, minute_input_tokens, day_requests, valid_until, exclusive=False):
        """Record independently verified usage from outside this runner."""
        counters = (minute_requests, minute_input_tokens, day_requests)
        if any(type(v) is not int or v < 0 for v in counters):
            raise ValueError("Usage counters must be verified nonnegative integers")
        lifetime = 4 * 3600 if exclusive else 60
        if not self.clock() < valid_until <= self.clock() + lifetime:
            raise ValueError("Project usage confirmation must be current")
        with closing(sqlite3.connect(self.database)) as store, store:
            store.execute("PRAGMA synchronous=FULL")
            store.execute("INSERT OR REPLACE INTO observation VALUES (1, ?, ?, ?, ?)",
                          (valid_until, *counters))

    def reserve(self, kind, input_tokens):
        """Persist an attempt before dispatch. Failures still consume the slot."""
        if kind not in {"generation", "metadata"} or type(input_tokens) is not int or input_tokens < 0:
            raise ValueError("Invalid Gemini reservation")
        if kind == "generation" and not input_tokens:
            raise ValueError("Generation requires a conservative input-token reservation")
        with closing(sqlite3.connect(self.database, timeout=10)) as store, store:
            store.execute("PRAGMA synchronous=FULL")
            store.execute("BEGIN IMMEDIATE")
            now = self.clock()
            external = store.execute("SELECT valid_until, minute_requests, minute_input_tokens, day_requests "
                                     "FROM observation WHERE id = 1").fetchone()
            if not external or now >= external[0]:
                raise QuotaRefused("Current external project usage is unverified")
            latest, generations = store.execute(
                "SELECT MAX(at), COUNT(CASE WHEN kind = 'generation' THEN 1 END) "
                "FROM reservations").fetchone()
            if latest is not None and latest > now:
                raise QuotaRefused("Clock moved backwards")
            if kind == "generation" and generations >= self.GENERATION_CAP:
                raise QuotaRefused("Generation attempt cap reached")
            minute_requests, minute_tokens = store.execute(
                "SELECT COUNT(*), COALESCE(SUM(input_tokens), 0) FROM reservations WHERE at >= ?",
                (now - 60,)).fetchone()
            day_requests, = store.execute("SELECT COUNT(*) FROM reservations WHERE at >= ?",
                                          (now - 86400,)).fetchone()
            if day_requests + external[3] >= self.RPD:
                raise QuotaRefused("Daily request margin reached")
            if minute_requests + external[1] >= self.RPM or minute_tokens + external[2] + input_tokens > self.TPM:
                raise QuotaRefused("Minute request or input-token margin reached")
            return store.execute("INSERT INTO reservations(at, kind, input_tokens) VALUES (?, ?, ?)",
                                 (now, kind, input_tokens)).lastrowid
