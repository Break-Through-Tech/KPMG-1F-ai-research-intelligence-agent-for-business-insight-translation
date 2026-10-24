"""Emit a synthetic browser fixture; no model, paper download or approval.

Run: python -m tests.source_reader_fixture > /tmp/source-reader-fixture.json
"""
import json

from src.paper_html import parse_paper_html
from src.research_chat import synthesize
from src.research_pipeline import run_research
from tests.test_paper_reader import STRUCTURED_HTML


def reader_fixture():
    raw = STRUCTURED_HTML.replace(b'</section>', b'<div class="ltx_para">' +
        b'Long passage retained without truncation. ' * 180 +
        b'END OF LONG PASSAGE.</div><div class="ltx_para">Inline formula: <math><mtable><mtr>' +
        b'<mtd><mn>12345</mn></mtd>' * 30 + b'</mtr></mtable></math></div></section>')
    passages, _ = parse_paper_html(raw, '2608.20318v1',
        'Synthetic structured reader fixture - not a real paper')
    passages.append({'chunk_id': 'missing-metadata', 'title': 'Plain text fixture',
        'source': 'synthetic', 'text': 'Plain text with no recovered structure or PDF page mapping.',
        'source_url': None, 'pdf_url': None, 'arxiv_id': None, 'page_number': None})
    claim = {'text': 'Fixture claim about the bounded experiment.', 'kind': 'finding',
             'support': [{'chunk_id': passages[0]['chunk_id'],
                          'quote': 'The measured result improves accuracy in this bounded experiment.'}]}
    summary = synthesize('Fixture question', passages, generate=lambda _: json.dumps({
        'status': 'ok', 'claims': [claim], 'limitations': []}))
    result = run_research({'query': 'Fixture question'}, retrieve=lambda q, k: passages,
                         summarize_fn=lambda q, p: summary)
    return {'mode': 'fixture', 'scenario': 'full', 'submitted_request': result['request'],
            'result': result, 'error': None}


if __name__ == '__main__':
    print(json.dumps(reader_fixture()))
