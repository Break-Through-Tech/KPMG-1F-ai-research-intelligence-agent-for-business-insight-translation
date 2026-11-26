"""Build a static preview from two allowlisted public-paper recordings."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
CASES = {
    "cu-dpo": {"2602.00931v2"},
    "fin-rate-crossstudy": {"2508.03553v1", "2602.07294v4"},
}
PRIVATE = re.compile(r"(?<![\w])[A-Za-z]:[\\/]|file://|localhost|127\.0\.0\.1|"
                     r"AIza[A-Za-z0-9_-]{30,}|\bsk-[A-Za-z0-9_-]{20,}|"
                     r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", re.I)


def verify(condition, reason):
    if not condition:
        raise ValueError(reason)


def check_public(value, field=""):
    if isinstance(value, dict):
        for key, child in value.items():
            verify(key not in {"index_path", "apikey", "api_key", "token", "reviewer",
                               "review_notes", "industry", "fixture_file", "authorization"},
                   f"Unexpected field: {key}")
            check_public(child, key)
    elif isinstance(value, list):
        for child in value:
            check_public(child, field)
    elif isinstance(value, str):
        verify(not PRIVATE.search(value), f"Possible private data in {field}")
        if field in {"url", "source_url", "html_url", "pdf_url"}:
            url = urlsplit(value)
            verify(url.scheme == "https" and url.netloc == "arxiv.org", f"Unexpected URL in {field}")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pick(record, fields):
    return {field: record[field] for field in fields.split() if field in record}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def export_case(source, api, name, papers, routes):
    fixture = read(source / "ui-consult/tests/fixtures" / f"recorded-{name}.json")
    original = fixture["envelope"]["result"]
    evidence = original["evidence"]
    verify({row["arxiv_id"] for row in evidence} == papers, f"Unexpected papers in {name}")
    for row in evidence:
        for field in ("html_url", "pdf_url", "source_url"):
            if row.get(field):
                verify(urlsplit(row[field]).path.split("/")[-1] == row["arxiv_id"],
                       f"Source version mismatch in {row['chunk_id']}")
    index = original["provenance"]["index"]["indexed_records_sha256"]
    verify(re.fullmatch(r"[a-f0-9]{64}", index), "Missing recording index identity")
    request = pick(original["request"], "query top_k")
    summary = pick(original["summary"], "status claims limitations limitation_support query "
                   "generation_method support_check answer_lead answer_scope")
    quality = original["summary"].get("quality_review")
    if quality:
        summary["quality_review"] = pick(quality, "coverage gap policy")
    brief_id = digest(name)[:32]
    version_id = digest(f"{name}:recorded")[:32]
    recorded = "2026-11-17T00:00:00+00:00"  # Fixture recording date; time-of-day is unavailable.
    brief = {"id": brief_id, "title": request["query"], "original_question": request["query"],
             "created_at": recorded, "updated_at": recorded, "archived": 0,
             "current_version": version_id}
    version = {"id": version_id, "brief_id": brief_id, "number": 1,
               "audience": "recorded research", "created_at": recorded}
    envelope = {
        "mode": fixture["envelope"]["mode"], "submitted_request": request,
        "result": {
            "request": request, "summary": summary, "evidence": evidence, "approved": False,
            "schema_version": original["schema_version"], "human_review": {"status": "pending"},
            "provenance": {"execution": original["provenance"]["execution"],
                           "index": {"indexed_records_sha256": index}},
        },
        "library": {"brief": brief, "version": version, "versions": [version], "reviews": [], "replayed": True},
    }
    check_public(envelope)
    write(api / "briefs" / f"{brief_id}.json", envelope)
    tables = fixture["full_tables"]
    check_public(tables)
    used_tables = set()
    for row in evidence:
        if row.get("representation") != "linearized_table":
            continue
        identity = f"{row['arxiv_id']}#{row['table_id']}"
        table = tables[identity]
        verify(table["index_sha256"] == index and table["arxiv_id"] == row["arxiv_id"]
               and table["table_id"] == row["table_id"] and table["complete"]
               and table["row_count"] == len(table["rows"])
               and row["chunk_id"] in {item["chunk_id"] for item in table["rows"]},
               f"Table identity mismatch in {row['chunk_id']}")
        filename = digest(f"{index}:{identity}")[:24] + ".json"
        routes[f"{index}:{row['chunk_id']}"] = f"/_recorded/tables/{filename}"
        if identity not in used_tables:
            write(api / "tables" / filename, table)
            used_tables.add(identity)
    verify(used_tables == set(tables), f"Unexpected full tables in {name}")
    return {**brief, "number": 1, "mode": envelope["mode"], "review_status": "pending"}


def replace_once(source, old, new):
    verify(source.count(old) == 1, f"Refresh changed a staging hook: {old[:60]}")
    return source.replace(old, new, 1)


def stage_ui(source, output):
    for folder, names in {
        "ui-consult": "index.html app.js async-guards.js chart-select.js chart-svg.js "
                      "consult.css evidence.js prefs.js",
        "ui": "answer-export.js math.js read-aloud.css read-aloud.mjs research-speech.js source-reader.js",
    }.items():
        for name in names.split():
            shutil.copyfile(source / folder / name, output / name)
    vendor = source / "ui/vendor/katex"
    for path in (vendor / "LICENSE", vendor / "katex.min.js", vendor / "katex.min.css",
                 *sorted((vendor / "fonts").glob("*.woff2"))):
        target = output / "vendor/katex" / path.relative_to(vendor)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    html = (output / "index.html").read_text(encoding="utf-8")
    html = replace_once(html, '<script src="/mock-api.js" defer></script>',
                        '<script src="/replay-api.js" defer></script>')
    html = replace_once(html, "Saved briefs keep their exact answer, evidence and review history.",
                        "These are recorded research drafts with their supporting evidence.")
    (output / "index.html").write_text(html, encoding="utf-8")
    app = (output / "app.js").read_text(encoding="utf-8")
    hooks = [
        ("  'use strict';", "  'use strict';\n  const fetch = window.StagingReplay.fetch;"),
        ("  $('#library-import').append(importControl",
         "  if (!window.StagingReplay) $('#library-import').append(importControl"),
        ("    const notice = panelNotices.get(demo);", """    if (recordedMode && window.StagingReplay) {
      panel.append(note('Recorded draft. Edits, imports and approvals are unavailable in staging.', 'warn', 'history'));
      return;
    }
    const notice = panelNotices.get(demo);"""),
        ("demo.library ? 'Review and approve' : 'Save as brief'",
         "recordedMode ? 'About this snapshot' : demo.library ? 'Review and approve' : 'Save as brief'"),
        ("demo.library ? 'Record a review' : 'Save to record a review'",
         "recordedMode ? 'About this snapshot' : demo.library ? 'Record a review' : 'Save to record a review'"),
        ("You can open and review saved answers here, but not ask new questions.",
         "Read-only replay of recorded research. This preview does not run AI."),
        ("Research is not running in this session. Open a brief recorded from a live run; its answer, evidence and review history are replayed exactly, with no model call.",
         "Explore two recorded research examples with public-paper evidence. This read-only preview does not run AI."),
        ("No saved briefs here. Generate an answer or import a result JSON file.",
         "No recorded briefs match your search."),
        ("All values match the paper exactly.",
         "Values match the extracted source cells."),
    ]
    for old, new in hooks:
        app = replace_once(app, old, new)
    (output / "app.js").write_text(app, encoding="utf-8")
    shutil.copyfile(HERE / "replay-api.js", output / "replay-api.js")


def build(source, output):
    verify(not output.exists(), "Choose a new output directory")
    output.mkdir(parents=True)
    stage_ui(source, output)
    api = output / "_recorded"
    routes = {}
    listing = [export_case(source, api, name, papers, routes) for name, papers in CASES.items()]
    write(api / "config.json", {"live": False, "library": True, "plain_language": False})
    write(api / "saved-result.json", None)
    write(api / "briefs.json", {"briefs": listing})
    write(api / "table-routes.json", routes)
    write(output / "vercel.json", read(source / "deploy/vercel-staging/vercel.base.json"))
    print(f"Built {len(listing)} recorded briefs with {len(set(routes.values()))} original tables")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve())
