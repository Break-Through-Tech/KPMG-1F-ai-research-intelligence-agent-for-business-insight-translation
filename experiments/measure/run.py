"""Reproduce the component measurements, without a provider or server."""
import argparse
import os
from pathlib import Path

for name in ("HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","HF_HUB_DISABLE_TELEMETRY"):
    os.environ[name]="1"
from common import HERE, LEDGER, digest, pinned
import retrieval
import validation
import tables
import localization
import source_checks
import verify_outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name",help="new run directory basename")
    args=parser.parse_args()
    out=HERE/args.name
    if out.parent.resolve()!=HERE or out.name in ("",".",".."):
        parser.error("supply a directory name directly under experiments/measure")
    out.mkdir()
    before=digest(LEDGER)
    data=pinned()
    completed=[]
    # Validators run before importing the export package for retrieval.
    for stage in (validation.run,tables.run,localization.saved,localization.historical_retrieval,retrieval.run,source_checks.run):
        print("RUN",stage.__module__,stage.__name__,flush=True)
        stage(out,data)
        completed.append(stage.__module__+"."+stage.__name__)
    localization.environment(out,before,completed,data)
    verify_outputs.run(out)
    print(out)
if __name__=="__main__":
    main()

