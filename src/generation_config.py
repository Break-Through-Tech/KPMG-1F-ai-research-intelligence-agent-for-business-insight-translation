"""Explicit, local-only BYOK settings. Importing this module reads no secrets."""
from dataclasses import dataclass, field
import os
import re
from urllib.parse import urlsplit

from src.research_pipeline import PipelineError


@dataclass(frozen=True)
class GenerationConfig:
    provider: str
    model: str
    api_key: str = field(repr=False)
    base_url: str | None = None

    def __post_init__(self):
        if self.provider not in {'gemini', 'openai', 'openai_compatible'}:
            raise PipelineError('RESEARCH_PROVIDER must be gemini, openai, or openai_compatible.')
        if not isinstance(self.api_key, str) or not self.api_key.strip():
            raise PipelineError('The selected generation provider requires a local API key.')
        if not isinstance(self.model, str) or not self.model.strip():
            raise PipelineError('Set RESEARCH_MODEL explicitly for this generation provider.')
        if self.provider == 'openai_compatible' and not self.base_url:
            raise PipelineError('Set RESEARCH_BASE_URL for openai_compatible.')
        if self.provider != 'openai_compatible' and self.base_url is not None:
            raise PipelineError('Custom endpoints require RESEARCH_PROVIDER=openai_compatible.')
        if self.base_url is not None:
            try:
                parsed = urlsplit(self.base_url)
                local_http = parsed.scheme == 'http' and parsed.hostname in {'localhost','127.0.0.1','::1'}
                valid = (parsed.scheme == 'https' or local_http) and parsed.hostname and not (
                    parsed.username or parsed.password or parsed.query or parsed.fragment)
                parsed.port  # Reject malformed ports without echoing the URL.
            except (ValueError, TypeError):
                valid = False
            if not valid:
                raise PipelineError('RESEARCH_BASE_URL requires HTTPS (or loopback HTTP), with no URL credentials/query/fragment.')

    @classmethod
    def from_environment(cls, environ=None):
        env = os.environ if environ is None else environ
        provider = env.get('RESEARCH_PROVIDER', 'gemini').strip().lower()
        if provider not in {'gemini','openai','openai_compatible'}:
            raise PipelineError('RESEARCH_PROVIDER must be gemini, openai, or openai_compatible.')
        default_key = {'gemini':'GOOGLE_API_KEY','openai':'OPENAI_API_KEY','openai_compatible':'RESEARCH_API_KEY'}[provider]
        key_env = (env.get('RESEARCH_API_KEY_ENV') or default_key).strip()
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key_env):
            raise PipelineError('RESEARCH_API_KEY_ENV must name an environment variable.')
        key = env.get(key_env, '').strip()
        if not key or 'Your API Key' in key:
            raise PipelineError(f'Set {key_env} locally for the selected provider; retrieval and --demo need no key.')
        model = env.get('RESEARCH_MODEL', '').strip()
        if not model and provider == 'gemini': model = env.get('GOOGLE_MODEL','gemini-2.5-flash').strip()
        base_url = env.get('RESEARCH_BASE_URL','').strip() or None
        return cls(provider,model,key,base_url)
