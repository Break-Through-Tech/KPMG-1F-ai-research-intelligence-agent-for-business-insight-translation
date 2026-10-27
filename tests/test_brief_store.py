"""Persistence, version/review isolation and contention: no model or index needed."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from src.brief_store import BriefStore, BriefConflict
from src.research_demo import load_demo


class BriefStoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'briefs' / 'library.sqlite3'
        self.store = BriefStore(self.path)
        self.envelope = load_demo({'query': 'Not executed'}, 'full')

    def save(self):
        return self.store.save(self.envelope)['library']

    def test_automatic_setup_and_restart_preserve_complete_snapshot(self):
        before = deepcopy(self.envelope)
        saved = self.store.save(self.envelope)
        reopened = BriefStore(self.path).load(saved['library']['brief']['id'])
        self.assertEqual(reopened['result'], self.envelope['result'])
        self.assertEqual(reopened['plain_language'], self.envelope['plain_language'])
        self.assertEqual(reopened['mode'], 'fixture')
        self.assertEqual(reopened['submitted_request']['query'], 'Not executed')
        self.assertEqual(reopened['library']['version']['fingerprint'], saved['library']['version']['fingerprint'])
        self.assertEqual(before, self.envelope)
        with self.store.connection() as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)
            self.assertEqual({r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")},
                             {'briefs', 'brief_versions', 'reviews'})

    def test_review_is_exact_version_and_never_inherited_or_imported(self):
        lib = self.save()
        reviewed = self.store.review(lib['brief']['id'], version_id=lib['version']['id'],
            fingerprint=lib['version']['fingerprint'], reviewer='Human Reviewer', decision='approve')
        self.assertEqual(reviewed['library']['reviews'][0]['decision'], 'approve')
        self.assertFalse(reviewed['result']['approved'])  # immutable pending source snapshot
        v2 = self.store.save(self.envelope, brief_id=lib['brief']['id'], expected_version=lib['version']['id'])
        self.assertEqual(v2['library']['version']['number'], 2)
        self.assertEqual(v2['library']['reviews'], [])
        old = self.store.load(lib['brief']['id'], lib['version']['id'])
        self.assertEqual(old['library']['reviews'][0]['decision'], 'approve')
        with self.assertRaises(BriefConflict):
            self.store.review(lib['brief']['id'], version_id=lib['version']['id'],
                fingerprint=lib['version']['fingerprint'], reviewer='Human Reviewer', decision='approve')
        imported = self.store.save(reviewed)
        self.assertEqual(imported['library']['reviews'], [])
        self.assertNotEqual(imported['library']['brief']['id'], lib['brief']['id'])

    def test_bad_fingerprints_and_regulatory_gate_block_review(self):
        lib = self.save()
        with self.assertRaises(BriefConflict):
            self.store.review(lib['brief']['id'], version_id=lib['version']['id'],
                fingerprint='wrong', reviewer='Human Reviewer', decision='approve')
        with self.assertRaises(ValueError):
            self.store.review(lib['brief']['id'], version_id=lib['version']['id'],
                fingerprint=lib['version']['fingerprint'], reviewer='Human Reviewer', decision='revise')
        self.envelope['result']['regulatory_checkpoint'] = {'unresolved': True}
        lib = self.save()
        with self.assertRaises(ValueError):
            self.store.review(lib['brief']['id'], version_id=lib['version']['id'],
                fingerprint=lib['version']['fingerprint'], reviewer='Human Reviewer', decision='approve')
        self.assertEqual(self.store.load(lib['brief']['id'])['library']['reviews'], [])

    def test_requested_changes_and_review_history_are_append_only(self):
        lib = self.save()
        args = dict(version_id=lib['version']['id'], fingerprint=lib['version']['fingerprint'], reviewer='Human')
        self.store.review(lib['brief']['id'], **args, decision='revise', notes='Check the uncertainty.')
        reviewed = self.store.review(lib['brief']['id'], **args, decision='approve', notes='Checked.')
        self.assertEqual([r['decision'] for r in reviewed['library']['reviews']], ['revise', 'approve'])
        for table in ['reviews', 'brief_versions']:
            with self.store.connection() as db:
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(f'DELETE FROM {table}')

    def test_rename_archive_restore_search_and_pagination(self):
        lib = self.save()
        args = dict(expected_version=lib['version']['id'])
        self.store.update(lib['brief']['id'], **args, title="Quoted ' title % _")
        self.assertEqual(len(self.store.list(query="' title")), 1)
        self.assertEqual(len(self.store.list(query='not found')), 0)
        self.assertEqual(len(self.store.list(query='% _')), 1)
        self.store.update(lib['brief']['id'], **args, archived=True)
        self.assertEqual(self.store.list(), [])
        self.assertEqual(len(self.store.list(archived=True)), 1)
        with self.assertRaises(BriefConflict):
            self.store.save(self.envelope, brief_id=lib['brief']['id'], **args)
        self.store.update(lib['brief']['id'], **args, archived=False)
        self.assertEqual(len(self.store.list()), 1)
        self.assertEqual(self.store.list(offset=1), [])

    def test_concurrent_revision_writers_cannot_overwrite_each_other(self):
        lib = self.save()
        def write(_):
            try:
                self.store.save(self.envelope, brief_id=lib['brief']['id'], expected_version=lib['version']['id'])
                return 'saved'
            except BriefConflict:
                return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(write, range(2))), ['saved', 'conflict'])
        self.assertEqual(len(self.store.load(lib['brief']['id'])['library']['versions']), 2)

    def test_transaction_failure_rolls_back_new_brief_and_version(self):
        with self.store.connection() as db:
            db.execute("CREATE TRIGGER fail BEFORE INSERT ON brief_versions BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.save()
        with self.store.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM briefs').fetchone()[0], 0)

    def test_invalid_snapshot_and_reviewed_result_rejected(self):
        self.envelope['result']['approved'] = True
        with self.assertRaises(ValueError):
            self.save()
        self.envelope = load_demo({'query': 'Q'}, 'full')
        self.envelope['result']['review_fingerprint'] = 'bad'
        with self.assertRaises(ValueError):
            self.save()
        self.assertEqual(self.store.list(), [])

    def test_imported_ui_metadata_is_validated_before_storage(self):
        for key, value in [('submitted_request', None), ('error', 'broken error envelope')]:
            with self.subTest(key=key):
                envelope = deepcopy(self.envelope)
                envelope[key] = value
                with self.assertRaises(ValueError):
                    self.store.save(envelope)
        self.assertEqual(self.store.list(), [])

    def test_startup_import_reuse_does_not_duplicate_snapshot(self):
        first = self.store.save(self.envelope, reuse=True)
        second = BriefStore(self.path).save(self.envelope, reuse=True)
        self.assertEqual(first['library']['version'], second['library']['version'])
        self.assertEqual(len(self.store.list()), 1)
