# Portable developer setup

The public integration branch can run the synthetic developer preview
without GitHub CLI authentication or restricted project assets. Install Git,
Python 3.11, and a running Docker Linux container daemon. From the checkout
root:

    python3.11 onboarding/setup.py --fixture
    python3.11 onboarding/setup.py start --fixture

On Windows, use py -3.11 in place of python3.11. Add --runtime native to both
commands if Docker is unavailable. Native setup creates a repository-local
environment with pinned Python dependencies and CPU Torch. The Docker image
targets Linux AMD64. Use --prepare-only to verify and stage without building
or installing dependencies.

For the real index, omit --fixture once an authorized release is available.
Authenticate GitHub CLI with your own account if the cleared release is private.
Use --asset-repo OWNER/REPO only when the approved release lives separately
from the clone origin. There is no automatic fixture fallback.

Open http://127.0.0.1:8821 and use the local login printed by start. Try the
scripted question printed at startup. This is a supervised offline developer
app. It retrieves real evidence, uses deterministic fixture responses for
the demo question, and abstains on other questions. It never invokes a
provider. Baseline is the default. Use start --engine s2 for the demo engine.
B1 is off. The Docker port is published to host loopback only. Saved drafts
use a local state directory or a Docker volume. The local password is generated
at startup and stays out of the repository. Use the separate Render procedure
for an approved deployment.

## What ships and what requires clearance

The Git checkout supplies the approved frontend, exact index manifest and
matching table audit. The audit records table IDs, row counts, source hashes
and extraction status. Setup downloads the public MiniLM models at their
exact upstream revisions and checks size and SHA-256. No model weights,
index text, vectors or historical runs are added to Git history.

The exact demo-100 parent text, search views and vectors are an indivisible
evaluated bundle. The version-specific license inventory covers all 100
papers. It records 47 CC BY, 3 CC BY-SA, 6 CC BY-NC-SA, 7 CC BY-NC-ND, and
37 arXiv non-exclusive distribution declarations. The arXiv-only grant
authorizes arXiv to distribute the submission. It does not establish rights
for this project to redistribute the extracted corpus. Publicly published
addresses are not the reason for withholding. The project data owner must
confirm the permitted audience and a redistribution basis for the entire
exact bundle, including any license and attribution obligations. Keep all
three corpus attachments together and unchanged.

- Paper-version inventory: demo-100-licenses.json
- arXiv's license guidance: https://info.arxiv.org/help/license/index.html
- arXiv-only terms: https://arxiv.org/licenses/nonexclusive-distrib/1.0/

Until clearance, use the explicit synthetic fixture path above. The optional
fresh-v4 corpus is not needed for application setup and is excluded. If only
private redistribution is cleared, a private release location is necessary.
If public redistribution is later approved, publication and the setup access
policy can be reviewed together. No new repository is needed for the fixture.

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
