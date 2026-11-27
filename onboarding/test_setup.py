import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import setup


class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name)
        self.data = b'pinned bytes'
        self.spec = {'release_tag': 'test-only', 'files': {'bundle/fixture': {
            'bytes': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest(),
            'release_asset': 'bundle--fixture'}}}

    def github(self, command, *, capture=False):
        if command[1] == 'repo':
            return 'PRIVATE'
        target = Path(command[command.index('--dir') + 1])
        (target / 'bundle--fixture').write_bytes(self.data)

    def test_private_download_and_verified_cache_hit(self):
        with patch.object(setup, 'exists', return_value='gh'), patch.object(setup, 'run', side_effect=self.github) as run:
            setup.acquire(self.spec, self.cache, 'example/private-assets')
            self.assertEqual((self.cache / 'bundle/fixture').read_bytes(), self.data)
            self.assertEqual(run.call_count, 2)
            setup.acquire(self.spec, self.cache, 'example/private-assets')
            self.assertEqual(run.call_count, 2)

    def test_bad_release_never_enters_cache(self):
        self.data = b'tampered'
        with patch.object(setup, 'exists', return_value='gh'), patch.object(setup, 'run', side_effect=self.github):
            with self.assertRaisesRegex(setup.SetupError, 'Checksum'):
                setup.acquire(self.spec, self.cache, 'example/private-assets')
        self.assertFalse((self.cache / 'bundle/fixture').exists())

    def test_rejects_public_repository(self):
        with patch.object(setup, 'exists', return_value='gh'), patch.object(setup, 'run', return_value='PUBLIC'):
            with self.assertRaisesRegex(setup.SetupError, 'not cleared'):
                setup.acquire(self.spec, self.cache, 'example/private-assets')

    def test_missing_release_explains_clearance(self):
        with patch.object(setup, 'exists', return_value='gh'), patch.object(
                setup, 'run', side_effect=['PRIVATE', setup.SetupError('release unavailable')]):
            with self.assertRaisesRegex(setup.SetupError, 'redistribution clearance'):
                setup.acquire(self.spec, self.cache, 'example/private-assets')


class RepositoryTests(unittest.TestCase):
    def test_origin_inference_supports_github_https_and_ssh(self):
        for origin in ('https://github.com/team/private.git', 'git@github.com:team/private.git',
                       'ssh://git@github.com/team/private.git'):
            with patch.object(setup, 'exists', return_value='git'), patch.object(setup, 'run', return_value=origin):
                self.assertEqual(setup.origin_repository(), 'team/private')

    def test_non_github_and_embedded_credentials_are_rejected(self):
        for origin in ('/local/clone', 'https://elsewhere.example/team/private',
                       'https://user:password@github.com/team/private'):
            with patch.object(setup, 'exists', return_value='git'), patch.object(setup, 'run', return_value=origin):
                self.assertIsNone(setup.origin_repository())


if __name__ == '__main__':
    unittest.main()
