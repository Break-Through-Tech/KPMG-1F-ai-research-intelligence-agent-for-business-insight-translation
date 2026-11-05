"""Lossless slicing checks, independent of embeddings and model downloads."""
import unittest
from evaluation.test_token_chunks import split_passage


class CharacterTokenizer:
    def num_special_tokens_to_add(self, pair=False):
        return 2

    def __call__(self, text, add_special_tokens=False, **kwargs):
        return {'input_ids': list(range(len(text)+(2 if add_special_tokens else 0))),
                'offset_mapping': [(i,i+1) for i in range(len(text))]}


class TokenChunkExperimentTests(unittest.TestCase):
    def test_short_text_remains_one_exact_span(self):
        text='Short result.'
        self.assertEqual(list(split_passage(text,CharacterTokenizer(),32,4)),[(0,len(text),text)])

    def test_long_sentences_unicode_and_numbers_are_preserved_with_budget(self):
        for text in ['A'*300, 'First sentence. Second result is 77.4%. Third result is 30.4%. '*5,
                     'α and café. This is not a gain. '*12]:
            chunks=list(split_passage(text,CharacterTokenizer(),64,8))
            coverage=set()
            for a,b,piece in chunks:
                self.assertEqual(piece,text[a:b])
                self.assertLessEqual(len(piece)+2,64)
                coverage.update(range(a,b))
            self.assertTrue(all(i in coverage for i,c in enumerate(text) if not c.isspace()))
            self.assertEqual(chunks[-1][1],len(text))
            self.assertTrue(all(a[0]<b[0] for a,b in zip(chunks,chunks[1:])))

    def test_sentence_end_is_preferred_and_invalid_budget_rejected(self):
        chunks=list(split_passage('First sentence is here. Second sentence is longer than the first.',CharacterTokenizer(),42,4))
        self.assertEqual(chunks[0][2],'First sentence is here. ')
        with self.assertRaises(ValueError):
            list(split_passage('A',CharacterTokenizer(),32,32))


if __name__=='__main__':
    unittest.main()
