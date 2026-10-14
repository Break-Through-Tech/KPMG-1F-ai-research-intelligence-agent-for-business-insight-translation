"""Native schema requests and fail-closed validation, without paid inference."""
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from src.generation import create_generate, SchemaResponseError
from src.generation_config import GenerationConfig
from src.research_pipeline import PipelineError
from src.summarization import response_schema, summarize


SCHEMA = response_schema(['a'])
VALID = {'status':'ok','claims':[{'text':'Supported text.','chunk_ids':['a']}],
         'limitations':[]}


def openai_generator(reply=VALID, finish='stop', refusal=None):
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(choices=[
        SimpleNamespace(finish_reason=finish, message=SimpleNamespace(
            content=json.dumps(reply), refusal=refusal))])
    with patch.dict('sys.modules', {'openai':SimpleNamespace(OpenAI=Mock(return_value=client))}):
        generate, metadata = create_generate(GenerationConfig('openai_compatible','local-model',
            'dummy-local-key','http://127.0.0.1:11434/v1'))
    return generate, metadata, client


def test_compatible_provider_requests_strict_schema_and_snapshots_input():
    generate, metadata, client = openai_generator()
    assert json.loads(generate('source prompt', response_schema=SCHEMA)) == VALID
    sent = client.chat.completions.create.call_args.kwargs['response_format']
    assert sent == {'type':'json_schema','json_schema':{
        'name':'research_output','strict':True,'schema':SCHEMA}}
    assert sent['json_schema']['schema'] is not SCHEMA
    assert generate.supports_response_schema is True
    assert metadata['schema_capability'] == 'native_request_and_local_validation_when_bound'
    assert 'dummy-local-key' not in json.dumps(metadata)


@pytest.mark.parametrize('reply', [
    {**VALID,'claims':['not an object']},
    {**VALID,'claims':[{'text':'claim','chunk_ids':'a'}]},
    {**VALID,'claims':[{'text':'claim','chunk_ids':['invented']}]},
    {**VALID,'claims':[{'text':'claim','chunk_ids':[]}]},
    {**VALID,'approved':True},
    {k:v for k,v in VALID.items() if k != 'limitations'},
    {**VALID,'status':'approved'},
    {**VALID,'claims':VALID['claims']*9},
    {**VALID,'claims':[{'text':'x'*601,'chunk_ids':['a']}]},
    {**VALID,'limitations':['limit']*9},
])
def test_server_ignoring_schema_is_rejected_locally_without_leaking_output(reply):
    generate, _, client = openai_generator(reply)
    with pytest.raises(SchemaResponseError) as exc:
        generate('private source prompt', response_schema=SCHEMA)
    assert 'private source prompt' not in str(exc.value)
    assert client.chat.completions.create.call_count == 1


@pytest.mark.parametrize('raw', ['{"status":"ok","status":"insufficient_evidence","claims":[],"limitations":[]}',
    '{"status":"ok","claims":[],"limitations":[NaN]}',
    '{"status":"ok","claims":[],"limitations":[1e999]}'])
def test_duplicate_and_nonfinite_json_rejected(raw):
    generate, _, client = openai_generator()
    client.chat.completions.create.return_value.choices[0].message.content = raw
    with pytest.raises(SchemaResponseError):
        generate('prompt', response_schema=SCHEMA)


@pytest.mark.parametrize('finish,refusal',[('length',None),('content_filter',None),('stop','refused')])
def test_partial_or_refused_completion_cannot_be_accepted(finish, refusal):
    generate, _, client = openai_generator(finish=finish, refusal=refusal)
    with pytest.raises(PipelineError):
        generate('prompt', response_schema=SCHEMA)
    assert client.chat.completions.create.call_count == 1


def test_unsupported_model_never_retries_or_downgrades_to_json_object():
    generate, _, client = openai_generator()
    client.chat.completions.create.side_effect = RuntimeError('private key and unsupported schema')
    with pytest.raises(PipelineError) as exc:
        generate('prompt', response_schema=SCHEMA)
    assert 'private key' not in str(exc.value)
    assert client.chat.completions.create.call_count == 1
    assert client.chat.completions.create.call_args.kwargs['response_format']['type'] == 'json_schema'


def test_invalid_schema_does_not_contact_provider():
    generate, _, client = openai_generator()
    with pytest.raises(PipelineError):
        generate('prompt', response_schema={'type':'made_up_type'})
    client.chat.completions.create.assert_not_called()


def test_schema_uses_only_context_included_ids_and_keeps_status_semantics():
    generate, _, client = openai_generator()
    result = summarize(' q ', [{'chunk_id':'a','text':'x'*180},
        {'chunk_id':'omitted','text':'y'*180}], generate=generate,max_context_chars=300)
    schema = client.chat.completions.create.call_args.kwargs['response_format']['json_schema']['schema']
    assert schema['properties']['claims']['items']['properties']['chunk_ids']['items']['enum'] == ['a']
    assert result['query'] == ' q '
    assert result['structured_output']['mode'] == 'native_schema_and_local_validation'
    assert result['structured_output']['schema_sha256']
    # Shape alone is not enough: an abstention with claims remains invalid.
    client.chat.completions.create.return_value.choices[0].message.content = json.dumps(
        {**VALID,'status':'insufficient_evidence'})
    assert summarize('q',[{'chunk_id':'a','text':'text'}],generate=generate)['error'] == 'malformed_response'


def test_schema_failure_retains_no_claims_and_distinct_error():
    generate, _, _ = openai_generator({**VALID,'claims':['bad']})
    result = summarize('q',[{'chunk_id':'a','text':'text'}],generate=generate)
    assert result['error'] == 'malformed_response'
    assert result['claims'] == []


def test_zero_context_skips_generation_instead_of_requesting_empty_enum():
    generate, _, client = openai_generator()
    result = summarize('q',[{'chunk_id':'a','text':'text','title':'x'*500}],
                       generate=generate,max_context_chars=200)
    assert result['status'] == 'insufficient_evidence'
    assert result['error'] is None
    client.chat.completions.create.assert_not_called()


def test_gemini_schema_request_uses_real_sdk_config():
    from google.genai import types
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(text=json.dumps(VALID),
        candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)])
    with patch('google.genai.Client',return_value=client):
        generate, _ = create_generate(GenerationConfig('gemini','test-model','test-key'))
    assert json.loads(generate('prompt',response_schema=SCHEMA)) == VALID
    options = client.models.generate_content.call_args.kwargs['config']
    assert options.response_json_schema == SCHEMA
    client.models.generate_content.return_value.candidates[0].finish_reason = types.FinishReason.MAX_TOKENS
    with pytest.raises(PipelineError):
        generate('prompt',response_schema=SCHEMA)


def test_bedrock_native_schema_matches_real_converse_sdk_shape():
    import boto3
    from botocore.stub import Stubber
    from tests.test_generation_bedrock import response
    client = boto3.session.Session().client('bedrock-runtime',region_name='us-east-1',
        aws_access_key_id='offline-id',aws_secret_access_key='offline-secret')
    expected = {'modelId':'test-model','messages':[{'role':'user','content':[{'text':
        'Return only one valid JSON object matching the requested format. '
        'No Markdown or surrounding commentary.\n\nprompt'}]}],
        'inferenceConfig':{'temperature':0},'outputConfig':{'textFormat':{'type':'json_schema',
            'structure':{'jsonSchema':{'name':'research_output','schema':json.dumps(SCHEMA)}}}}}
    with Stubber(client) as stub:
        stub.add_response('converse',response(json.dumps(VALID)),expected)
        with patch('boto3.client',return_value=client):
            generate, _ = create_generate(GenerationConfig('bedrock','test-model',region='us-east-1'))
        assert json.loads(generate('prompt',response_schema=SCHEMA)) == VALID
        stub.assert_no_pending_responses()
