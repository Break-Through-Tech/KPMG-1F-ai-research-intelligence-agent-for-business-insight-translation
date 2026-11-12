"""V3: recognising questions about several papers or systems, independent of phrasing.

Synthetic names only; none of these strings come from the evaluation questions.
"""
import unittest

from src.experimental.evidence_coverage import multi_source_intent, with_result_coverage
from src.experimental.question_parts import named_targets, question_parts


def p(cid, paper, text='x y z', section='results'):
    return {'chunk_id': cid, 'arxiv_id': paper, 'title': f'Paper {paper}', 'text': text, 'section': section,
            'source': 'html', 'page_number': None, 'pdf_url': '', 'html_url': '', 'source_url': ''}


class NamedTargetTests(unittest.TestCase):
    def test_quoted_titles_and_single_quoted_names_are_targets(self):
        self.assertEqual(named_targets('Does "Zephyr" agree with "Granite Paths for Agents"?'),
                         ['"Zephyr"', '"Granite Paths for Agents"'])

    def test_coined_names_are_targets_and_and_separates_them(self):
        self.assertEqual(named_targets('How do QuillNet and Harbor-RL handle long inputs?'), ['QuillNet', 'Harbor-RL'])
        self.assertEqual(named_targets('Is Lumen Graph Search cheaper than TinyRAG-X?'), ['Lumen Graph Search', 'TinyRAG-X'])

    def test_possessives_generic_acronyms_and_sentence_starts_are_not_separate_targets(self):
        self.assertEqual(named_targets("What did QuillNet's authors find about LLM and RAG costs?"), ['QuillNet'])
        self.assertEqual(named_targets('Which AI methods reduce GPU memory?'), [])
        self.assertEqual(named_targets('Explain how retrieval helps agents.'), [])


class PhrasingIndependenceTests(unittest.TestCase):
    def test_two_named_targets_split_whatever_the_wording(self):
        for q in ('Compare QuillNet and Harbor-RL on long inputs.',
                  'How do the conclusions of "Zephyr Nets" differ from those of "Granite Paths"?',
                  'Where do QuillNet and Harbor-RL disagree about long inputs?',
                  'Would QuillNet still help if Harbor-RL were used for training?'):
            with self.subTest(q=q):
                self.assertEqual(len(question_parts(q)), 2)

    def test_single_target_question_is_not_split_by_names(self):
        self.assertEqual(question_parts('How accurate is QuillNet on long inputs?'), [])


class SelectionTests(unittest.TestCase):
    def test_target_split_is_kept_only_when_targets_reach_different_papers(self):
        main = [p(f'a{i}', 'A') for i in range(16)]
        same = lambda q, k: [p(f's{q[:4]}{i}', 'A') for i in range(k)]
        other = lambda q, k: [p(f'o{q[:4]}{i}', 'B' if 'Harbor' in q else 'A') for i in range(k)]
        q = 'Where do QuillNet and Harbor-RL disagree about long inputs?'
        kept = with_result_coverage(lambda qq, k: main[:k], [], retrieve_part=same)(q, 8)
        self.assertEqual([x['chunk_id'] for x in kept], [f'a{i}' for i in range(8)])  # same paper: no split
        split = with_result_coverage(lambda qq, k: main[:k], [], retrieve_part=other)(q, 8)
        self.assertIn('B', {x['arxiv_id'] for x in split})

    def test_multi_source_language_balances_the_two_leading_papers(self):
        main = [p(f'a{i}', 'A') for i in range(10)] + [p(f'b{i}', 'B') for i in range(6)]
        search = with_result_coverage(lambda q, k: main[:k], [])
        out = search('What do the two papers on long inputs suggest together?', 8)
        self.assertGreaterEqual(sum(x['arxiv_id'] == 'B' for x in out), 2)
        out = search('What does the study on long inputs suggest?', 8)
        self.assertEqual({x['arxiv_id'] for x in out}, {'A'})

    def test_intent_cues_are_generic(self):
        self.assertTrue(multi_source_intent('How do both studies measure cost?'))
        self.assertTrue(multi_source_intent('Read alongside the benchmark, what changes?'))
        self.assertFalse(multi_source_intent('How does the method work on long inputs?'))


if __name__ == '__main__':
    unittest.main()
