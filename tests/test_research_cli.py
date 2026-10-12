import io
import json
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import Mock, patch
import main
from src.research_pipeline import PipelineError


class CLITests(unittest.TestCase):
    def test_cli_offline_business_is_json_without_network_imports(self):
        completed = subprocess.run([sys.executable, 'main.py', '--demo', '--query', 'agents',
                                    '--mode', 'business', '--industry', 'banking', '--jurisdiction', 'US'],
                                   capture_output=True, text=True, check=True)
        result = json.loads(completed.stdout)
        self.assertFalse(result['approved'])
        self.assertEqual(result['provenance']['execution'], 'synthetic_fixture')
        check = subprocess.run([sys.executable, '-c',
                                'import main,sys; assert "google.genai" not in sys.modules; '
                                'assert "sentence_transformers" not in sys.modules; '
                                'assert "chromadb" not in sys.modules'], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_current_input_hash_is_not_claimed_as_indexed_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / 'data/processed/chunks.parquet'
            corpus.parent.mkdir(parents=True)
            corpus.write_bytes(b'current-input-not-verified-against-index')
            with patch.object(main, '__file__', str(root / 'main.py')), patch.object(
                    main, 'persistent_retrieve', return_value=main.demo_retrieve('agents', 5)), \
                    redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main.main(['--query', 'agents', '--mode', 'retrieval']), 0)
            provenance = json.loads(out.getvalue())['provenance']
            self.assertIsNone(provenance['corpus_sha256'])
            self.assertEqual(provenance['input_file_sha256'], sha256(corpus.read_bytes()).hexdigest())

    def test_cli_missing_index_key_or_adapter_is_actionable(self):
        for argv, expected in [(['--query', 'agents', '--mode', 'retrieval'], 'index missing'),
                               (['--query', 'agents', '--mode', 'business', '--industry', 'banking'], 'adapter unavailable'),
                               (['--query', 'agents', '--demo', '--mode', 'business'], '--industry')]:
            with patch('main.Path.is_file', return_value=False), redirect_stdout(
                    io.StringIO()), redirect_stderr(io.StringIO()) as err:
                self.assertEqual(main.main(argv), 1)
            self.assertIn(expected, json.loads(err.getvalue())['error'])
        with patch.dict('os.environ', {'GOOGLE_API_KEY': ''}), patch.dict(
                sys.modules, {'dotenv': Mock(load_dotenv=Mock())}):
            with self.assertRaisesRegex(PipelineError, 'GOOGLE_API_KEY'):
                main.create_generate()
        with self.assertRaisesRegex(PipelineError, 'unavailable'):
            main.load_adapter('src.not_here:translate')


if __name__ == '__main__':
    unittest.main()
