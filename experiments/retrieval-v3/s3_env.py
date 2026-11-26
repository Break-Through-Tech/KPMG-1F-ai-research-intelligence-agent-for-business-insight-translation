"""Import setup for S3: the frozen consolidated-v2 modules (imported, never edited), the shared experiment modules and
this folder. Nothing here calls a model."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
V2 = EXP / 'consolidated-v2'
for path in (V2, EXP / 'measure/fresh-diagnostic-v1', HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
import env as v2env  # noqa: E402,F401  (puts the repository root and the frozen shared modules on the path)

ROOT = v2env.ROOT
FROZEN_V2_FILES = ('evidence.py', 'synthesis.py', 'review.py', 'publication.py', 'engine.py', 'accounting.py',
                   'env.py', 'adapter.py', 'assist_route.py')
