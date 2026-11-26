# Portable developer setup

Use a private checkout of this integration branch. Install Git, GitHub CLI
and Python 3.11 or newer. Authenticate GitHub CLI with gh auth login and
use your own team account. For Docker mode, run a local Linux container
daemon (Docker Desktop on Windows, Docker Engine on Linux). The built
image targets Linux AMD64. No provider credentials are needed.

From the checkout root on Windows:

    py -3.11 onboarding/setup.py
    py -3.11 onboarding/setup.py start

On Linux:

    python3.11 onboarding/setup.py
    python3.11 onboarding/setup.py start

If Docker is unavailable, add --runtime native to both commands. Native
setup requires Python 3.11 and uses a fresh repository-local environment
with pinned CPU Torch and a version-locked dependency set. Linux dependency
resolution and container startup still require local Linux verification.
Use --prepare-only with setup to verify and stage without installing or
building. Windows package versions are pinned and were exercised locally.
Python package installers may need public package repositories. Model
inference uses only staged files.

Open http://127.0.0.1:8821 and use the local login printed by start. Try the
scripted question printed at startup. This is a supervised offline developer
app. It retrieves real evidence, uses deterministic fixture responses for
the demo question, and abstains on other questions. It never invokes a
provider. Baseline is the default. Use start --engine s2 for the demo engine.
B1 is off. The Docker port is published to host loopback only. Saved drafts
use a local state directory or a Docker volume. The local password is generated
at startup and stays out of the repository. Use the separate Render procedure
for an approved deployment.

## Asset source and clearance

The current code remote is public. The intended source is a separate private
team repository with a Release tagged s2-runtime-v1. Set KPMG_ASSET_REPO
or use --asset-repo for a separate asset repository. By default setup uses
the GitHub origin of the private clone. A separately created private team repository can host the onboarding code
and the release together.
Never publish the approved UI branch or the asset release to the public
remote.
Setup verifies repository visibility, fetches the named release attachments
using the caller's GitHub CLI login, and checks each size and SHA-256
before accepting it. The asset manifest lists the attachment filename
for each required path. A cache hit checks the bytes again. An incomplete
or corrupted cache fails with a specific error. Remove a damaged cached
file and rerun setup to reacquire it. Runtime contexts are rebuilt from
the checked-out source plus verified assets. All paths are relative to
the checkout. No ZIP needs to be transferred manually.

Use one private Release for the exact demo-100 corpus, table audit and both
model snapshots. Release attachments keep large data out of Git history and
avoid adding an LFS client, per-clone smudge behavior and separate LFS quotas.
Pinned external model revisions are a viable alternative, but the exact
evaluated snapshots would still need verification and the private corpus
would still require a separate distribution path. This setup uses one
authenticated retrieval and integrity policy for all runtime data.
The approved frontend is checked in under onboarding/frontend, with
path-specific byte preservation and independent SHA-256 checks. Historical
evaluation assets, validation sets, replay logs and scoring records are not
required by this bootstrap.

**Publication is blocked on project data-use clearance.** Demo-100
parents.jsonl and views.json contain a publicly reproduced address inside
a research scenario. The optional fresh-v4 versions additionally include
published author correspondence and are outside runtime setup. No project
rule clearing publication of the scenario address was located. Exact
bytes are required. The project data owner must explicitly clear the
published scenario text and the team-private release audience. After clearance,
an authorized maintainer can create the private release and attach the
21 exact files using the names in assets.json. Verify release access and
the full manifest on a fresh clone. If clearance is denied, the existing
pinned engine cannot be distributed through this release; changing the
corpus requires a separately approved provenance and evaluation decision.
No asset release or upload is part of this change.

Run bootstrap unit tests with python -m unittest discover -s onboarding
-p test_setup.py (as one line). Keep the package cache, credentials, state,
and generated contexts out of Git.


## Synthetic onboarding fixture before data clearance

From the clone, run:

    python3.11 onboarding/setup.py --fixture
    python3.11 onboarding/setup.py start --fixture

Use py -3.11 in place of python3.11 on Windows. The same --runtime native
option is available for both steps. The fixture needs Docker and Python for
the Docker route, and downloads size- and SHA-256-verified public model files
from the pinned Hugging Face revisions. It requires no GitHub Release or
provider login. Its one artificial passage, zero search vector, and empty
matching table audit exercise startup and evidence handling, not retrieval
quality or chart coverage. Ask the printed fixture question and expect a
cited synthetic answer and a pending review. Use --engine s2 on start to
exercise the optional engine. Its cache, Docker image and saved state are
separate from the real runtime. Normal setup still requires the exact
private release and cannot accept the fixture as a substitute.

For ownership, permission assignments and the approval-gated attachment
preparer, see PUBLISHING.md.
