"""Synthetic adapter fixtures, not real paper findings."""
def demo_retrieve(query, top_k):
    return [{'chunk_id': 'synthetic-html-1', 'text': 'Synthetic agents need task-specific evaluation.',
             'distance': 0.25, 'arxiv_id': 'synthetic', 'title': 'Synthetic fixture, not a paper',
             'pdf_url': 'https://example.com/fixture.pdf', 'source': 'html',
             'source_url': 'https://example.com/fixture#results', 'page_number': None,
             'html_url': 'https://example.com/fixture#results', 'section': 'results'},
            {'chunk_id': 'synthetic-pdf-2', 'text': 'Synthetic evidence requires human checks.',
             'distance': 0.5, 'arxiv_id': 'synthetic', 'title': 'Synthetic fixture, not a paper',
             'pdf_url': 'https://example.com/fixture.pdf', 'source': 'pdf',
             'source_url': 'https://example.com/fixture.pdf#page=2', 'page_number': 2}][:top_k]


def demo_summary(query, passages):
    return {'status': 'ok', 'query': query, 'claims': [
        {'text': p['text'], 'chunk_ids': [p['chunk_id']]} for p in passages],
        'limitations': ['Synthetic fixture only; no real corpus or model was evaluated.']}


def demo_translate(summary, passages, *, industry):
    return {'status': 'ok', 'industry': industry, 'implications': [
        {'text': 'Consider a task-specific evaluation pilot.',
         'chunk_ids': [passages[0]['chunk_id']], 'suggested_action': 'Design a bounded pilot.',
         'assumptions': ['Synthetic example; not verified industry advice.']}],
        'risks': ['Human source verification required.'], 'limitations': ['Fixture-only translation.']}


