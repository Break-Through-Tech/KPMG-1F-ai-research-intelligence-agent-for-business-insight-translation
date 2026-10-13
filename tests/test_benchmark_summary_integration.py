"""Exercise the CLI/capture join, not just the adapter in isolation."""
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
from unittest.mock import patch

import main
from evaluation import run_benchmarks
from src.summarization import prompt_provenance


def response(chunk_id='synthetic-html-1'):
    return json.dumps({'status': 'ok', 'claims': [
        {'text': 'Agents need task-specific evaluation.', 'chunk_ids': [chunk_id]}],
        'limitations': ['Synthetic fixture only.']})


def test_benchmark_default_bounds_context_records_prompt_and_preserves_query():
    prompts = []
    def generate(prompt):
        prompts.append(prompt)
        return response()
    with tempfile.TemporaryDirectory() as directory:
        cases = Path(directory) / 'cases.json'
        cases.write_text(json.dumps([{'query_id': 'q01', 'query': ' agents '}]))
        output = Path(directory) / 'run'
        with patch.object(main, 'persistent_retrieve', main.demo_retrieve), patch(
                'src.generation.create_generate', return_value=(generate, {'provider': 'test'})), \
                redirect_stdout(io.StringIO()):
            assert run_benchmarks.main(['--mode', 'summary', '--cases', str(cases),
                                        '--output', str(output)]) == 0
        artifact = json.loads((output / 'run.json').read_text())
        summary = artifact['cases'][0]['result']['summary']
        assert summary['query'] == ' agents '
        assert summary['included_chunks'][0]['chunk_id'] == 'synthetic-html-1'
        assert len(prompts) == 1
        assert artifact['provenance']['generation'] == {'provider': 'test', **prompt_provenance()}
        assert not artifact['cases'][0]['result']['approved']


def test_benchmark_rejected_model_citation_is_retained_and_nonzero():
    with tempfile.TemporaryDirectory() as directory:
        cases = Path(directory) / 'cases.json'
        cases.write_text(json.dumps([{'query_id': 'q01', 'query': 'agents'}]))
        output = Path(directory) / 'run'
        with patch.object(main, 'persistent_retrieve', main.demo_retrieve), patch(
                'src.generation.create_generate', return_value=(lambda p: response('invented'), {})), \
                redirect_stdout(io.StringIO()) as stdout:
            assert run_benchmarks.main(['--mode', 'summary', '--cases', str(cases),
                                        '--output', str(output)]) == 1
        artifact = json.loads((output / 'run.json').read_text())
        summary = artifact['cases'][0]['result']['summary']
        assert summary['error'] == 'invalid_citations'
        assert summary['claims'] == []
        assert json.loads(stdout.getvalue())['summary_failed'] == 1


def test_cli_default_uses_the_same_merged_adapter_and_prompt():
    with patch.object(main, 'persistent_retrieve', main.demo_retrieve), patch.object(
            main, 'create_generate', return_value=(lambda p: response(), {})), \
            redirect_stdout(io.StringIO()) as stdout:
        assert main.main(['--query', ' agents ', '--mode', 'summary']) == 0
    result = json.loads(stdout.getvalue())
    assert result['summary']['query'] == ' agents '
    assert result['summary']['included_chunks']
    assert result['provenance']['generation']['prompt_sha256'] == prompt_provenance()['prompt_sha256']


def test_explicit_external_adapter_does_not_claim_builtin_prompt():
    with tempfile.TemporaryDirectory() as directory:
        cases = Path(directory) / 'cases.json'
        cases.write_text(json.dumps([{'query_id': 'q01', 'query': 'agents'}]))
        output = Path(directory) / 'run'
        def adapter(q, p, *, generate):
            return main.demo_summary(q, p)
        with patch.object(main, 'persistent_retrieve', main.demo_retrieve), patch.object(
                main, 'load_adapter', return_value=adapter), patch(
                'src.generation.create_generate', return_value=(lambda p: '{}', {})), \
                redirect_stdout(io.StringIO()):
            assert run_benchmarks.main(['--mode', 'summary', '--summary-adapter', 'custom:summary',
                                        '--cases', str(cases), '--output', str(output)]) == 0
        generation = json.loads((output / 'run.json').read_text())['provenance']['generation']
        assert generation['summary_adapter'] == 'custom:summary'
        assert generation['prompt_version'] == 'external-adapter-unspecified'
        assert 'prompt_sha256' not in generation
