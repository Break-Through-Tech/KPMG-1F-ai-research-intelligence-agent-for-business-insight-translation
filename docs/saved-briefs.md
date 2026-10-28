# Saved briefs: local SQLite library

The research desk automatically saves validated answer snapshots. Python's built-in
`sqlite3` is the only storage dependency: no database server, credentials, SQL
commands, or manual schema setup are required.

```sh
python -m src.research_demo                          # fixture examples; clearly labeled
python -m src.research_demo --result path/to/result.json
python -m src.research_demo --library /local/path/library.sqlite3
python -m src.research_demo --no-library             # disposable runs, no persistence
```

The existing `--paper`, `--index`, provider and model options are unchanged. Live
research still requires explicit provider selection; opening saved work never
calls a provider or retrieval. `--result` imports the existing result (and optional
presentation) at startup; identical startup imports are reused instead of duplicated.

## Team workflow

- Generate an answer normally. **Saved brief · Version 1** confirms the save.
  Fixture answers stay labeled synthetic; they are not live research.
- **Saved briefs** opens a searchable, paginated library. Open any answer without
  regeneration, including its retained evidence, locations, provenance and
  validated optional plain-language presentation.
- Expand the answer's **Saved brief** disclosure to rename or archive it, browse
  versions, record a review, or export a JSON snapshot.
- **Show archived briefs** finds archived work; **Restore brief** brings it back.
  There is no permanent-delete operation.
- **Import result JSON** accepts existing pending result files or exported
  response envelopes. Imported review decisions are **not** trusted or adopted.
- **Import a new version JSON** appends a validated snapshot to the current brief.
  Audience metadata can be supplied through the API; this feature does not add
  audience-specific generation.
- With live research configured, **Revise with new research** targets the next
  accepted answer at the selected brief. A visible banner identifies the target
  and offers cancellation. Edit the question to include the requested changes,
  then send it normally. This intentionally reruns retrieval/generation using the
  *current* configured source, not a replay of the old index. Selecting a revision
  starts a fresh research exchange, abandoning unrelated pending clarification;
  **New research conversation** cancels the revision target. Selection is ignored
  while a research request is running. Original snapshots
  remain untouched. Review notes are not silently injected into model prompts.
- Storage failures do not erase a successfully generated answer. An expanded save
  warning offers snapshot export or **Save as separate brief**, with no model
  retry. A stale revision target also leaves the answer available to save separately.

Each checkout defaults to `data/briefs/library.sqlite3`; the directory and SQLite
sidecars are Git-ignored. Local teammates have separate libraries. Exchange
snapshots using JSON export/import, not Git or a cloud-synced live database file.
This is a loopback-only app, not a multi-user authenticated team service. Reviewer
names are self-reported labels, not verified identities.

## Storage and review contract

Three tables are created automatically on startup (`PRAGMA user_version = 1`):

| Table | Responsibility |
| --- | --- |
| `briefs` | Title, original question, timestamps, archive flag, current version pointer |
| `brief_versions` | Immutable numbered snapshots, audience, entire response envelope JSON, SHA-256 fingerprint |
| `reviews` | Append-only decisions, reviewer, notes, exact version and snapshot fingerprint, canonical reviewed-result JSON |

A write transaction inserts both the version and current-version pointer or
neither. SQLite foreign keys keep versions and reviews attached to their owners.
Separate connections per operation support the threaded HTTP server. Competing
revision writers use `BEGIN IMMEDIATE` plus an expected-version check: only one
can advance the same head. Archived or historical versions cannot receive new
reviews or become a revision target. Old versions and their review histories stay
readable; approvals never carry into a new version.

Reviews reuse `research_review`'s full-content fingerprint and regulatory approval
gates. Loading verifies the stored snapshot hash and review/content association.
These are integrity checks, not proof that research claims are correct or sources
are certified. A review decision applies to the exact retained snapshot; optional
plain-language meaning review and source verification remain separate concerns.

The generated result JSON stays an immutable **pending draft**. Library decisions
live separately and are included in snapshot JSON exports; existing HTML/Markdown
exports retain their original pending-draft contract. Importing a snapshot strips
library IDs and reviews, so copied approval is never granted in the new library.

Schema versions newer than the app understands fail closed. Do not delete a
library to resolve a schema error. To back up without SQLite tooling, stop the app
and copy the database file; keep the backup private because it contains questions,
research outputs, evidence and reviewer notes. No retention policy deletes records.

## API

All routes inherit the desk's loopback Host/Origin/fetch-site boundary and no-store
responses. JSON mutations are bounded at 8 MB; none invoke a model.

| Method / route | Operation |
| --- | --- |
| `GET /api/briefs?q=...&archived=0&offset=0` | List 30 matching current briefs |
| `GET /api/briefs/{id}?version={version_id}` | Reopen exact snapshot; omit version for current |
| `POST /api/briefs` | Import `{result}` or `{envelope}`; optional title/audience |
| `POST /api/briefs` with `brief_id`, `expected_version` | Append an imported version |
| `POST /api/briefs/{id}` | Rename/archive/restore with `expected_version` |
| `POST /api/briefs/{id}/reviews` | Record `version_id`, `fingerprint`, reviewer, decision (`approve`, `revise`, `reject`), notes |

`revise` requires notes. Mutations on stale versions return 409. Research/demo
requests may include `library_revision: {brief_id, expected_version}`; the target
is checked before generation and again atomically at save time. If it changes
while generation is in progress, the accepted answer is returned with
`library_error`, without claiming it was saved.

## Verification

```sh
python -m pytest tests/test_brief_store.py tests/test_brief_library_http.py
python -m pytest
```

Tests cover restart persistence, immutable snapshots and append-only reviews,
transaction rollback, simultaneous revision writers, review/regulatory guards,
archive/restore, import, HTTP boundaries, and preserving accepted results when
storage fails. Offline fixtures and browser automation do not establish live model
quality, source certification, or VoiceOver acceptance.
