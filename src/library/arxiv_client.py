"""Polite arXiv HTTP client: one request at a time, minimum spacing, backoff on 429/5xx."""
import time

API = 'https://export.arxiv.org/api/query'
RETRY_STATUS = {429, 500, 502, 503, 504}


class RateLimited(RuntimeError):
    """arXiv kept refusing after every backoff; the caller should pause and resume later."""


class ArxivClient:
    def __init__(self, *, delay=3.5, attempts=5, backoff=(30, 60, 120, 240), timeout=30,
                 session=None, sleep=time.sleep, clock=time.monotonic):
        if session is None:
            import requests
            session = requests.Session()
            session.headers['User-Agent'] = 'KPMG-1F-research-library/0.1 (local research prototype)'
        self.session, self.delay, self.attempts = session, delay, attempts
        self.backoff, self.timeout, self.sleep, self.clock = backoff, timeout, sleep, clock
        self.last = None
        self.requests = 0

    def _wait(self):
        if self.last is not None:
            remaining = self.delay - (self.clock() - self.last)
            if remaining > 0:
                self.sleep(remaining)
        self.last = self.clock()

    def get(self, url, *, params=None, max_bytes=8_000_000):
        """Return (status, bytes). 404/403/410 return their status; retryable errors back off."""
        import requests
        for attempt in range(self.attempts):
            self._wait()
            self.requests += 1
            try:
                response = self.session.get(url, params=params, timeout=self.timeout, allow_redirects=False)
            except requests.RequestException:
                if attempt + 1 == self.attempts:
                    raise
                self.sleep(self.backoff[min(attempt, len(self.backoff) - 1)])
                continue
            if response.status_code in RETRY_STATUS:
                retry_after = response.headers.get('Retry-After', '')
                wait = int(retry_after) if retry_after.isdigit() else self.backoff[min(attempt, len(self.backoff) - 1)]
                if attempt + 1 == self.attempts:
                    if response.status_code == 429:
                        raise RateLimited('arXiv rate limit persisted after backoff.')
                    response.raise_for_status()
                self.sleep(min(wait, 600))
                continue
            if response.status_code in (403, 404, 410):
                return response.status_code, b''
            if response.status_code != 200:
                return response.status_code, b''
            content = response.content
            if len(content) > max_bytes:
                raise ValueError('arXiv resource exceeded the download limit.')
            return 200, content
        raise RuntimeError('unreachable')
