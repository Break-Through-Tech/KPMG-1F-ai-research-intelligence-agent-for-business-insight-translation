import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.request import Request

from fetch_demo100 import NAMES, SafeRedirect, download


class Transport:
    def __init__(self, bodies):
        self.bodies = bodies
        self.requests = []

    def open(self, request, *, timeout):
        self.requests.append(request)
        return io.BytesIO(self.bodies[request.full_url.rsplit('/', 1)[1]])


class DownloadTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cache = self.root / 'cache'
        self.manifest = self.root / 'assets.json'
        self.bodies = {name.replace('/', '--'): name.encode() for name in NAMES}
        self.manifest.write_text(json.dumps({'files': {
            name: {'release_asset': name.replace('/', '--'), 'bytes': len(name.encode()),
                   'sha256': hashlib.sha256(name.encode()).hexdigest()} for name in NAMES}}))

    def test_verified_download_and_cache_hit(self):
        transport = Transport(self.bodies)
        download('https://assets.example/runtime', 'fixture', self.manifest, self.cache, opener=transport)
        download('https://assets.example/runtime', None, self.manifest, self.cache, opener=transport)
        self.assertEqual(len(transport.requests), 3)
        self.assertTrue(all(r.get_header('Authorization') == 'Bearer fixture' for r in transport.requests))
        self.assertEqual({p.relative_to(self.cache).as_posix() for p in self.cache.rglob('*') if p.is_file()}, NAMES)

    def test_bad_hash_leaves_no_bundle_files(self):
        self.bodies['demo-100--views.json'] = b'x' * len('demo-100/views.json')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            download('https://assets.example/runtime', None, self.manifest, self.cache, opener=Transport(self.bodies))
        self.assertFalse((self.cache / 'demo-100').exists())

    def test_truncation_leaves_no_bundle_files(self):
        self.bodies['demo-100--views.json'] = b'short'
        with self.assertRaisesRegex(ValueError, 'truncated'):
            download('https://assets.example/runtime', None, self.manifest, self.cache,
                     opener=Transport(self.bodies))
        self.assertFalse((self.cache / 'demo-100').exists())

    def test_corrupt_cache_is_rejected_without_network(self):
        parent = self.cache / 'demo-100/parents.jsonl'
        parent.parent.mkdir(parents=True)
        parent.write_bytes(b'corrupt')
        transport = Transport(self.bodies)
        with self.assertRaisesRegex(ValueError, 'failed verification'):
            download('https://assets.example/runtime', None, self.manifest, self.cache,
                     opener=transport)
        self.assertEqual(transport.requests, [])
        self.assertEqual(parent.read_bytes(), b'corrupt')

    def test_same_origin_redirect_retains_token(self):
        original = Request('https://assets.example/runtime')
        original.add_unredirected_header('Authorization', 'Bearer fixture')
        redirect = SafeRedirect().redirect_request(
            original, None, 302, '', {}, 'https://assets.example/object')
        self.assertEqual(redirect.get_header('Authorization'), 'Bearer fixture')

    def test_cross_origin_redirect_does_not_forward_token(self):
        original = Request('https://assets.example/runtime')
        original.add_unredirected_header('Authorization', 'Bearer fixture')
        redirect = SafeRedirect().redirect_request(original, None, 302, '', {}, 'https://objects.example/signed')
        self.assertIsNone(redirect.get_header('Authorization'))
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            SafeRedirect().redirect_request(original, None, 302, '', {}, 'http://objects.example/unsafe')


if __name__ == '__main__':
    unittest.main()
