"""Dedicated generator for downstream business translation only.

Validated configuration (evaluation/business-translation-capability-diagnostic):
gemini-4-hydrogen, thinking_level=high, temperature 0, JSON output, one call.
It is separate from research generation: its own model and key variables, no
provider fallback, and at most one bounded retry for a transient HTTP 503.
Importing this module reads no secrets and contacts no provider.
"""
import os
import re
import time

from src.research_pipeline import PipelineError

MODEL = 'gemini-4-hydrogen'
THINKING_LEVEL = 'high'
GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/'
DEFAULT_KEY_ENV = 'BUSINESS_TRANSLATION_API_KEY'
RESEARCH_KEY_ENVS = ('GOOGLE_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY', 'RESEARCH_API_KEY')
RETRY_DELAY_SECONDS = 5
TIMEOUT_MS = 75000  # Two attempts plus the retry delay give a 155-second provider budget.


class BusinessTranslationUnavailable(PipelineError):
    """The business model stayed unavailable (HTTP 503) after one bounded retry."""


def business_config(environ=None):
    """Read business-only settings. Business translation stays off unless enabled."""
    env = os.environ if environ is None else environ
    if env.get('BUSINESS_TRANSLATION_ENABLED', '').strip().lower() not in {'1', 'true', 'yes'}:
        raise PipelineError('Business translation is disabled. Set BUSINESS_TRANSLATION_ENABLED=1 to enable it.')
    model = env.get('BUSINESS_TRANSLATION_MODEL', MODEL).strip()
    if model != MODEL:
        raise PipelineError(f'Business translation is validated only with {MODEL}; no other model is used.')
    endpoint = env.get('GOOGLE_GEMINI_BASE_URL', '').strip()
    if endpoint and endpoint.rstrip('/') != GEMINI_ENDPOINT.rstrip('/'):
        raise PipelineError('Business translation requires the official Gemini API endpoint.')
    if env.get('GOOGLE_VERTEX_BASE_URL', '').strip() or any(
            env.get(name, '').strip().lower() not in {'', '0', 'false'}
            for name in ('GOOGLE_GENAI_USE_VERTEXAI', 'GOOGLE_GENAI_USE_ENTERPRISE')):
        raise PipelineError('Business translation requires Gemini Developer API configuration, without Vertex overrides.')
    key_env = env.get('BUSINESS_TRANSLATION_API_KEY_ENV', DEFAULT_KEY_ENV).strip()
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key_env) or key_env in RESEARCH_KEY_ENVS:
        raise PipelineError('BUSINESS_TRANSLATION_API_KEY_ENV must name a dedicated key variable, not a research key.')
    key = env.get(key_env, '').strip()
    if not key:
        raise PipelineError(f'Set {key_env} to the dedicated business translation key.')
    if any(key == env.get(name, '').strip() for name in RESEARCH_KEY_ENVS):
        raise PipelineError('The business translation key must differ from the research keys.')
    return {'model': model, 'api_key': key, 'key_env': key_env}


def _is_transient_503(error):
    return getattr(error, 'code', None) == 503 or getattr(error, 'status_code', None) == 503


def create_business_generate(environ=None, *, client=None, sleep=time.sleep):
    """Return (generate, metadata). generate(prompt) -> JSON text; one retry on 503 only."""
    config = business_config(environ)
    from google.genai import types
    if client is None:
        from google import genai
        client = genai.Client(api_key=config['api_key'], vertexai=False, http_options=types.HttpOptions(
            base_url=GEMINI_ENDPOINT, timeout=TIMEOUT_MS,
            client_args={'follow_redirects': False, 'trust_env': False},
            retry_options=types.HttpRetryOptions(attempts=1)))
    request = types.GenerateContentConfig(response_mime_type='application/json', temperature=0,
                                          thinking_config=types.ThinkingConfig(thinking_level=THINKING_LEVEL))

    def generate(prompt):
        for attempt in (1, 2):
            generate.provider_attempts = attempt
            try:
                return client.models.generate_content(model=config['model'], contents=prompt, config=request).text
            except Exception as error:
                if not _is_transient_503(error):
                    raise
                if attempt == 2:
                    raise BusinessTranslationUnavailable(
                        'Business translation model is temporarily unavailable.') from None
                sleep(RETRY_DELAY_SECONDS)

    metadata = {'provider': 'gemini', 'model': config['model'], 'temperature': 0,
                'effort': f'thinking_level={THINKING_LEVEL}', 'execution': 'free_tier_public_data_only'}
    return generate, metadata
