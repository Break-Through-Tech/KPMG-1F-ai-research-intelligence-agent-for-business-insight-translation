"""Split a research question into independently retrievable parts.

Purely syntactic: clause boundaries, interrogative/auxiliary clause starts and
explicit comparisons. It never uses paper titles, topics or expected answers.
"""
import re

from .retriever import tokens

CLAUSE_START = (r'what|how|why|which|who|whom|whether|when|where|do|does|did|is|are|was|were|'
                r'can|could|should|will|would|has|have|had')
COMPARE = re.compile(r'\b(compare|comparing|comparison of|versus|vs\.?|difference between|differences between)\b', re.I)
STOP_ENTITY = re.compile(r'^(make|makes|made|do|does|did|is|are|was|were|perform|performs|differ|differs|'
                         r'in|on|for|to|with|when|at|by|reduce|reduces|improve|improves|handle|handles)$', re.I)
MAX_PARTS = 3


def _clauses(question):
    parts = re.split(r'\?\s*|;\s*', question)
    out = []
    for part in parts:
        out.extend(re.split(r',\s*(?:and|but|or)\s+|\s+(?:and|but)\s+(?=(?:' + CLAUSE_START + r')\b)',
                            part, flags=re.I))
    return [c.strip(' ,.') for c in out if c and c.strip(' ,.')]


def _comparison(clause):
    """'Compare how A and B do X' -> ['A do X', 'B do X'] without knowing A or B."""
    cue = COMPARE.search(clause)
    if not cue or ' and ' not in clause[cue.end():]:
        return []
    if len(clause[:cue.start()].split()) > 2:  # the question must ask for the comparison, not mention one
        return []
    body = re.sub(r'^\s*(how|what|whether)\s+', '', clause[cue.end():], flags=re.I)
    left, right = body.split(' and ', 1)
    words = right.split()
    cut = next((i for i, w in enumerate(words) if i and STOP_ENTITY.match(w.strip(',.'))), len(words))
    entity_b, rest = ' '.join(words[:cut]), ' '.join(words[cut:])
    entity_a = left.strip()
    if not entity_a or not entity_b:
        return []
    return [f'{entity_a} {rest}'.strip(), f'{entity_b} {rest}'.strip()]


QUOTED = re.compile(r'"[^"]+"|“[^”]+”')


def _protect(text):
    """Quoted spans (usually paper titles) are atomic: never split inside them."""
    spans = []

    def keep(m):
        spans.append(m.group())
        return f'\u0000{len(spans) - 1}\u0000'
    return QUOTED.sub(keep, text), spans


def _restore(text, spans):
    return re.sub('\u0000(\\d+)\u0000', lambda m: spans[int(m.group(1))], text)


# Everyday field vocabulary, not names of specific systems or papers.
GENERIC_ACRONYMS = {'AI', 'ML', 'LLM', 'LLMS', 'LM', 'LMS', 'RAG', 'NLP', 'GPU', 'GPUS', 'CPU', 'API', 'APIS', 'KV',
                    'QA', 'US', 'EU', 'UK', 'USD', 'PDF', 'HTML', 'SOTA', 'VLM', 'VLMS', 'MLLM', 'MLLMS', 'AGI', 'IT'}
CONNECTORS = {'of', 'for', 'in', 'on', 'with', 'to', 'the', 'a', 'an', 'via', 'from', 'at', 'by'}  # 'and'/'or' separate names
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-.]*[A-Za-z0-9]|[A-Za-z0-9]")


def _named(word):
    """A coined name: two or more capitals or a capital with digits (LowRAM, DP-MemArc, GPT-4)."""
    pieces = [p for p in re.split(r'[-.]', word) if p]
    if not any(c.isupper() for c in word):
        return False
    distinctive = [p for p in pieces if p.upper() not in GENERIC_ACRONYMS
                   and (sum(c.isupper() for c in p) >= 2 or (any(c.isupper() for c in p) and any(c.isdigit() for c in p)))]
    return bool(distinctive)


def named_targets(question):
    """Distinct things a question names: quoted spans, coined names and capitalized multi-word names.

    Purely orthographic; it never consults titles, topics or expected answers.
    """
    masked, spans = _protect(question)
    targets = [s for s in spans if tokens(s)]
    words = [(m.group(), m.start(), m.end()) for m in WORD.finditer(masked) if '\u0000' not in m.group()]
    sentence_starts = {0} | {m.end() for m in re.finditer(r'[.?!:;]\s+', masked)}
    run = []

    def close():
        while run and run[-1][0].lower() in CONNECTORS:
            run.pop()
        while run and run[0][1] in sentence_starts and not _named(run[0][0]):
            run.pop(0)  # an ordinary sentence-opening word ('Is', 'Does') is not part of a name
        if run:
            names = [w for w, _, _ in run if _named(w)]
            caps = [w for w, s, _ in run if w[0].isupper() and w.lower() not in CONNECTORS
                    and w.upper() not in GENERIC_ACRONYMS and s not in sentence_starts]
            if names or len(caps) >= 2:
                targets.append(masked[run[0][1]:run[-1][2]])
        run.clear()
    for w, s, e in words:
        if w[0].isupper() or _named(w):
            if run and masked[run[-1][2]:s].strip(" -") not in ('',):
                close()
            run.append((w, s, e))
        elif run and w.lower() in CONNECTORS and masked[run[-1][2]:s].strip() == '':
            run.append((w, s, e))
        else:
            close()
    close()
    cleaned = (re.sub(r"['’]s$", '', t.strip()) for t in targets)
    return list(dict.fromkeys(t for t in cleaned if t))


def _target_parts(question, targets):
    context = question
    for t in targets:
        context = context.replace(t, ' ')
    context = re.sub(r'\s+', ' ', re.sub(r'\b(and|or|vs\.?|versus)\b\s*(?=[,?.]|$)', ' ', context)).strip(' ,.?')
    return [f'{t} {context}'.strip() for t in targets]


def question_parts(question):
    """Return 0-3 sub-questions; empty when the question has a single part.

    A question naming two or more distinct targets (titles, systems, methods) gets
    one part per target, whatever the phrasing ('compare', 'differ', 'versus', 'both',
    'how do A and B relate'...). Otherwise clause and explicit-comparison splitting apply.
    """
    targets = named_targets(question)
    if len(targets) >= 2:
        return _target_parts(question, targets)[:MAX_PARTS]
    masked, spans = _protect(question)
    parts = []
    for clause in _clauses(masked):
        split = _comparison(clause)
        parts.extend(_restore(p, spans) for p in (split or [clause]))
    parts = [p for p in dict.fromkeys(parts) if len(tokens(p)) >= 2]
    if len(parts) < 2:
        return []
    return parts[:MAX_PARTS]
