"""Fetch the three evaluated demo-100 artifacts from an approved HTTPS location."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

NAMES = {'demo-100/parents.jsonl', 'demo-100/views.json', 'demo-100/vectors.npy'}


def origin(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        raise ValueError('Use an HTTPS URL without embedded credentials.')
    return parts.hostname, parts.port or 443


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        same_origin = origin(req.full_url) == origin(newurl)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            authorization = req.get_header('Authorization')
            redirected.remove_header('Authorization')
            if same_origin and authorization:
                redirected.add_unredirected_header('Authorization', authorization)
        return redirected


def matches(path, item):
    if not path.is_file() or path.is_symlink() or path.stat().st_size != item['bytes']:
        return False
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256']


def download(base, token, manifest, cache, *, opener=None):
    origin(base)
    if urlsplit(base).query or urlsplit(base).fragment:
        raise ValueError('Configure an artifact directory URL, without query or fragment.')
    spec = json.loads(manifest.read_bytes())['files']
    items = {name: spec[name] for name in sorted(NAMES)}
    missing = []
    for name, item in items.items():
        expected_name = name.replace('/', '--')
        if item['release_asset'] != expected_name:
            raise ValueError('Unexpected artifact name in pinned manifest.')
        target = cache / name
        if not matches(target, item):
            if target.exists() or target.is_symlink():
                raise ValueError(f'Cached {expected_name} failed verification. Remove the damaged cache entry and rerun.')
            missing.append((name, item))
    if not missing:
        print('All three demo-100 artifacts verified in cache.')
        return
    cache.mkdir(parents=True, exist_ok=True)
    opener = opener or build_opener(SafeRedirect())
    with tempfile.TemporaryDirectory(prefix='demo100-', dir=cache) as directory:
        staging = Path(directory)
        for name, item in missing:
            label = item['release_asset']
            request = Request(base.rstrip('/') + '/' + quote(label, safe=''))
            if token:
                request.add_unredirected_header('Authorization', f'Bearer {token}')
            path = staging / label
            try:
                with opener.open(request, timeout=30) as response, path.open('wb') as target:
                    remaining = item['bytes']
                    while remaining:
                        block = response.read(min(remaining, 1024 * 1024))
                        if not block:
                            break
                        target.write(block)
                        remaining -= len(block)
                    if remaining or response.read(1):
                        raise ValueError('size mismatch')
            except OSError as error:
                code = getattr(error, 'code', None)
                detail = f'HTTP {code}' if code else type(error).__name__
                raise ValueError(f'Could not fetch {label}: {detail}. Check approved storage access.') from None
            except ValueError:
                raise ValueError(f'{label} was truncated, oversized or redirected to an unsafe URL.') from None
            if not matches(path, item):
                raise ValueError(f'SHA-256 mismatch: {label}. Nothing from this download was activated.')
        for name, item in missing:
            target = cache / name
            target.parent.mkdir(parents=True, exist_ok=True)
            (staging / item['release_asset']).replace(target)
    print('All three demo-100 artifacts verified.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('onboarding/assets.json'))
    parser.add_argument('--cache', type=Path, default=Path('.kpmg-onboarding/assets'))
    args = parser.parse_args()
    base = os.environ.get('KPMG_ARTIFACT_BASE_URL')
    if not base:
        sys.exit('Set KPMG_ARTIFACT_BASE_URL to the approved HTTPS artifact directory.')
    try:
        download(base, os.environ.get('KPMG_ARTIFACT_TOKEN'), args.manifest, args.cache)
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f'Artifact preparation failed: {error}')


if __name__ == '__main__':
    main()
