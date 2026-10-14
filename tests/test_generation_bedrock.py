"""Offline Bedrock contract/signing tests: no AWS requests or billable inference."""
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from src.generation import create_generate
from src.generation_config import GenerationConfig
from src.research_pipeline import PipelineError


def response(text='{"status":"ok"}', *, stop='end_turn'):
    return {'output': {'message': {'role': 'assistant', 'content': [{'text': text}]}},
            'stopReason': stop, 'usage': {'inputTokens': 4, 'outputTokens': 4, 'totalTokens': 8},
            'metrics': {'latencyMs': 1}}


class BedrockTests(unittest.TestCase):
    def config(self):
        return GenerationConfig('bedrock', 'test-model', region='us-east-1')

    def test_environment_uses_aws_chain_without_reading_foreign_keys(self):
        env = {'RESEARCH_PROVIDER': 'bedrock', 'RESEARCH_MODEL': 'test-model',
               'AWS_REGION': 'us-east-1', 'AWS_DEFAULT_REGION': 'us-west-2',
               'GOOGLE_API_KEY': 'foreign-secret', 'OPENAI_API_KEY': 'foreign-secret',
               'RESEARCH_API_KEY': 'foreign-secret',
               'AWS_BEARER_TOKEN_BEDROCK': 'private-token', 'AWS_PROFILE': 'private-profile'}
        config = GenerationConfig.from_environment(env)
        self.assertEqual(config.region, 'us-east-1')
        self.assertEqual(config.api_key, '')
        self.assertNotIn('secret', repr(config))
        self.assertNotIn('private', repr(config))
        env['AWS_REGION'] = ''
        self.assertEqual(GenerationConfig.from_environment(env).region, 'us-west-2')

    def test_bedrock_requires_explicit_model_region_and_native_auth(self):
        for kwargs in ({'model': ''}, {'region': None}, {'region': ''},
                       {'region': 'https://private.example'}, {'api_key': 'foreign-secret'},
                       {'base_url': 'https://private.example'}):
            values = {'provider': 'bedrock', 'model': 'test-model', 'region': 'us-east-1'}
            values.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(PipelineError) as caught:
                GenerationConfig(**values)
            self.assertNotIn('private.example', str(caught.exception))
            self.assertNotIn('foreign-secret', str(caught.exception))
        with self.assertRaises(PipelineError):
            GenerationConfig.from_environment({'RESEARCH_PROVIDER': 'bedrock',
                'RESEARCH_MODEL': 'test-model', 'AWS_REGION': 'us-east-1',
                'RESEARCH_API_KEY_ENV': 'TEAM_KEY'})
        with self.assertRaises(PipelineError):
            GenerationConfig('openai', 'test-model', 'key', region='us-east-1')

    def test_request_timeouts_retry_endpoint_isolation_and_provenance(self):
        client = Mock()
        client.converse.return_value = response()
        with patch('boto3.client', return_value=client) as factory:
            generate, metadata = create_generate(self.config())
            self.assertEqual(json.loads(generate('source prompt')), {'status': 'ok'})
        self.assertEqual(factory.call_args.args, ('bedrock-runtime',))
        self.assertEqual(factory.call_args.kwargs['region_name'], 'us-east-1')
        options = factory.call_args.kwargs['config']
        self.assertEqual(options.connect_timeout, 10)
        self.assertEqual(options.read_timeout, 60)
        self.assertEqual(options.retries['total_max_attempts'], 1)
        self.assertTrue(options.ignore_configured_endpoint_urls)
        self.assertNotIn('endpoint_url', factory.call_args.kwargs)
        self.assertNotIn('aws_access_key_id', factory.call_args.kwargs)
        request = client.converse.call_args.kwargs
        self.assertEqual(request['modelId'], 'test-model')
        self.assertEqual(request['inferenceConfig'], {'temperature': 0})
        self.assertIn('source prompt', request['messages'][0]['content'][0]['text'])
        self.assertEqual(metadata['provider'], 'bedrock')
        self.assertEqual(metadata['region'], 'us-east-1')
        self.assertEqual(metadata['json_mode'], 'prompt_requested_and_validated')
        self.assertNotIn('api_key', metadata)

    def test_real_sdk_stubber_validates_converse_request_and_response(self):
        import boto3
        from botocore.stub import Stubber
        client = boto3.session.Session().client('bedrock-runtime', region_name='us-east-1',
            aws_access_key_id='test-only-id', aws_secret_access_key='test-only-secret')
        expected = {'modelId': 'test-model',
            'messages': [{'role': 'user', 'content': [{'text':
                'Return only one valid JSON object matching the requested format. '
                'No Markdown or surrounding commentary.\n\nsource prompt'}]}],
            'inferenceConfig': {'temperature': 0}}
        with Stubber(client) as stub:
            stub.add_response('converse', response(), expected)
            with patch('boto3.client', return_value=client):
                generate, _ = create_generate(self.config())
                self.assertEqual(generate('source prompt'), '{"status":"ok"}')
            stub.assert_no_pending_responses()

    def test_real_sdk_signing_uses_bearer_or_iam_without_network(self):
        import boto3
        from botocore.awsrequest import AWSResponse

        class Body:
            def stream(self, amt=None, decode_content=False):
                yield json.dumps(response()).encode()

        cases = [({'AWS_BEARER_TOKEN_BEDROCK': 'test-only-bearer'}, b'Bearer test-only-bearer'),
                 ({'AWS_ACCESS_KEY_ID': 'test-only-id', 'AWS_SECRET_ACCESS_KEY': 'test-only-secret',
                   'AWS_SESSION_TOKEN': 'test-only-session'}, b'AWS4-HMAC-SHA256 Credential=test-only-id/')]
        for credentials, prefix in cases:
            env = {**credentials, 'AWS_EC2_METADATA_DISABLED': 'true'}
            with self.subTest(auth=prefix), patch.dict(os.environ, env, clear=True), \
                    patch('boto3.DEFAULT_SESSION', None):
                generate, _ = create_generate(self.config())
                # Intercept all HTTP transport; request signing remains real.
                with patch('botocore.httpsession.URLLib3Session.send', return_value=AWSResponse(
                        'https://bedrock-runtime.us-east-1.amazonaws.com', 200,
                        {'content-type': 'application/json'}, Body())) as send:
                    self.assertEqual(generate('source prompt'), '{"status":"ok"}')
                self.assertEqual(send.call_count, 1)
                request = send.call_args.args[0]
                self.assertTrue(request.headers['Authorization'].startswith(prefix))
                if 'AWS_SESSION_TOKEN' in credentials:
                    self.assertEqual(request.headers['X-Amz-Security-Token'], b'test-only-session')
                self.assertTrue(request.url.startswith(
                    'https://bedrock-runtime.us-east-1.amazonaws.com/'))

    def test_malformed_nonjson_and_nonobject_output_fails_safely(self):
        client = Mock()
        with patch('boto3.client', return_value=client):
            generate, _ = create_generate(self.config())
        for raw in ('private raw text', '```json\n{}\n```', '[]', 'null',
                    '{"score":NaN}', '{"score":1e999}', ''):
            client.converse.return_value = response(raw)
            with self.subTest(raw=raw), self.assertRaises(PipelineError) as caught:
                generate('private prompt')
            self.assertNotIn('private', str(caught.exception))

    def test_truncation_guardrail_and_nontext_blocks_do_not_pass(self):
        client = Mock()
        with patch('boto3.client', return_value=client):
            generate, _ = create_generate(self.config())
        for stop in ('max_tokens', 'guardrail_intervened', 'content_filtered', 'tool_use', None):
            client.converse.return_value = response(stop=stop)
            with self.subTest(stop=stop), self.assertRaises(PipelineError):
                generate('prompt')
        for blocks in ([], [{'toolUse': {'toolUseId': 'private'}}], [{'text': 42}],
                       [{'text': '{}', 'toolUse': {}}]):
            value = response()
            value['output']['message']['content'] = blocks
            client.converse.return_value = value
            with self.subTest(blocks=blocks), self.assertRaises(PipelineError):
                generate('prompt')
        value = response()
        value['output']['message']['content'] = [{'text': '{"status":'}, {'text': '"ok"}'}]
        client.converse.return_value = value
        self.assertEqual(json.loads(generate('prompt')), {'status': 'ok'})

    def test_aws_failure_is_sanitized_without_fallback(self):
        client = Mock()
        client.converse.side_effect = RuntimeError('private credential and request payload')
        with patch('boto3.client', return_value=client), patch('openai.OpenAI') as other:
            generate, _ = create_generate(self.config())
            with self.assertRaises(PipelineError) as caught:
                generate('private prompt')
            self.assertNotIn('private', str(caught.exception))
            self.assertTrue(caught.exception.__suppress_context__)
            other.assert_not_called()
            self.assertEqual(client.converse.call_count, 1)
        with patch('boto3.client', side_effect=RuntimeError('private credentials')):
            with self.assertRaises(PipelineError) as caught:
                create_generate(self.config())
            self.assertNotIn('private', str(caught.exception))

    def test_ambient_endpoint_override_is_ignored_by_real_sdk(self):
        import boto3
        env = {'AWS_ACCESS_KEY_ID': 'test-only-id', 'AWS_SECRET_ACCESS_KEY': 'test-only-secret',
               'AWS_ENDPOINT_URL': 'https://unselected.example',
               'AWS_ENDPOINT_URL_BEDROCK_RUNTIME': 'https://unselected.example',
               'AWS_EC2_METADATA_DISABLED': 'true'}
        with patch.dict(os.environ, env, clear=True), patch('boto3.DEFAULT_SESSION', None), \
                patch('boto3.client', wraps=boto3.client) as factory:
            create_generate(self.config())
            options = factory.call_args.kwargs
            client = boto3.DEFAULT_SESSION.client('bedrock-runtime', **options)
            self.assertEqual(client.meta.endpoint_url, 'https://bedrock-runtime.us-east-1.amazonaws.com')

    def test_import_remains_lazy_without_aws_modules(self):
        result = subprocess.run([sys.executable, '-c',
            'import src.generation, src.generation_config, sys; '
            'assert "boto3" not in sys.modules; assert "botocore" not in sys.modules'],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
