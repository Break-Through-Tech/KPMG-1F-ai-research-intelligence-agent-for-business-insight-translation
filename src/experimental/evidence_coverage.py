"""Candidate expansion only: final selection belongs to relevance ranking."""
import re
from collections import defaultdict

from .retriever import tokens


def coverage_candidates(question, parents, papers):
    """Offer results/methods passages without reserving evidence slots."""
    return [p['chunk_id'] for p in parents if p.get('arxiv_id') in papers
            and re.search(r"results?|evaluation|experiments?|performance|methods?|methodology", p.get('section', ''), re.I)]


def _configuration_terms(text):
    text = re.sub(r'\bw/o\b', 'without', text, flags=re.I)
    text = re.sub(r'\bw/(?=\s|$)', 'with', text, flags=re.I)
    text = re.sub(r'\bfine[- ]tun(?:ed|ing)\b', 'ft', text, flags=re.I)
    return set(tokens(text))


def comparison_pair(question, ranked, byid, papers):
    """Keep an unambiguous pair of explicitly requested numeric rows together."""
    if not re.search(r'\b(?:and|vs|versus|compar\w*|between)\b', question, re.I):
        return []
    if not re.search(r'\b(?:scores?|ranges?|accuracy|auc|rates?|counts?|latency|values?|pass@\d+)\b',
                     question, re.I):
        return []
    requested = _configuration_terms(question)
    eligible = defaultdict(list)
    for ident in ranked:
        row = byid[ident]
        if row['arxiv_id'] not in papers or not row.get('table_id'):
            continue
        label = _configuration_terms(row['row_label'])
        if label and label <= requested:
            eligible[(row['arxiv_id'], row['table_id'])].append((ident, label))

    pairs = []
    for matches in eligible.values():
        specific = [(ident, label) for ident, label in matches
                    if not any(label < other for _, other in matches)]
        if len(specific) != 2 or specific[0][1] == specific[1][1]:
            continue
        first, second = specific
        row = byid[first[0]]
        table_terms = _configuration_terms(' '.join(
            [row.get('caption', '')] + [header['text'] for header in row['table_headers'][1:]]
        ))
        # Require a table-level match beyond the two row labels.
        if requested.intersection(table_terms) - first[1] - second[1]:
            pairs.append([first[0], second[0]])
    return pairs[0] if len(pairs) == 1 else []
