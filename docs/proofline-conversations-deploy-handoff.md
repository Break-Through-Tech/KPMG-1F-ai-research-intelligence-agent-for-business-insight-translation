# Deployment handoff: Proofline conversations (for desktop Codex)

## 1. What to deploy
- **Branch:** `khoi/proofline-conversations`. Deploy the branch head; the code commit is `1125a99`, and this
  handoff is the only commit after it.
- **Fast-forward:** the branch descends from production `25b53af`, so `deploy/azure-vm` can move forward to it
  without a force-push. **Not yet merged into `main`.** PR review and merging are handled separately.

## 2. Changes since production `25b53af`
| Commit | Change |
|---|---|
| `fec3155`, `96023bb` | Desktop polish: unified research typography and refined gradients (UI only) |
| `061591a` | Persistent conversations: ordered research turns, follow-up resolution, migration, sidebar history with Rename, Archive and Delete (soft delete), and the "Interpreted as …" line |
| `1426b7e` | History menu uses the light surface; the rename field selects its text |
| `1125a99` | Follow-ups inherit the previous turn's verified business context when the semantic classifier is unavailable |

**Unchanged:**
- Standard S2 (sealed engine, prompts and schemas; both seals `verified`).
- The query-clarification prompt.
- Hydrogen v1.2 and the Muse Wonder fallback.
- Semantic intent recognition.
- The evidence handoff, research contracts and the brief-store protection triggers.

**How follow-ups work:**
- A follow-up that refers back to earlier turns is resolved into one standalone question. That costs at most one
  Flash-Lite call, with no retry, on the classifier's ledger (`intent-usage.sqlite3`).
- S2 researches only that standalone question. Earlier answers are never used as evidence; each turn keeps its
  own retrieval, citations and business insight.
- Ambiguous follow-ups, or ones the resolver fails on, get a clarification question and no research.

## 3. Tests completed
- **Offline suite:** 186 passed, 262 subtests, including 20 conversation tests and 9 subtests. Covered:
  - migration, reopening and ordering;
  - history never carrying evidence;
  - resolution, topic change, ambiguous and failed resolution;
  - soft delete and the protection triggers;
  - deletion during a running request;
  - business refusal on deleted conversations;
  - inheritance rules: confirmed continuity only, no inheritance on topic change, research-only, ambiguous
    questions, a usable classifier verdict or an older turn, and tamper rejection;
  - provenance.
- **Known flake:** one intermittent Windows socket reset (WinError 10053) on HTTP tests in combined runs. It
  passes in isolation, and nothing in that code changed.
- **Browser smoke**, real demo-100 index, scripted providers:
  - **Default mode:** conversation continuity, clarification, rename, reopen, delete, and a deletion that
    persists across a server restart.
  - **Business mode:** the previous flows plus inherited business context on a follow-up, recorded as
    `context_provenance.source = inherited`.
- **Hosted-fixture gate:** baseline and S2 both pass.
- **Live check on `1426b7e`** (15 Flash-Lite calls, local):
  - the business question, then "What about the risks?" resolved to insurance claims risks;
  - an ambiguous follow-up got a clarification;
  - a topic change was researched as asked, sharing no evidence with earlier turns;
  - the conversation persisted.

  The inheritance fix was made after that run: its trigger was a classifier timeout in the risks follow-up.
- **Visual review:** the history menu and the rename and delete dialogs match the polished UI (screenshots
  were taken locally).

## 4. Remaining limitations
- **Inheritance not tested live:** verified offline and in the browser with scripted providers only.
- **Resolution heuristic:** questions of six words or fewer always make a resolution call.
- **Pending clarifications** are held in memory and lost on restart; the user asks again.
- **Soft delete only:** the data stays in the database and VM backups, and the dialog discloses this.
  Archived conversations have no restore view yet; their answers remain in the Library.
- **Evidence browser tests** (`ui-consult/tests/evidence.test.html`) need recorded fixtures that are not in
  the repo.
- **Shared quota:** on Flash-Lite 503 outages, the research engine's existing two retries can consume quota
  quickly.

## 5. Conversation database migration
- **Automatic and idempotent:** the migration runs at service start (`build_handler` →
  `ConversationStore.migrate()`). It adds `conversations` and `conversation_turns` to
  `/var/lib/kpmg/briefs.sqlite3` with `CREATE IF NOT EXISTS`. `PRAGMA user_version` stays 1.
- **Existing data:** each existing brief becomes a one-turn conversation with id `c<brief_id>`. No existing row
  is changed or deleted.
- **Expected after start:** the number of conversations equals the number of briefs (29 before this deploy,
  plus any added since), and every one has `turn_count = 1`.
- **Back up `briefs.sqlite3` before deploying** (section 6). There is no down-migration; older releases ignore
  the new tables.

## 6. Azure deployment and verification
VM `kpmg-preview`, URL https://kpmg-proofline.mexicocentral.cloudapp.azure.com (user `reviewer`; the password
is unchanged, in `/etc/kpmg/preview.env`). **No new environment variables are required.**

**1. Back up** (`T=$(date -u +%Y%m%dT%H%M%SZ)`):
- `sudo cp -p /etc/kpmg/preview.env /etc/kpmg/preview.env.bak-pre-conversations-$T`.
- Online SQLite `.backup` copies (as the `kpmg` user) of `briefs`, `provider-usage`, `intent-usage`,
  `muse-spend` and `gemini-smoke-attempts` (`.sqlite3`) into `/var/lib/kpmg/backups/*-pre-conversations-$T.sqlite3`,
  with mode 0600 and `pragma integrity_check` = ok.
- Record the brief, version and review counts.

**2. Fast-forward** `deploy/azure-vm` to the branch head, with no force-push.

**3. Install:**
```
cd /opt/kpmg/app && sudo -u kpmg git fetch -q origin && sudo -u kpmg git checkout <head>
sudo KPMG_DOMAIN=kpmg-proofline.mexicocentral.cloudapp.azure.com KPMG_DATA_DEVICE=/dev/disk/azure/scsi1/lun0 bash deploy/azure/install.sh
```
Expect about 25 s of downtime. The log should show `Research preview ready` and `business-fallback enabled`.

**4. Verify without model calls:**
- the running commit; HTTPS returns 401 without credentials;
- `/api/config` reports `live: true` and 7,667 records (`78d8efd7`);
- both seals print `verified`;
- the brief, version and review counts are unchanged;
- `GET /api/conversations` lists the migrated conversations;
- an existing saved answer reopens from the history sidebar with its citations;
- the ⋯ menu shows Rename, Archive and Delete from history.

**5. Minimal live check** (budget about 8 Flash-Lite calls; avoid Hydrogen and Muse by not triggering business
generation):
- a business question, then "What about the risks?". Expect "Interpreted as …", the same conversation and
  position 2;
- an ambiguous "What about that one?". Expect a clarification and no research.

## 7. Existing configuration and rollback
- **Configuration** in `/etc/kpmg/preview.env` (unchanged):
  - `KPMG_DEPLOY_MODE=real`, `RESEARCH_ENGINE=s2`, `S2_PAPER_BALANCE=0`, `KPMG_GEMINI_DEDICATED_FREE=true`;
  - `BUSINESS_TRANSLATION_ENABLED=1`, `BUSINESS_FALLBACK_ENABLED=1`, `MUSE_DAILY_CAP_USD=5`;
  - `GOOGLE_API_KEY`, `BUSINESS_TRANSLATION_API_KEY`, `META_MODEL_API_KEY`, `KPMG_REVIEW_PASSWORD`.

  The file is `root:kpmg 0640`.
- **Ledgers:**
  - research: `/var/lib/kpmg/provider-usage.sqlite3`;
  - classifier and follow-up resolution: `intent-usage.sqlite3` (6 per minute, 60 per day; the two now share
    it);
  - Muse spending: `muse-spend.sqlite3`.
- **Roll back to `25b53af`:**
  1. `sudo -u kpmg git -C /opt/kpmg/app checkout 25b53af`.
  2. Restore the `preview.env` backup.
  3. Re-run `install.sh` with the same variables.

  `25b53af` ignores the conversation tables. **Caveat:** briefs from conversations soft-deleted on the new
  release will reappear as individual briefs in the old library, because the old list does not filter them.
  Restore the `briefs-pre-conversations-*` backup if that matters.
- **Data restore** (only if damaged): stop the service, copy the `*-pre-conversations-*` backups into
  `/var/lib/kpmg/`, then start it.
- **Older checkpoints** on the VM: `*-pre-25b53af-*`, `*-pre-2309de9-*`, `*-pre-7d762c8-*`.
