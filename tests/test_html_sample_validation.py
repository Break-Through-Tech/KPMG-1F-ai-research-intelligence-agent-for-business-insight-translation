"""Synthetic checks that the corpus validator rejects broken provenance."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.data_ingestion.chunking import chunk_html_sections
from src.data_ingestion.html_parser import parse_html_sections
from tests.validate_html_sample import inspect_paper, is_subsequence
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

    def test_persistent_transport_and_stale_records(self):
        frame=pd.concat([self.frame,self.frame],ignore_index=True)
        frame.loc[1,'chunk_id']='second'
        result=validate_transport(frame,self.root/'transport.sqlite')
        self.assertEqual(result['first_count'],2)
        self.assertEqual(result['stale_rows_after_upload_only'],1)
        self.assertEqual(result['count_after_explicit_rebuild'],1)
        self.assertEqual(result['live_azure_requests'],0)


if __name__=='__main__':
    unittest.main()
