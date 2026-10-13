"""Offline runner integration: use the existing Gemini configuration owner."""
import io
import json
import runpy
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from tests.research_fixtures import demo_retrieve

SCRIPT = Path(__file__).resolve().parents[1] / "try_summarize.py"


def run_helper(real=False):
    retrieval = ModuleType("src.retrieval")
    retrieval.search = Mock(return_value=demo_retrieve("agents", 5))
    args = [str(SCRIPT), "agents"] + (["--real"] if real else [])
    with patch.dict(sys.modules, {"src.retrieval": retrieval}), patch.object(
            sys, "argv", args), redirect_stdout(io.StringIO()) as output:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    return output.getvalue()


def test_real_runner_uses_google_configuration_without_llm_settings():
    response = json.dumps({"status": "ok", "claims": [{
        "text": "Synthetic agents need task-specific evaluation.",
        "chunk_ids": ["synthetic-html-1"]}], "limitations": ["Synthetic fixture only."]})
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(text=response)
    genai = ModuleType("google.genai")
    genai.Client = Mock(return_value=client)
    types = ModuleType("google.genai.types")
    types.GenerateContentConfig = Mock()
    types.HttpOptions = Mock()
    types.HttpRetryOptions = Mock()
    genai.types = types
    google = ModuleType("google")
    google.genai = genai
    dotenv = ModuleType("dotenv")
    dotenv.load_dotenv = Mock()
    with patch.dict(sys.modules, {"google": google, "google.genai": genai,
            "google.genai.types": types, "dotenv": dotenv}), patch.dict(
            "os.environ", {"GOOGLE_API_KEY": "fake-offline-key",
                           "GOOGLE_MODEL": "configured-test-model"}, clear=True):
        output = run_helper(real=True)
    genai.Client.assert_called_once_with(api_key="fake-offline-key",
                                       http_options=types.HttpOptions.return_value)
    types.HttpRetryOptions.assert_called_once_with(attempts=1)
    types.HttpOptions.assert_called_once_with(timeout=60000,
        retry_options=types.HttpRetryOptions.return_value)
    call = client.models.generate_content.call_args.kwargs
    assert call["model"] == "configured-test-model"
    assert "synthetic-html-1" in call["contents"]
    types.GenerateContentConfig.assert_called_once_with(
        response_mime_type="application/json", temperature=0)
    assert "status: ok" in output


def test_fake_runner_does_not_create_provider():
    with patch("src.generation.create_generate") as create_generate:
        output = run_helper()
    create_generate.assert_not_called()
    assert "status: ok" in output
