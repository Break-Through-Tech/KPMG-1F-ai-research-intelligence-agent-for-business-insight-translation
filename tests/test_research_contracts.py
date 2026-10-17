"""Source-boundary regressions; no keys, network, index, or third-party packages."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock

from src.research_contracts import (
    validate_request, validate_evidence, validate_output, validate_summary,
    validate_business_insight, validate_result,
)
from src.research_pipeline import run_research

FIXTURES = Path(__file__).parent / 'fixtures/research'


def fixture(name='normal'):
    return json.loads((FIXTURES / f'{name}-v1.json').read_text())


class ResearchContractTests(unittest.TestCase):
    def test_versioned_fixtures_and_additive_metadata_are_preserved(self):
        for name in ('normal', 'empty', 'insufficient'):
            result = fixture(name)
            result['future_metadata'] = {'fixture_only': True}
            result['request']['future_context'] = ['retained']
            for passage in result['evidence']:
                passage['future_citation'] = {'locator_version': 2}
            before = deepcopy(result)
            with self.subTest(name=name):
                validate_result(result)
                self.assertEqual(result, before)

    def test_invalid_fixture_mutations_are_rejected(self):
        invalid = fixture('invalid')
        self.assertEqual(invalid['schema_version'], '1.0')
        for mutation in invalid['mutations']:
            result = fixture()
            node = result
            for key in mutation['path'][:-1]:
                node = node[key]
            node[mutation['path'][-1]] = mutation['value']
            with self.subTest(name=mutation['name']), self.assertRaises(ValueError):
                validate_result(result)

    def test_request_default_is_copied_without_stripping_query(self):
        original = {'query': ' agents ', 'future': {'values': []}}
        request = validate_request(original)
        self.assertEqual(request['top_k'], 5)
        self.assertEqual(request['query'], original['query'])
        request['future']['values'].append(1)
        self.assertNotIn('top_k', original)
        self.assertEqual(original['future']['values'], [])

    def test_bad_request_shapes_are_rejected(self):
        for request in (None, [], {}, {'query': ' '}, {'query': 1},
                        *({'query': 'a', 'top_k': k} for k in (True, 0, -1, 1.5, '5', None)),
                        {'query': 'a', 'industry': None}, {'query': 'a', 'jurisdiction': ''}):
            with self.subTest(request=request), self.assertRaises(ValueError):
                validate_request(request)

    def test_pdf_page_and_url_must_agree_before_summary_is_called(self):
        for key, value in [('page_number', -1), ('page_number', True),
                           ('page_number', 0), ('page_number', 1.5), ('page_number', '2'),
                           ('page_number', None), ('source_url', 'https://other.example/p.pdf#page=2'),
                           ('source_url', 'https://example.com/fixture.pdf#page=99')]:
            passages = fixture()['evidence']
            passages[1][key] = value
            summarize = Mock()
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                run_research({'query': 'a'}, retrieve=lambda *a: passages, summarize_fn=summarize)
            summarize.assert_not_called()

    def test_pdf_legacy_base_locator_and_html_without_anchor_remain_valid(self):
        passages = fixture()['evidence']
        passages[1]['source_url'] = passages[1]['pdf_url']
        passages[0]['source_url'] = passages[0]['html_url'] = 'https://example.com/fixture'
        self.assertEqual(validate_evidence(passages), {p['chunk_id'] for p in passages})

    def test_html_page_heading_and_missing_metadata_are_rejected(self):
        for key, value in [('page_number', 2), ('page_number', False),
                           ('source_url', 'https://example.com/fixture#other'),
                           ('html_url', 'https://other.example/#results'),
                           ('source', 'unknown'), ('source', []), ('title', ''), ('arxiv_id', None)]:
            passages = fixture()['evidence']
            passages[0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_evidence(passages)
        for key in ('source', 'source_url', 'page_number', 'title', 'pdf_url', 'arxiv_id'):
            passages = fixture()['evidence']
            del passages[0][key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                validate_evidence(passages)

    def test_invalid_urls_are_rejected_without_echoing_values(self):
        for url in ('', '/relative', 'javascript:SECRET', 'file:///tmp/SECRET',
                    'https://user:SECRET@example.com/x', 'https:///x',
                    'https://[broken', 'https://example.com:bad/x', 'https://example.com/a b',
                    'https://example.com/a\x00b'):
            passages = fixture()['evidence']
            passages[0]['source_url'] = passages[0]['html_url'] = url
            with self.subTest(url=url), self.assertRaises(ValueError) as caught:
                validate_evidence(passages)
            self.assertNotIn('SECRET', str(caught.exception))

    def test_duplicate_ids_and_nonfinite_or_boolean_distances_are_rejected(self):
        passages = fixture()['evidence']
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_evidence(passages + passages)
        for distance in (True, '0.5', float('nan'), float('inf')):
            passages[0]['distance'] = distance
            with self.subTest(distance=distance), self.assertRaises(ValueError):
                validate_evidence(passages)
        passages[0]['distance'] = None
        validate_evidence(passages)
        del passages[0]['distance']
        validate_evidence(passages)

    def test_synthetic_fixture_is_explicit_and_cannot_carry_paper_locators(self):
        passage = {'chunk_id': 'synthetic-1', 'text': 'Invented fixture.', 'title': 'Synthetic',
                   'source': 'synthetic', 'arxiv_id': None, 'pdf_url': None,
                   'source_url': None, 'page_number': None}
        validate_evidence([passage])
        for key, value in [('arxiv_id', 'real-id'), ('source_url', 'https://example.com/p'),
                           ('page_number', 1), ('html_url', 'https://example.com/p')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_evidence([{**passage, key: value}])

    def test_stage_shapes_reject_unknown_duplicate_and_malformed_citations(self):
        result = fixture()
        ids = validate_evidence(result['evidence'])
        for key, field in [('summary', 'claims'), ('business_insight', 'implications')]:
            for citations in ([], ['unknown'], ['synthetic-html-1'] * 2, [{}], [None], 'synthetic-html-1'):
                output = deepcopy(result[key])
                output[field][0]['chunk_ids'] = citations
                with self.subTest(stage=key, citations=citations), self.assertRaises(ValueError):
                    validate_output(output, field, ids)
            for status in ([], {}, None, True, 'approved'):
                output = {**result[key], 'status': status}
                with self.subTest(status=status), self.assertRaises(ValueError):
                    validate_output(output, field, ids)
            with self.assertRaises(ValueError):
                validate_output({**result[key], 'status': 'insufficient_evidence'}, field, ids)
            for value in (None, 'not-a-list', [1]):
                with self.subTest(limitations=value), self.assertRaises(ValueError):
                    validate_output({**result[key], 'limitations': value}, field, ids)

    def test_summary_query_and_business_context_must_match(self):
        result = fixture()
        ids = validate_evidence(result['evidence'])
        with self.assertRaisesRegex(ValueError, 'query'):
            validate_summary(result['summary'], ids, query='different')
        with self.assertRaisesRegex(ValueError, 'industry'):
            validate_business_insight(result['business_insight'], ids, industry='different')
        for field, value in [('risks', None), ('implications', []), ('industry', '')]:
            output = {**result['business_insight'], field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_business_insight(output, ids)
        for field, value in [('suggested_action', ''), ('assumptions', [1])]:
            output = deepcopy(result['business_insight'])
            output['implications'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_business_insight(output, ids)

    def test_result_schema_review_and_missing_required_fields_fail_closed(self):
        for field in ('schema_version', 'request', 'evidence', 'summary', 'human_review', 'approved'):
            result = fixture()
            del result[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                validate_result(result)
        for field, value in [('schema_version', '2.0'), ('approved', True), ('approved', 0),
                             ('provenance', []), ('regulatory_checkpoint', 'advisory'),
                             ('human_review', {}), ('human_review', {'status': 'approve', 'reviewer': 'x', 'notes': None})]:
            result = {**fixture(), field: value}
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                validate_result(result)
        result = fixture()
        result['summary'] = fixture('insufficient')['summary']
        with self.assertRaisesRegex(ValueError, 'supported summary'):
            validate_result(result)

    def test_contract_and_pipeline_import_and_execute_with_stdlib_only(self):
        script = '''import json, sys
from pathlib import Path
from src.research_contracts import validate_result
from src.research_pipeline import run_research
r = json.loads(Path("tests/fixtures/research/normal-v1.json").read_text())
out = run_research(r["request"], retrieve=lambda q,k: r["evidence"],
    summarize_fn=lambda q,p: r["summary"],
    translate_fn=lambda s,p,industry: r["business_insight"])
validate_result(out)
assert out["evidence"] == r["evidence"] and out["approved"] is False
assert not any(m in sys.modules for m in ("chromadb", "sentence_transformers", "google.genai", "openai"))
'''
        completed = subprocess.run([sys.executable, '-S', '-c', script],
            cwd=FIXTURES.parents[2], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == '__main__':
    unittest.main()
