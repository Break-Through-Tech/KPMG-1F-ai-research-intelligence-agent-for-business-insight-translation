"""Deterministic question components for component-coverage retrieval (no model calls).

A consultant question is a business preamble plus several asks ("What did X do, what did it report on A, B and C,
and what limits apply?"). Each ask becomes one component query. Asks after the first usually drop the subject
("what limits apply"), so every component query is prefixed with the question's named terms (MARASON, CliBench,
MedQA-CS, GPT-4, quoted phrases). Unnamed subjects ("the survey") are handled by paper scoping at selection
time, not here. The business preamble is not added: it describes the client, not the evidence.

Fixed before any coverage measurement; not tuned on results.
"""
import re

MAX_COMPONENTS = 6
_ASK = r'(?:what|how|which|when|where|why|whether|who|does|do|did|is|are|can|could|should)\b'
_PREP = r'(?:(?:on|in|for|with|by|from|at|to|under|against|about)\s+)?'
_SPLIT = re.compile(r',\s*(?:and\s+|or\s+)?(?=' + _PREP + _ASK + r')|;\s*'
                    r'|\s+and\s+(?=' + _PREP + r'(?:what|how|which|when|where|why|whether)\b)', re.I)
_STARTS_ASK = re.compile(r'^' + _PREP + _ASK, re.I)
_NAMED = re.compile(r'"[^"]{2,60}"|“[^”]{2,60}”|\b[A-Za-z]*[A-Z][a-z0-9]*[A-Z0-9][A-Za-z0-9.-]*\b')
_GENERIC = {'llm', 'llms', 'ai', 'ml', 'nlp', 'rag', 'gpu', 'gpus', 'api', 'apis'}


def named_terms(text):
    """Names with internal capitals or digits (MARASON, CliBench, MedQA-CS, GPT-3.5) and quoted phrases;
    generic acronyms (LLM, AI, RAG...) are not names."""
    seen = [q.strip('"“”') for q in re.findall(r'"[^"]{2,60}"|“[^”]{2,60}”', text)]
    for word in re.findall(r'[A-Za-z0-9][A-Za-z0-9.]*(?:-[A-Za-z0-9.]+)*', text):  # hyphenated names stay whole
        term = word.rstrip('.')
        caps, digits = sum(c.isupper() for c in term), any(c.isdigit() for c in term)
        if not (caps >= 2 or (caps and digits)) or re.search(r'-(?:based|like|style|driven)$', term, re.I):
            continue
        if len(term) >= 3 and term.lower() not in _GENERIC and term.lower() not in {t.lower() for t in seen}:
            seen.append(term)
    return seen


def components(question):
    """0-MAX_COMPONENTS component queries; empty when the question has a single ask."""
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+', question.strip()) if s.strip()]
    asks = [s for s in sentences if s.endswith('?')] or sentences[-1:]
    parts = []
    for ask in asks:
        pieces = [p.strip(' ,;?') for p in _SPLIT.split(ask) if p.strip(' ,;?')]
        lead = ''
        for piece in pieces:  # a leading context phrase ("In the X study,") joins the ask that follows it
            if not _STARTS_ASK.match(piece) and not parts and lead == '' and piece is pieces[0] and len(pieces) > 1:
                lead = piece + ', '
                continue
            if len(piece.split()) >= 2:
                parts.append(lead + piece)
            lead = ''
    parts = list(dict.fromkeys(parts))
    if len(parts) < 2:
        return []
    names = named_terms(' '.join(asks))
    out = []
    for part in parts[:MAX_COMPONENTS]:
        missing = [n for n in names if n.lower() not in part.lower()]
        out.append(' '.join(missing + [part]) + '?')
    return out


if __name__ == '__main__':
    # self-check on a synthetic question (not from any evaluation set)
    q = ('A retailer is evaluating demand forecasting. What does the FooNet paper propose, how accurate was it on '
         'the M5 benchmark, and what limits apply?')
    got = components(q)
    assert len(got) == 3, got
    assert got[1].startswith('FooNet M5') or got[1].startswith('FooNet'), got
    assert all(g.endswith('?') for g in got)
    assert components('What is FooNet?') == []
    print(got)
