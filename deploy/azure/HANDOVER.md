# Hosted research preview: handover (26 Nov 2026, updated after the frontend deploy)

| | |
|---|---|
| Website | https://kpmg-proofline.mexicocentral.cloudapp.azure.com (user `reviewer`) |
| Password | on the VM: `sudo grep ^KPMG_REVIEW_PASSWORD= /etc/kpmg/preview.env` |
| Deployed commit | `f950d96` on `deploy/azure-vm` (= `integration/kpmg-blue-azure`), deployed 26 Nov 2026 20:35 UTC; staged context `f950d96-1dh66xl0-ready` |
| Frontend | Approved KPMG-blue research-publication UI (Answer / Sources / Evidence views, research notes, KPMG logo, bundled Inter and Source Serif 4 under OFL 1.1) |
| Engine | S2 consolidated-v2 Standard, B1 paper balance off (`RESEARCH_ENGINE=s2`, `S2_PAPER_BALANCE=0`) |
| Mode | real: exact demo-100 index (7,667 records, `parents.jsonl` SHA-256 `78d8efd7…`) and Gemini `gemini-3.1-flash-lite` |
| VM | `kpmg-preview`, Mexico Central, Standard_B2als_v2 (2 vCPU, 4 GiB), Ubuntu 24.04 |
| Fallback | `deploy/render-native` at `9e53008` (Render) |

`f950d96` = `edc3e43` (backend, unchanged) + the approved frontend (`b89536b`, `9b98c6a`, merged in `1356f1c`) + hosted wiring for the logo and fonts (`f950d96`: `onboarding/frontend`, `assets.json`, `stage.py`, `server.py` allowlist).

`edc3e43` = `9a85c92` (Azure VM scripts) + sanitized provider-failure logging (`b7b4d52`) + installer
re-staging fix (`9302af8`) + calibrated budget reservations (`8d3b026`) + bounded retry of Gemini 5xx errors
(`edc3e43`). Frozen engine files are unchanged; `seal_s3.py` and `seal_v3.py` both print `verified`.

## Fixes after the first browser test (26 Nov, 12:58 PM Central)

1. **Local budget.** "How accurately do LLMs answer financial analysis questions on SEC filings…" failed at the
   review stage with `provider-failure stage=local_budget`. Reservations were 2 tokens per request byte (about 7×
   real usage), so drafting + review reserved 162,122 against the 160,000 minute budget and the review call was
   refused locally. Now one token per 2 bytes plus 8,192 for the reply (still about 1.8× real input): 54,866 for
   the same question. All limits are unchanged.
2. **Gemini server errors.** The retest then hit `ServerError 503 UNAVAILABLE` from Gemini, and the client made
   exactly one attempt. Provider 5xx responses are now retried at most twice (after 2 s and 6 s); every attempt is
   reserved in the ledger first. 4xx (including 429 quota), timeouts, finish-reason, parsing and schema failures
   are never retried; validation is unchanged. Verified: the same question then answered (5 verbatim-cited
   findings, one interpretation withheld by the G4/G5 gate) after Gemini returned 500 and 504 on two attempts.

## Frontend deploy (26 Nov 2026, `f950d96`)

Installed with the procedure below; no Gemini calls. Verified afterwards: `preview.env` byte-identical (real mode, S2,
`S2_PAPER_BALANCE=0`, dedicated free key), briefs 8 / versions 8 / reviews 1 and quota ledger 15 attempts unchanged,
SQLite integrity ok, both seals `verified`; over public HTTPS the new UI, `kpmg-logo-white.png` and all
`/fonts/*.woff2` serve (licence texts and `mock-api.js` are not served); saved Fin-RATE and CU-DPO briefs render with
mapped citations, the Table 2 chart and source cells, research notes and the library. Restart ready in 22 s.
Rollback to `edc3e43` and roll-forward to `f950d96` were rehearsed (about 30 s each, data unchanged).

Pre-deploy backups on the VM: `/etc/kpmg/preview.env.bak-pre-f950d96-20261126T203400Z` and
`/var/lib/kpmg/backups/{briefs,provider-usage,gemini-smoke-attempts}-pre-f950d96-20261126T203400Z.sqlite3` (0600).

### Rollback checkpoints

| Commit | What it is |
|---|---|
| `f950d96` | Current: approved frontend on the `edc3e43` backend |
| `edc3e43` | Previous deployment: budget calibration and Gemini 5xx retries, original consultant UI |
| `9302af8` / `9a85c92` | Earlier VM installs (see Roll back for the `context.txt` note before `9302af8`) |

## Verified on the hosted server

- HTTPS (Let's Encrypt, auto-renewed by Caddy), HTTP → HTTPS redirect, Basic auth, exact Host and same-Origin
  checks, cross-site requests refused, port 8821 closed to the internet, firewall 22/80/443 only, SSH keys only.
- Live S2 answer to the known CU-DPO question: correct lead finding (35–46% → 68–78% across seven base models),
  verbatim citations to the retrieved passages and Table 2 rows, two unsupported draft claims withheld by the P4
  gate, human review pending. Audited Table 2 (16 rows, complete) served for the chart. Saved brief reopens
  identically.
- Latency 32.6 s for CU-DPO (retrieval 5.6, drafting 2.7, review 23.9). Memory about 840–950 MiB at work, 1.36 GiB peak, of the 3 GiB service limit.
- S2 default, saved data and security checks persist across service restarts and full VM reboots (site healthy
  about 50 s after a reboot). The data disk mounts by UUID; device names can change between boots.

## Operate

All on the VM (`ssh -i kpmg-preview_key.pem azureuser@kpmg-proofline.mexicocentral.cloudapp.azure.com`).

| Task | Command |
|---|---|
| Status | `systemctl status kpmg-preview caddy` |
| Logs | `sudo journalctl -u kpmg-preview -f` (provider problems appear as `provider-failure stage=… error=…`) |
| Restart | `sudo systemctl restart kpmg-preview` (ready in about 21 s for S2; check the log for `Research preview ready`) |
| Health | `curl -s https://kpmg-proofline.mexicocentral.cloudapp.azure.com/healthz` → `{"status": "ready"}` |
| Settings | `sudoedit /etc/kpmg/preview.env`, then restart |
| Pause billing | Portal → VM → **Stop** (deallocates; disks and public IP still billed). **Start** brings the site back. |

## Known limitations

- **Generation limits.** Each S2 question is two Gemini calls reserving about 50–60k of the 160k-per-minute
  budget, and at most 6 calls per minute and 60 per rolling 24 hours are allowed (retries count). That is about
  3 questions a minute and up to 30 a day. When a limit is reached the page shows "Summary failed … retry";
  `journalctl` shows `provider-failure stage=local_budget`.
- **Latency depends on Gemini.** Normally about 20–35 s per S2 answer (the first question after a restart adds
  about 10 s of retrieval warm-up). While Gemini is degraded, retries can stretch one answer to about 3 minutes
  (observed 26 Nov, 19:06 UTC: 500 and 504 before success). If all three attempts fail, the page shows the same
  retry message; re-asking in the same browser session resumes from the saved stages.
- One early S2 drafting failure (26 Nov, 09:31) predates the logging; its cause is unconfirmed.
- Answers are research findings with human review pending; business and regulatory analysis is disabled.
- A single shared `reviewer` login. Research results are auto-saved to the library; briefs can be archived,
  not deleted (versions and reviews are append-only). The four synthetic hosting-test briefs are archived.
- The Gemini key must stay a dedicated free-tier Developer API key (`KPMG_GEMINI_DEDICATED_FREE=true`).
- Auto-shutdown (if enabled in the portal) takes the site offline at the scheduled time.
- Each code update stages a new context of about 235 MB under
  `experiments/render-staging/image-context-onboarding/`; older ones can be removed when the disk fills.

## Roll back

| To | Steps |
|---|---|
| Baseline engine | In `/etc/kpmg/preview.env` set `RESEARCH_ENGINE=baseline`, keep `S2_PAPER_BALANCE=0`; restart. The previous settings file is saved as `/etc/kpmg/preview.env.bak-baseline-default`. |
| Synthetic fixture (no Gemini) | Set `KPMG_DEPLOY_MODE=fixture`; restart. |
| Previous UI (`edc3e43`) or earlier code | `cd /opt/kpmg/app && sudo -u kpmg git fetch && sudo -u kpmg git checkout <commit>`, then `sudo rm -f .kpmg-onboarding/context.txt` (required for commits before `9302af8`), then re-run the installer: `sudo KPMG_DOMAIN=kpmg-proofline.mexicocentral.cloudapp.azure.com KPMG_DATA_DEVICE=/dev/disk/azure/scsi1/lun0 bash deploy/azure/install.sh`. Settings, password and data are kept. |
| Render | Follow `deploy/render/DEPLOYMENT-READINESS.md` on `deploy/render-native`. |

The installer keeps `/etc/kpmg/preview.env`, the password and everything on the data disk; it re-verifies the
index hashes on the next start.
