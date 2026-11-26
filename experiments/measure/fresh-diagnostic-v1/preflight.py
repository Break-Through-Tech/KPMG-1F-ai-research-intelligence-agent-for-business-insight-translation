"""Verify the frozen files and run original-question B2 lookups without generation."""
from time import perf_counter

from prepare import BUNDLE, HERE, ROOT, CLI, ENCODER, RERANKER, PIN, digest, read, save


def verify():
    sealed = read(HERE / "seal.json")
    for name, checksum in sealed["files"].items():
        if digest(ROOT / name) != checksum:
            raise ValueError(f"Sealed file changed: {name}")
    for name, checksum in sealed["bundle"]["artifact_sha256"].items():
        if digest(BUNDLE / name) != checksum:
            raise ValueError(f"Bundle file changed: {name}")
    for role, asset in sealed["local_assets"].items():
        from pathlib import Path
        p = Path(asset["path"])
        if role == "cli":
            if p != CLI or digest(p) != asset["sha256"]:
                raise ValueError("CLI changed")
        elif {f.name: digest(f) for f in p.iterdir() if f.is_file()} != asset["sha256"]:
            raise ValueError(f"Model asset changed: {role}")
    return sealed


def open_route():
    import torch
    from src.experimental.b2 import open_b2
    torch.set_num_threads(4)
    retrieve, identity, *_ = open_b2(BUNDLE, encoder_path=ENCODER, reranker_path=RERANKER,
                                    table_comparisons=True)
    index = identity()
    if index["indexed_records_sha256"] != PIN or not index.get("table_comparisons"):
        raise ValueError("Unexpected B2 configuration")
    return retrieve, identity


def offline():
    from pathlib import Path
    import subprocess
    verify()
    started = perf_counter()
    retrieve, identity = open_route()
    init_seconds = perf_counter() - started
    version = subprocess.run([str(CLI), "--version"], capture_output=True, text=True,
                             check=True, timeout=15).stdout.strip()
    cache = read(Path.home() / ".codex/models_cache.json")
    listed = any(item.get("slug") == "gpt-6.1-sol" and item.get("visibility") == "list"
                 for item in cache["models"])
    result = []
    for question in read(HERE / "references.json"):
        started = perf_counter()
        ids = [p["chunk_id"] for p in retrieve(question["question"], 8)]
        elapsed = perf_counter() - started
        coverage = [point["point_id"] for point in question["required_points"]
                    if any(set(group) <= set(ids) for group in point["anchors"])]
        result.append({"id": question["id"], "chunk_ids": ids, "points_with_exact_anchors": coverage,
                       "required_point_count": len(question["required_points"]), "seconds": elapsed})
        print(question["id"], f"{len(coverage)}/{len(question['required_points'])}", flush=True)
    save(HERE, "offline-retrieval.json", {"model_listed_in_local_cache": listed, "cli_version": version,
                                        "b2_init_seconds": init_seconds, "identity": identity(),
                                        "provider_invocations": 0, "original_query_only": result})


if __name__ == "__main__":
    offline()
