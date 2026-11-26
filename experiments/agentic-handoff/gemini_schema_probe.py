"""One Gemini schema probe using generated fixture data only."""
import argparse
import json
import os
from pathlib import Path
import time

import httpx
from jsonschema import Draft202012Validator

from gemini_paired import GeminiRun, ROOT, MODEL, gemini_synthesis_schema, write
from gemini_quota import GeminiQuota
from src.research_chat import attach_validated_citations, synthesis_schema
from numeric_checks import ground_claim


def fixture(*, simplified=False):
    packet = evidence_fixture(simplified=simplified)
    ids = [p["chunk_id"] for p in packet]
    prompt = ("This is a synthetic schema test. Return one finding with an exact quote "
              "and one of the supplied chunk IDs. Use status ok and no limitations.\n"
              + json.dumps(packet))
    schema = synthesis_schema(sorted(ids))
    Draft202012Validator.check_schema(schema)
    return {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                                 "responseJsonSchema": schema}}

def evidence_fixture(*, simplified=False):
    prose, tables = (8, 6) if simplified else (3, 8)
    ids = [f"2099.01234v1_c{i:04d}" for i in range(prose)]
    ids += [f"2099.01234v1_table_{i:016x}_1" for i in range(tables)]
    return [{"chunk_id": key, "text": (
        ("Synthetic Table 1 | Method A | Accuracy | 71 percent. " if simplified and "table" in key else
         "Fixture method A scored 71 percent. ") +
        "Fixture method B scored 63 percent. This is invented test data. ") * (40 if simplified else 32)}
        for key in ids]

def run_probe(client, quota, folder, *, simplified=False):
    payload = fixture(simplified=simplified)
    full_schema = payload["generationConfig"]["responseJsonSchema"]
    if simplified:
        payload["generationConfig"]["responseJsonSchema"] = gemini_synthesis_schema(full_schema)
    reserved = 2 * len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 4096
    live = GeminiRun(client, quota, folder)
    try:
        response, ticket = live.request("generateContent", payload, kind="generation", tokens=reserved)
    except RuntimeError:
        write(folder / "diagnostic.json", {"status": "stopped", "stop": live.stopped})
        return False
    usage = response.get("usageMetadata") or {}
    candidates = response.get("candidates") or []
    schema_valid = citations_valid = numbers_valid = False
    if len(candidates) == 1 and candidates[0].get("finishReason") == "STOP":
        text = "".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])
                       if not p.get("thought"))
        try:
            value = json.loads(text)
            schema_valid = Draft202012Validator(full_schema).is_valid(value)
            if schema_valid and simplified and value["status"] == "ok" and value["claims"]:
                packet = evidence_fixture(simplified=True)
                items = value["claims"] + value["limitations"]
                attach_validated_citations(items, packet)
                citations_valid = True
                sources = {row["chunk_id"]: row for row in packet}
                numbers_valid = not any(ground_claim(claim, sources)["contradictions"] for claim in value["claims"])
        except (TypeError, ValueError):
            pass
    write(folder / "diagnostic.json", {"status": "accepted_http", "schema_valid": schema_valid,
          "ticket": ticket, "model_version": response.get("modelVersion"), "usage": usage,
          **({"citations_valid": citations_valid, "numbers_valid": numbers_valid, "published": False}
             if simplified else {})})
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-once", action="store_true", required=True)
    parser.add_argument("--simplified", action="store_true")
    args = parser.parse_args()
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        raise SystemExit("GOOGLE_API_KEY is unavailable in this terminal.")
    name = "gemini-f03-simplified-schema-probe-v1" if args.simplified else "gemini-f02-schema-diagnostic-v1"
    out = ROOT / "data/processed" / name
    if out.exists():
        raise SystemExit("The diagnostic directory already exists. No request sent.")
    print(f"Confirm kpmg is Free with billing disabled, {MODEL} quota is available, and other project traffic is paused.")
    if input("Type FREE EXCLUSIVE to confirm, or press Enter to stop: ") != "FREE EXCLUSIVE":
        raise SystemExit("Project status unconfirmed. No request sent.")
    try:
        daily = int(input("Verified upper bound on project requests in the preceding 24 hours: "))
    except ValueError:
        raise SystemExit("Daily usage unverified. No request sent.") from None
    if not 0 <= daily < GeminiQuota.RPD:
        raise SystemExit("Insufficient daily margin. No request sent.")
    print("Waiting 61 seconds to clear earlier minute traffic.", flush=True)
    time.sleep(61)
    out.mkdir()
    quota = GeminiQuota(out / "attempts.sqlite3")
    quota.GENERATION_CAP = 1
    quota.observe(minute_requests=0, minute_input_tokens=0, day_requests=daily, valid_until=time.time() + 55)
    with httpx.Client(headers={"x-goog-api-key": key}, timeout=60, follow_redirects=False,
                      transport=httpx.HTTPTransport(retries=0, trust_env=False), trust_env=False) as client:
        run_probe(client, quota, out, simplified=args.simplified)
    print(f"Diagnostic stopped after its one allowed request. Receipt saved in {out}")


if __name__ == "__main__":
    main()
