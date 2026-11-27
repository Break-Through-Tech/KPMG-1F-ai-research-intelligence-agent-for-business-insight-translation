"""Optional adaptive research assistance (PROTOTYPE, not a default; 0 model calls to decide).

After Baseline retrieval builds the protected packet, this decides whether the Multi-Agent planner and supplementary
searches are worth one extra call. It uses only signals that are directly checkable against the packet, because the
earlier routing study (b2-adaptive-handoff.md) found that question complexity, facet coverage and score gaps did NOT
reliably predict evidence sufficiency. So complexity alone never activates assistance.

Activation signals (any one activates):
  A1 named_entity_missing   a paper, method or benchmark named in the question is absent from every packet passage.
  A2 concentration          the question names two or more entities, but one paper supplies > 80% of the packet.
Logged but never activating on their own: requested-part count, incomplete-table notes.
Every decision records the signals and the reason, so routing can be audited and later validated on fresh data.
"""
import re

GENERIC = {'A', 'An', 'The', 'What', 'How', 'Which', 'When', 'Why', 'Who', 'Is', 'Are', 'Does', 'Do', 'Did', 'Can',
           'For', 'In', 'On', 'And', 'Or', 'Of', 'To', 'LLM', 'LLMs', 'AI', 'EU', 'UK', 'US', 'U.S.', 'English',
           'Japanese', 'Chinese', 'NGO', 'R&D', 'GPT-style'}
NAME = re.compile(r"'([^']{3,80})'|\"([^\"]{3,80})\"|\b([A-Z][a-z]*[A-Z][A-Za-z0-9\-]*|[A-Z]{3,}[A-Za-z0-9\-]*)\b")
PART = re.compile(r',|;|\band\b|\?|\bhow\b|\bwhat\b|\bwhich\b|\bwhether\b', re.I)


def named_entities(question):
    """Quoted titles and distinctive names (CamelCase or acronyms such as HarmNet, AutoJailbreak, CLINIC, BOA)."""
    out = []
    for match in NAME.finditer(question):
        name = next(g for g in match.groups() if g)
        if name not in GENERIC and name not in out:
            out.append(name)
    return out


def _present(name, passages):
    folded = name.casefold()
    words = [w for w in re.findall(r'[a-z0-9]+', folded) if len(w) > 3]
    for p in passages:
        hay = f"{p.get('title', '')} {p.get('text', '')}".casefold()
        if folded in hay or (len(words) >= 2 and sum(w in hay for w in words) >= len(words) * 0.75):
            return True
    return False


def decide(question, packet):
    passages = packet['passages']
    names = named_entities(question)
    missing = [n for n in names if not _present(n, passages)]
    papers = {}
    for p in passages:
        papers[p.get('arxiv_id')] = papers.get(p.get('arxiv_id'), 0) + 1
    top_share = max(papers.values()) / len(passages) if passages else 0.0
    signals = {'named_entities': names, 'missing_entities': missing, 'papers_in_packet': len(papers),
               'top_paper_share': round(top_share, 2), 'requested_parts': len([s for s in PART.split(question) if s and s.strip()]),
               'incomplete_table_notes': len(packet.get('notes', []))}
    reasons = []
    if missing:
        reasons.append(f"A1: named in the question but absent from the packet: {', '.join(missing)}")
    if len(names) >= 2 and top_share > 0.8:
        reasons.append(f'A2: {len(names)} named entities but one paper supplies {top_share:.0%} of the packet')
    return {'activate': bool(reasons), 'reasons': reasons or ['no checkable coverage gap; Standard evidence kept'],
            'signals': signals, 'validated': False}
