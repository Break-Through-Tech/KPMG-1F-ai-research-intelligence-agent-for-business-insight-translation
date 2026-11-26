"""Durable, cross-process call ledger for the cumulative model-call authorization (SQLite).

Why SQLite: a reservation must be atomic across independently started processes on Windows, and a
crash must never leave a half-written record that undercounts. SQLite gives both: ``BEGIN IMMEDIATE``
takes the database write lock across processes (count-then-insert is one transaction), and a crash
before COMMIT rolls back completely; there are no partial records. ``synchronous=FULL`` with the
rollback journal makes a committed reservation durable before the provider is called.

Rules:
- Every row counts against the authorization whatever its state: ``reserved`` (in flight in this
  process), ``completed``, ``failed`` and ``unresolved`` (reserved by another or a crashed process and
  never finished). A reservation is committed BEFORE its provider call.
- An optional experiment cap (for example 14 calls for the A/B run) is enforced in the same
  transaction as the overall cap. Its value is recorded once and can never be changed or raised.
- Fail closed: a missing file, a failed integrity check, an unknown schema, an unknown state, a
  changed authorization, or a row count below the recorded high-water mark all refuse every call.
- Never reset: the ledger is created only by ``init`` from an explicit seed; ``init`` refuses an
  existing file. There is no delete or reset operation.

Create once from the strictly parsed JSONL seed:
    py -3.14 call_ledger.py init --ledger X.sqlite3 --authorized 40 --seed codex-authorization-40.ledger.jsonl
Inspect (read-only):
    py -3.14 call_ledger.py status --ledger X.sqlite3
"""
import argparse
import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

SCHEMA_VERSION = '1'
STATES = ('reserved', 'completed', 'failed', 'unresolved')


class LedgerError(RuntimeError):
    """The ledger cannot be trusted or the authorization is used up. No call is made."""


def _connect(path):
    # check_same_thread=False: the HTTP server calls from worker threads; the wrapper's own lock
    # serializes use within a process, and SQLite's file lock serializes processes.
    connection = sqlite3.connect(str(path), timeout=30, isolation_level=None, check_same_thread=False)
    connection.execute('PRAGMA journal_mode=DELETE')
    connection.execute('PRAGMA synchronous=FULL')
    connection.execute('PRAGMA foreign_keys=ON')
    return connection


def parse_seed(seed_path):
    """Strictly parse a JSONL call log. Any incomplete or malformed line refuses the whole seed."""
    raw = Path(seed_path).read_bytes()
    if raw and not raw.endswith(b'\n'):
        raise LedgerError('Seed ends with an incomplete record (no final newline); repair it by hand first.')
    rows = []
    for number, line in enumerate(raw.decode('utf-8').split('\n')[:-1] if raw else [], 1):
        if not line.strip():
            raise LedgerError(f'Seed line {number} is blank; every line must be one call record.')
        try:
            record = json.loads(line)
        except ValueError:
            raise LedgerError(f'Seed line {number} is not valid JSON.') from None
        if not isinstance(record, dict) or not isinstance(record.get('at'), str) or 'outcome' not in record:
            raise LedgerError(f'Seed line {number} lacks the required "at" and "outcome" fields.')
        rows.append(record)
    return rows, hashlib.sha256(raw).hexdigest()


def init(path, *, authorized, seed):
    """Create a new ledger from a seed log. Refuses to overwrite anything."""
    path = Path(path)
    if path.exists():
        raise LedgerError(f'{path} already exists; a ledger is never recreated or reset.')
    records, digest = parse_seed(seed)
    import ab_profile
    approved = ab_profile.approved_seed(digest)
    if approved is not None:
        raise LedgerError(f'This seed belongs to the approved authorization {approved!r}, whose one ledger is '
                          f"{ab_profile.AUTHORIZATIONS[approved]['ledger_path']}; a second ledger is never created.")
    if len(records) > int(authorized):
        raise LedgerError('The seed already exceeds the authorization.')
    # A temporary file unique to THIS initializer: competing initializers never share or overwrite it.
    temporary = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.creating')
    connection = _connect(temporary)
    try:
        connection.execute('BEGIN IMMEDIATE')
        connection.execute('CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        connection.execute('CREATE TABLE caps (name TEXT PRIMARY KEY, cap INTEGER NOT NULL CHECK (cap >= 0))')
        connection.execute(f'''CREATE TABLE calls (
            id TEXT PRIMARY KEY, state TEXT NOT NULL CHECK (state IN {STATES}),
            experiment TEXT, instance TEXT, pid INTEGER, reserved_at TEXT NOT NULL,
            finished_at TEXT, outcome TEXT, seconds REAL, source TEXT)''')
        meta = {'schema_version': SCHEMA_VERSION, 'authorized': str(int(authorized)), 'created_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'seed_path': str(Path(seed).resolve()), 'seed_sha256': digest, 'seed_records': str(len(records)),
                'high_water': str(len(records))}
        connection.executemany('INSERT INTO meta VALUES (?, ?)', meta.items())
        for number, record in enumerate(records, 1):
            state = 'completed' if record.get('outcome') == 'ok' else 'failed'
            connection.execute('INSERT INTO calls (id, state, reserved_at, finished_at, outcome, seconds, source) VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (f'seed-{digest[:12]}-{number:03d}', state, record['at'], record['at'], str(record.get('outcome')),
                                record.get('seconds'), f"{record.get('seeded_from', 'seed')}#call{record.get('session_call', record.get('call'))}"))
        connection.execute('COMMIT')
    except BaseException:
        connection.close()
        temporary.unlink(missing_ok=True)
        raise
    connection.close()
    try:
        _publish_if_absent(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return status(path)


def _publish_if_absent(temporary, path):
    """Atomically create ``path`` from ``temporary`` only if ``path`` does not exist.

    A hard link is created-if-absent by the file system itself (NTFS and POSIX): it fails with
    FileExistsError when the name exists, even if another initializer published a moment ago. Unlike
    os.replace it can never overwrite. Volumes without hard links are refused rather than risk an overwrite.
    """
    try:
        os.link(temporary, path)
    except FileExistsError:
        raise LedgerError(f'{path} appeared during initialization; the existing ledger was kept and nothing was overwritten.') from None
    except OSError as error:
        raise LedgerError(f'Cannot publish the ledger atomically on this volume ({type(error).__name__}); nothing was written.') from None


class CallLedger:
    """One open ledger. Each process uses its own instance; SQLite serializes them."""

    def __init__(self, path, *, authorized, experiment=None, experiment_cap=None, lock_experiment=False):
        self.path = Path(path)
        if not self.path.is_file():
            raise LedgerError(f'Call ledger {self.path} does not exist; it is never created implicitly.')
        if (experiment is None) != (experiment_cap is None):
            raise LedgerError('An experiment name and its cap must be given together.')
        if lock_experiment and experiment is None:
            raise LedgerError('Locking a ledger to an experiment needs the experiment name and cap.')
        self.instance = uuid.uuid4().hex
        self.experiment = experiment
        try:
            self.connection = _connect(self.path)
        except sqlite3.Error as error:
            raise LedgerError(f'The ledger cannot be opened: {type(error).__name__}.') from None
        try:
            meta = self._verify()
        except LedgerError:
            self.connection.close()
            raise
        if int(meta['authorized']) != int(authorized):
            self.connection.close()
            raise LedgerError(f"The ledger authorizes {meta['authorized']} calls, not {authorized}; the authorization is never changed here.")
        self.authorized = int(meta['authorized'])
        if experiment is not None:
            import ab_profile
            owner = ab_profile.allocation_owner(experiment)
            problems = []
            unapproved = ab_profile.unapproved_experiment(meta.get('seed_sha256'), experiment)
            if unapproved:
                problems.append(unapproved)
            if owner is not None:
                profile = ab_profile.PROFILES[owner]
                problems = ab_profile.identity_errors(profile, self.path, meta)
                if int(experiment_cap) != profile['experiment_cap']:
                    problems.append(f"Its cap is {profile['experiment_cap']}, not {experiment_cap}.")
            if f'closed:{experiment}' in meta:
                problems.append(f'The {experiment!r} allocation was closed on {meta[f"closed:{experiment}"]}; it is never reopened.')
            if problems:
                self.connection.close()
                raise LedgerError(f'Allocation {experiment!r} refused: ' + ' '.join(problems))
        locked = meta.get('locked_experiment')
        if locked is not None and experiment != locked:
            self.connection.close()
            raise LedgerError(f'This ledger is locked to experiment {locked!r}; it cannot be opened '
                              f'{"without an experiment" if experiment is None else f"as {experiment!r}"}. No call is made.')
        if experiment is not None:
            try:
                self._register_experiment(experiment, int(experiment_cap), lock_experiment)
            except LedgerError:
                self.connection.close()
                raise

    def _verify(self):
        try:
            if self.connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise LedgerError('The ledger failed its integrity check.')
            meta = dict(self.connection.execute('SELECT key, value FROM meta'))
            if meta.get('schema_version') != SCHEMA_VERSION:
                raise LedgerError('Unknown ledger schema.')
            states = {row[0] for row in self.connection.execute('SELECT DISTINCT state FROM calls')}
            if not states <= set(STATES):
                raise LedgerError('The ledger contains an unknown call state.')
            total = self.connection.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
        except sqlite3.Error as error:
            raise LedgerError(f'The ledger cannot be read: {type(error).__name__}.') from None
        if total < int(meta['high_water']) or total < int(meta['seed_records']):
            raise LedgerError('The ledger has fewer records than it has held before; refusing (possible reset or rollback).')
        return meta

    def _register_experiment(self, name, cap, lock=False):
        try:
            self.connection.execute('BEGIN IMMEDIATE')
            locked = self.connection.execute("SELECT value FROM meta WHERE key = 'locked_experiment'").fetchone()
            if locked is not None and locked[0] != name:
                self.connection.execute('ROLLBACK')
                raise LedgerError(f'This ledger is locked to experiment {locked[0]!r}; {name!r} is refused.')
            closed = {key[len('closed:'):] for (key,) in self.connection.execute("SELECT key FROM meta WHERE key LIKE 'closed:%'")}
            other = next((row[0] for row in self.connection.execute('SELECT name FROM caps WHERE name != ?', (name,))
                          if row[0] not in closed), None)
            other = (other,) if other is not None else None
            if other is not None:
                self.connection.execute('ROLLBACK')
                raise LedgerError(f'This ledger already belongs to experiment {other[0]!r}; {name!r} is refused.')
            row = self.connection.execute('SELECT cap FROM caps WHERE name = ?', (name,)).fetchone()
            if row is None:
                self.connection.execute('INSERT INTO caps VALUES (?, ?)', (name, cap))
            elif row[0] != cap:
                self.connection.execute('ROLLBACK')
                raise LedgerError(f'Experiment {name!r} already has a cap of {row[0]}; it is never changed.')
            if locked is None:
                # Registering a capped experiment ALWAYS locks the ledger to it (the ``lock`` flag is kept for callers
                # that state it explicitly): from now on every process must open this ledger as this experiment,
                # so omitting or renaming the experiment can never escape its cap. There is no unlock operation.
                self.connection.execute("INSERT INTO meta VALUES ('locked_experiment', ?)", (name,))
            self.connection.execute('COMMIT')
        except sqlite3.Error as error:
            self._rollback()
            raise LedgerError(f'Could not register the experiment cap: {type(error).__name__}.') from None

    def _rollback(self):
        try:
            self.connection.execute('ROLLBACK')
        except sqlite3.Error:
            pass

    def reserve(self):
        """Atomically check both caps and record a reservation. Returns its unique ID."""
        call_id = uuid.uuid4().hex
        try:
            self.connection.execute('BEGIN IMMEDIATE')  # cross-process write lock: count and insert are one step
            meta = self._verify()
            # Re-read inside the transaction: another process may have locked the ledger after this one opened it.
            if meta.get('locked_experiment') is not None and self.experiment != meta['locked_experiment']:
                self.connection.execute('ROLLBACK')
                raise LedgerError(f"Ledger is locked to experiment {meta['locked_experiment']!r}; no call made.")
            if self.experiment is not None and f'closed:{self.experiment}' in meta:
                self.connection.execute('ROLLBACK')
                raise LedgerError(f'The {self.experiment!r} allocation is closed; no call made.')
            total = self.connection.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
            if total >= self.authorized:
                self.connection.execute('ROLLBACK')
                raise LedgerError(f'Cumulative authorized cap of {self.authorized} calls reached; no call made.')
            if self.experiment is not None:
                cap = self.connection.execute('SELECT cap FROM caps WHERE name = ?', (self.experiment,)).fetchone()[0]
                used = self.connection.execute('SELECT COUNT(*) FROM calls WHERE experiment = ?', (self.experiment,)).fetchone()[0]
                if used >= cap:
                    self.connection.execute('ROLLBACK')
                    raise LedgerError(f'Experiment cap of {cap} calls for {self.experiment!r} reached; no call made.')
            self.connection.execute('INSERT INTO calls (id, state, experiment, instance, pid, reserved_at) VALUES (?, ?, ?, ?, ?, ?)',
                                    (call_id, 'reserved', self.experiment, self.instance, os.getpid(), time.strftime('%Y-%m-%dT%H:%M:%S')))
            self.connection.execute("UPDATE meta SET value = CAST(MAX(CAST(value AS INTEGER), ?) AS TEXT) WHERE key = 'high_water'", (total + 1,))
            self.connection.execute('COMMIT')
        except LedgerError:
            self._rollback()
            raise
        except sqlite3.Error as error:
            self._rollback()
            raise LedgerError(f'Could not record the reservation: {type(error).__name__}; no call made.') from None
        return call_id

    def finish(self, call_id, state, *, outcome=None, seconds=None):
        if state not in ('completed', 'failed', 'unresolved'):
            raise ValueError('state must be completed, failed or unresolved')
        try:
            self.connection.execute('BEGIN IMMEDIATE')
            changed = self.connection.execute(
                'UPDATE calls SET state = ?, finished_at = ?, outcome = ?, seconds = ? WHERE id = ? AND state = ? AND instance = ?',
                (state, time.strftime('%Y-%m-%dT%H:%M:%S'), outcome, seconds, call_id, 'reserved', self.instance)).rowcount
            self.connection.execute('COMMIT')
        except sqlite3.Error as error:
            self._rollback()
            raise LedgerError(f'Could not finish reservation {call_id}: {type(error).__name__}.') from None
        if changed != 1:
            raise LedgerError(f'Reservation {call_id} is not an open reservation of this process.')

    def usage(self):
        self._verify()
        rows = self.connection.execute('SELECT state, instance, experiment FROM calls').fetchall()
        counts = {state: 0 for state in STATES}
        for state, instance, _experiment in rows:
            # A reservation left open by another (or a crashed) process is unresolved: it still counts.
            counts['unresolved' if state == 'reserved' and instance != self.instance else state] += 1
        out = {'authorized': self.authorized, 'used': len(rows), 'remaining': max(0, self.authorized - len(rows)),
               'states': counts, 'ledger': str(self.path)}
        if self.experiment is not None:
            cap = self.connection.execute('SELECT cap FROM caps WHERE name = ?', (self.experiment,)).fetchone()[0]
            used = sum(1 for _s, _i, e in rows if e == self.experiment)
            out['experiment'] = {'name': self.experiment, 'cap': cap, 'used': used, 'remaining': max(0, cap - used)}
            out['remaining'] = min(out['remaining'], out['experiment']['remaining'])
        return out

    def close(self):
        self.connection.close()


def close_experiment(path, *, authorized, experiment):
    """End an experiment's allocation for good (an explicit owner action; nothing calls this automatically).

    Its calls stay counted. The ledger lock is released so the calls the allocation did not use remain
    available for a separately approved purpose; the closed allocation can never be registered, reopened or
    spent again. Refuses an unknown experiment or a ledger locked to another one.
    """
    connection = _connect(Path(path))
    try:
        connection.execute('BEGIN IMMEDIATE')
        meta = dict(connection.execute('SELECT key, value FROM meta'))
        if int(meta['authorized']) != int(authorized):
            raise LedgerError(f"The ledger authorizes {meta['authorized']} calls, not {authorized}.")
        if connection.execute('SELECT 1 FROM caps WHERE name = ?', (experiment,)).fetchone() is None:
            raise LedgerError(f'No allocation named {experiment!r} exists in this ledger.')
        if meta.get('locked_experiment') not in (None, experiment):
            raise LedgerError(f"The ledger is locked to {meta['locked_experiment']!r}, not {experiment!r}.")
        if f'closed:{experiment}' in meta:
            raise LedgerError(f'{experiment!r} is already closed.')
        connection.execute('INSERT INTO meta VALUES (?, ?)', (f'closed:{experiment}', time.strftime('%Y-%m-%dT%H:%M:%S')))
        connection.execute("DELETE FROM meta WHERE key = 'locked_experiment'")
        connection.execute('COMMIT')
    except BaseException:
        try:
            connection.execute('ROLLBACK')
        except sqlite3.Error:
            pass
        raise
    finally:
        connection.close()
    return status(path)


def status(path):
    """Read-only summary: counts by state, authorization, caps, seed provenance."""
    path = Path(path)
    if not path.is_file():
        raise LedgerError(f'{path} does not exist.')
    connection = sqlite3.connect(f'file:{path.resolve().as_posix()}?mode=ro', uri=True)
    try:
        meta = dict(connection.execute('SELECT key, value FROM meta'))
        states = dict(connection.execute('SELECT state, COUNT(*) FROM calls GROUP BY state'))
        total = connection.execute('SELECT COUNT(*) FROM calls').fetchone()[0]
        caps = dict(connection.execute('SELECT name, cap FROM caps'))
        connection_counts = connection.execute('SELECT experiment, COUNT(*) FROM calls WHERE experiment IS NOT NULL GROUP BY experiment').fetchall()
        integrity = connection.execute('PRAGMA integrity_check').fetchone()[0]
    finally:
        connection.close()
    return {'ledger': str(path), 'integrity': integrity, 'authorized': int(meta['authorized']), 'used': total,
            'remaining': int(meta['authorized']) - total, 'states': states, 'experiment_caps': caps,
            'seed_records': int(meta['seed_records']), 'seed_sha256': meta['seed_sha256'], 'high_water': int(meta['high_water']),
            'locked_experiment': meta.get('locked_experiment'), 'created_at': meta.get('created_at'),
            'closed_experiments': sorted(key[len('closed:'):] for key in meta if key.startswith('closed:')),
            'experiment_used': dict(connection_counts)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    create = sub.add_parser('init')
    create.add_argument('--ledger', type=Path, required=True)
    create.add_argument('--authorized', type=int, required=True)
    create.add_argument('--seed', type=Path, required=True)
    show = sub.add_parser('status')
    show.add_argument('--ledger', type=Path, required=True)
    close = sub.add_parser('close-experiment', help='End an allocation for good and unlock the ledger (explicit owner action).')
    close.add_argument('--ledger', type=Path, required=True)
    close.add_argument('--authorized', type=int, required=True)
    close.add_argument('--experiment', required=True)
    args = parser.parse_args(argv)
    if args.command == 'init':
        result = init(args.ledger, authorized=args.authorized, seed=args.seed)
    elif args.command == 'close-experiment':
        result = close_experiment(args.ledger, authorized=args.authorized, experiment=args.experiment)
    else:
        result = status(args.ledger)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
