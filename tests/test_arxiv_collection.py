"""Offline collector boundary tests."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.arxiv_collection import atomic_write, collect, parse_feed, identity

def feed(ids, total=None):
    entries = ''.join(f'''<entry><id>http://arxiv.org/abs/{i}</id><title>Title {i}</title>
        <summary>Agents and reasoning</summary><author><name>A</name></author>
        <category term="cs.AI"/><published>2026-01-01T00:00:00Z</published>
        <updated>2026-01-02T00:00:00Z</updated></entry>''' for i in ids)
    return f'''<feed xmlns="http://www.w3.org/2005/Atom"
        xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
        <opensearch:totalResults>{len(ids) if total is None else total}</opensearch:totalResults>
        {entries}</feed>'''.encode()


class FakeHTTP:
    def __init__(self, pages=(), pdf=b'%PDF-1.4\nfixture\n%%EOF'):
        self.pages, self.pdf, self.calls = iter(pages), pdf, []

    def get(self, url, *, params=None):
        self.calls.append((url, params))
        if params is not None:
            return next(self.pages)
        if isinstance(self.pdf, Exception):
            raise self.pdf
        return self.pdf


def args(output, **overrides):
    values = dict(ids=[],category='cs.AI',query=None,keyword=[],since='2026-01-01',
                  until='2026-01-03',max_results=2,page_size=2,output=Path(output),
                  dry_run=False,download=False)
    values.update(overrides)
    return argparse.Namespace(**values)


class CollectorTests(unittest.TestCase):
    def test_dry_run_never_mutates_even_with_download(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'absent'
            r = collect(args(path,dry_run=True,download=True),http=FakeHTTP([feed(['2601.00001v1'])]))
            self.assertFalse(path.exists())
            self.assertEqual(r['would_download'],1)

    def test_seen_id_does_not_stop_scanning_and_cap_resumes(self):
        with tempfile.TemporaryDirectory() as temp:
            r = collect(args(temp,max_results=1,page_size=1),http=FakeHTTP([feed(['2601.00001v1'],3)]))
            self.assertEqual(r['coverage_status'],'truncated_resumable')
            fake = FakeHTTP([feed(['2601.00001v1','2601.00002v1'],3)])
            r = collect(args(temp),http=fake)
            self.assertEqual(fake.calls[0][1]['start'],1)
            self.assertEqual((r['existing'],r['new'],r['candidate_records']),(1,1,2))

    def test_failed_download_retries_without_recollecting(self):
        with tempfile.TemporaryDirectory() as temp:
            r = collect(args(temp,download=True),http=FakeHTTP([feed(['2601.00001v1'])],pdf=OSError('offline')))
            self.assertEqual(r['pending_download_failures'],1)
            fake = FakeHTTP()
            r = collect(args(temp,download=True),http=fake)
            self.assertEqual((r['downloads_completed'],r['pending_download_failures']),(1,0))
            self.assertEqual(len(fake.calls),1)
            self.assertTrue((Path(temp)/'pdfs/2601.00001v1.pdf').exists())

    def test_versions_retained_and_filters_cannot_reuse_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            r = collect(args(temp),http=FakeHTTP([feed(['2601.00001v1','2601.00001v2'])]))
            self.assertEqual((r['new_versions'],r['candidate_records']),(1,2))
            with self.assertRaises(ValueError):
                collect(args(temp,category='cs.CL'),http=FakeHTTP())

    def test_exhausted_resume_repairs_interrupted_manifest_without_redownload(self):
        with tempfile.TemporaryDirectory() as temp:
            collect(args(temp,download=True),http=FakeHTTP(
                [feed(['2601.00001v1'])],pdf=OSError('offline')))
            out = Path(temp)

            def interrupt_manifest(path, text):
                if Path(path).name == 'manifest.json':
                    raise OSError('interrupted publication')
                atomic_write(path, text)

            with patch('src.arxiv_collection.atomic_write', side_effect=interrupt_manifest):
                with self.assertRaisesRegex(OSError, 'interrupted publication'):
                    collect(args(temp,download=True),http=FakeHTTP())
            checkpoint = json.loads((out/'checkpoint.json').read_text())
            self.assertTrue(checkpoint['exhausted'])
            row = checkpoint['records']['2601.00001v1']
            self.assertEqual(row['download_status'], 'complete')
            self.assertEqual(json.loads((out/'manifest.json').read_text())['papers'][0]
                             ['download_status'], 'failed')

            fake = FakeHTTP()
            report = collect(args(temp,download=True),http=fake)
            self.assertEqual(report['coverage_status'], 'window_exhausted')
            self.assertEqual(report['downloads_existing'], 1)
            self.assertEqual(report['downloads_completed'], 0)
            self.assertEqual(fake.calls, [])
            manifest = json.loads((out/'manifest.json').read_text())
            self.assertEqual(manifest['papers'], [row])
            self.assertEqual(sha256((out/row['pdf_path']).read_bytes()).hexdigest(),
                             manifest['papers'][0]['pdf_sha256'])

    def test_exhausted_metadata_only_resume_restores_missing_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            collect(args(temp),http=FakeHTTP([feed(['2601.00001v1'])]))
            out = Path(temp)
            for name in ('metadata.jsonl', 'metadata.csv', 'manifest.json'):
                (out/name).unlink()
            fake = FakeHTTP()
            report = collect(args(temp),http=fake)
            self.assertEqual(report['coverage_status'], 'window_exhausted')
            self.assertEqual(fake.calls, [])
            row = json.loads((out/'metadata.jsonl').read_text())
            with (out/'metadata.csv').open(newline='') as source:
                self.assertEqual(list(csv.DictReader(source)), [row])
            manifest = json.loads((out/'manifest.json').read_text())
            checkpoint = json.loads((out/'checkpoint.json').read_text())
            self.assertEqual(manifest['papers'], list(checkpoint['records'].values()))
            self.assertEqual(manifest['metadata_csv_sha256'],
                             sha256((out/'metadata.csv').read_bytes()).hexdigest())

    def test_exhausted_dry_run_does_not_repair_exports_or_mutate_files(self):
        with tempfile.TemporaryDirectory() as temp:
            collect(args(temp,download=True),http=FakeHTTP([feed(['2601.00001v1'])]))
            out = Path(temp)
            (out/'manifest.json').unlink()
            before = {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            fake = FakeHTTP()
            collect(args(temp,dry_run=True,download=True),http=fake)
            after = {p.relative_to(out): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            self.assertEqual(after, before)
            self.assertEqual(fake.calls, [])

    def test_empty_page_not_false_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            r = collect(args(temp),http=FakeHTTP([feed([],5)]))
            self.assertEqual((r['coverage_status'],r['next_start']),('failed_resumable',0))

    def test_exact_replay_requires_every_requested_version(self):
        with tempfile.TemporaryDirectory() as temp:
            a = args(temp,ids=['1706.03762v7'],since=None,until=None,category=None)
            r = collect(a,http=FakeHTTP([feed(['1706.03762v6'])]))
            self.assertEqual(r['coverage_status'],'failed_resumable')
            self.assertEqual(r['candidate_records'],0)

    def test_invalid_feed_and_identity_rejected(self):
        with self.assertRaises(ValueError):
            identity('../secret')
        with self.assertRaises(ValueError):
            parse_feed(feed(['2601.00001']))

    def test_download_budget_defers_known_missing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            collect(args(temp),http=FakeHTTP([feed(['2601.00001v1','2601.00002v1'])]))
            fake = FakeHTTP()
            r = collect(args(temp,download=True,max_results=1),http=fake)
            self.assertEqual((r['downloads_completed'],r['downloads_deferred']),(1,1))
            self.assertEqual(len(fake.calls),1)


if __name__ == '__main__':
    unittest.main()
