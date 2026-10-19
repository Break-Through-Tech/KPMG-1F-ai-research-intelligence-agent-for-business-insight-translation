"""Math provenance: preserve original TeX and honest HTML locators / PDF fallback."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.paper_html import parse_paper_html, fetch_arxiv_html
from src.research_chat import load_paper


HTML = br'''<article class="ltx_document"><section id="S2">
<h2>Scoring</h2><div class="ltx_para">We define
<math alttext="x_\perp" display="inline"><mi>x</mi></math>.</div>
<table id="S2.E1" class="ltx_equation"><tr><td><math display="block"
alttext="\sigma(x)=\begin{cases}0.1 &amp; x\leq b\\1 &amp; x&gt;b\end{cases}">
<mi>scrambled PDF text</mi></math></td><td>(1)</td></tr></table>
<div class="ltx_para">With <math><semantics><mi>y</mi>
<annotation encoding="application/x-tex">\phi^*</annotation></semantics></math>.</div>
</section><div class="ltx_bibliography"><div class="ltx_para">references</div></div></article>'''


class PaperHtmlTests(TestCase):
    def test_preserves_inline_and_display_tex_without_duplicate_blocks(self):
        passages, source = parse_paper_html(HTML, '2608.20318v1', 'Test')
        self.assertEqual(len(passages), 1)
        passage = passages[0]
        self.assertIn(r'\(x_\perp\)', passage['text'])
        self.assertIn(r'\[\sigma(x)=\begin{cases}0.1 & x\leq b\\1 & x>b\end{cases}\]', passage['text'])
        self.assertIn(r'\(\phi^*\)', passage['text'])
        self.assertEqual(passage['text'].count(r'\sigma(x)'), 1)
        self.assertNotIn('scrambled', passage['text'])
        self.assertNotIn('references', passage['text'])
        self.assertIsNone(passage['page_number'])
        self.assertEqual(passage['source_url'], 'https://arxiv.org/html/2608.20318v1#S2')
        self.assertEqual(source['format'], 'arxiv-html-with-tex')

    def test_rejects_error_pages_and_oversized_html(self):
        for html in [b'<html>Not found</html>', b'x' * 5_000_001]:
            with self.assertRaises(ValueError):
                parse_paper_html(html, '2608.20318v1', 'Test')

    def test_fetch_requires_version_before_network_access(self):
        for aid in ['2608.20318', '../secret', '2608.20318v1?redirect=other']:
            with self.assertRaises(ValueError):
                fetch_arxiv_html(aid)

    def test_html_preference_and_unavailable_html_pdf_fallback(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / '2608.20318v1_Test.pdf'
            path.write_bytes(b'local placeholder')
            with patch('src.paper_html.fetch_arxiv_html', return_value=HTML):
                passages, source = load_paper(path)
            self.assertEqual(passages[0]['source'], 'html')
            self.assertIn('evidence', source)
            with patch('src.paper_html.fetch_arxiv_html', side_effect=OSError), patch('src.research_chat.subprocess.run') as run:
                run.return_value.stdout = 'Actual extracted PDF text.\f'
                passages, source = load_paper(path)
            self.assertEqual(passages[0]['source'], 'pdf')
            self.assertEqual(source['html_fallback'], 'OSError')
            self.assertEqual(source['format'], 'pdf-text')
