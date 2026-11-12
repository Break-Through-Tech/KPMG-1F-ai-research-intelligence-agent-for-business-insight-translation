"""Candidate expansion only: final selection belongs to relevance ranking."""
import re


def coverage_candidates(question, parents, papers):
    """Offer results/methods passages without reserving evidence slots."""
    if not re.search(r"\b(how often|success rate|pass rate|accuracy|benchmark|still|currently|current|today|latest|now)\b", question, re.I):
        return []
    return [p['chunk_id'] for p in parents if p.get('arxiv_id') in papers
            and re.search(r"results?|evaluation|experiments?|performance|methods?|methodology", p.get('section', ''), re.I)]
