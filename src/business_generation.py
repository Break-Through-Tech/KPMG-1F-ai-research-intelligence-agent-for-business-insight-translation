"""Dedicated generator for downstream business translation only.

Validated configuration (evaluation/business-translation-capability-diagnostic):
gemini-4-hydrogen, thinking_level=high, temperature 0, JSON output, one call.
It is separate from research generation: its own model and key variables, no
provider fallback, and at most one bounded retry for a temporary provider failure
(HTTP 500/502/503/504, timeout or dropped connection) or a short rate limit.
Exhausted quotas, authentication errors and invalid requests are never retried.
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
MAX_RATE_LIMIT_WAIT_SECONDS = 20  # Longer provider waits are reported, not slept, within the 170 s proxy budget.
TIMEOUT_MS = 75000  # Two attempts plus the retry delay give a 155-second provider budget.

# Sanitized provider failure categories. Only these enums, HTTP codes and gRPC status names are
# recorded or logged; provider messages and details can echo request content and are never kept.
TEMPORARY, RATE_LIMITED, QUOTA_EXHAUSTED = 'temporary', 'rate_limited', 'quota_exhausted'
AUTHENTICATION, INVALID_REQUEST, UNKNOWN = 'authentication', 'invalid_request', 'unknown'
RETRYABLE_ONCE = {TEMPORARY, RATE_LIMITED}


class BusinessProviderError(PipelineError):
    """A classified provider failure. Carries no provider text."""

    def __init__(self, category, *, http_status=None, provider_status=None, retry_after=None):
        self.category, self.http_status = category, http_status
        self.provider_status, self.retry_after = provider_status, retry_after
        super().__init__(f'Business translation provider failure: {category}.')

    def diagnostics(self):
        return {key: value for key, value in (
            ('category', self.category), ('http_status', self.http_status),
            ('provider_status', self.provider_status), ('retry_after_seconds', self.retry_after))
            if value is not None}


class BusinessTranslationUnavailable(BusinessProviderError):
    """The business model stayed temporarily unavailable after one bounded retry."""

    def __init__(self, message='Business translation model is temporarily unavailable.', **kwargs):
        kwargs.setdefault('category', TEMPORARY)
        category = kwargs.pop('category')
        super().__init__(category, **kwargs)


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


def _seconds(value):
    match = re.fullmatch(r'\s*(\d+(?:\.\d+)?)s\s*', value) if isinstance(value, str) else None
    return round(float(match[1]), 1) if match else None


def classify_provider_error(error):
    """Map a provider exception to a sanitized BusinessProviderError (never raises)."""
    if isinstance(error, BusinessProviderError):
        return error
    name = type(error).__name__.lower()
    code = getattr(error, 'code', None)
    code = code if isinstance(code, int) else getattr(error, 'status_code', None)
    status = getattr(error, 'status', None)
    status = status if isinstance(status, str) and re.fullmatch(r'[A-Z_]{3,40}', status) else None
    details = getattr(error, 'details', None)
    violations, retry_after = [], None
    entries = (details.get('error', {}).get('details') if isinstance(details, dict) else None) or []
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get('@type', ''))
        if kind.endswith('QuotaFailure'):
            violations += [str(v.get('quotaId', '')) for v in entry.get('violations', []) if isinstance(v, dict)]
        elif kind.endswith('RetryInfo'):
            retry_after = _seconds(entry.get('retryDelay'))
        elif kind.endswith('ErrorInfo') and entry.get('reason') in {'API_KEY_INVALID', 'API_KEY_SERVICE_BLOCKED'}:
            return BusinessProviderError(AUTHENTICATION, http_status=code, provider_status=status)
    meta = {'http_status': code, 'provider_status': status}
    if code in {500, 502, 503, 504} or any(word in name for word in ('timeout', 'connect', 'remoteprotocol')):
        return BusinessProviderError(TEMPORARY, **meta)
    if code == 429 or status == 'RESOURCE_EXHAUSTED':
        daily = any(re.search(r'per ?day|perday', quota, re.I) for quota in violations)
        if daily or (violations and retry_after is None):
            return BusinessProviderError(QUOTA_EXHAUSTED, **meta)
        return BusinessProviderError(RATE_LIMITED, retry_after=retry_after, **meta)
    if code in {401, 403} or status in {'UNAUTHENTICATED', 'PERMISSION_DENIED'}:
        return BusinessProviderError(AUTHENTICATION, **meta)
    if isinstance(code, int) and 400 <= code < 500:
        return BusinessProviderError(INVALID_REQUEST, **meta)
    return BusinessProviderError(UNKNOWN, **meta)


def _is_transient_503(error):  # retained for callers and tests of the original policy
    return getattr(error, 'code', None) == 503 or getattr(error, 'status_code', None) == 503


def create_business_generate(environ=None, *, client=None, sleep=time.sleep):
    """Return (generate, metadata). generate(prompt) -> JSON text.

    At most two attempts: one retry for a temporary failure (after RETRY_DELAY_SECONDS) or for a
    short rate limit (after the provider's retry delay, capped). Everything else raises at once.
    generate.provider_attempts and generate.attempt_log record sanitized per-attempt outcomes."""
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
        generate.attempt_log = []
        for attempt in (1, 2):
            generate.provider_attempts = attempt
            try:
                text = client.models.generate_content(model=config['model'], contents=prompt, config=request).text
                generate.attempt_log.append({'category': 'ok'})
                return text
            except Exception as error:
                failure = classify_provider_error(error)
            generate.attempt_log.append(failure.diagnostics())
            wait = (RETRY_DELAY_SECONDS if failure.category == TEMPORARY else
                    max(RETRY_DELAY_SECONDS, failure.retry_after or RETRY_DELAY_SECONDS)
                    if failure.category == RATE_LIMITED else None)
            if attempt == 2 or wait is None or wait > MAX_RATE_LIMIT_WAIT_SECONDS:
                if failure.category in RETRYABLE_ONCE and type(failure) is BusinessProviderError:
                    failure = BusinessTranslationUnavailable(**{'category': failure.category, **{
                        k: v for k, v in vars(failure).items() if k in ('http_status', 'provider_status', 'retry_after')}})
                raise failure from None
            sleep(wait)

    metadata = {'provider': 'gemini', 'model': config['model'], 'temperature': 0,
                'effort': f'thinking_level={THINKING_LEVEL}', 'execution': 'free_tier_public_data_only'}
    return generate, metadata
