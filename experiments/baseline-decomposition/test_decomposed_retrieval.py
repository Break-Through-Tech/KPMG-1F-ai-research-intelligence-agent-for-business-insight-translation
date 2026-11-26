"""Offline regression tests for opt-in Baseline question decomposition. No model or index is loaded."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]
from decomposed_retrieval import CAP, decompose, decomposed  # noqa: E402
from question_parts import question_parts  # noqa: E402


def passage(cid, text='text about results'):
    return {'chunk_id': cid, 'text': text, 'arxiv_id': cid.split('_')[0], 'title': 't', 'pdf_url': 'https://arxiv.org/pdf/x',
            'source': 'html', 'source_url': 'https://arxiv.org/html/x', 'page_number': None, 'section': 'Results'}


class Index:
    """Fake B2: each query maps to a ranked list; records the calls."""

    def __init__(self, routes, fail=()):
        self.routes, self.fail, self.calls = routes, set(fail), []

    def __call__(self, query, top_k):
        self.calls.append((query, top_k))
        if query in self.fail:
            raise RuntimeError('search failed')
        return [passage(c) for c in self.routes.get(query, [])][:top_k]


class Splitting(unittest.TestCase):
    def test_simple_question_is_searched_once(self):
        q = 'How accurate is QuillNet on long inputs?'
        self.assertEqual(question_parts(q), [])
        index = Index({q: ['a_1', 'a_2']})
        self.assertEqual([p['chunk_id'] for p in decomposed(index)(q, 8)], ['a_1', 'a_2'])
        self.assertEqual(len(index.calls), 1)

    def test_multipart_question_searches_original_then_each_part(self):
        q = 'I am comparing CG-RAG and SAM-RAG. How does each choose material?'
        queries = decompose(q)
        self.assertEqual(queries[0], q)
        self.assertEqual(len(queries), 3)
        self.assertTrue(queries[1].startswith('CG-RAG') and queries[2].startswith('SAM-RAG'))

    def test_part_identical_to_question_is_not_searched_twice(self):
        self.assertEqual(decompose('Q', splitter=lambda q: ['Q', 'q', ' Q ']), ['Q'])


class Merging(unittest.TestCase):
    def routes(self):
        return {'Q': [f'o_{i}' for i in range(8)], 'p1': ['o_0', 'x_1', 'x_2'], 'p2': ['y_1', 'o_1', 'y_2']}

    def test_round_robin_keeps_original_top_results_first_and_deduplicates(self):
        index = Index(self.routes())
        ids = [p['chunk_id'] for p in decomposed(index, splitter=lambda q: ['p1', 'p2'])('Q', 8)]
        self.assertEqual(ids[:3], ['o_0', 'y_1', 'o_1'])  # rank 1 of each search, duplicate o_0 skipped
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids.count('o_1'), 1)

    def test_cap_is_enforced_and_original_top_three_always_survive(self):
        routes = {'Q': [f'o_{i}' for i in range(8)], **{f'p{j}': [f'p{j}_{i}' for i in range(8)] for j in range(3)}}
        ids = [p['chunk_id'] for p in decomposed(Index(routes), splitter=lambda q: ['p0', 'p1', 'p2'])('Q', 8)]
        self.assertEqual(len(ids), CAP)
        self.assertTrue({'o_0', 'o_1', 'o_2'} <= set(ids))

    def test_passages_are_passed_through_unchanged(self):
        index = Index(self.routes())
        out = decomposed(index, splitter=lambda q: ['p1'])('Q', 8)
        self.assertEqual(out[0], passage('o_0'))  # ids, provenance and text untouched

    def test_failed_or_empty_part_search_is_skipped(self):
        index = Index(self.routes(), fail={'p1'})
        ids = [p['chunk_id'] for p in decomposed(index, splitter=lambda q: ['p1', 'missing'])('Q', 8)]
        self.assertEqual(ids, [f'o_{i}' for i in range(8)])

    def test_failure_of_the_original_search_still_propagates(self):
        with self.assertRaises(RuntimeError):
            decomposed(Index({}, fail={'Q'}), splitter=lambda q: ['p1'])('Q', 8)

    def test_top_k_is_passed_to_every_search(self):
        index = Index(self.routes())
        decomposed(index, splitter=lambda q: ['p1', 'p2'])('Q', 8)
        self.assertEqual({k for _, k in index.calls}, {8})


class BaselineUnchanged(unittest.TestCase):
    def test_baseline_synthesis_receives_the_merged_packet_with_no_extra_calls(self):
        sys.path.insert(0, str(HERE.parents[1] / 'experiments/agentic'))
        import fake_provider
        from src.experimental.demo import create_research
        routes = {'Q?': [f'o_{i}' for i in range(8)], 'p1': [f'x_{i}' for i in range(8)]}
        index = decomposed(Index(routes), splitter=lambda q: ['p1'])
        identity = lambda: {'collection': 'fixture', 'count': 16, 'indexed_records_sha256': 'fixture'}
        prompts = []

        def generate(prompt, *, response_schema=None):
            prompts.append(prompt)
            return json.dumps(fake_provider.answer(prompt))
        generate.supports_response_schema = True
        research = create_research((index, identity, 'fixture', {'method': 'fixture'}), generate, {'provider': 'fake'}, 8)
        research.execute({'query': 'Q?', 'context_id': research.context_id, 'interpret_context': False})
        synthesis = [p for p in prompts if p.startswith('Synthesize an answer')]
        packet = json.loads(synthesis[0].split('Return only JSON matching the supplied schema.\n', 1)[1])['paper_passages']
        self.assertEqual(len(packet), 14)  # 8 original + 6 from the part, capped
        self.assertEqual(len(prompts), 2)  # still one synthesis + one quality review: no extra model calls


if __name__ == '__main__':
    unittest.main()
