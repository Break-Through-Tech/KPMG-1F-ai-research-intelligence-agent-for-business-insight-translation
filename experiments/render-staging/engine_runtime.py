"""Offline-configurable engine construction for the supervised research preview."""
from contextvars import ContextVar
from hashlib import sha256
from hmac import compare_digest, digest
from http.cookies import CookieError, SimpleCookie
import json
from pathlib import Path
import re
from secrets import token_hex
import sys

SESSION = ContextVar('s2_preview_session', default=None)
COOKIE = 'kpmg_s2_session'
RUNTIME_FILES = {
    'retrieval-v3': 's2_adapter s2_paper_balance s3_env paper_balance components',
    'consolidated-v2': 'adapter env engine evidence publication assist_route review synthesis accounting',
    'verification-repair': 'verification_v2 numeric_checks_v2 interpretation_gate',
    'evidence-budget': 'evidence_budget',
    'agentic': 'statistical_reports',
}


def engine_settings(env):
    engine = env.get('RESEARCH_ENGINE', 'baseline')
    balance = env.get('S2_PAPER_BALANCE', '0')
    if engine not in ('baseline', 's2') or balance not in ('0', '1'):
        raise ValueError('Invalid research engine configuration.')
    if engine == 'baseline' and balance == '1':
        raise ValueError('Paper balancing requires the S2 engine.')
    return engine, balance == '1'


def session_token(header, key):
    cookies = SimpleCookie()
    try:
        cookies.load(header or '')
    except CookieError:
        cookies.clear()
    value = cookies[COOKIE].value if COOKIE in cookies else ''
    ident, _, signature = value.partition('.')
    if re.fullmatch(r'[a-f0-9]{64}', ident):
        expected = digest(key, ident.encode(), sha256).hex()
        if compare_digest(signature.encode(), expected.encode()):
            return ident, None
    ident = token_hex(32)
    signature = digest(key, ident.encode(), sha256).hex()
    return ident, f'{COOKIE}={ident}.{signature}; Path=/api; HttpOnly; SameSite=Strict'


def build_s2(bundle, encoder_path, reranker_path, generate, metadata, checkpoint_root,
             *, paper_balance=False):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'retrieval-v3'))
    from s2_adapter import create_s2_research
    from evidence_budget import open_ranked
    from src.research_review import assess_regulatory

    retrieval = open_ranked(bundle, encoder_path=encoder_path,
                            reranker_path=reranker_path, table_comparisons=False)
    with (bundle / 'parents.jsonl').open(encoding='utf-8') as stream:
        rows = {row['chunk_id']: row for row in map(json.loads, stream)}
    checkpoint_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    research = create_s2_research(retrieval=retrieval, generate=generate, metadata=metadata,
                                  checkpoint_root=checkpoint_root, rows=rows,
                                  paper_balance=paper_balance)
    research.regulatory_assessor = assess_regulatory
    execute = research.execute

    def execute_for_session(payload, *, session_id=None):
        identity = session_id or SESSION.get()
        if not identity:
            raise ValueError('An isolated S2 session is required.')
        return execute(payload, session_id=identity)

    research.execute = execute_for_session
    return research, retrieval[1]()
