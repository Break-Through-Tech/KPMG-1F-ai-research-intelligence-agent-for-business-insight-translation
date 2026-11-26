"""Approved authorizations and execution profiles (``live_backend.py --profile``).

There is ONE authoritative ledger for the approved 40-call authorization. It is identified by all of:
its canonical path, the SHA-256 of the seed it was created from (the 20 recorded attempts), and the
``created_at`` stamp written when it was created. The 14-call ``ab-agentic-1`` allocation lives in that
same ledger, so the overall cap and the allocation are enforced in one transaction.

Supported paths fail closed:
- ``call_ledger.init`` refuses the approved seed (its ledger already exists): no second ledger.
- ``CallLedger`` refuses to register or use the ``ab-agentic-1`` allocation in any ledger whose path or
  identity is not the canonical one.
- ``--profile ab-agentic-1`` refuses any other ledger path, a missing or different identity, and any
  flag that differs from the profile.

Trust boundary: this is a local file. Someone who copies the file elsewhere AND edits this module (or
the ledger code) can create another allocation; no purely local mechanism can prevent that. What is
guaranteed is that every supported application path refuses it.
"""
import os
from pathlib import Path

CANONICAL_LEDGER = Path(r'D:\KPMG-demo-corpus\table-endpoint-exp\codex-authorization-40.ledger.sqlite3')

AUTHORIZATIONS = {
    'codex-laptop-40': {
        'ledger_path': CANONICAL_LEDGER,
        'authorized': 40,
        # SHA-256 of codex-authorization-40.ledger.jsonl, the 20 recorded attempts the ledger was created from.
        'seed_sha256': '4bdef6d010a4f0070bcea0f43232dcb31b60b8af79cd02ded19f142a3dc051cc',
        'created_at': '2026-11-18T20:49:37',
        # The only experiment allocations this authorization may hold. A new, separately approved purpose is added
        # here deliberately; lookalike names ("AB-AGENTIC-1") are refused by the ledger and the launcher.
        'experiments': ('ab-agentic-1',),
    },
}

PROFILES = {
    'ab-agentic-1': {
        'authorization': 'codex-laptop-40',
        'experiment': 'ab-agentic-1',
        'experiment_cap': 14,
        'authorized': 40,
        'seed_sha256': AUTHORIZATIONS['codex-laptop-40']['seed_sha256'],
        'ledger_path': CANONICAL_LEDGER,
        'created_at': AUTHORIZATIONS['codex-laptop-40']['created_at'],
        # The initial A/B run compares research answers only: no industry, no business translation, no risk step.
        'research_only': True,
    },
}


def same_path(a, b):
    return os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))


def approved_seed(seed_sha256):
    """The authorization a seed belongs to, if any."""
    return next((name for name, a in AUTHORIZATIONS.items() if a['seed_sha256'] == seed_sha256), None)


def unapproved_experiment(seed_sha256, experiment):
    """An error message if ``experiment`` is not approved for the authorization this ledger belongs to, else None."""
    authorization = approved_seed(seed_sha256)
    if authorization is None or experiment is None:
        return None
    approved = AUTHORIZATIONS[authorization].get('experiments', ())
    if experiment not in approved:
        return (f'Experiment {experiment!r} is not approved for authorization {authorization!r} '
                f'(approved: {", ".join(approved) or "none"}).')
    return None


def allocation_owner(experiment):
    """The profile an experiment name belongs to, if any."""
    return next((name for name, p in PROFILES.items() if p['experiment'] == experiment), None)


def identity_errors(profile, ledger_path, meta):
    """Why ``ledger_path`` with metadata ``meta`` is not the profile's canonical ledger (empty = it is)."""
    errors = []
    if not same_path(ledger_path, profile['ledger_path']):
        errors.append(f"Only the canonical ledger {profile['ledger_path']} carries this allocation (got {ledger_path}).")
    if meta.get('seed_sha256') != profile['seed_sha256']:
        errors.append('This is not the approved authorization ledger (its seed does not match).')
    if not meta.get('created_at'):
        errors.append('The ledger has no identity (created_at missing).')
    elif meta.get('created_at') != profile['created_at']:
        errors.append('The ledger identity does not match the approved ledger (different creation).')
    return errors


def profile_errors(name, *, ledger, authorized, experiment, experiment_cap):
    """Return the reasons a launch does not match the named profile (empty list = matches). Read-only."""
    profile = PROFILES.get(name)
    if profile is None:
        return [f'Unknown profile {name!r}.']
    errors = []
    if ledger is None:
        errors.append('--call-ledger is required for this profile.')
    if authorized != profile['authorized']:
        errors.append(f"--authorized-calls must be {profile['authorized']} for this profile (got {authorized}).")
    if experiment != profile['experiment']:
        errors.append(f"--experiment must be exactly {profile['experiment']!r} for this profile (got {experiment!r}).")
    if experiment_cap != profile['experiment_cap']:
        errors.append(f"--experiment-cap must be exactly {profile['experiment_cap']} for this profile (got {experiment_cap}).")
    if ledger is not None:
        import call_ledger
        try:
            status = call_ledger.status(Path(ledger))
        except Exception as error:
            return errors + [f'The ledger cannot be read: {error}']
        if status['integrity'] != 'ok':
            errors.append('The ledger failed its integrity check.')
        errors += identity_errors(profile, ledger, status)
        if status['authorized'] != profile['authorized']:
            errors.append(f"The ledger authorizes {status['authorized']} calls, not {profile['authorized']}.")
        recorded = status['experiment_caps'].get(profile['experiment'])
        if recorded is not None and recorded != profile['experiment_cap']:
            errors.append(f"The ledger already records a cap of {recorded} for {profile['experiment']!r}.")
        if profile['experiment'] in status.get('closed_experiments', []):
            errors.append(f"The {profile['experiment']!r} allocation is closed; it is never reopened.")
        if status['locked_experiment'] not in (None, profile['experiment']):
            errors.append(f"The ledger is locked to another experiment, {status['locked_experiment']!r}.")
    return errors
