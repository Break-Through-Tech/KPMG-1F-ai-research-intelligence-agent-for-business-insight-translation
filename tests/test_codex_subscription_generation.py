import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.codex_generation import create_codex_generate, DISABLED_FEATURES, REQUIRED_EXEC_FLAGS
from src.research_pipeline import PipelineError


class CodexSubscriptionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.binary=Path(self.temp.name)/'codex';self.binary.write_text('fixture binary')
        self.help = SimpleNamespace(returncode=0, stdout=' '.join(REQUIRED_EXEC_FLAGS), stderr='')

    def test_old_cli_is_rejected_before_login_or_generation(self):
        with patch('src.codex_generation.subprocess.run', return_value=SimpleNamespace(
                returncode=0, stdout='--sandbox --json', stderr='')) as run:
            with self.assertRaisesRegex(PipelineError, 'required text-only isolation'):
                create_codex_generate(model='gpt-test', binary=self.binary)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][-2:], ['exec', '--help'])

    def test_explicit_environment_binary_is_used_without_path_fallback(self):
        with patch.dict('os.environ', {'RESEARCH_CODEX_BIN': str(self.binary)}), patch(
                'src.codex_generation.shutil.which') as which, patch(
                'src.codex_generation.subprocess.run', side_effect=[self.help,
                    SimpleNamespace(returncode=0, stdout='Logged in using ChatGPT', stderr='')]) as run:
            create_codex_generate(model='gpt-test')
        which.assert_not_called()
        self.assertEqual(run.call_args.args[0][0], str(self.binary))

    def test_chatgpt_login_only_and_api_auth_environment_is_removed(self):
        with patch('src.codex_generation.subprocess.run',side_effect=[self.help, SimpleNamespace(
                returncode=0,stdout='',stderr='Logged in using an API key')]):
            with self.assertRaisesRegex(PipelineError,'ChatGPT'):create_codex_generate(model='gpt-test',binary=self.binary)

    def test_schema_output_uses_isolated_read_only_ephemeral_no_config_route(self):
        seen=[]
        def run(command,**kwargs):
            seen.append((command,kwargs))
            if command[-2:]==['exec','--help']: return self.help
            if command[-2:]==['login','status']:
                return SimpleNamespace(returncode=0,stdout='',stderr='Logged in using ChatGPT')
            output=Path(command[command.index('-o')+1]);output.write_text('{"answer":"café α"}', encoding='utf-8')
            return SimpleNamespace(returncode=0,stdout=json.dumps({'type':'turn.completed','usage':{'output_tokens':3}}),stderr='')
        with patch.dict('os.environ',{'CODEX_API_KEY':'secret','OPENAI_API_KEY':'secret','OPENAI_BASE_URL':'private','UNRELATED_SECRET':'private'}),patch('src.codex_generation.subprocess.run',side_effect=run):
            receipts=[];fn,meta=create_codex_generate(model='gpt-test',binary=self.binary,receipts=receipts)
            text=fn('Return JSON for café α.',response_schema={'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False})
        self.assertEqual(json.loads(text),{'answer':'café α'});self.assertEqual(receipts[0]['status'],'ok')
        command,kw=seen[-1]
        self.assertEqual(kw['encoding'], 'utf-8')
        self.assertIn('café α', kw['input'])
        for flag in ['--ignore-user-config','--ephemeral','--skip-git-repo-check','--strict-config','--output-schema']:self.assertIn(flag,command)
        self.assertEqual(command[command.index('--sandbox')+1],'read-only')
        for _,kw in seen:
            self.assertNotIn('CODEX_API_KEY',kw['env']);self.assertNotIn('OPENAI_API_KEY',kw['env'])
        self.assertNotIn('UNRELATED_SECRET',seen[-1][1]['env'])
        for feature in DISABLED_FEATURES:
            self.assertIn(feature,command)
            self.assertEqual(command[command.index(feature)-1],'--disable')
        self.assertIn('approval_policy="never"',command)
        self.assertEqual(meta['auth'],'existing_chatgpt_login')

    def test_tool_using_response_is_rejected_without_provider_fallback(self):
        def run(command,**kwargs):
            if command[-2:]==['exec','--help']: return self.help
            if command[-2:]==['login','status']:return SimpleNamespace(returncode=0,stdout='Logged in using ChatGPT',stderr='')
            Path(command[command.index('-o')+1]).write_text('{}')
            return SimpleNamespace(returncode=0,stdout=json.dumps({'type':'item.completed','item':{'type':'command_execution'}}),stderr='')
        with patch('src.codex_generation.subprocess.run',side_effect=run):
            fn,_=create_codex_generate(model='gpt-test',binary=self.binary)
            with self.assertRaises(PipelineError):fn('Return JSON')

    def test_ignored_configuration_fails_closed_even_with_valid_answer(self):
        def run(command,**kwargs):
            if command[-2:]==['exec','--help']: return self.help
            if command[-2:]==['login','status']:
                return SimpleNamespace(returncode=0,stdout='Logged in using ChatGPT',stderr='')
            Path(command[command.index('-o')+1]).write_text('{}')
            event={'type':'item.completed','item':{'type':'error',
                   'message':'Codex is ignoring an unrecognized configuration setting'}}
            return SimpleNamespace(returncode=0,stdout=json.dumps(event),stderr='')
        with patch('src.codex_generation.subprocess.run',side_effect=run):
            fn,_=create_codex_generate(model='gpt-test',binary=self.binary)
            with self.assertRaises(PipelineError):fn('Return JSON')

    def test_provider_timeout_error_does_not_expose_payload(self):
        import subprocess
        with patch('src.codex_generation.subprocess.run',side_effect=[
            self.help, SimpleNamespace(returncode=0,stdout='Logged in using ChatGPT',stderr=''),
            subprocess.TimeoutExpired('SECRET',300)]):
            fn,_=create_codex_generate(model='gpt-test',binary=self.binary)
            with self.assertRaises(PipelineError) as caught:fn('Return JSON')
            self.assertNotIn('SECRET',str(caught.exception))


if __name__=='__main__':unittest.main()
