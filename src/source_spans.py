"""Versioned, exact slices of packed source text; no generated offsets or quotes."""
from hashlib import sha256
import re

POLICY = 'displayed-source-spans-v1'
MAX_SPAN_CHARS = 1000
MIN_SPAN_CHARS = 15


def text_hash(text):
    return sha256(text.encode('utf-8')).hexdigest()


def build_spans(passages):
    """Sentence/paragraph slices, with overlapping windows for long sentences.

    Offsets are Python Unicode character offsets in the normalized displayed
    passage, not byte offsets or offsets in a PDF. Callers exclude synthetic
    truncation markers before passing source text here.
    """
    spans = []
    for passage in passages:
        text = passage['text']
        digest = text_hash(text)
        boundaries = [0] + [m.end() for m in re.finditer(r'(?<=[.!?])\s+|\n{2,}', text)] + [len(text)]
        for left, right in zip(boundaries, boundaries[1:]):
            start, end = left, right
            while start < end and text[start].isspace():
                start += 1
            while end > start and text[end - 1].isspace():
                end -= 1
            if end - start < MIN_SPAN_CHARS:
                # Include neighboring source context instead of inventing padding.
                start = max(0, end - MIN_SPAN_CHARS)
            while end - start >= MIN_SPAN_CHARS:
                stop = min(end, start + MAX_SPAN_CHARS)
                if stop < end:
                    split = text.rfind(' ', start + MIN_SPAN_CHARS, stop)
                    if split > start:
                        stop = split
                if len(re.sub(r'\s+', ' ', text[start:stop]).strip()) < MIN_SPAN_CHARS:
                    break
                spans.append({'span_id': f's{len(spans):04d}',
                              'span_policy': POLICY, 'chunk_id': passage['chunk_id'],
                              'start': start, 'end': stop, 'source_sha256': digest})
                if stop == end:
                    break
                start = max(start + 1, stop - 120)
    return spans


def hydrate_selection(selection, spans, passages):
    """Fail closed on stale sources, bad offsets or unknown IDs; never alias IDs."""
    menu = {span['span_id']: span for span in spans}
    sources = {p['chunk_id']: p['text'] for p in passages}
    if len(menu) != len(spans) or len(sources) != len(passages):
        raise ValueError('Duplicate span or source ID')
    facts = []
    for fact in selection['facts']:
        span = menu.get(fact['span_id'])
        if span is None or span['span_policy'] != POLICY:
            raise ValueError('Unknown span ID or policy')
        text = sources.get(span['chunk_id'])
        if text is None or text_hash(text) != span['source_sha256']:
            raise ValueError('Source text changed after span construction')
        start, end = span['start'], span['end']
        if (type(start) is not int or type(end) is not int or
                not 0 <= start < end <= len(text) or
                not MIN_SPAN_CHARS <= end - start <= MAX_SPAN_CHARS):
            raise ValueError('Invalid source span bounds')
        facts.append({'chunk_id': span['chunk_id'], 'quote': text[start:end],
                      'finding': fact['finding'], 'relevance': fact['relevance'],
                      'source_span': dict(span)})
    return {**selection, 'facts': facts}


def render_menu(spans, passages):
    """JSON framing never interprets source delimiters as trusted metadata."""
    import json
    sources = {p['chunk_id']: p['text'] for p in passages}
    return json.dumps([{'span_id': s['span_id'], 'chunk_id': s['chunk_id'],
                        'text': sources[s['chunk_id']][s['start']:s['end']]}
                       for s in spans], ensure_ascii=False)
