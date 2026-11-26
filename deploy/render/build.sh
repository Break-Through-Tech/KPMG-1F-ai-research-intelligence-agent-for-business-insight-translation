#!/usr/bin/env bash
# Render native-Python build for the supervised research preview.
#
# Reuses the existing pinned Python 3.11 lock, the onboarding asset verifier and
# experiments/render-staging/stage.py. It adds no engine code and copies no data
# that setup.py has not size- and SHA-256-verified.
#
#   KPMG_DEPLOY_MODE=fixture  synthetic one-passage index; infrastructure check only
#   KPMG_DEPLOY_MODE=real     exact demo-100 index; the cleared release files must
#                             already be in .kpmg-onboarding/assets (see
#                             DEPLOYMENT-READINESS.md, "Asset download interface")
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

if [ "$mode" = real ] && [ -n "${KPMG_ASSET_FETCH:-}" ]; then
  # Hook for the non-interactive authorized download owned by the onboarding work.
  # It must only place verified files under .kpmg-onboarding/assets/.
  python -B "$KPMG_ASSET_FETCH" --dest .kpmg-onboarding/assets
fi

if [ "$mode" = real ]; then
  # Fail closed before setup.py would try an arXiv reconstruction, which cannot
  # reproduce the evaluated index (see onboarding/README.md). setup.py then
  # re-verifies every file's size and SHA-256.
  python - <<'EOF'
import json, pathlib, sys
spec = json.loads(pathlib.Path('onboarding/assets.json').read_bytes())
missing = [name for name, item in spec['files'].items()
           if item['source'] == 'release' and not (pathlib.Path('.kpmg-onboarding/assets') / name).is_file()]
if missing:
    sys.exit('Real mode needs the cleared release files in .kpmg-onboarding/assets: ' + ', '.join(missing))
EOF
fi

if ! git rev-parse HEAD >/dev/null 2>&1; then
  # stage.py and setup.py record the checkout commit with `git rev-parse`. If the
  # build has no usable .git, answer only that lookup from Render's deploy commit.
  if [ -z "${RENDER_GIT_COMMIT:-}" ]; then
    echo "No Git checkout and no RENDER_GIT_COMMIT; cannot record the deployed commit." >&2
    exit 2
  fi
  shim="$(mktemp -d)"
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
  export PATH="$shim:$PATH"
  echo "Recording deploy commit from RENDER_GIT_COMMIT=$RENDER_GIT_COMMIT"
fi

args=(--runtime native --prepare-only)
if [ "$mode" = fixture ]; then
  args+=(--fixture)
fi
python -B onboarding/setup.py "${args[@]}"
echo "Render build complete ($mode)."
