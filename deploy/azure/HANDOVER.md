# Hosted research preview: handover (26 Nov 2026)

| | |
|---|---|
| Website | https://kpmg-proofline.mexicocentral.cloudapp.azure.com (user `reviewer`) |
| Password | on the VM: `sudo grep ^KPMG_REVIEW_PASSWORD= /etc/kpmg/preview.env` |
| Deployed commit | `9302af8` on `deploy/azure-vm` (staged context `9302af8-q419u00z-ready`) |
| Engine | S2 consolidated-v2 Standard, B1 paper balance off (`RESEARCH_ENGINE=s2`, `S2_PAPER_BALANCE=0`) |
| Mode | real: exact demo-100 index (7,667 records, `parents.jsonl` SHA-256 `78d8efd7…`) and Gemini `gemini-3.1-flash-lite` |
| VM | `kpmg-preview`, Mexico Central, Standard_B2als_v2 (2 vCPU, 4 GiB), Ubuntu 24.04 |
| Fallback | `deploy/render-native` at `9e53008` (Render) |

`9302af8` = `9a85c92` (Azure VM scripts) + sanitized provider-failure logging (`b7b4d52`) + installer
re-staging fix. Frozen engine files are unchanged; `seal_s3.py` and `seal_v3.py` both print `verified`.

## Verified on the hosted server

- HTTPS (Let's Encrypt, auto-renewed by Caddy), HTTP → HTTPS redirect, Basic auth, exact Host and same-Origin
  checks, cross-site requests refused, port 8821 closed to the internet, firewall 22/80/443 only, SSH keys only.
- Live S2 answer to the known CU-DPO question: correct lead finding (35–46% → 68–78% across seven base models),
  verbatim citations to the retrieved passages and Table 2 rows, two unsupported draft claims withheld by the P4
  gate, human review pending. Audited Table 2 (16 rows, complete) served for the chart. Saved brief reopens
  identically.
- Latency 32.6 s (retrieval 5.6, drafting 2.7, review 23.9). Memory about 840–920 MiB of the 3 GiB service limit.
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

- **Pace S2 questions about a minute apart.** Each S2 question reserves about 130k of the local 160k-per-minute
  generation budget (the reservation is 2 × request bytes, about 8× the real token count). A second question
  inside the minute ends with "Summary failed … retry". Other limits: 6 calls per minute and 60 calls per
  rolling 24 hours, so about 30 S2 questions a day (7 synthetic-fixture reservations from 26 Nov count until
  about 08:50 VM time on 27 Nov).
- About 33 s per S2 answer, mostly the review stage.
- One early S2 drafting failure (26 Nov, 09:31) could not be reproduced in two later runs; its cause is
  unconfirmed. If it recurs, the `provider-failure` log line names the category.
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
| Earlier code | `cd /opt/kpmg/app && sudo -u kpmg git fetch && sudo -u kpmg git checkout <commit>`, then `sudo rm -f .kpmg-onboarding/context.txt` (required for commits before `9302af8`), then re-run the installer: `sudo KPMG_DOMAIN=kpmg-proofline.mexicocentral.cloudapp.azure.com KPMG_DATA_DEVICE=/dev/disk/azure/scsi1/lun0 bash deploy/azure/install.sh`. Settings, password and data are kept. |
| Render | Follow `deploy/render/DEPLOYMENT-READINESS.md` on `deploy/render-native`. |

The installer keeps `/etc/kpmg/preview.env`, the password and everything on the data disk; it re-verifies the
index hashes on the next start.
