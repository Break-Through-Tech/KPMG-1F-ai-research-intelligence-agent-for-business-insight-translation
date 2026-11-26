#!/usr/bin/env bash
# Render native-Python build for the supervised research preview.
#
# Reuses the pinned Python 3.11 lock, onboarding/fetch_demo100.py, onboarding/setup.py
# verification and experiments/render-staging/stage.py. It adds no engine code and
# stages nothing that setup.py has not size- and SHA-256-verified.
#
#   KPMG_DEPLOY_MODE=fixture  synthetic one-passage index; hosting check only.
#   KPMG_DEPLOY_MODE=real     exact demo-100 index, from one of:
#     KPMG_ARTIFACT_BASE_URL set   downloaded and staged here (optional KPMG_ARTIFACT_TOKEN)
#     KPMG_ARTIFACT_BASE_URL unset the three files are read from the persistent disk at
#                                  startup (deploy/render/start.py); this build only
#                                  installs dependencies and fetches the public models.
set -euo pipefail
cd "$(dirname "$0")/../.."

mode="${KPMG_DEPLOY_MODE:-}"
case "$mode" in
  fixture|real) ;;
  *) echo "Set KPMG_DEPLOY_MODE to fixture or real." >&2; exit 2 ;;
esac

version="$(python -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
if [ "$version" != "3.11.9" ]; then
  echo "Python 3.11.9 is required (found $version). Set PYTHON_VERSION=3.11.9." >&2
  exit 2
fi

# Same dependency steps as onboarding/setup.py install_native(), into Render's environment.
python -m pip install --disable-pip-version-check --index-url https://download.pytorch.org/whl/cpu \
  --no-deps torch==2.15.0+cpu
python -m pip install --disable-pip-version-check --no-deps -r onboarding/requirements-py311.lock.txt
python -m pip check

if ! git rev-parse HEAD >/dev/null 2>&1; then
  # stage.py and setup.py record the checkout commit with `git rev-parse`. If the
  # build has no usable .git, answer only that lookup from Render's deploy commit.
  # The shim lives in the project directory so start.py can reuse it at runtime.
  if [ -z "${RENDER_GIT_COMMIT:-}" ]; then
    echo "No Git checkout and no RENDER_GIT_COMMIT; cannot record the deployed commit." >&2
    exit 2
  fi
  shim=.kpmg-onboarding/git-shim
  mkdir -p "$shim"
  cat > "$shim/git" <<'SHIM'
#!/bin/sh
if [ "$1" = "-C" ]; then shift 2; fi
case "$*" in
  "rev-parse HEAD") echo "$RENDER_GIT_COMMIT" ;;
  "rev-parse --short HEAD") echo "$RENDER_GIT_COMMIT" | cut -c1-7 ;;
  *) echo "git is unavailable in this build (requested: $*)" >&2; exit 1 ;;
esac
SHIM
  chmod +x "$shim/git"
  export PATH="$PWD/$shim:$PATH"
  echo "Recording deploy commit from RENDER_GIT_COMMIT=$RENDER_GIT_COMMIT"
fi

if [ "$mode" = fixture ]; then
  python -B onboarding/setup.py --runtime native --prepare-only --fixture
elif [ -n "${KPMG_ARTIFACT_BASE_URL:-}" ]; then
  python -B onboarding/fetch_demo100.py
  python -B onboarding/setup.py --runtime native --prepare-only
else
  # Disk mode: fetch and verify the public models and checked-in metadata now; the
  # three index files are verified and staged from the disk when the service starts.
  python -B - <<'EOF'
import json, sys
from pathlib import Path
sys.path.insert(0, 'onboarding')
import setup
spec = json.loads(Path('onboarding/assets.json').read_bytes())
public = {name: item for name, item in spec['files'].items() if item['source'] != 'release'}
setup.acquire_open_files(public, setup.CACHE / 'assets', synthetic=False)
print('Public models and metadata verified; demo-100 will load from the persistent disk at startup.')
EOF
fi
echo "Render build complete ($mode)."
