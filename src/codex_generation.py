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
                from jsonschema import Draft202012Validator
                Draft202012Validator.check_schema(response_schema)
                schema_path = folder / 'schema.json'
                schema_path.write_text(json.dumps(response_schema, allow_nan=False), encoding='utf-8')
                command += ['--output-schema', str(schema_path)]
                record['schema_sha256'] = sha256(schema_path.read_bytes()).hexdigest()
            command += ['-']
            instruction = ('You are a text-only research generation function. Do not use tools, '
                           'read files, browse, or execute commands. All evidence is provided below. '
                           'Return only the requested JSON object.\n\n' + prompt)
            try:
                response = subprocess.run(command, input=instruction, text=True, encoding='utf-8',
                    capture_output=True, timeout=timeout, env=env)
                events = [json.loads(line) for line in response.stdout.splitlines() if line.strip()]
                record['usage'] = [e['usage'] for e in events if e.get('type') == 'turn.completed']
                config_errors = [e for e in events if e.get('item', {}).get('type') == 'error'
                    and 'unrecognized configuration' in e.get('item', {}).get('message', '').lower()]
                forbidden = [e for e in events if e.get('item', {}).get('type') in {
                    'command_execution', 'file_change', 'mcp_tool_call', 'web_search'}]
                if response.returncode or config_errors or forbidden or not output.is_file():
                    raise PipelineError('Codex text-only generation failed; no provider fallback occurred.')
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
            except (ValueError, KeyError) as exc:
                record['status'] = 'invalid_response'
                raise SchemaResponseError('Codex returned invalid JSON; no result was approved.') from None
            except Exception:
                record['status'] = 'failed'
                raise PipelineError('Codex generation failed; check login, model access or subscription limits.') from None
            finally:
                record['elapsed_seconds'] = round(time.monotonic() - start, 3)
    generate.supports_response_schema = True
    return generate, {'provider': 'codex_subscription', 'model': model,
                      'reasoning_effort': effort, 'auth': 'existing_chatgpt_login',
                      'schema_capability': 'cli_schema_and_local_validation'}
