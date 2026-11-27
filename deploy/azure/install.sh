#!/usr/bin/env bash
# One-time (and re-runnable) setup of the supervised research preview on one Ubuntu VM.
#
#   sudo KPMG_DOMAIN=<label>.<region>.cloudapp.azure.com \
#        KPMG_DATA_DEVICE=/dev/disk/azure/scsi1/lun0 \
#        bash /opt/kpmg/app/deploy/azure/install.sh
#
# Reuses deploy/render/build.sh and deploy/render/start.py unchanged. Adds only what a
# plain VM lacks: Python 3.11.9, a service account, the persistent data disk, systemd,
# Caddy for HTTPS and the host firewall. Re-running keeps the existing password and mode.
set -euo pipefail

APP=/opt/kpmg/app
VENV=/opt/kpmg/venv
STATE=/var/lib/kpmg
ENV_FILE=/etc/kpmg/preview.env
DOMAIN="${KPMG_DOMAIN:-}"
DEVICE="${KPMG_DATA_DEVICE:-}"

[ "$(id -u)" = 0 ] || { echo "Run with sudo." >&2; exit 2; }
[ -f "$APP/deploy/render/build.sh" ] || { echo "Clone the repository to $APP first." >&2; exit 2; }
if ! [[ "$DOMAIN" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ ]]; then
  echo "Set KPMG_DOMAIN to the VM's DNS name, e.g. kpmg-preview.eastus.cloudapp.azure.com." >&2
  exit 2
fi

echo "== Packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl ca-certificates gnupg ufw debian-keyring debian-archive-keyring apt-transport-https >/dev/null
if ! command -v caddy >/dev/null; then
  curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt -o /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq
  apt-get install -y -qq caddy >/dev/null
fi

echo "== Service account"
id kpmg >/dev/null 2>&1 || useradd --system --home-dir /opt/kpmg --shell /usr/sbin/nologin kpmg
chown -R kpmg:kpmg /opt/kpmg

echo "== Persistent data disk at $STATE"
mkdir -p "$STATE"
if [ -n "$DEVICE" ]; then
  [ -b "$DEVICE" ] || { echo "Data disk $DEVICE not found. Attach it in the portal." >&2; exit 2; }
  real="$(readlink -f "$DEVICE")"
  if ! blkid "$real" >/dev/null 2>&1; then
    echo "Formatting new empty data disk $real (ext4)."
    mkfs.ext4 -q -L kpmg-state "$real"
  fi
  uuid="$(blkid -s UUID -o value "$real")"
  grep -q "UUID=$uuid" /etc/fstab || echo "UUID=$uuid $STATE ext4 defaults,nofail,x-systemd.device-timeout=30s 0 2" >> /etc/fstab
  mountpoint -q "$STATE" || mount "$STATE"
fi
mountpoint -q "$STATE" || { echo "$STATE is not a mounted disk. Set KPMG_DATA_DEVICE." >&2; exit 2; }
mkdir -p "$STATE/assets/demo-100"
chown -R kpmg:kpmg "$STATE"
chmod 0700 "$STATE"

echo "== Python 3.11.9"
if [ ! -x /opt/kpmg/bin/uv ]; then
  curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/opt/kpmg/bin UV_NO_MODIFY_PATH=1 sh >/dev/null
fi
export UV_PYTHON_INSTALL_DIR=/opt/kpmg/python
[ -x "$VENV/bin/python" ] || /opt/kpmg/bin/uv venv --quiet --seed --python 3.11.9 "$VENV"
chown -R kpmg:kpmg /opt/kpmg

echo "== Build (fixture context and real-mode models)"
for mode in fixture real; do
  runuser -u kpmg -- env HOME=/opt/kpmg PATH="$VENV/bin:/usr/bin:/bin" KPMG_DEPLOY_MODE=$mode \
    bash "$APP/deploy/render/build.sh" | grep -vE '^(Requirement already satisfied|Looking in indexes)'
done
# Real mode stages demo-100 from the data disk only when no context is recorded. Clear the record so the
# next start re-verifies and stages the index against the code just checked out, not an older snapshot.
rm -f "$APP/.kpmg-onboarding/context.txt"

echo "== Configuration $ENV_FILE"
install -d -m 0750 -o root -g kpmg /etc/kpmg
if [ ! -f "$ENV_FILE" ]; then
  password="$(head -c 36 /dev/urandom | base64 | tr -d '\n')"
  sed -e "s|@DOMAIN@|$DOMAIN|" -e "s|@PASSWORD@|$password|" "$APP/deploy/azure/preview.env.template" > "$ENV_FILE"
fi
sed -i "s|^KPMG_ORIGIN=.*|KPMG_ORIGIN=https://$DOMAIN|" "$ENV_FILE"
chown root:kpmg "$ENV_FILE"
chmod 0640 "$ENV_FILE"

echo "== systemd and HTTPS"
install -m 0644 "$APP/deploy/azure/kpmg-preview.service" /etc/systemd/system/kpmg-preview.service
sed "s|@DOMAIN@|$DOMAIN|" "$APP/deploy/azure/Caddyfile" > /etc/caddy/Caddyfile
systemctl daemon-reload
systemctl enable --quiet kpmg-preview caddy
systemctl restart kpmg-preview
systemctl reload-or-restart caddy

if [ "${KPMG_SKIP_FIREWALL:-0}" != 1 ]; then
  echo "== Firewall (22, 80, 443 only)"
  ufw allow OpenSSH >/dev/null
  ufw allow 80/tcp >/dev/null
  ufw allow 443/tcp >/dev/null
  ufw --force enable >/dev/null
fi

echo
echo "Installed. Site: https://$DOMAIN  (user: reviewer)"
echo "Password:  sudo grep ^KPMG_REVIEW_PASSWORD= $ENV_FILE"
echo "Logs:      sudo journalctl -u kpmg-preview -f"
