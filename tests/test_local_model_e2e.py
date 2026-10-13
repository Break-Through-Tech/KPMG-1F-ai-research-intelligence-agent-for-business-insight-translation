"""Opt-in real local provider + persistent retrieval + frozen export smoke.

KPMG_LOCAL_E2E=1 enables this test. It requires a built local index, cached
MiniLM weights, and explicit loopback openai_compatible BYOK configuration.
There are no fixtures, fake embeddings, paid providers or automatic approval.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

import pytest


@pytest.mark.skipif(os.getenv('KPMG_LOCAL_E2E') != '1', reason='Opt-in local-model/index integration')
def test_real_local_summary_cli_and_benchmark():
    from src.generation_config import GenerationConfig
    from evaluation.run_benchmarks import artifact_id
    config = GenerationConfig.from_environment()
    assert config.provider == 'openai_compatible'
    assert urlsplit(config.base_url).hostname in {'localhost', '127.0.0.1', '::1'}
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / 'evaluation/benchmark_cases.json').read_text())[:1]
    with tempfile.TemporaryDirectory() as directory:
        cases_path = Path(directory) / 'cases.json'
        cases_path.write_text(json.dumps(cases))
        output = Path(directory) / 'run'
        completed = subprocess.run([sys.executable, '-m', 'evaluation.run_benchmarks',
            '--mode', 'summary', '--cases', str(cases_path), '--output', str(output)],
            cwd=root, capture_output=True, text=True, timeout=180)
        assert output.is_dir(), completed.stderr
        artifact = json.loads((output / 'run.json').read_text())
        assert artifact['run_id'] == artifact_id(artifact)
        assert artifact['provenance']['execution'] == 'persistent_corpus'
        assert artifact['provenance']['generation']['model'] == config.model
        assert artifact['provenance']['generation']['summary_adapter'] == 'src.summarization:summarize'
        assert completed.returncode == 0, completed.stdout + completed.stderr
        result = artifact['cases'][0]['result']
        assert result['evidence']
        assert result['summary']['error'] is None
        assert not result['approved']
        ids = {p['chunk_id'] for p in result['evidence']}
        assert all(set(c['chunk_ids']) <= ids for c in result['summary']['claims'])
        assert (output / 'review.csv').is_file()
        completed = subprocess.run([sys.executable, 'main.py', '--query', cases[0]['query'],
            '--mode', 'summary'], cwd=root, capture_output=True, text=True, timeout=180)
        assert completed.returncode == 0, completed.stderr
        cli = json.loads(completed.stdout)
        assert cli['summary']['error'] is None
        assert cli['provenance']['generation']['prompt_sha256'] == artifact['provenance']['generation']['prompt_sha256']
        assert not cli['approved']
