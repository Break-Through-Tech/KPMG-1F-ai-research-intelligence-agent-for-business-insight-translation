import unittest

from src.experimental.evidence_coverage import comparison_pair


def row(label, table='T1', paper='demo-v1'):
    return {'arxiv_id': paper, 'table_id': table, 'row_label': label, 'caption': 'Benchmark accuracy',
            'table_headers': [{'text': 'Model'}, {'text': 'Accuracy'}]}


class ComparisonRowsTests(unittest.TestCase):
    def test_configured_rows_win_over_generic_and_opposite_conditions(self):
        rows = {'plain': row('Our Prism'), 'prism': row('Our Prism [w/ FT Model-2]'),
                'quartz': row('Quartz [w/ FT Model-2] w/ reasoning'),
                'no-reason': row('Quartz [w/ FT Model-2] w/o reasoning'),
                'other-model': row('Quartz [w/ FT Model-3] w/ reasoning')}
        self.assertEqual(comparison_pair(
            'Compare benchmark accuracy for fine-tuned Model-2, Prism and Quartz with reasoning.',
            list(rows), rows, {'demo-v1'}), ['prism', 'quartz'])
        self.assertEqual(comparison_pair(
            'Compare benchmark accuracy for fine-tuned Model-2, Prism and Quartz without reasoning.',
            list(rows), rows, {'demo-v1'}), ['prism', 'no-reason'])

    def test_ambiguous_tables_and_duplicate_labels_leave_rank_alone(self):
        for rows in (
            {'a': row('IOI'), 'b': row('Docstring'), 'other': row('IOI')},
            {'a': row('IOI'), 'b': row('Docstring'), 'c': row('IOI', 'T2'), 'd': row('Docstring', 'T2')},
        ):
            with self.subTest(rows=rows):
                self.assertEqual(comparison_pair(
                    'Compare accuracy for IOI and Docstring.', list(rows), rows, {'demo-v1'}), [])

    def test_requires_comparison_table_match_and_shortlisted_paper(self):
        rows = {'a': row('IOI'), 'b': row('Docstring')}
        for question, papers in (('Describe IOI and Docstring.', {'demo-v1'}),
                                 ('Compare latency for IOI and Docstring.', {'demo-v1'}),
                                 ('Compare accuracy for IOI and Docstring.', {'unrelated'})):
            with self.subTest(question=question, papers=papers):
                self.assertEqual(comparison_pair(question, list(rows), rows, papers), [])

    def test_compares_single_word_labels_in_a_relevant_table(self):
        rows = {'a': row('IOI'), 'b': row('Docstring')}
        self.assertEqual(comparison_pair(
            'Compare accuracy for IOI and Docstring.', list(rows), rows, {'demo-v1'}), ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
