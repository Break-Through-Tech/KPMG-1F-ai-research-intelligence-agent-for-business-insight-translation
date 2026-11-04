"""Offline experimental policies; never selected by production ingestion.

All intervals are half-open offsets into one source block. TeX math/literals are
atomic. Token ceilings are soft only for indivisible units; oversize is explicit.
"""
from dataclasses import dataclass
import math

import numpy as np

from src.semantic_chunking_adapter import _units


@dataclass(frozen=True)
class Policy:
    name: str
    threshold: float = .72
    min_tokens: int = 0
    max_tokens: int | None = None
    overlap_tokens: int = 0
    percentile: float | None = None
    max_chars: int = 1800


POLICIES = [
    Policy('original'),
    Policy('threshold35', .35), Policy('threshold50', .50),
    Policy('threshold65', .65),
    Policy('minimum80', min_tokens=80),
    Policy('minimum80_token240', min_tokens=80, max_tokens=240),
    Policy('minimum80_token240_overlap32', min_tokens=80, max_tokens=240, overlap_tokens=32),
    Policy('threshold50_minimum80_token240', .50, 80, 240),
    Policy('percentile20_minimum80_token240', min_tokens=80, max_tokens=240, percentile=20),
]


def units(text, tex=False):
    return _units(text, 1800, tex)


def semantic_intervals(text, spans, vectors, count_tokens, policy):
    if not spans:
        return []
    if not -1 <= policy.threshold <= 1 or policy.min_tokens < 0:
        raise ValueError('Invalid threshold/minimum')
    if policy.max_tokens is not None and not 0 <= policy.overlap_tokens < policy.max_tokens:
        raise ValueError('Invalid overlap')
    v = np.asarray(vectors, dtype=float)
    if v.ndim != 2 or len(v) != len(spans) or not np.isfinite(v).all():
        raise ValueError('Invalid embeddings')
    norms = np.linalg.norm(v, axis=1)
    if np.any(norms == 0):
        raise ValueError('Zero embedding')
    v = v / norms[:, None]
    threshold = policy.threshold
    if policy.percentile is not None and len(v) > 1:
        threshold = float(np.percentile(np.sum(v[:-1] * v[1:], axis=1), policy.percentile))
    output = []
    start = 0
    for i in range(1, len(spans)):
        a, b = spans[start][0], spans[i][1]
        centroid = v[start:i].mean(axis=0)
        length = np.linalg.norm(centroid)
        similarity = float(centroid @ v[i] / length) if length else -1
        current = count_tokens(text[a:spans[i-1][1]])
        too_big = b - a > policy.max_chars or (
            policy.max_tokens is not None and count_tokens(text[a:b]) > policy.max_tokens)
        if too_big or (current >= policy.min_tokens and similarity < threshold):
            output.append((a, spans[i-1][1]))
            following = i
            # Only repeat whole source units; never bisect math or loop forever.
            if policy.overlap_tokens:
                while following > start + 1 and count_tokens(text[spans[following-1][0]:spans[i-1][1]]) <= policy.overlap_tokens:
                    following -= 1
                if (spans[i][1] - spans[following][0] > policy.max_chars or
                        count_tokens(text[spans[following][0]:spans[i][1]]) > policy.max_tokens):
                    following = i
            start = following
    output.append((spans[start][0], spans[-1][1]))
    return output


def merge_intervals(intervals, text=None):
    """Merge only contiguous/overlapping evidence from the SAME source block."""
    merged = []
    for a, b in sorted(intervals):
        if not 0 <= a < b:
            raise ValueError('Invalid source interval')
        if merged and (a <= merged[-1][1] or (text is not None and not text[merged[-1][1]:a].strip())):
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    return merged


def select_context(chunks, scores, blocks, count_tokens, *, budget=None, top_k=None, neighbors=0, candidate_limit=200):
    """Rank then pack whole source windows, deduplicated under an exact token cap.

    Oversize windows are skipped, never cut into a fake citation. Neighbors stay
    within one block (one PDF page/HTML section/TeX include block). Textual budget
    includes document/query-prefix overhead via the injected counter, not model
    generation prompt framing. Rank ties are stable. top_k counts seed chunks.
    """
    if budget is not None and budget < 1 or neighbors < 0:
        raise ValueError('Invalid context budget')
    if len(scores) != len(chunks) or not np.isfinite(scores).all():
        raise ValueError('Invalid scores')
    order = np.argsort(-np.asarray(scores), kind='stable')[:candidate_limit]
    by_block = {}
    positions = {}
    for index, chunk in enumerate(chunks):
        key = chunk['block']
        positions[index] = len(by_block.setdefault(key, []))
        by_block[key].append(index)
    selected = {}
    seeds = 0
    skipped = 0
    for index in order:
        if top_k is not None and seeds >= top_k:
            break
        chunk = chunks[int(index)]
        key = chunk['block']
        siblings = by_block[key]
        pos = positions[int(index)]
        window = [chunks[j] for j in siblings[max(0, pos-neighbors):pos+neighbors+1]]
        candidate = {k: list(v) for k, v in selected.items()}
        candidate[key] = merge_intervals(candidate.get(key, []) + [(x['start'], x['end']) for x in window], blocks[key]['text'])
        cost = sum(count_tokens(blocks[k]['text'][a:b]) for k, spans in candidate.items() for a, b in spans)
        if budget is not None and cost > budget:
            skipped += 1
            continue
        if candidate != selected:
            selected = candidate
            seeds += 1
        if budget is not None and cost == budget:
            break
    evidence = [dict(block=k, start=a, end=b, text=blocks[k]['text'][a:b])
                for k, spans in selected.items() for a, b in spans]
    return dict(evidence=evidence, tokens=sum(count_tokens(x['text']) for x in evidence),
                seeds=seeds, skipped_over_budget=skipped)


def choose_policy(variants):
    """Selection must never inspect validation results."""
    choices = []
    for label, result in variants.items():
        if label in ('baseline', 'token_only240_overlap32'):
            continue
        for mode in ('tokens1600', 'tokens1600_neighbors'):
            summary = result['summaries'][mode]['tuning']
            choices.append((-summary['complete'], summary['mean_tokens'], label, mode))
    _, _, label, mode = min(choices)
    return label, mode
