import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.codex_generation import create_codex_generate
from src.research_pipeline import PipelineError


class CodexSubscriptionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.binary=Path(self.temp.name)/'codex';self.binary.write_text('fixture binary')

    def test_chatgpt_login_only_and_api_auth_environment_is_removed(self):
        with patch('src.codex_generation.subprocess.run',return_value=SimpleNamespace(
                returncode=0,stdout='',stderr='Logged in using an API key')):
            with self.assertRaisesRegex(PipelineError,'ChatGPT'):create_codex_generate(model='gpt-test',binary=self.binary)

    def test_schema_output_uses_isolated_read_only_ephemeral_no_config_route(self):
        seen=[]
        def run(command,**kwargs):
            seen.append((command,kwargs))
            if command[-2:]==['login','status']:
                return SimpleNamespace(returncode=0,stdout='',stderr='Logged in using ChatGPT')
            output=Path(command[command.index('-o')+1]);output.write_text('{"answer":"ok"}')
            return SimpleNamespace(returncode=0,stdout=json.dumps({'type':'turn.completed','usage':{'output_tokens':3}}),stderr='')
        with patch.dict('os.environ',{'CODEX_API_KEY':'secret','OPENAI_API_KEY':'secret','OPENAI_BASE_URL':'private'}),patch('src.codex_generation.subprocess.run',side_effect=run):
            receipts=[];fn,meta=create_codex_generate(model='gpt-test',binary=self.binary,receipts=receipts)
            text=fn('Return JSON.',response_schema={'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False})
        self.assertEqual(json.loads(text),{'answer':'ok'});self.assertEqual(receipts[0]['status'],'ok')
        command,kw=seen[-1]
        for flag in ['--ignore-user-config','--ephemeral','--skip-git-repo-check','--output-schema']:self.assertIn(flag,command)
        self.assertEqual(command[command.index('--sandbox')+1],'read-only')
        for _,kw in seen:
            self.assertNotIn('CODEX_API_KEY',kw['env']);self.assertNotIn('OPENAI_API_KEY',kw['env'])
        self.assertEqual(meta['auth'],'existing_chatgpt_login')

    def test_tool_using_response_is_rejected_without_provider_fallback(self):
        def run(command,**kwargs):
            if command[-2:]==['login','status']:return SimpleNamespace(returncode=0,stdout='Logged in using ChatGPT',stderr='')
            Path(command[command.index('-o')+1]).write_text('{}')
            return SimpleNamespace(returncode=0,stdout=json.dumps({'type':'item.completed','item':{'type':'command_execution'}}),stderr='')
        with patch('src.codex_generation.subprocess.run',side_effect=run):
            fn,_=create_codex_generate(model='gpt-test',binary=self.binary)
            with self.assertRaises(PipelineError):fn('Return JSON')

    def test_provider_timeout_error_does_not_expose_payload(self):
        import subprocess
        with patch('src.codex_generation.subprocess.run',side_effect=[
            SimpleNamespace(returncode=0,stdout='Logged in using ChatGPT',stderr=''),
            subprocess.TimeoutExpired('SECRET',300)]):
            fn,_=create_codex_generate(model='gpt-test',binary=self.binary)
            with self.assertRaises(PipelineError) as caught:fn('Return JSON')
            self.assertNotIn('SECRET',str(caught.exception))


if __name__=='__main__':unittest.main()
