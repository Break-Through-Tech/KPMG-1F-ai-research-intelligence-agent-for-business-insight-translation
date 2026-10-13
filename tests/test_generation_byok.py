import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from src.generation import create_generate
from src.generation_config import GenerationConfig
from src.research_pipeline import PipelineError


class BYOKTests(unittest.TestCase):
    def test_legacy_gemini_and_empty_template_override(self):
        config = GenerationConfig.from_environment({'GOOGLE_API_KEY':'test-secret',
            'RESEARCH_MODEL':'', 'RESEARCH_API_KEY_ENV':''})
        self.assertEqual(config.provider,'gemini')
        self.assertEqual(config.model,'gemini-2.5-flash')
        self.assertNotIn('test-secret',repr(config))

    def test_selected_provider_never_borrows_other_key(self):
        for provider in ['openai','openai_compatible']:
            with self.assertRaises(PipelineError):
                GenerationConfig.from_environment({'RESEARCH_PROVIDER':provider,
                    'GOOGLE_API_KEY':'other-secret','RESEARCH_MODEL':'test-model'})
        config = GenerationConfig.from_environment({'RESEARCH_PROVIDER':'openai',
            'RESEARCH_MODEL':'test-model','RESEARCH_API_KEY_ENV':'MY_TEAM_KEY','MY_TEAM_KEY':'own-secret'})
        self.assertEqual(config.api_key,'own-secret')
        with self.assertRaises(PipelineError):
            GenerationConfig.from_environment({'RESEARCH_PROVIDER':'openai','OPENAI_API_KEY':'own-secret'})

    def test_custom_endpoints_are_explicit_and_validated(self):
        for endpoint in ['http://remote.example/v1','https://key:secret@example.com/v1',
                         'https://example.com/v1?api_key=secret','https://example.com/#secret',
                         'https://example.com:broken/v1']:
            with self.subTest(endpoint=endpoint), self.assertRaises(PipelineError) as error:
                GenerationConfig('openai_compatible','test-model','test-key',endpoint)
            self.assertNotIn('secret',str(error.exception))
        for endpoint in ['https://example.com/v1','http://localhost:8080/v1','http://127.0.0.1:8080/v1']:
            GenerationConfig('openai_compatible','test-model','test-key',endpoint)
        with self.assertRaises(PipelineError):
            GenerationConfig('openai','test-model','test-key','https://example.com/v1')
        with self.assertRaises(PipelineError):
            GenerationConfig('openai_compatible','test-model','test-key')

    def test_openai_request_and_safe_provenance(self):
        client=Mock()
        client.chat.completions.create.return_value=SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"status":"ok"}'))])
        factory=Mock(return_value=client)
        with patch.dict('sys.modules',{'openai':SimpleNamespace(OpenAI=factory)}), patch.dict(
                os.environ,{'OPENAI_BASE_URL':'https://unselected.example'}):
            generate,metadata=create_generate(GenerationConfig('openai','test-model','private-key'))
            self.assertEqual(json.loads(generate('source prompt'))['status'],'ok')
        self.assertEqual(factory.call_args.kwargs['base_url'],'https://api.openai.com/v1')
        self.assertEqual(factory.call_args.kwargs['max_retries'],0)
        self.assertEqual(client.chat.completions.create.call_args.kwargs['response_format'],{'type':'json_object'})
        self.assertNotIn('private-key',json.dumps(metadata))
        self.assertNotIn('api_key',metadata)

    def test_custom_provider_uses_only_explicit_endpoint(self):
        factory=Mock(return_value=Mock())
        with patch.dict('sys.modules',{'openai':SimpleNamespace(OpenAI=factory)}):
            create_generate(GenerationConfig('openai_compatible','local-model','own-key','http://localhost:8080/v1'))
        self.assertEqual(factory.call_args.kwargs['base_url'],'http://localhost:8080/v1')
        self.assertEqual(factory.call_args.kwargs['api_key'],'own-key')

    def test_provider_errors_and_empty_output_are_safe(self):
        client=Mock(); factory=Mock(return_value=client)
        with patch.dict('sys.modules',{'openai':SimpleNamespace(OpenAI=factory)}):
            generate,_=create_generate(GenerationConfig('openai','test-model','private-key'))
        client.chat.completions.create.side_effect=RuntimeError('private-key source prompt https://private.example')
        with self.assertRaises(PipelineError) as error: generate('source prompt')
        self.assertNotIn('private-key',str(error.exception))
        self.assertNotIn('source prompt',str(error.exception))
        client.chat.completions.create.side_effect=None
        client.chat.completions.create.return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=''))])
        with self.assertRaisesRegex(PipelineError,'empty output'): generate('source prompt')
        with self.assertRaises(PipelineError): generate('')

    def test_gemini_stays_lazy_and_requests_json(self):
        from google import genai
        from google.genai import types
        # Check real SDK configuration shapes; mock the client so no call is billed.
        types.HttpOptions(timeout=60000,retry_options=types.HttpRetryOptions(attempts=1))
        client=Mock();client.models.generate_content.return_value=SimpleNamespace(text='{"status":"ok"}')
        with patch.object(genai,'Client',return_value=client):
            generate,metadata=create_generate(GenerationConfig('gemini','test-model','own-key'))
            generate('source prompt')
        self.assertEqual(metadata['provider'],'gemini')
        self.assertEqual(client.models.generate_content.call_args.kwargs['config'].response_mime_type,'application/json')


if __name__ == '__main__': unittest.main()
