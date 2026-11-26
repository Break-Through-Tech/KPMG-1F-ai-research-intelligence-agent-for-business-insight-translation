#!/usr/bin/env bash
# Install the three uploaded demo-100 files onto the persistent data disk.
#
#   scp parents.jsonl views.json vectors.npy <user>@<vm>:~/demo-100/
#   sudo bash /opt/kpmg/app/deploy/azure/load-index.sh ~/demo-100
#
# Checks each file's size and SHA-256 against onboarding/assets.json before copying.
# deploy/render/start.py verifies them again and stages them when real mode starts.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Run with sudo." >&2; exit 2; }
SOURCE="${1:?Usage: load-index.sh <directory containing parents.jsonl views.json vectors.npy>}"
TARGET=/var/lib/kpmg/assets/demo-100
mountpoint -q /var/lib/kpmg || { echo "/var/lib/kpmg is not mounted." >&2; exit 2; }

/opt/kpmg/venv/bin/python - "$SOURCE" <<'EOF'
import hashlib, json, sys
from pathlib import Path
source = Path(sys.argv[1])
files = json.loads(Path('/opt/kpmg/app/onboarding/assets.json').read_bytes())['files']
bad = []
for name in ('parents.jsonl', 'views.json', 'vectors.npy'):
    item, path = files['demo-100/' + name], source / name
    if not path.is_file() or path.stat().st_size != item['bytes']:
        bad.append(f'{name}: missing or wrong size (expected {item["bytes"]} bytes)')
        continue
    with path.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != item['sha256']:
            bad.append(f'{name}: SHA-256 mismatch')
            continue
    print(f'verified {name} ({item["bytes"]} bytes)')
if bad:
    sys.exit('Not installed. ' + '; '.join(bad))
EOF

install -d -o kpmg -g kpmg -m 0700 "$TARGET"
for name in parents.jsonl views.json vectors.npy; do
  install -o kpmg -g kpmg -m 0600 "$SOURCE/$name" "$TARGET/$name.partial"
  mv -f "$TARGET/$name.partial" "$TARGET/$name"
done
echo "Installed to $TARGET."
echo "To serve them: sudoedit /etc/kpmg/preview.env (KPMG_DEPLOY_MODE=real, plus the Gemini settings),"
echo "then: sudo systemctl restart kpmg-preview"
