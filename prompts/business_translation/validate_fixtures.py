"""Offline design-fixture integrity checks; does not call or evaluate a model."""
import json
from pathlib import Path
from string import Template


def validate():
    root = Path(__file__).resolve().parent
    fixtures = json.loads((root / 'fixtures.json').read_text())
    assert len(fixtures) >= 3
    for fixture in fixtures:
        assert fixture['synthetic'] is True
        evidence = fixture['evidence']
        known = {p['chunk_id'] for p in evidence}
        assert len(known) == len(evidence)
        for passage in evidence:
            assert {'chunk_id', 'text', 'distance', 'arxiv_id', 'title', 'pdf_url',
                    'source', 'source_url', 'page_number'} <= passage.keys()
            assert passage['source'] == 'synthetic'
            assert passage['text'].strip()
        summary = fixture['summary']
        assert summary['status'] in ('ok', 'insufficient_evidence')
        for claim in summary['claims']:
            assert claim['chunk_ids'] and set(claim['chunk_ids']) <= known
        expected = fixture['expected']
        assert set(expected) == {'status', 'industry', 'implications', 'risks', 'limitations'}
        assert expected['industry'] == fixture['industry']
        assert expected['status'] in ('ok', 'insufficient_evidence')
        for field in ('risks', 'limitations'):
            assert isinstance(expected[field], list)
            assert all(isinstance(s, str) and s.strip() for s in expected[field])
        if expected['status'] == 'insufficient_evidence':
            assert expected['implications'] == []
        for implication in expected['implications']:
            assert set(implication) == {'text', 'chunk_ids', 'suggested_action', 'assumptions'}
            assert implication['chunk_ids'] and set(implication['chunk_ids']) <= known
            assert isinstance(implication['text'], str) and implication['text'].strip()
            assert isinstance(implication['suggested_action'], str) and implication['suggested_action'].strip()
            assert isinstance(implication['assumptions'], list)
            assert all(isinstance(s, str) and s.strip() for s in implication['assumptions'])
        for name in ('baseline-v1.txt', 'counterevidence-v1.txt'):
            rendered = Template((root / name).read_text()).substitute(
                industry=fixture['industry'], summary_json=json.dumps(summary),
                evidence_json=json.dumps(evidence))
            assert fixture['industry'] in rendered
            assert json.dumps(summary) in rendered
            assert json.dumps(evidence) in rendered
    print(f'{len(fixtures)} synthetic fixtures validated against both templates; no model run.')


if __name__ == '__main__':
    validate()
