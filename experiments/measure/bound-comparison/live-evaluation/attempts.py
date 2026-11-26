"""Private, durable budget at the HTTP dispatch boundary."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3

import httpx2

TOTAL = 9
PER_QUESTION = 3
QUESTION_IDS = ("agreemate", "accuraterag", "training-counts")


class CapReached(RuntimeError):
    pass


class AttemptBudget:
    def __init__(self, path):
        self.path = Path(path).resolve()

    @classmethod
    def create(cls, path):
        budget = cls(path)
        with budget.path.open("xb"):
            pass
        with closing(budget.connect()) as db:
            db.execute("""CREATE TABLE attempts (
                id INTEGER PRIMARY KEY, question TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'reserved', http_status INTEGER,
                usage_json TEXT)""")
        return budget

    def connect(self):
        db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, isolation_level=None)
        db.execute("PRAGMA synchronous=FULL")
        return db

    def reserve(self, question):
        if question not in QUESTION_IDS:
            raise CapReached("question is outside this evaluation")
        with closing(self.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            total, per_question = db.execute(
                "SELECT COUNT(*), COUNT(CASE WHEN question = ? THEN 1 END) FROM attempts", (question,)
            ).fetchone()
            if total >= TOTAL or per_question >= PER_QUESTION:
                raise CapReached("HTTP attempt budget exhausted")
            record = db.execute("INSERT INTO attempts(question) VALUES (?)", (question,)).lastrowid
            db.commit()
            return record

    def finish(self, record, status, http_status=None, usage=None):
        with closing(self.connect()) as db:
            db.execute("UPDATE attempts SET status = ?, http_status = ?, usage_json = ? WHERE id = ?",
                       (status, http_status, json.dumps(usage) if usage is not None else None, record))

    def records(self):
        with closing(self.connect()) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute("SELECT * FROM attempts ORDER BY id")]


class BudgetedTransport(httpx2.BaseTransport):
    def __init__(self, budget, question, inner=None):
        self.budget, self.question = budget, question
        self.inner = inner if inner is not None else httpx2.HTTPTransport(retries=0, trust_env=False)

    def handle_request(self, request):
        url = request.url
        if (request.method, url.scheme, url.host, url.port, url.path, url.query) != (
                "POST", "https", "api.openai.com", None, "/v1/chat/completions", b""):
            raise ValueError("request is outside the approved endpoint")
        attempt = self.budget.reserve(self.question)
        response = None
        try:
            response = self.inner.handle_request(request)
            response.read()
        except Exception as exc:
            if response is not None:
                response.close()
            self.budget.finish(attempt, type(exc).__name__, getattr(response, "status_code", None))
            raise
        usage = None
        if response.is_success:
            try:
                usage = response.json().get("usage")
            except (ValueError, AttributeError):
                pass
        self.budget.finish(attempt, "response", response.status_code, usage)
        return response

    def close(self):
        self.inner.close()


def question_client(budget, question, *, inner=None):
    return httpx2.Client(transport=BudgetedTransport(budget, question, inner),
                         follow_redirects=False, trust_env=False, timeout=60)
