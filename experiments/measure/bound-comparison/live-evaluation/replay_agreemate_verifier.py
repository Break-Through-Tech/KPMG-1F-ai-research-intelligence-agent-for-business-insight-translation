"""Reapply the Verification Agent once to the archived AgreeMate inputs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_codex_shadow import BINARY, MODEL, OUTPUT as ARCHIVE, QuestionGenerator, write
from agents import VerificationAgent
from contracts import CallBudget, ProviderFailure, verification_schema
from src.codex_generation import create_codex_generate
from src.research_chat import attach_validated_citations

OUTPUT = ARCHIVE.parent / "numerical-shadow-agreemate-verification-replay"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_digest(value):
    return sha256(json.dumps(value, allow_nan=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="use the single approved verification attempt")
    args = parser.parse_args()
    if args.execute and OUTPUT.exists():
        parser.error("the one-shot replay directory already exists")

    archived = ARCHIVE / "agreemate"
    draft = archived / "research-response.json"
    packet = archived / "synthesis-evidence.json"
    inputs = {path.name: sha256(path.read_bytes()).hexdigest() for path in (draft, packet)}
    prior = read(archived / "result.json")
    original_receipt = read(archived / "provider-attempts.json")[-1]
    if prior["answer"]["error"]["stage"] != "verification_agent" or original_receipt["status"] != "failed":
        raise ValueError("the saved run does not match the failed AgreeMate verification")
    claims, passages = read(draft)["claims"], read(packet)
    attach_validated_citations(claims, passages)
    task = {"payload": {"question": prior["question"], "claims": claims, "passages": passages}}
    expected_wire = verification_schema(len(claims))
    if json_digest(expected_wire) != original_receipt["schema_sha256"]:
        raise ValueError("the full local schema differs from the archived schema")
    del expected_wire["properties"]["verdicts"]["items"]["properties"]["issues"]["uniqueItems"]
    receipts = []
    recorded = {}

    def checked(delegate):
        def generate(prompt, *, response_schema=None):
            fingerprint = sha256(prompt.encode()).hexdigest()
            if fingerprint != original_receipt["prompt_sha256"]:
                raise ValueError("verification prompt differs from the original")
            if response_schema != expected_wire:
                raise ValueError("unexpected change in provider schema")
            recorded.update(prompt_sha256=fingerprint, wire_schema_sha256=json_digest(response_schema))
            return delegate(prompt, response_schema=response_schema)
        generate.supports_response_schema = True
        return generate

    if not args.execute:
        def fixture(prompt, *, response_schema):
            return json.dumps({"coverage": "full", "missing_aspects": [],
                               "verdicts": [{"index": 0, "verdict": "supported", "issues": [], "reason": "fixture"}],
                               "retrieval_request": {"needed": False, "query": "", "reason": "fixture"}})
        status, _ = VerificationAgent().run(task, CallBudget(checked(fixture), 1))
        if not recorded or status != "ok":
            raise RuntimeError("offline replay check failed")
        print(json.dumps({**recorded, "status": "offline_preflight_passed", "provider_attempts": 0}))
        return

    original, metadata = create_codex_generate(model=MODEL, binary=BINARY, effort="low", timeout=300,
                                               receipts=receipts)
    OUTPUT.mkdir(parents=True)
    write(OUTPUT / "inputs.json", {"sha256": inputs, "provider": metadata, "original_receipt": original_receipt,
                                   "application_attempt_limit": 1})
    attempt = CallBudget(checked(QuestionGenerator(OUTPUT, original)), 1)
    try:
        status, verification = VerificationAgent().run(task, attempt)
        result = {"agent_status": status, "verification": verification}
    except ProviderFailure as error:
        result = {"agent_status": "provider_failure", "error": error.details()}
    finally:
        write(OUTPUT / "provider-attempts.json", receipts)
    unchanged = inputs == {path.name: sha256(path.read_bytes()).hexdigest() for path in (draft, packet)}
    write(OUTPUT / "result.json", {**result, **recorded, "archive_unchanged": unchanged,
                                  "cli_invocations": len(receipts)})
    print(json.dumps({**result, "archive_unchanged": unchanged, "cli_invocations": len(receipts)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
