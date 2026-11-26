# Single Ubuntu VM on Azure

Runs the existing application unchanged: `deploy/render/build.sh` builds, `deploy/render/start.py`
starts, `server.py` serves the approved UI and API on one HTTPS origin. This folder adds only the
VM pieces: Python 3.11.9, a `kpmg` service account, the data disk at `/var/lib/kpmg` (SQLite and
the index), systemd autostart, Caddy HTTPS (Let's Encrypt) and the host firewall.
`deploy/render-native` remains the Render fallback.

## Create the VM (portal.azure.com)

1. **Virtual machines → Create → Azure virtual machine.**
2. **Basics:** subscription *Azure for Students*; resource group (new) `kpmg-preview-rg`; name
   `kpmg-preview`; region *East US* (or another region your subscription allows); availability
   *No infrastructure redundancy required*; image **Ubuntu Server 24.04 LTS – x64 Gen2**;
   size **Standard_B2als_v2** (2 vCPU, 4 GiB); authentication **SSH public key**, username
   `azureuser`, key *Generate new key pair*; inbound ports **SSH (22), HTTP (80), HTTPS (443)**.
3. **Disks:** OS disk *Standard SSD (LRS)*, *Delete with VM* on. **Create and attach a new disk:**
   *Standard SSD (LRS)*, **4 GiB**, LUN 0.
4. **Networking:** defaults (new virtual network, new public IP, basic NSG with the three ports);
   tick *Delete public IP and NIC when VM is deleted*.
5. **Management:** **Enable auto-shutdown** at a time that suits you. **Monitoring:** boot
   diagnostics *Disable*.
6. **Review + create → Create**, and download the private key.
7. VM **Overview → DNS name → Configure**: DNS name label, for example `kpmg-preview-kn` →
   **Save**. The site is `https://<label>.<region>.cloudapp.azure.com`.

## Install (on the VM)

    ssh -i kpmg-preview_key.pem azureuser@<label>.<region>.cloudapp.azure.com
    sudo git clone --branch deploy/azure-vm https://github.com/Break-Through-Tech/KPMG-1F-ai-research-intelligence-agent-for-business-insight-translation.git /opt/kpmg/app
    sudo KPMG_DOMAIN=<label>.<region>.cloudapp.azure.com KPMG_DATA_DEVICE=/dev/disk/azure/scsi1/lun0 bash /opt/kpmg/app/deploy/azure/install.sh
    sudo grep ^KPMG_REVIEW_PASSWORD= /etc/kpmg/preview.env

If `/dev/disk/azure/scsi1/lun0` is missing, `lsblk` shows the empty 4 GiB disk (for example
`/dev/sdc`). Open the site, sign in as `reviewer`, ask *What does the test fixture contain?*

## Load the real index (after clearance)

From the desktop folder that holds the three files:

    ssh -i kpmg-preview_key.pem azureuser@<fqdn> "mkdir -p ~/demo-100"
    scp -i kpmg-preview_key.pem parents.jsonl views.json vectors.npy azureuser@<fqdn>:~/demo-100/
    ssh -i kpmg-preview_key.pem azureuser@<fqdn> "sudo bash /opt/kpmg/app/deploy/azure/load-index.sh ~/demo-100 && rm -r ~/demo-100"

Then `sudoedit /etc/kpmg/preview.env`: `KPMG_DEPLOY_MODE=real`, `GOOGLE_API_KEY=…`,
`KPMG_GEMINI_DEDICATED_FREE=true`; then `sudo systemctl restart kpmg-preview` and
`sudo journalctl -u kpmg-preview -f`.

## Operate

| Task | Command |
|---|---|
| Logs | `sudo journalctl -u kpmg-preview -f` |
| Restart | `sudo systemctl restart kpmg-preview` |
| Engine | `RESEARCH_ENGINE=baseline` or `s2` in `/etc/kpmg/preview.env`, then restart |
| Update code | `sudo -u kpmg git -C /opt/kpmg/app fetch` and `sudo -u kpmg git -C /opt/kpmg/app checkout origin/deploy/azure-vm`, then re-run `install.sh` with the same variables (it re-stages real mode on the next start) |
| Roll back code | `sudo -u kpmg git -C /opt/kpmg/app checkout <commit>`, then re-run `install.sh` |
| Pause billing | Portal → VM → **Stop** (deallocates; disks and public IP still billed) |

Current deployment, limitations and rollback: [HANDOVER.md](HANDOVER.md).
