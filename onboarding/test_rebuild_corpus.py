import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import rebuild_corpus as rebuild


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def geturl(self):
        return 'https://arxiv.org/html/2601.00001v1'

    class headers:
        @staticmethod
        def get_content_type():
            return 'text/html'


class CorpusTests(unittest.TestCase):
    def test_drift_is_reported_and_not_cached(self):
        raw = b'<html>expected</html>'
        pin = hashlib.sha256(raw).hexdigest()
        paper = {'id': '2601.00001v1', 'html_sha256': pin}
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / 'arxiv-html'
            with patch.object(rebuild, 'urlopen', return_value=Response(b'<html>changed</html>')), patch.object(rebuild.time, 'sleep'):
                result = rebuild.retrieve_sources(cache, papers=[paper])
            self.assertEqual(result[0]['status'], 'changed')
            self.assertNotEqual(result[0]['actual_sha256'], pin)
            self.assertFalse((cache / '2601.00001v1.html').exists())
            self.assertEqual(json.loads((cache.parent / 'source-verification.json').read_bytes()), result)

    def test_exact_input_is_cached_without_rewriting(self):
        raw = b'<html>expected</html>'
        paper = {'id': '2601.00001v1', 'html_sha256': hashlib.sha256(raw).hexdigest()}
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / 'arxiv-html'
            with patch.object(rebuild, 'urlopen', return_value=Response(raw)) as get, patch.object(rebuild.time, 'sleep'):
                self.assertEqual(rebuild.retrieve_sources(cache, papers=[paper])[0]['status'], 'exact')
                self.assertEqual(rebuild.retrieve_sources(cache, papers=[paper])[0]['status'], 'exact')
            self.assertEqual(get.call_count, 1)
            self.assertEqual((cache / '2601.00001v1.html').read_bytes(), raw)

    def test_serialization_preserves_order_crlf_and_no_final_separator(self):
        self.assertEqual(rebuild.encode_parents([{'b': 1, 'a': 2}, {'c': 3}]),
                         b'{"b": 1, "a": 2}\r\n{"c": 3}')


if __name__ == '__main__':
    unittest.main()
