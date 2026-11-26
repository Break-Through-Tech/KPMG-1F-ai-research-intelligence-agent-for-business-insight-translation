"""Save the unchanged current workflow for a future comparator."""
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUNDLE = Path("D:/KPMG-demo-corpus/main-727b0b3/data/processed/demo-bundles/demo-100")


def snapshot():
    paths = sorted([*ROOT.joinpath("src").rglob("*.py"),
                    *ROOT.joinpath("experiments", "agentic").glob("*.py")])
    contents = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in paths}
    archive = HERE / "current-multi-agent.zip"
    with ZipFile(archive, "x", compression=ZIP_DEFLATED) as dest:
        for name, data in contents.items():
            dest.writestr(ZipInfo(name), data, compress_type=ZIP_DEFLATED)
    manifest = {
        "archive_sha256": sha256(archive.read_bytes()).hexdigest(),
        "files": {name: sha256(data).hexdigest() for name, data in contents.items()},
        "packages": {name: version(name) for name in
                     ("numpy", "jsonschema", "sentence-transformers", "torch")},
        "corpus_manifest_sha256": sha256((BUNDLE / "manifest.json").read_bytes()).hexdigest(),
    }
    with (HERE / "current-multi-agent.json").open("x", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)
        file.write("\n")


if __name__ == "__main__":
    snapshot()
