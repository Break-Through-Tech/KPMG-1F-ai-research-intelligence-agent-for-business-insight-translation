"""Synthetic checks that the corpus validator rejects broken provenance."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.data_ingestion.chunking import chunk_html_sections
from src.data_ingestion.html_parser import parse_html_sections
from tests.validate_html_sample import inspect_paper, is_subsequence, classify_candidate, normalize, git_provenance, summarize_omissions, verify_semantic_evidence, portable_command, write_report, serialize_report
from tests.html_transport import validate_transport


class HtmlValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.aid = '2601.00001v1'
        self.html = ('<section class="ltx_section" id="S1"><h2 class="ltx_title">Results</h2>'
                     '<div class="ltx_para" id="S1.p1">' + 'Evidence about research agents. ' * 20 +
                     '</div></section>')
        (self.root / f'{self.aid}.html').write_text(self.html, encoding='utf-8')
        self.metadata = dict(arxiv_id=self.aid, title='Research', authors='Author', categories='cs.AI',
                             abstract='Abstract', published='2026-01-01', updated='2026-01-01',
                             pdf_url=f'https://arxiv.org/pdf/{self.aid}')
        self.frame = pd.DataFrame([{**chunk, **self.metadata, 'source': 'html'} for chunk in
            chunk_html_sections(parse_html_sections(self.html), self.aid, 'Research')])

    def inspect(self, frame):
        with patch('tests.validate_html_sample.config.HTML_DIR', self.root), \
             patch('tests.validate_html_sample.config.PROJECT_ROOT', self.root), \
             patch('tests.validate_html_sample.resolve_pdf_path', return_value=None):
            return inspect_paper(self.metadata, frame)

    def test_valid_cached_source(self):
        self.assertEqual(self.inspect(self.frame)['failures'], [])

    def test_invented_page_and_bad_anchor_fail(self):
        for field, value in [('page_number', 1), ('html_url', f'https://arxiv.org/html/{self.aid}#missing'),
                             ('text', 'These words do not occur in the original source.'),
                             ('section', 'not the cited heading')]:
            with self.subTest(field=field):
                frame=self.frame.copy(); frame[field]=value
                self.assertTrue(self.inspect(frame)['failures'])

    def test_source_word_order_is_checked(self):
        self.assertTrue(is_subsequence('one three','one two three'))
        self.assertFalse(is_subsequence('three one','one two three'))

    def test_other_section_cannot_support_the_cited_passage(self):
        other = 'Evidence exclusive to the other section. ' * 10
        html = self.html + ('<section class="ltx_section" id="S2">'
                           '<h2 class="ltx_title">Discussion</h2>'
                           '<div class="ltx_para">' + other + '</div></section>')
        (self.root / f'{self.aid}.html').write_text(html)
        frame = self.frame.copy()
        frame['text'] = other.strip()
        self.assertTrue(self.inspect(frame)['failures'])

    def test_pdf_passage_must_belong_to_the_cited_original_page(self):
        pdf = self.root / 'fixture.pdf'
        pdf.write_bytes(b'page extraction is injected for this source-scope check')
        frame = self.frame.copy()
        frame['source'] = 'pdf'
        frame['page_number'] = 2
        frame['text'] = 'Evidence on page two.'
        with patch('tests.validate_html_sample.config.PROJECT_ROOT', self.root), \
             patch('tests.validate_html_sample.resolve_pdf_path', return_value=pdf), \
             patch('tests.validate_html_sample.extract_pages', return_value=[
                 {'page': 1, 'text': 'Different page evidence.'},
                 {'page': 2, 'text': 'Evidence on page two.'}]):
            self.assertEqual(inspect_paper(self.metadata, frame)['failures'], [])
            for page in (1, 3):
                frame['page_number'] = page
                self.assertTrue(inspect_paper(self.metadata, frame)['failures'])

    def test_persistent_transport_and_stale_records(self):
        frame=pd.concat([self.frame,self.frame],ignore_index=True)
        frame.loc[0,'chunk_id']='original:/ chunk id \u03b1'
        frame.loc[1,'chunk_id']='second'
        frame.loc[1,'arxiv_id']='synthetic-pdf'
        frame.loc[1,'source']='pdf'
        frame.loc[1,'page_number']=3
        frame.loc[1,'text']='Synthetic PDF evidence on page three.'
        result=validate_transport(frame,self.root/'chroma')
        self.assertEqual(result['first_count'],2)
        self.assertEqual(result['stale_rows_removed'],1)
        self.assertEqual(result['count_after_corpus_rerun'],1)
        self.assertTrue(result['invalid_input_preserved_usable_data'])
        self.assertTrue(result['original_ids_preserved'])
        self.assertTrue(result['public_contract_verified'])
        self.assertTrue(result['pre_upsert_failure_preserved_data'])
        self.assertTrue(result['post_upsert_delete_failure']['retry_repaired'])
        self.assertFalse(result['post_upsert_delete_failure']['full_corpus_rollback'])


    def test_omission_triage_detects_unhandled_nested_paragraph(self):
        from bs4 import BeautifulSoup
        html = ('<section class="ltx_section" id="S1"><h2 class="ltx_title">Limitations</h2>'
                '<section class="ltx_paragraph" id="S1.P1"><h4 class="ltx_title">Risk</h4>'
                '<div class="ltx_para" id="S1.P1.p1">' + 'Missing substantive safety evidence. ' * 10 + '</div></section></section>')
        parsed = parse_html_sections(html)
        retained = normalize(' '.join(s['text'] for s in parsed))
        node = BeautifulSoup(html, 'html.parser').find(id='S1.P1.p1')
        result = classify_candidate(node, retained, '')
        self.assertTrue(result['automated_structural_omission_candidate'])
        self.assertEqual(result['category'], 'potentially_missing_meaningful_text')

    def test_math_filter_is_distinct_from_missing_prose(self):
        from bs4 import BeautifulSoup
        node = BeautifulSoup('<div class="ltx_para">Retained prose.'
                             '<div class="ltx_equation">removed equation</div></div>', 'html.parser').div
        result = classify_candidate(node, 'Retained prose.', 'Retained prose.')
        self.assertEqual(result['category'], 'scientific_detail_filtered')
        self.assertTrue(result['projected_text_in_parser'])
        self.assertFalse(result['automated_structural_omission_candidate'])

    def test_false_positive_projection_is_not_a_confirmed_omission(self):
        from bs4 import BeautifulSoup
        node = BeautifulSoup('<div class="ltx_para">Evidence <span class="ltx_tag">1</span> retained.</div>', 'html.parser').div
        result = classify_candidate(node, 'Evidence retained.', 'Evidence retained.')
        self.assertEqual(result['category'], 'false_positive_review_candidate')
        self.assertFalse(result['automated_structural_omission_candidate'])


    def test_filtered_equations_do_not_hide_independent_structural_flag(self):
        from bs4 import BeautifulSoup
        html = ('<section class="ltx_section"><section class="ltx_paragraph">'
                '<div class="ltx_para">' + 'Absent substantive scientific prose. ' * 10 +
                '<div class="ltx_equation">equation</div></div></section></section>')
        node = BeautifulSoup(html, 'html.parser').find(class_='ltx_para')
        result = classify_candidate(node, '', '')
        self.assertEqual(result['category'], 'scientific_detail_filtered')
        self.assertTrue(result['automated_structural_omission_candidate'])

    def test_git_provenance_without_local_refs_is_optional(self):
        import subprocess
        with patch('tests.validate_html_sample.subprocess.check_output',
                   side_effect=subprocess.CalledProcessError(128, 'git')) as command:
            result = git_provenance()
        self.assertIsNone(result['origin_main_sha'])
        self.assertIsNone(result['main_sha'])
        self.assertFalse(any('khoi-' in str(call) for call in command.call_args_list))

    def test_markdown_command_is_portable_without_altering_execution_details(self):
        report = {'command': 'python -m tests.validate_html_sample --semantic-evidence C:/personal/result.json',
                  'semantic_smoke': {}, 'cached_pdf_fallback': {}, 'automated_tests': {}}
        original = report['command']
        command = portable_command(report)
        self.assertNotIn('C:/', command)
        self.assertIn('<temporary-results.json>', command)
        self.assertEqual(report['command'], original)

    def test_structural_flag_overlaps_primary_scientific_category(self):
        papers = [{'arxiv_id': 'fixture', 'omissions': {}, 'candidates_for_40_43': [
            {'triage': {'category': category, 'automated_structural_omission_candidate': True}}
            for category in ['scientific_detail_filtered', 'potentially_missing_meaningful_text']]}]
        summary = summarize_omissions(papers)
        self.assertEqual(summary['automated_structural_omission_candidate_paragraphs'], 2)
        self.assertEqual(summary['structural_candidates_by_primary_category']['scientific_detail_filtered'], 1)
        self.assertIn('not individual human confirmations', summary['review_scope'])

    def test_report_uses_current_counts_and_does_not_claim_old_absence(self):
        paper = {'arxiv_id': '2606.01494v1', 'source_modes': ['html'], 'chunks': 1,
                 'sections': {'results': 1}, 'source_urls': [], 'source_hashes': {},
                 'omissions': {}, 'failures': [], 'candidates_for_40_43': [{
                     'element_id': 'S1.SS0.SSS0.Px3.p1', 'triage': {
                         'category': 'false_positive_review_candidate',
                         'projected_text': 'Retained example prose.',
                         'projected_text_in_parser': True,
                         'automated_structural_omission_candidate': False}}]}
        report = {'status': 'PASS', 'papers': [paper], 'persisted_chunks': 1,
                  'failures': [], 'omission_summary': summarize_omissions([paper]),
                  'run_utc': 'fixture', 'branch': 'fixture', 'repo_sha': 'fixture',
                  'environment': {'python': '3.12', 'packages': {
                      'chromadb': 'fixture', 'sentence-transformers': 'fixture'}},
                  'source_files_unchanged': True, 'protected_inputs_unchanged': True}
        write_report(report, self.root / 'report')
        text = (self.root / 'report/html-ingestion-validation.md').read_text()
        self.assertIn('0 paragraphs are automatically flagged', text)
        self.assertIn('not 0 individually human-verified defects', text)
        self.assertNotIn('113 are potentially missing', text)
        self.assertNotIn('Confirmed behavioral examples', text)
        self.assertNotIn('their projected prose is absent', text)
        self.assertIn('Projected prose retained: True', text)

    def test_serialized_receipts_remove_personal_paths_without_changing_evidence(self):
        import json
        report = {'command': 'python -m tests.html_transport data/processed/chunks.parquet '
                             'C:/Users/contributor/private/run/index /Users/contributor/run/result.json --semantic',
                  'historical_execution_details': [{'log_path': r'C:\Users\contributor\run\full.log'}],
                  'corpus_sha256': 'original-hash', 'indexed_count': 877,
                  'papers': [{'text': 'Source passage unchanged.', 'source_url': 'https://arxiv.org/html/example'}]}
        encoded = serialize_report(report)
        public = json.loads(encoded)
        self.assertNotIn('contributor', encoded)
        self.assertIn('<local-output>/index', public['command'])
        self.assertEqual(public['historical_execution_details'][0]['log_path'], '<local-output>/full.log')
        for key in ('corpus_sha256', 'indexed_count', 'papers'):
            self.assertEqual(public[key], report[key])
        self.assertIn('contributor', report['command'])

    def test_semantic_receipt_rejects_stale_corpus_and_implementation(self):
        from src import retrieval
        from tests.html_transport import SEMANTIC_PROBES
        report = {'input_hashes': {'data/processed/chunks.parquet': 'current-corpus'},
                  'implementation_hashes': {'tests/validate_html_sample.py': 'current-validator',
                      'tests/html_transport.py': 'current-worker', 'src/retrieval.py': 'current-retrieval'},
                  'persisted_chunks': 3}
        frame = pd.DataFrame([{'chunk_id': f'probe-{i}', 'arxiv_id': aid,
            'text': marker + ' fixture evidence', 'title': 'Fixture', 'pdf_url': f'https://arxiv.org/pdf/{aid}',
            'source': 'html', 'html_url': f'https://arxiv.org/html/{aid}#S1', 'section': 'results', 'page_number': None}
            for i, (_, aid, marker) in enumerate(SEMANTIC_PROBES)])
        hits = [{'chunk_id': row['chunk_id'], 'text': row['text'], 'distance': 0.5,
                 **retrieval.citation_metadata(row), 'page_number': None} for row in frame.to_dict('records')]
        evidence = {'status': 'COMPLETED', 'corpus_sha256': 'current-corpus',
                    'implementation_hashes': dict(report['implementation_hashes']),
                    'model': retrieval.EMBEDDING_MODEL, 'dimensions': 384,
                    'indexed_count': 3, 'citation_checks': 'PASS', 'expected_paper_hits': 3,
                    'probes': [{'query': q, 'expected_paper': aid, 'hits': hits,
                                'expected_evidence_ids': [frame.iloc[i].chunk_id],
                                'expected_evidence_excerpt': frame.iloc[i].text,
                                'expected_paper_in_top_5': True} for i, (q, aid, _) in enumerate(SEMANTIC_PROBES)]}
        self.assertIs(verify_semantic_evidence(evidence, report, frame), evidence)
        windows_report = {**report, 'input_hashes': {'data\\processed\\chunks.parquet': 'current-corpus'}}
        self.assertIs(verify_semantic_evidence(evidence, windows_report, frame), evidence)
        for field, value in [('corpus_sha256', 'old-corpus'), ('implementation_hashes', None),
                             ('indexed_count', 876), ('dimensions', 768), ('status', 'FAILED'), ('probes', [])]:
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    verify_semantic_evidence({**evidence, field: value}, report, frame)
        for path in report['implementation_hashes']:
            with self.subTest(path=path):
                stale = {**evidence, 'implementation_hashes': {**evidence['implementation_hashes'], path: 'old'}}
                with self.assertRaisesRegex(ValueError, 'implementation'):
                    verify_semantic_evidence(stale, report, frame)

        import copy
        for field, value in [('chunk_id', 'absent-ID'), ('text', 'invented passage'),
                             ('source_url', 'https://invalid.example/wrong'), ('page_number', 99),
                             ('section', 'wrong heading'), ('distance', float('nan'))]:
            with self.subTest(corrupted_hit=field):
                bad = copy.deepcopy(evidence)
                bad['probes'][0]['hits'][0][field] = value
                with self.assertRaises(ValueError):
                    verify_semantic_evidence(bad, report, frame)
        for field, value in [('expected_evidence_ids', ['absent-ID']), ('expected_paper_in_top_5', False)]:
            with self.subTest(corrupted_probe=field):
                bad = copy.deepcopy(evidence)
                bad['probes'][0][field] = value
                with self.assertRaises(ValueError):
                    verify_semantic_evidence(bad, report, frame)
        with self.assertRaises(ValueError):
            verify_semantic_evidence({**evidence, 'expected_paper_hits': 99}, report, frame)


if __name__=='__main__':
    unittest.main()
