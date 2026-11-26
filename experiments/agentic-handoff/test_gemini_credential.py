"""Windows Credential Manager integration using only a disposable test secret."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

from gemini_credential import APPROVED, CredentialError, KEY_NAME, TARGET, WindowsCredentials, launch


@unittest.skipUnless(sys.platform == "win32", "Windows Credential Manager required")
class LauncherTests(unittest.TestCase):
    def test_real_windows_round_trip_and_child_only(self):
        store = WindowsCredentials()
        temporary_target = TARGET + ".offline-test." + uuid4().hex
        secret = "offline-fixture-" + uuid4().hex
        store.put(temporary_target, secret)
        try:
            self.assertTrue(store.get(temporary_target) == secret)
            with TemporaryDirectory() as temp:
                child = Path(temp) / "probe.py"
                child.write_text(
                    "import hashlib,os,sys\n"
                    "assert hashlib.sha256(os.environ['GOOGLE_API_KEY'].encode()).hexdigest() == sys.argv[1]\n"
                    "assert 'OPENAI_API_KEY' not in os.environ\n"
                    "print('child received dummy credential')\n", encoding="utf-8",
                )
                from hashlib import sha256
                expected = sha256(secret.encode()).hexdigest()
                def check_launch(command, **kwargs):
                    self.assertTrue(all(secret not in arg for arg in command))
                    self.assertEqual(kwargs["env"][KEY_NAME], secret)
                    result = subprocess.run(command, **kwargs, capture_output=True, text=True)
                    self.assertTrue(secret not in result.stdout + result.stderr)
                    self.assertEqual(result.stdout.strip(), "child received dummy credential")
                    return result
                with patch("gemini_credential.TARGET", temporary_target), patch.dict(
                    APPROVED, {"fixture": (child, expected)}
                ), patch.dict(os.environ, {"OPENAI_API_KEY": "offline-unused"}):
                    old = os.environ.get(KEY_NAME)
                    self.assertEqual(launch("fixture", store, run=check_launch), 0)
                    self.assertEqual(os.environ.get(KEY_NAME), old)
        finally:
            store.delete(temporary_target)
        with self.assertRaises(CredentialError):
            store.get(temporary_target)

    def test_broken_environment_rejected_before_loading_key(self):
        def probe(command, **kwargs):
            self.assertNotIn(KEY_NAME, kwargs["env"])
            self.assertEqual(command[1:3], ["-I", "-c"])
            return subprocess.CompletedProcess(command, 1)
        with self.assertRaisesRegex(CredentialError, "cannot import the runner"):
            launch("grounded-stage-a", None, probe=probe)  # store=None: reading the key would raise instead

    def test_unapproved_command_rejected_before_loading_key(self):
        with self.assertRaisesRegex(CredentialError, "no launcher entry"):
            launch("unapproved", None)
