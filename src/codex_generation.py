"""Explicit subscription-backed, text-only Codex CLI generation for experiments.

No API keys, auth copying, model fallback, or repository access. Saved ChatGPT
login is checked before use. Each invocation has an empty temporary working
directory, disables execution/integration features before generation, and
refuses unexpected tool-using responses; this is not a production API service.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

from src.generation import SchemaResponseError
from src.research_pipeline import PipelineError


DISABLED_FEATURES = ('shell_tool', 'unified_exec', 'code_mode', 'code_mode_host',
                     'apps', 'plugins', 'hooks', 'multi_agent', 'multi_agent_v2',
                     'browser_use', 'computer_use', 'view_image', 'memories',
                     'shell_snapshot', 'workspace_dependencies', 'skill_search')
REQUIRED_EXEC_FLAGS = ('--ignore-user-config', '--strict-config', '--ephemeral',
                       '--skip-git-repo-check', '--sandbox', '--json', '--output-schema')


def _exit_diagnostic(response):
    # Keep only allowlisted metadata. CLI error strings can include the prompt,
    # source passages, endpoint details or credentials.
    messages = [response.stderr or '']
    for line in response.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and (event.get('type') in {'error', 'turn.failed'}
                or (isinstance(event.get('item'), dict) and event['item'].get('type') == 'error')):
            messages.append(json.dumps(event))
    text = '\n'.join(messages).lower()
    status = re.search(r'\b(?:http(?: status)?|status(?:_code| code)?)\b["\s:=]+([45]\d\d)\b', text)
    result = {'category': 'cli_exit', 'exit_code': response.returncode}
    if status:
        result['http_status'] = int(status[1])
    for code in ('invalid_json_schema', 'rate_limit_exceeded', 'insufficient_quota', 'model_not_found'):
        if re.search(rf'\b{code}\b', text):
            result['provider_code'] = code
            break
    if result.get('provider_code') == 'invalid_json_schema' or 'invalid schema' in text:
        result['category'] = 'invalid_json_schema'
        if re.search(r'\buniqueitems\b', text):
            result['schema_keyword'] = 'uniqueItems'
    elif result.get('http_status') == 429 or result.get('provider_code') == 'rate_limit_exceeded':
        result['category'] = 'rate_limited'
    elif result.get('http_status') in {401, 403}:
        result['category'] = 'authentication'
    elif result.get('http_status', 0) >= 500:
        result['category'] = 'upstream_unavailable'
    return result


def _failure(record, diagnostic, *, invalid=False):
    record['status'] = 'invalid_response' if invalid else 'failed'
    record['diagnostic'] = diagnostic
    error = (SchemaResponseError('Codex returned invalid JSON or schema output; no result was approved.')
             if invalid else PipelineError('Codex generation failed; check login, model access or subscription limits.'))
    error.codex_diagnostic = diagnostic.copy()
    return error


def create_codex_generate(*, model, binary=None, effort='medium', timeout=300,
                          receipts=None):
    binary = binary or os.environ.get('RESEARCH_CODEX_BIN') or shutil.which('codex')
    if not binary or not Path(binary).is_file():
        raise PipelineError('Codex CLI unavailable; specify its installed binary.')
    if not isinstance(model, str) or not model.strip():
        raise ValueError('Specify the Codex model explicitly')
    if effort not in {'low', 'medium', 'high', 'xhigh'}:
        raise ValueError('Unsupported experiment reasoning effort')
    # Retain only runtime/auth location variables, not operator secrets or
    # integration configuration. Existing ChatGPT credentials stay in place.
    env = {k: v for k, v in os.environ.items() if k in {
        'HOME', 'PATH', 'USER', 'LOGNAME', 'TMPDIR', 'CODEX_HOME',
        'SYSTEMROOT', 'APPDATA', 'LOCALAPPDATA'}}
    # Probe the explicitly selected executable without reading user config or
    # sending evidence to a model. Never silently drop an isolation flag or try
    # another binary/provider when an old CLI is selected.
    try:
        help_result = subprocess.run([str(binary), 'exec', '--help'], env=env,
                                     capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        raise PipelineError('Codex CLI compatibility check failed; select a compatible --codex-bin.') from None
    if help_result.returncode or any(flag not in help_result.stdout for flag in REQUIRED_EXEC_FLAGS):
        raise PipelineError('Codex CLI lacks required text-only isolation options. Select a compatible --codex-bin or RESEARCH_CODEX_BIN; no fallback occurred.')
    try:
        login = subprocess.run([str(binary), 'login', 'status'], env=env,
                               capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        raise PipelineError('Codex login status check failed') from None
    if login.returncode or 'Logged in using ChatGPT' not in login.stdout + login.stderr:
        raise PipelineError('This adapter requires an existing ChatGPT Codex login, not API-key auth.')
    receipts = receipts if receipts is not None else []

    def generate(prompt, *, response_schema=None):
        from jsonschema import Draft202012Validator, ValidationError
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError('Generation requires a nonempty prompt')
        record = {'provider': 'codex_subscription', 'model': model, 'reasoning_effort': effort,
                  'prompt_sha256': sha256(prompt.encode()).hexdigest(), 'status': 'started'}
        receipts.append(record)
        start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='research-codex-') as scratch:
            folder = Path(scratch)
            output = folder / 'answer.json'
            command = [str(binary), 'exec', '--ignore-user-config', '--strict-config', '--ephemeral',
                       '--skip-git-repo-check', '--sandbox', 'read-only', '--json',
                       '--color', 'never', '-C', scratch, '-m', model,
                       '-c', 'model_provider="openai"', '-c', 'web_search="disabled"',
                       '-c', f'model_reasoning_effort="{effort}"',
                       '-c', 'approval_policy="never"',
                       '-o', str(output)]
            # Prompt instructions and post-hoc rejection are not isolation.
            # Remove shell/exec and integration routes before sending evidence.
            for feature in DISABLED_FEATURES:
                command += ['--disable', feature]
            if response_schema is not None:
                Draft202012Validator.check_schema(response_schema)
                schema_path = folder / 'schema.json'
                schema_path.write_text(json.dumps(response_schema, allow_nan=False), encoding='utf-8')
                command += ['--output-schema', str(schema_path)]
                record['schema_sha256'] = sha256(schema_path.read_bytes()).hexdigest()
            command += ['-']
            instruction = ('You are a text-only research generation function. Do not use tools, '
                           'read files, browse, or execute commands. All evidence is provided below. '
                           'Return only the requested JSON object.\n\n' + prompt)
            phase = 'subprocess'
            try:
                response = subprocess.run(command, input=instruction, text=True, encoding='utf-8',
                    capture_output=True, timeout=timeout, env=env)
                if response.returncode:
                    record['usage'] = []
                    raise _failure(record, _exit_diagnostic(response))
                phase = 'cli_events'
                events = [json.loads(line) for line in response.stdout.splitlines() if line.strip()]
                record['usage'] = [e['usage'] for e in events if e.get('type') == 'turn.completed']
                config_errors = [e for e in events if e.get('item', {}).get('type') == 'error'
                    and 'unrecognized configuration' in e.get('item', {}).get('message', '').lower()]
                forbidden = [e for e in events if e.get('item', {}).get('type') in {
                    'command_execution', 'file_change', 'mcp_tool_call', 'web_search'}]
                if config_errors or forbidden:
                    category = 'configuration' if config_errors else 'forbidden_tool_output'
                    raise _failure(record, {'category': category, 'exit_code': response.returncode})
                if not output.is_file():
                    diagnostic = _exit_diagnostic(response)
                    if diagnostic['category'] == 'cli_exit':
                        diagnostic['category'] = 'missing_output'
                    raise _failure(record, diagnostic)
                phase = 'answer'
                raw = output.read_text(encoding='utf-8')
                if response_schema is not None:
                    def pairs(items):
                        result = {}
                        for k, v in items:
                            if k in result:
                                raise ValueError('Duplicate JSON member')
                            result[k] = v
                        return result
                    def nonfinite(value):
                        raise ValueError('Nonfinite JSON constant')
                    parsed = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
                    Draft202012Validator(response_schema).validate(parsed)
                record.update(status='ok', response_sha256=sha256(raw.encode()).hexdigest())
                return raw
            except PipelineError:
                raise
            except subprocess.TimeoutExpired as error:
                failure = _failure(record, {'category': 'timeout', 'exception_type': type(error).__name__})
            except (ValueError, KeyError, ValidationError) as error:
                category = 'invalid_answer' if phase == 'answer' else 'cli_protocol'
                failure = _failure(record, {'category': category, 'exception_type': type(error).__name__},
                                   invalid=phase == 'answer')
            except Exception as error:
                failure = _failure(record, {'category': phase, 'exception_type': type(error).__name__})
            finally:
                record['elapsed_seconds'] = round(time.monotonic() - start, 3)
            # Raise after the handler exits so consumers cannot log a raw
            # exception from __context__.
            raise failure from None
    generate.supports_response_schema = True
    return generate, {'provider': 'codex_subscription', 'model': model,
                      'reasoning_effort': effort, 'auth': 'existing_chatgpt_login',
                      'schema_capability': 'cli_schema_and_local_validation'}
