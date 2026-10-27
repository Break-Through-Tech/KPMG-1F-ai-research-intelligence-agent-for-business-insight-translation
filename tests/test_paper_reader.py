"""Source reading retention is separate from citation support and approval."""
from hashlib import sha256
from unittest import TestCase

from bs4 import BeautifulSoup

from src.paper_html import parse_paper_html
from src.paper_reader import retain_reader
from src.research_chat import synthesize


STRUCTURED_HTML = rb'''<article class="ltx_document"><section id="S1"><h2>Results</h2>
<div class="ltx_para"><h3>Measured result</h3><p>The measured result improves accuracy in this bounded experiment.</p>
<ul><li>First constraint</li><li>Second constraint</li></ul><ol start=3><li value=4>Numbered constraint</li></ol>
<math display="block"><mfrac><mi>x</mi><mn>2</mn></mfrac></math>
<math alttext="\binom{n}{k}"><mfrac linethickness="0"><mi>n</mi><mi>k</mi></mfrac></math></div>
<table><caption>Source measurements</caption><colgroup span="2"></colgroup><thead>
<tr><th id="results" colspan="2" scope="colgroup">Results</th></tr><tr><th id="model" scope="col">Model</th>
<th id="score" scope="col">Score</th></tr></thead><tbody><tr><th id="base" scope="row" rowspan="0">Base</th>
<td headers="base score results">12</td></tr><tr><td headers="base score results">13</td></tr></tbody></table>
<figure><img src="https://invalid.example/never-fetch" alt="Two source-labeled bars" onerror="bad()">
<figcaption>Accuracy by model.</figcaption></figure>
<figure><img src="missing"><figcaption>Caption only.</figcaption></figure>
</section></article>'''


def flatten(nodes):
    for node in nodes:
        if isinstance(node, dict):
            yield node
            yield from flatten(node['children'])


class PaperReaderTests(TestCase):
    def test_image_only_reader_blocks_survive_without_becoming_quote_text(self):
        paragraph = b'<div class="ltx_para">Evidence text.</div>'
        figure = b'<figure><img alt="Trend rises"></figure>'
        for blocks in (figure + paragraph, paragraph + figure):
            with self.subTest(blocks=blocks):
                raw = b'<article class="ltx_document"><section id="S1">' + blocks + b'</section></article>'
                passages, _ = parse_paper_html(raw, '2608.20318v1', 'Test')
                self.assertEqual(passages[0]['text'], 'Evidence text.')
                reader = passages[0]['reader']
                self.assertIn('Source-supplied image description: Trend rises', str(reader['nodes']))
                tags = [node['tag'] for node in reader['nodes']]
                self.assertEqual(tags, ['figure', 'div'] if blocks.startswith(figure) else ['div', 'figure'])
                self.assertTrue(reader['limitations'])

    def test_image_only_missing_description_limitation_survives(self):
        raw = b'<article class="ltx_document"><section id="S1"><div class="ltx_para">Evidence text.</div><figure><img src="missing"></figure></section></article>'
        passages, _ = parse_paper_html(raw, '2608.20318v1', 'Test')
        self.assertEqual(passages[0]['text'], 'Evidence text.')
        self.assertTrue(any('No source-supplied image description' in item for item in passages[0]['reader']['limitations']))

    def test_column_group_structure_survives_with_grouped_headers(self):
        passages, _ = parse_paper_html(STRUCTURED_HTML, '2608.20318v1', 'Test')
        nodes = list(flatten(passages[0]['reader']['nodes']))
        self.assertEqual(next(node for node in nodes if node['tag'] == 'colgroup')['attrs']['span'], '2')
        self.assertEqual(next(node for node in nodes if node['tag'] == 'th')['attrs']['scope'], 'colgroup')
        nested = STRUCTURED_HTML.replace(b'<colgroup span="2"></colgroup>', b'<colgroup><col span="2"></colgroup>')
        passages, _ = parse_paper_html(nested, '2608.20318v1', 'Test')
        self.assertEqual(next(node for node in flatten(passages[0]['reader']['nodes']) if node['tag'] == 'col')['attrs']['span'], '2')

    def test_unknown_math_semantics_rejects_the_whole_passage_reader(self):
        for expression in [b'<menclose notation="updiagonalstrike"><mi>x</mi></menclose>',
                           b'<mfenced open="[" close="]" separators=";"><mi>x</mi><mi>y</mi></mfenced>']:
            with self.subTest(expression=expression):
                raw = STRUCTURED_HTML.replace(b'<mi>x</mi>', expression, 1)
                passages, _ = parse_paper_html(raw, '2608.20318v1', 'Test')
                self.assertEqual(passages[0]['reader']['nodes'], [])
                self.assertIn('The measured result improves accuracy', passages[0]['text'])
                self.assertTrue(any('Unsupported MathML attributes' in item for item in passages[0]['reader']['limitations']))

    def test_binomial_bar_thickness_survives_source_retention(self):
        passages, _ = parse_paper_html(STRUCTURED_HTML, '2608.20318v1', 'Test')
        fractions = [node for node in flatten(passages[0]['reader']['nodes']) if node['tag'] == 'mfrac']
        self.assertEqual(fractions[1]['attrs']['linethickness'], '0')
        self.assertIn(r'\binom{n}{k}', passages[0]['text'])

    def test_unsupported_math_elements_are_not_flattened_into_a_different_expression(self):
        raw = STRUCTURED_HTML.replace(b'<mi>x</mi>', b'<maction><mi>x</mi><mi>y</mi></maction>', 1)
        passages, _ = parse_paper_html(raw, '2608.20318v1', 'Test')
        self.assertEqual(passages[0]['reader']['nodes'], [])
        self.assertTrue(any('Unsupported MathML structure' in item for item in passages[0]['reader']['limitations']))

    def test_rejected_fraction_thickness_falls_back_for_the_whole_passage(self):
        raw = STRUCTURED_HTML.replace(b'linethickness="0"', b'linethickness="url(remote)"')
        passages, _ = parse_paper_html(raw, '2608.20318v1', 'Test')
        self.assertEqual(passages[0]['reader']['nodes'], [])
        self.assertIn(r'\binom{n}{k}', passages[0]['text'])
        self.assertTrue(any('Unsupported MathML fraction thickness' in item for item in passages[0]['reader']['limitations']))

    def test_retains_source_math_lists_headers_captions_and_provenance(self):
        passages, source = parse_paper_html(STRUCTURED_HTML, '2608.20318v1', 'Structured test')
        self.assertEqual(len(passages), 1)
        passage = passages[0]
        reader = passage['reader']
        self.assertEqual(reader['source_sha256'], sha256(STRUCTURED_HTML).hexdigest())
        self.assertEqual(reader['source_sha256'], source['sha256'])
        self.assertEqual(reader['provenance'], 'source-html')
        nodes = list(flatten(reader['nodes']))
        self.assertTrue({'h3', 'ul', 'li', 'math', 'mfrac', 'table', 'caption', 'th', 'td', 'figcaption'} <= {node['tag'] for node in nodes})
        cell = next(node for node in nodes if node['tag'] == 'td')
        self.assertEqual(cell['attrs']['headers'], 'base score results')
        self.assertEqual(next(node for node in nodes if node['tag'] == 'ol')['attrs']['start'], '3')
        self.assertEqual(next(node for node in nodes if node['tag'] == 'th' and node['attrs'].get('id') == 'score')['attrs']['scope'], 'col')
        self.assertIn('The measured result improves accuracy in this bounded experiment.', passage['text'])
        self.assertEqual(passage['text'].count('Source measurements'), 1)
        rendered_data = str(reader)
        self.assertIn('Source-supplied image description: Two source-labeled bars', rendered_data)
        self.assertIn('Source-supplied caption:', rendered_data)
        self.assertNotIn('never-fetch', rendered_data)
        self.assertNotIn('onerror', rendered_data)
        self.assertTrue(any('caption alone' in gap for gap in reader['limitations']))

    def test_scripts_urls_and_attributes_are_not_retained_as_executable_markup(self):
        soup = BeautifulSoup('<div class="ltx_para" style="color:red" onclick="bad()"><script>bad()</script><iframe src="remote"></iframe><a href="javascript:bad()">Readable link text</a><math href="bad"><mi onclick="bad()">x</mi></math><!-- hidden --></div>', 'html.parser')
        reader = retain_reader([soup.div], 'a' * 64)
        nodes = list(flatten(reader['nodes']))
        self.assertNotIn('script', {node['tag'] for node in nodes})
        self.assertNotIn('iframe', {node['tag'] for node in nodes})
        self.assertIn('Readable link text', str(reader))
        self.assertNotIn('bad()', str(reader))
        self.assertNotIn('color:red', str(reader))
        self.assertNotIn('hidden', str(reader))

    def test_unknown_table_relationships_are_not_invented(self):
        soup = BeautifulSoup('<table><tr><td>Unlabeled value</td></tr></table>', 'html.parser')
        reader = retain_reader([soup.table], 'a' * 64)
        self.assertTrue(any('No row or column headers' in gap for gap in reader['limitations']))
        self.assertNotIn('th', {node['tag'] for node in flatten(reader['nodes'])})

    def test_reader_depth_limit_falls_back_without_losing_canonical_quote_text(self):
        raw = b'<article class="ltx_document"><div class="ltx_para">' + b'<div>' * 60 + b'Retained canonical evidence.' + b'</div>' * 60 + b'</div></article>'
        passages, _ = parse_paper_html(raw, '2608.20318v1', 'Test')
        self.assertEqual(passages[0]['text'], 'Retained canonical evidence.')
        self.assertEqual(passages[0]['reader']['nodes'], [])
        self.assertTrue(passages[0]['reader']['limitations'])

    def test_reader_data_cannot_substitute_for_exact_quote_membership(self):
        import json
        passages, _ = parse_paper_html(STRUCTURED_HTML, '2608.20318v1', 'Test')
        claim = {'text': 'Test claim', 'kind': 'finding', 'support': [{
            'chunk_id': passages[0]['chunk_id'], 'quote': 'Two source-labeled bars'}]}
        # Image alt is source-owned reader context, but is NOT in canonical text.
        with self.assertRaisesRegex(ValueError, 'absent from its cited passage'):
            synthesize('Q', passages, generate=lambda _: json.dumps({'status': 'ok', 'claims': [claim], 'limitations': []}))

    def test_reader_metadata_is_not_additional_generation_evidence(self):
        import json
        passages, _ = parse_paper_html(STRUCTURED_HTML, '2608.20318v1', 'Test')
        prompts = []
        def generate(prompt):
            prompts.append(prompt)
            return json.dumps({'status': 'insufficient_evidence', 'claims': [], 'limitations': [{
                'text': 'The evidence is bounded.', 'support': [{
                    'chunk_id': passages[0]['chunk_id'],
                    'quote': 'The measured result improves accuracy in this bounded experiment.'}]}]})
        synthesize('Q', passages, generate=generate)
        self.assertNotIn('"reader":', prompts[0])
        self.assertNotIn('Two source-labeled bars', prompts[0])

    def test_real_arxiv_literal_intent_and_bounded_math_layout_are_retained(self):
        raw = STRUCTURED_HTML.replace(b'<math display="block">', b'<math display="block" intent=":literal" displaystyle="true"><mstyle mathsize="0.7em"><mspace width="0.497em"/>', 1).replace(b'</math>', b'</mstyle></math>', 1)
        passages, _ = parse_paper_html(raw, '2608.20318v1', 'Test')
        nodes = list(flatten(passages[0]['reader']['nodes']))
        self.assertEqual(next(n for n in nodes if n['tag'] == 'math')['attrs']['intent'], ':literal')
        self.assertEqual(next(n for n in nodes if n['tag'] == 'mspace')['attrs']['width'], '0.497em')
        self.assertEqual(next(n for n in nodes if n['tag'] == 'mstyle')['attrs']['mathsize'], '0.7em')

    def test_unknown_intent_and_unsafe_math_layout_fail_closed(self):
        for attr in ['intent="custom(x)"', 'lspace="url(remote)"', 'mathsize="999em"', 'displaystyle="yes"']:
            with self.subTest(attr=attr):
                raw = STRUCTURED_HTML.replace(b'<math display="block">', ('<math display="block" '+attr+'>').encode(), 1)
                passages, _ = parse_paper_html(raw, '2608.20318v1', 'Test')
                self.assertEqual(passages[0]['reader']['nodes'], [])
                self.assertTrue(passages[0]['reader']['limitations'])
