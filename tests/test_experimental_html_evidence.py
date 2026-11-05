"""New-layout tests for the candidate table reader; not model accuracy tests."""
import unittest
import sys
from pathlib import Path
sys.dont_write_bytecode=True


from src.experimental.html_evidence import extract_html_evidence, validate_source_bindings
from src.research_contracts import validate_evidence

AID = '2601.00001v1'


def page(rows, caption='Results', cls='', wrap=None):
    html = (f'<figure class="ltx_table" id="T1"><figcaption>{caption}</figcaption>'
            f'<table class="{cls}">' + ''.join('<tr>' + r + '</tr>' for r in rows) + '</table></figure>')
    if wrap:
        html = f'<figure id="outer"><figcaption>{wrap}</figcaption>{html}</figure>'
    return '<section class="ltx_section" id="S1"><h2 class="ltx_title">Results</h2>' + html + '</section>'


def th(text, attrs='', col=True):
    return f'<th class="{"ltx_th_column" if col else "ltx_th_row"}" {attrs}>{text}</th>'


def extract(html):
    return extract_html_evidence(html, AID, 'Paper')


def values(row):
    return [c['text'] for c in row['table_cells']]


class CandidateTableTests(unittest.TestCase):
    def test_merged_row_label_repeats_on_each_row_and_is_marked(self):
        html = page([th('Model') + th('Setting') + th('Acc'),
                     th('A', 'rowspan="2"', col=False) + '<td>Base</td><td>0.46</td>',
                     '<td>Plus</td><td>0.78</td>',
                     th('B', 'rowspan="2"', col=False) + '<td>Base</td><td>0.44</td>',
                     '<td>Plus</td><td>0.76</td>'])
        rows = extract(html)['passages']
        self.assertEqual([values(r) for r in rows], [['A', 'Base', '0.46'], ['A', 'Plus', '0.78'],
                                                      ['B', 'Base', '0.44'], ['B', 'Plus', '0.76']])
        self.assertIn('Model: A; Setting: Plus; Acc: 0.78', rows[1]['text'])
        self.assertTrue(rows[1]['table_cells'][0]['merged_from_previous_row'])
        self.assertNotIn('merged_from_previous_row', rows[0]['table_cells'][0])
        validate_evidence(rows)
        self.assertTrue(validate_source_bindings(rows, html, AID, 'Paper'))

    def test_stacked_headers_bind_each_value_to_its_own_column(self):
        html = page([th('Method', 'rowspan="2"') + th('Open', 'colspan="2"') + th('Close', 'colspan="2"'),
                     th('Partial') + th('Success') + th('Partial') + th('Success'),
                     th('X', col=False) + '<td>2</td><td>0</td><td>8</td><td>1</td>'])
        result = extract(html)
        row = result['passages'][0]
        self.assertEqual([h['text'] for h in row['table_headers']],
                         ['Method', 'Open / Partial', 'Open / Success', 'Close / Partial', 'Close / Success'])
        self.assertIn('Method: X; Open / Partial: 2; Open / Success: 0; Close / Partial: 8; Close / Success: 1',
                      row['text'])
        self.assertEqual(row['header_rows'], 2)
        self.assertEqual(result['coverage']['tables'][0]['header_rows'], 2)

    def test_full_width_row_becomes_group_for_following_rows_only(self):
        html = page([th('Model') + th('Score'), th('Vendor A', 'colspan="2"', col=False),
                     '<td>m1</td><td>1</td>', th('Vendor B', 'colspan="2"', col=False), '<td>m2</td><td>2</td>'])
        rows = extract(html)['passages']
        self.assertEqual([r['row_group'] for r in rows], ['Vendor A', 'Vendor B'])
        self.assertEqual([r['table_row'] for r in rows], [1, 2])
        self.assertIn('Row group: Vendor B; Model: m2; Score: 2', rows[1]['text'])

    def test_empty_cell_is_reported_never_filled(self):
        rows = extract(page([th('Name') + th('A') + th('B'), '<td>x</td><td></td><td>2</td>']))['passages']
        self.assertEqual(values(rows[0]), ['x', '', '2'])
        self.assertIn('A: [empty in source]; B: 2', rows[0]['text'])

    def test_row_header_in_second_column_is_data_not_a_second_header(self):
        rows = extract(page([th('Name') + th('n') + th('Score'),
                             th('x', col=False) + th('173', col=False) + '<td>0.2</td>']))['passages']
        self.assertEqual(values(rows[0]), ['x', '173', '0.2'])

    def test_repeated_label_kept_but_identical_row_rejected(self):
        ok = extract(page([th('Name') + th('Metric') + th('V'),
                           '<td>a</td><td>m1</td><td>1</td>', '<td>a</td><td>m2</td><td>2</td>']))
        self.assertEqual(len(ok['passages']), 2)
        same = extract(page([th('Name') + th('V'), '<td>a</td><td>1</td>', '<td>a</td><td>1</td>']))
        self.assertEqual(same['coverage']['tables'][0]['reason'], 'duplicate_row')

    def test_unmarked_top_row_is_flagged_as_assumed(self):
        rows = extract(page(['<td>Models</td><td>Accuracy</td>', '<td>A</td><td>0.96</td>']))['passages']
        self.assertEqual(rows[0]['header_provenance'], 'first_row_assumed')
        self.assertEqual(rows[0]['header_review'], 'pending_human_verification')

    def test_numeric_top_row_is_not_assumed_to_be_headers(self):
        result = extract(page(['<td>A</td><td>0.96</td>', '<td>B</td><td>0.97</td>']))
        self.assertEqual(result['coverage']['tables'][0]['reason'], 'explicit_column_headers_missing')

    def test_subtable_keeps_outer_and_inner_caption(self):
        rows = extract(page([th('N') + th('V'), '<td>a</td><td>1</td>'], caption='(a) Inner', wrap='Table 4: Outer'))['passages']
        self.assertEqual(rows[0]['caption'], 'Table 4: Outer (a) Inner')

    def test_ambiguous_merges_still_reject_whole_table(self):
        cases = [
            (page([th('N') + th('A') + th('B'), '<td>x</td><td colspan="2">9</td>']), 'body_partial_colspan'),
            (page([th('N', 'rowspan="2"') + th('V'), '<td>1</td>']), 'header_span_into_data'),
            (page([th('N') + th('V'), '<td rowspan="3">x</td><td>1</td>']), 'merged_or_invalid_cell_span'),
            (page([th('N') + th('V'), '<td rowspan="0">x</td><td>1</td>']), 'merged_or_invalid_cell_span'),
            (page([th('N') + th('V'), '<td colspan="x">x</td><td>1</td>']), 'merged_or_invalid_cell_span'),
            (page([th('N') + th('V'), '<td>x</td><td>1</td><td>2</td>']), 'row_width_mismatch'),
            (page([th('N') + th('V'), '<td></td><td>1</td>']), 'empty_or_duplicate_row_label'),
            (page([th('N') + th('V'), th('M') + th('W'), '<td>a</td><td>1</td>', th('Q') + th('R')]), 'multiple_header_rows'),
            (page([th('Same') + th('Same'), '<td>a</td><td>1</td>']), 'empty_or_duplicate_header'),
            (page([th('Only', 'colspan="2"'), '<td>a</td><td>1</td>']), 'explicit_column_headers_missing'),
        ]
        for html, reason in cases:
            with self.subTest(reason=reason):
                result = extract(html)
                self.assertEqual(result['passages'], [])
                self.assertEqual(result['coverage']['tables'][0]['reason'], reason)

    def test_spacer_rows_are_counted_and_skipped(self):
        result = extract(page([th('N') + th('V'), '<td>a</td><td>1</td>', '<td></td><td></td>', '<td>b</td><td>2</td>']))
        self.assertEqual(len(result['passages']), 2)
        self.assertEqual(result['coverage']['tables'][0]['blank_rows_skipped'], 1)

    def test_source_validator_rejects_changed_value_or_column(self):
        from copy import deepcopy
        html=page([th('Name')+th('Score'),'<td>x</td><td>1</td>'])
        rows=extract(html)['passages']
        bad=deepcopy(rows);bad[0]['table_cells'][1]['text']='99'
        with self.assertRaises(ValueError):validate_source_bindings(bad,html,AID,'Paper')
        bad=deepcopy(rows);bad[0]['table_headers'][1]['text']='Other metric'
        with self.assertRaises(ValueError):validate_source_bindings(bad,html,AID,'Paper')

    def test_appendix_only_when_explicitly_requested(self):
        html = '<section class="ltx_appendix" id="A1">' + page([th('N') + th('V'), '<td>a</td><td>1</td>']) + '</section>'
        self.assertEqual(extract_html_evidence(html, AID, 'Paper', include_appendix=False)['passages'], [])
        rows=extract(html)['passages']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['appendix_id'],'A1')
        self.assertEqual(rows[0]['document_region'],'appendix')
        self.assertTrue(validate_source_bindings(rows,html,AID,'Paper'))


if __name__ == '__main__':
    unittest.main()
