"""Opt-in peer-inspired retrieval experiments; production defaults are unchanged.

All passage text and source locators stay bound to a frozen, versioned corpus.
Ranking signals are not confidence or independent semantic quality labels.
"""
from copy import deepcopy
from collections import defaultdict


def fuse(rankings, *, method):
    """RRF over passage IDs, retaining channel ranks and the original citations."""
    rows, scores, ranks = {}, defaultdict(float), defaultdict(dict)
    for channel, ranking in rankings.items():
        seen = set()
        for rank, row in enumerate(ranking, 1):
            ident = row['chunk_id']
            if ident in seen:
                raise ValueError('Duplicate ID in ranking')
            seen.add(ident)
            if ident in rows and any(rows[ident].get(k) != row.get(k) for k in
                                     ('text', 'arxiv_id', 'source_url')):
                raise ValueError('Conflicting passage identity')
            rows.setdefault(ident, deepcopy(row))
            scores[ident] += 1 / (60 + rank)
            ranks[ident][channel] = rank
    result = []
    for ident in sorted(rows, key=lambda k: (-scores[k], k)):
        row = rows[ident]
        row['retrieval'] = {'method': method, 'rrf_score': scores[ident],
                            'channel_ranks': ranks[ident]}
        result.append(row)
    return result


def cap_papers(rows, *, top_k=5, per_paper=2):
    """Optional breadth policy, not the default retrieval contract."""
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 1
           for x in (top_k, per_paper)):
        raise ValueError('Counts must be positive integers')
    counts, selected = defaultdict(int), []
    for row in rows:
        paper = row['arxiv_id']  # Versions are never silently merged.
        if counts[paper] < per_paper:
            selected.append(deepcopy(row))
            counts[paper] += 1
        if len(selected) == top_k:
            break
    return selected


def fuse_papers(paper_ranking, passages, evidence):
    """1J-inspired paper-level RRF with one independently retrieved evidence row.

paper_ranking contains exact version IDs ranked by title/abstract similarity;
passages supplies the chunk-derived paper ranking. evidence(paper_id) performs
an explicit within-paper search, so a paper need not occur in the chunk pool.
"""
    chunk_papers = list(dict.fromkeys(p['arxiv_id'] for p in passages))
    scores, ranks = defaultdict(float), defaultdict(dict)
    for channel, ranking in [('metadata', paper_ranking), ('chunks', chunk_papers)]:
        for rank, paper in enumerate(ranking, 1):
            scores[paper] += 1 / (60 + rank)
            ranks[paper][channel] = rank
    result = []
    for paper in sorted(scores, key=lambda k: (-scores[k], k)):
        row = deepcopy(evidence(paper))
        if row['arxiv_id'] != paper:
            raise ValueError('Within-paper evidence returned another paper')
        row['retrieval'] = {'method': 'metadata-chunk-paper-rrf',
                            'rrf_score': scores[paper], 'channel_ranks': ranks[paper]}
        result.append(row)
    return result


class NeighborContext:
    """Whole-passage, budgeted expansion in explicit frozen table order.

    Table adjacency is not proof of continuity in the original document.
    Boundaries include exact version, source modality, section and subsection.
    PDF neighbors keep their own pages; added neighbors receive no fake score.
    """
    def __init__(self, rows, *, count_tokens):
        self.rows, self.groups, self.positions = {}, defaultdict(list), {}
        self.count_tokens = count_tokens
        for ordinal, original in enumerate(rows):
            row = deepcopy(original)
            ident = row['chunk_id']
            if ident in self.rows:
                raise ValueError('Duplicate corpus ID')
            if not row.get('text', '').strip():
                raise ValueError('Empty corpus text')
            key = tuple(row.get(k) for k in ('arxiv_id', 'source'))
            self.positions[ident] = (key, len(self.groups[key]), ordinal)
            self.groups[key].append(ident)
            self.rows[ident] = row

    def expand(self, anchors, *, window=1, token_budget=6000):
        if any(isinstance(x, bool) or not isinstance(x, int) or x < 1
               for x in (window, token_budget)):
            raise ValueError('Window/budget must be positive integers')
        selected, used = {}, 0
        for anchor in anchors:
            ident = anchor['chunk_id']
            if ident not in self.rows or any(anchor.get(k) != self.rows[ident].get(k)
                    for k in ('text', 'arxiv_id', 'source_url')):
                raise ValueError('Anchor differs from frozen corpus')
            if ident in selected:
                raise ValueError('Duplicate anchor')
            row = deepcopy(anchor)
            row['context'] = {'role': 'anchor', 'anchor_chunk_ids': [ident],
                              'corpus_ordinal': self.positions[ident][2]}
            selected[ident] = row
            used += self.count_tokens(row['text'])
        if used > token_budget:
            raise ValueError('Anchors exceed context budget; none silently removed')
        skipped = set()
        # Round-robin across anchors: one paper cannot consume the budget first.
        for distance in range(1, window + 1):
            for anchor in anchors:
                key, position, _ = self.positions[anchor['chunk_id']]
                group = self.groups[key]
                for offset in (-distance, distance):
                    pos = position + offset
                    if not 0 <= pos < len(group):
                        continue
                    # Do not jump over another section with an identical label
                    # later in the document. Every intervening row must agree.
                    scope = lambda r: tuple(r.get(k) for k in ('section', 'subsection')) + (
                        r.get('source_url') if r.get('source') == 'html' else None,)
                    anchor_scope = scope(self.rows[anchor['chunk_id']])
                    if any(scope(self.rows[group[j]]) != anchor_scope
                           for j in range(min(pos, position), max(pos, position)+1)):
                        continue
                    ident = group[pos]
                    if ident in selected:
                        origins = selected[ident]['context']['anchor_chunk_ids']
                        if anchor['chunk_id'] not in origins:
                            origins.append(anchor['chunk_id'])
                        continue
                    row = deepcopy(self.rows[ident])
                    size = self.count_tokens(row['text'])
                    if used + size > token_budget:
                        skipped.add(ident)
                        continue
                    row.pop('retrieval', None)
                    row.pop('distance', None)
                    row['context'] = {'role': 'neighbor',
                                      'anchor_chunk_ids': [anchor['chunk_id']],
                                      'corpus_ordinal': self.positions[ident][2]}
                    selected[ident], used = row, used + size
        return list(selected.values()), {'text_tokens': used, 'token_budget': token_budget,
                    'budget_scope': 'sum of passage-text tokens; excludes prompt and citation overhead',
                    'skipped_for_budget': sorted(skipped - selected.keys()),
                    'neighbor_count': sum(r['context']['role'] == 'neighbor' for r in selected.values())}
