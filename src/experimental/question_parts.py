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


def question_parts(question):
    """Return 0-3 sub-questions; empty when the question has a single part."""
    masked, spans = _protect(question)
    parts = []
    for clause in _clauses(masked):
        split = _comparison(clause)
        parts.extend(_restore(p, spans) for p in (split or [clause]))
    parts = [p for p in dict.fromkeys(parts) if len(tokens(p)) >= 2]
    if len(parts) < 2:
        return []
    return parts[:MAX_PARTS]
