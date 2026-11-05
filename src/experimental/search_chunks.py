"""Token-bounded search views with immutable, full source passages as evidence.

Views are retrieval inputs only. Always resolve them back to their full parent
before synthesis, so table headers/cells and source locators remain together.
"""
from copy import deepcopy
from hashlib import sha256
import json
import math
import re


def record_hash(parent):
    return sha256(json.dumps(parent, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def split_passage(text, tokenizer, budget=224, overlap=32):
    """Yield exact character spans without silently dropping non-whitespace text."""
    if (not isinstance(text, str) or not text.strip() or isinstance(budget, bool)
            or not isinstance(budget, int) or isinstance(overlap, bool)
            or not isinstance(overlap, int) or overlap < 0 or budget <= overlap + 4):
        raise ValueError('Provide nonempty text and a token budget larger than overlap + 4.')
    reserve = tokenizer.num_special_tokens_to_add(pair=False)
    if reserve >= budget:
        raise ValueError('Special tokens exceed the requested budget.')
    start, covered = 0, 0
    while start < len(text):
        rest = text[start:]
        offsets = tokenizer(rest, add_special_tokens=False, truncation=False,
                            return_offsets_mapping=True)['offset_mapping']
        if not offsets:
            if rest.strip():
                raise ValueError('Tokenizer cannot represent source text.')
            break
        if len(offsets) + reserve <= budget:
            end = len(text)
        else:
            end = start + offsets[budget - reserve - 1][1]
            boundaries = [start + m.end() for m in re.finditer(r'(?<=[.!?])\s+|\n+', rest[:end-start])]
            candidates = [b for b in boundaries if b >= start + (end-start)//2]
            if candidates:
                end = candidates[-1]
        piece = text[start:end]
        tokens = tokenizer(piece, add_special_tokens=False, truncation=False,
                           return_offsets_mapping=True)['offset_mapping']
        while len(tokens) + reserve > budget:
            end = start + tokens[budget-reserve-1][0]
            piece = text[start:end]
            tokens = tokenizer(piece, add_special_tokens=False, truncation=False,
                               return_offsets_mapping=True)['offset_mapping']
        if end <= start or not piece.strip() or (start > covered and text[covered:start].strip()):
            raise ValueError('Chunking lost source text or failed to advance.')
        actual = len(tokenizer(piece, add_special_tokens=True, truncation=False)['input_ids'])
        if actual > budget:
            raise ValueError('Complete embedding input exceeds its token budget.')
        yield start, end, piece
        covered = max(covered, end)
        if end == len(text) or not text[end:].strip():
            break
        next_start = start + tokens[max(1, len(tokens)-overlap)][0] if overlap and len(tokens)>1 else end
        start = next_start if next_start > start else end
    if text[covered:].strip():
        raise ValueError('Chunking left source content uncovered.')


def make_search_views(parents, tokenizer, *, budget=224, overlap=32):
    views, seen = [], set()
    for parent in parents:
        ident = parent.get('chunk_id')
        if not isinstance(ident, str) or not ident.strip() or ident in seen:
            raise ValueError('Source parents need unique nonempty IDs.')
        seen.add(ident)
        digest = record_hash(parent)
        for number, (start, end, text) in enumerate(split_passage(parent.get('text'), tokenizer, budget, overlap)):
            views.append({'view_id': f'{ident}__v{budget}_{number:04d}', 'parent_chunk_id': ident,
                'char_start': start, 'char_end': end, 'text': text,
                'text_tokens': len(tokenizer(text, add_special_tokens=True, truncation=False)['input_ids']),
                'parent_record_sha256': digest, 'purpose': 'retrieval_only_not_citable'})
    return views


def collapse_to_parents(views, distances, parents, *, top_k=5):
    """Deduplicate best-view matches and return complete, original evidence records.

    Distances are ranking signals, not answer confidence or source verification.
    """
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError('top_k must be a positive integer.')
    if len(views) != len(distances):
        raise ValueError('Each search view needs one distance.')
    by_id = {p['chunk_id']: p for p in parents}
    if len(by_id) != len(parents):
        raise ValueError('Duplicate parent IDs.')
    hashes, seen, best = {}, set(), {}
    for view, distance in zip(views, distances):
        ident, view_id = view['parent_chunk_id'], view['view_id']
        if ident not in by_id or view_id in seen:
            raise ValueError('Unknown parent or duplicate search view.')
        seen.add(view_id)
        if isinstance(distance, bool) or not math.isfinite(float(distance)) or float(distance) < 0:
            raise ValueError('Search distances must be finite nonnegative numbers.')
        parent = by_id[ident]
        if ident not in hashes:
            hashes[ident] = record_hash(parent)
        a, b = view['char_start'], view['char_end']
        if (isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, int) or not isinstance(b, int)
                or not 0 <= a < b <= len(parent['text']) or parent['text'][a:b] != view['text']
                or hashes[ident] != view['parent_record_sha256']
                or view.get('purpose') != 'retrieval_only_not_citable'):
            raise ValueError('Search view no longer matches its complete source parent.')
        key = (float(distance), view_id)
        if ident not in best or key < best[ident]:
            best[ident] = key
    results = []
    for ident in sorted(best, key=lambda i: (best[i][0], i))[:top_k]:
        result = deepcopy(by_id[ident])
        result['distance'] = best[ident][0]
        result['retrieval'] = {'method': 'token-view-parent-min-l2-v1',
            'matched_view_id': best[ident][1], 'evidence_policy': 'complete_original_parent'}
        results.append(result)
    return results
