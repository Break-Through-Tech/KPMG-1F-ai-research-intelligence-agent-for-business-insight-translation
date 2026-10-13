import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from tests import research_fixtures as main
from src.research_pipeline import run_research


class GenerationTests(unittest.TestCase):
    def test_persistent_chroma_to_generated_draft(self):
        from src.generation import summarize_with_generation
        try:
            from src import retrieval
            from tests.test_retrieval import FakeModel, chunks
        except ImportError:
            self.skipTest('Persistent integration requires requirements.txt dependencies')
        import tempfile
        from pathlib import Path
        import chromadb
        with tempfile.TemporaryDirectory() as directory, patch.object(
                retrieval, 'CHROMA_DIR', Path(directory)), redirect_stdout(io.StringIO()):
            model = FakeModel()
            frame = chunks('a', 'b')
            retrieval.store_embeddings(frame, model.encode(frame['text'].tolist()))
            # Reopen the on-disk collection; use fake embeddings and generation,
            # not network/model access or the actual locked corpus.
            client = chromadb.PersistentClient(path=directory)
            result = run_research({'query': 'agent', 'top_k': 1},
                retrieve=lambda q, k: retrieval.search(q, k, client=client, model=model),
                summarize_fn=lambda q, p: summarize_with_generation(q, p,
                    generate=lambda prompt: json.dumps(main.demo_summary(q, p))))
            self.assertEqual(result['evidence'][0]['chunk_id'], 'a')
            self.assertEqual(result['summary']['claims'][0]['chunk_ids'], ['a'])
            self.assertFalse(result['approved'])

    def test_interim_generation_requires_structured_output(self):
        from src.generation import summarize_with_generation
        result = summarize_with_generation('agents', main.demo_retrieve('agents', 5),
                                           generate=lambda p: json.dumps(main.demo_summary('agents', [])))
        self.assertEqual(result['query'], 'agents')
        with self.assertRaises(json.JSONDecodeError):
            summarize_with_generation('agents', [], generate=lambda p: 'not JSON')



if __name__ == '__main__':
    unittest.main()
