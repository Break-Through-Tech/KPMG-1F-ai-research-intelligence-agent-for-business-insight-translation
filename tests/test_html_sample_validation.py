import unittest
from tests.validate_html_sample import verify_html, verify_pdf


class SourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.html = '<section class="ltx_section" id="S1"><h2 class="ltx_title">Introduction</h2><div class="ltx_para">Original source passage.</div></section>'
        self.chunk = {'text':'Original source passage.', 'section':'introduction',
                      'subsection':'', 'page_number':None, 'html_url':'https://arxiv.org/html/example#S1'}

    def test_real_scope_and_text(self):
        verify_html(self.chunk,self.html)

    def test_missing_anchor_and_invented_text_rejected(self):
        for change in ({'html_url':'https://arxiv.org/html/example#absent'},
                       {'text':'Invented passage.'}, {'page_number':1}):
            with self.subTest(change=change), self.assertRaises(AssertionError):
                verify_html({**self.chunk,**change},self.html)

    def test_text_in_other_section_is_not_support(self):
        html = self.html + '<section id="S2">Unrelated passage.</section>'
        with self.assertRaises(AssertionError):
            verify_html({**self.chunk,'text':'Unrelated passage.'},html)

    def test_pdf_wrong_page_and_text_rejected(self):
        verify_pdf({'page_number':2,'text':'correct'}, {2:'correct page'}, 2)
        for chunk in ({'page_number':3,'text':'correct'}, {'page_number':1,'text':'correct'},
                      {'page_number':2,'text':'fabricated'}):
            with self.subTest(chunk=chunk), self.assertRaises(AssertionError):
                verify_pdf(chunk,{2:'correct page'},2)
