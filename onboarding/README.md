# Portable developer setup

The public integration branch can run the synthetic developer preview
without GitHub CLI authentication or restricted project assets. Install Git,
Python 3.11, and a running Docker Linux container daemon. From the checkout
root:

    python3.11 onboarding/setup.py --fixture
    python3.11 onboarding/setup.py start --fixture

On Windows, use py -3.11 in place of python3.11. Add --runtime native to both
commands if Docker is unavailable. Native setup creates a checkout-specific environment with pinned Python
dependencies and CPU Torch. Windows uses an automatically selected short
path under its temporary directory to avoid Torch wheel path limits.
If the environment is cleaned up, run setup again. The Docker image
targets Linux AMD64. Use --prepare-only to verify and stage without building
or installing dependencies.

For the real index, omit --fixture. Setup automatically fetches the exact
versioned arXiv HTML listed in demo-100-sources.json and compares each
response to the evaluated input hash. No GitHub login or transfer is
required for this path. It runs the existing extractor and CPU bundle
builder only if the source inputs match. There is no fixture fallback.
Use the synthetic preview explicitly when upstream differences block the
real index.

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

Standard setup stores the source-check report under
.kpmg-onboarding/source-verification.json. Changed or unavailable HTML
stops setup. If the source pass succeeds, the reconstruction records per-paper
parent counts and hashes, then compares the aggregate parents, views and
embedding bytes. It promotes the index only on an exact match. The
expected configuration is CPU encoding with token224_parent, 224 tokens,
32-token overlap, evaluated parent order, and CRLF parent serialization.
The original evaluation is not rerun.

A versioned arXiv ID pins the paper revision. It cannot pin the HTML
renderer output. The indexed data also includes six papers with old v1.2
supplement rows. That legacy extractor is absent from this checkout, so
those rows cannot currently be reproduced by the ordinary extraction
route. A manually reconstructed, semantically similar index is not
accepted in place of the evaluated one.

Run a fresh source-only diagnostic without installing models:

    python3.11 onboarding/rebuild_corpus.py --check-sources

The optional fresh-v4 corpus is outside application setup. No separate
repository is required for source reconstruction or the fixture.

Run bootstrap unit tests with python -m unittest discover -s onboarding
-p "test_*.py" (as one line). Keep the package cache, credentials, state,
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


## Download of the exact approved index

Use this path once an approved storage location is configured. Set
`KPMG_ARTIFACT_BASE_URL` to its HTTPS directory URL with no query string.
If authentication is required, inject the read-only bearer secret as
`KPMG_ARTIFACT_TOKEN` through the runner's secret store. Both variables
are read from the environment. Keep token values out of Git and logs.

From the checkout root, run the following as one preparation step in a
POSIX shell (including Linux native Render builds):

    python3.11 onboarding/fetch_demo100.py && python3.11 onboarding/setup.py --prepare-only

On Windows PowerShell, run:

    py -3.11 onboarding/fetch_demo100.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    py -3.11 onboarding/setup.py --prepare-only

The endpoint must serve `demo-100--parents.jsonl`,
`demo-100--views.json` and `demo-100--vectors.npy`. The downloader is
noninteractive and verifies all sizes and SHA-256 hashes against
`onboarding/assets.json` before promoting files into the existing
`.kpmg-onboarding/assets/demo-100` cache. A verified cache hit skips
downloads. The optional bearer token is retained only on same-origin
HTTPS redirects. The setup step prints the verified runtime context.
It does not install native dependencies in prepare-only mode.

Run the downloader tests with:

    python3.11 -m unittest discover -s onboarding -p test_fetch_demo100.py
