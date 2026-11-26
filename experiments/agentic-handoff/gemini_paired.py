"""One-shot Gemini-only paired comparison. No reference text enters generation."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import sys
import time

import httpx
from jsonschema import Draft202012Validator, ValidationError

from gemini_quota import GeminiQuota, QuotaRefused

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "experiments/measure/fresh-diagnostic-v1")]
from capture import Capture, SEPARATOR, to_envelope, write
from agents import OrchestratorAgent, ORCHESTRATOR_PROMPT
from handoff import EvidenceHandoffOrchestrator
from preflight import open_route, verify

MODEL = "gemini-3.1-flash-lite"
BASE = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}"
ARMS = {"current": OrchestratorAgent, "handoff": EvidenceHandoffOrchestrator}


def sanitized_google_error(response):
    """Keep bounded diagnostic fields, never headers or the raw response body."""
    try:
        error = response.json().get("error")
    except (ValueError, AttributeError):
        return None
    if not isinstance(error, dict):
        return None

    key = response.request.headers.get("x-goog-api-key", "")

    def clean(value):
        if not isinstance(value, str):
            return None
        if key:
            value = value.replace(key, "[redacted]")
        value = re.sub(r"(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9_.~+/=-]+", "[redacted]", value)
        value = re.sub(r"AIza[\w-]{15,}|eyJ[\w-]+\.[\w-]+\.[\w-]+", "[redacted]", value)
        value = re.sub(r"https?://\S+", "[redacted URL]", value)
        value = re.sub(r'"[^"]*"|\x27[^\x27]*\x27|\x60[^\x60]*\x60', "[redacted literal]", value)
        # Keep diagnostics on one line and avoid saving large echoed payloads.
        return " ".join(value.split())[:400]

    def fields(obj, names):
        return {name: clean(obj[name]) for name in names if isinstance(obj.get(name), str)}

    def objects(obj, name):
        values = obj.get(name)
        return [item for item in values[:8] if isinstance(item, dict)] if isinstance(values, list) else []

    result = fields(error, ("status", "message"))
    result["details"] = []
    for detail in objects(error, "details"):
        item = fields(detail, ("@type", "reason", "domain", "retryDelay"))
        for name in ("fieldViolations", "violations"):
            entries = [fields(v, ("field", "description", "reason", "quotaId", "quotaMetric"))
                       for v in objects(detail, name)]
            if entries:
                item[name] = entries
        if item:
            result["details"].append(item)
    return result

SYNTHESIS_PREFIX = "Synthesize an answer"


def gemini_synthesis_schema(schema):
    """Keep the output shape while reducing constrained-decoder state growth."""
    wire = deepcopy(schema)
    for name in ("claims", "limitations"):
        rows = wire["properties"][name]
        rows.pop("maxItems", None)
        item = rows["items"]["properties"]
        item["text"].pop("minLength", None)
        item["text"].pop("maxLength", None)
        support = item["support"]
        support.pop("minItems", None)
        support.pop("maxItems", None)
        fields = support["items"]["properties"]
        fields["chunk_id"].pop("enum", None)
        fields["quote"].pop("minLength", None)
        fields["quote"].pop("maxLength", None)
    return wire

class _Transient(Exception):
    """Provider overload (HTTP 503) or timeout; retried only when transient_retries > 0."""


class GeminiRun:
    supports_response_schema = True

    def __init__(self, client, quota, folder, *, pause=time.sleep, simplify_synthesis=True, transient_retries=0):
        self.client, self.quota, self.folder, self.pause = client, quota, folder, pause
        self.simplify_synthesis = simplify_synthesis
        # Opt-in. Each retry is a new reserved attempt with its own receipt, counted against the same caps.
        self.transient_retries = transient_retries
        self.stopped = None
        self.model_version = None

    def request(self, endpoint, payload, *, kind="metadata", tokens=0):
        for attempt in range(self.transient_retries + 1):
            try:
                return self._request_once(endpoint, payload, kind=kind, tokens=tokens)
            except _Transient:
                if attempt == self.transient_retries:
                    raise RuntimeError(self.stopped) from None
                self.stopped = None
                self.pause(60 * (attempt + 1))  # back off 60 s, then 120 s

    def _request_once(self, endpoint, payload, *, kind, tokens):
        if self.stopped:
            raise RuntimeError(self.stopped)
        try:
            while True:
                try:
                    ticket = self.quota.reserve(kind, tokens)
                    break
                except QuotaRefused as error:
                    if str(error) != "Minute request or input-token margin reached" or tokens > self.quota.TPM:
                        raise
                    self.pause(61)
            started = time.perf_counter()
            status = None
            google_error = None
            try:
                response = (self.client.get(BASE) if endpoint == "model"
                            else self.client.post(f"{BASE}:{endpoint}", json=payload))
                status = response.status_code
                if response.is_error:
                    google_error = sanitized_google_error(response)
                response.raise_for_status()
                data = response.json()
            finally:
                write(self.folder / f"{ticket:03}-http.json",
                      {"method": endpoint, "kind": kind, "status": status,
                       "reserved_input_tokens": tokens, "seconds": time.perf_counter() - started,
                       **({"google_error": google_error} if google_error is not None else {})})
        except (httpx.HTTPError, ValueError, QuotaRefused) as exc:
            status = locals().get("status")
            self.stopped = f"{type(exc).__name__}" + (f" HTTP {status}" if status else "")
            if self.transient_retries and (status == 503 or isinstance(exc, httpx.TimeoutException)):
                raise _Transient() from None
            raise RuntimeError(self.stopped) from None
        return data, ticket

    def __call__(self, prompt, *, response_schema):
        wire_schema = (gemini_synthesis_schema(response_schema)
                       if self.simplify_synthesis and prompt.startswith(SYNTHESIS_PREFIX)
                       else response_schema)
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload = {"contents": contents, "generationConfig": {
            "temperature": 0, "responseMimeType": "application/json",
            "responseJsonSchema": wire_schema,
        }}
        # Byte-length reserve includes the schema and JSON framing. Confirm the
        # token count with Gemini and charge both operations against local margins.
        estimated = 2 * len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 4096
        if estimated > self.quota.TPM:
            self.stopped = "Request cannot fit the conservative token margin"
            raise RuntimeError(self.stopped)
        count, _ = self.request("countTokens", {"contents": contents}, tokens=estimated)
        total = count.get("totalTokens")
        if type(total) is not int or not 0 < total <= estimated:
            self.stopped = "Gemini input token count could not be reconciled"
            raise RuntimeError(self.stopped)
        response, ticket = self.request("generateContent", payload, kind="generation", tokens=estimated)
        usage = response.get("usageMetadata") or {}
        model_version = response.get("modelVersion")
        write(self.folder / f"{ticket:03}-usage.json", {"model_version": model_version, "usage": usage})
        if (type(usage.get("promptTokenCount")) is not int or not 0 < usage["promptTokenCount"] <= estimated
                or not model_version or self.model_version not in (None, model_version)):
            self.stopped = "Gemini usage or model identity could not be reconciled"
            raise RuntimeError(self.stopped)
        self.model_version = model_version
        candidates = response.get("candidates") or []
        if len(candidates) != 1 or candidates[0].get("finishReason") != "STOP":
            self.stopped = "Gemini generation did not complete"
            raise RuntimeError(self.stopped)
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        try:
            Draft202012Validator(response_schema).validate(json.loads(text))
        except (ValueError, TypeError, ValidationError):
            raise RuntimeError("Gemini returned invalid structured output") from None
        return text


def replay_pair(folder, question, retrieve, identity, generate, arm_order, *, quote_grounding=False, scope_review=False,
                withhold_interpretations=False):
    """One shared plan, matched initial retrieval, normal budgeted retries."""
    planner_reply = None
    initial_packet = None
    synthesis_round = 0
    cache = {}
    index = identity()

    def same_retrieve(query, k):
        if k != 8 or identity() != index:
            generate.stopped = "Frozen retrieval identity or cap changed"
            raise RuntimeError(generate.stopped)
        if (query, k) not in cache:
            cache[query, k] = retrieve(query, k)
        from copy import deepcopy
        return deepcopy(cache[query, k])

    def shared(prompt, *, response_schema):
        nonlocal planner_reply, initial_packet, synthesis_round
        if prompt.startswith(ORCHESTRATOR_PROMPT):
            if planner_reply is None:
                planner_reply = generate(prompt, response_schema=response_schema)
                write(folder / "shared-plan.json", {"response": planner_reply})
            return planner_reply
        if prompt.startswith("Synthesize an answer"):
            synthesis_round += 1
            if synthesis_round == 1:
                packet = json.loads(prompt.split(SEPARATOR, 1)[1])["paper_passages"]
                if initial_packet is not None and packet != initial_packet:
                    generate.stopped = "Initial evidence differs across paired arms"
                    raise RuntimeError(generate.stopped)
                initial_packet = packet
        return generate(prompt, response_schema=response_schema)

    answers = {}
    for name in arm_order:
        synthesis_round = 0
        capture = Capture(folder / name, shared)
        engine = ARMS[name](generate=capture, retrieve=same_retrieve, top_k=8, max_calls=5,
                            index_sha256=index["indexed_records_sha256"],
                            **({"research_only": True} if name == "current" else {}))
        if quote_grounding:  # opt-in, applied identically to both arms
            from quote_grounding import enable
            enable(engine)
        if scope_review:  # opt-in, applied identically to both arms
            import scope_review as scope
            scope.enable(engine)
        if withhold_interpretations:  # opt-in, applied identically to both arms
            import interpretation_policy
            interpretation_policy.enable(engine)
        result = engine.run(question)
        write(capture.directory / "agentic.json", result)
        answer = to_envelope(result, top_k=8, provenance={"index": index, "generation": {"model": MODEL}},
                             context_id="gemini-handoff-pair")
        write(capture.directory / "result.json", answer)
        answers[name] = answer
        if capture.violation or generate.stopped or result["status"] == "execution_error":
            raise RuntimeError(generate.stopped or "Comparison stopped on execution or integrity failure")
    return answers


# Opt-in staged modes: (output directory, questions, scope review, withhold interpretations). Quote grounding is
# on in every staged mode, identically in both arms; each pair costs at most 9 generations (shared plan + 2 x 4).
STAGED = {
    "grounded_stage_a": ("gemini-handoff-paired-v3-grounded-stage-a", ("F01", "F03"), False, False),
    "scoped_stage_a": ("gemini-handoff-paired-v4-scoped-stage-a", ("F01", "F03"), True, False),
    "policy_stage_a": ("gemini-handoff-paired-v5-policy-stage-a", ("F01", "F03"), False, True),
    "policy_stage_b": ("gemini-handoff-paired-v6-policy-stage-b",
                       ("F04", "F05", "F06", "F07", "F08", "F09", "F10"), False, True),
    # v6 stopped on Gemini 503 overload before any pair completed; same questions and settings, plus bounded retry.
    "policy_stage_b_retry": ("gemini-handoff-paired-v7-policy-stage-b-retry",
                             ("F04", "F05", "F06", "F07", "F08", "F09", "F10"), False, True),
}
RETRYING = {"policy_stage_b_retry": 2}  # up to 2 retries per request on HTTP 503 or timeout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.add_argument("--resume-after-metadata-failure", action="store_true")
    parser.add_argument("--continue-f03-f10", action="store_true")
    parser.add_argument("--simplified-v2", action="store_true")
    parser.add_argument("--grounded-stage-a", action="store_true",
                        help="F01 and F03 only, simplified-v2 wire, quote grounding in both arms")
    parser.add_argument("--scoped-stage-a", action="store_true",
                        help="as --grounded-stage-a, plus scope review in both arms")
    parser.add_argument("--policy-stage-a", action="store_true",
                        help="as --grounded-stage-a, plus withholding interpretations in both arms")
    parser.add_argument("--policy-stage-b", action="store_true",
                        help="F04-F10, quote grounding and withholding interpretations in both arms")
    parser.add_argument("--policy-stage-b-retry", action="store_true",
                        help="as --policy-stage-b, plus up to 2 retries per request on HTTP 503 or timeout")
    args = parser.parse_args()
    if sum((args.continue_f03_f10, args.resume_after_metadata_failure, args.simplified_v2,
            *(getattr(args, mode) for mode in STAGED))) > 1:
        parser.error("Choose only one run mode.")
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not key:
        raise SystemExit("GOOGLE_API_KEY is unavailable in this terminal.")
    sealed = ROOT / "experiments/measure/fresh-diagnostic-v1"
    if sha256((sealed / "seal.json").read_bytes()).hexdigest() != "d79d8719f53d5822d0ca9f11ebadb391acec6b7d2fe224ef0e288045dafc12dd":
        raise SystemExit("Frozen seal hash changed.")
    verify()
    for name, digest in json.loads((HERE / "current-multi-agent.json").read_bytes())["files"].items():
        if sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise SystemExit(f"Comparator source changed: {name}")
    questions = json.loads((sealed / "questions.json").read_bytes())
    if [q["id"] for q in questions] != [f"F{i:02d}" for i in range(1, 11)]:
        raise SystemExit("Frozen schedule changed.")
    import subprocess
    process_check = """
$ErrorActionPreference = 'Stop'
$processes = @(Get-CimInstance Win32_Process)
$ancestors = @()
$nextId = __PID__
while ($nextId -and $nextId -notin $ancestors) {
    $ancestors += $nextId
    $nextId = ($processes | Where-Object ProcessId -eq $nextId).ParentProcessId
}
@($processes | Where-Object {
    $_.ProcessId -notin $ancestors -and $_.Name -match '^python' -and
    $_.CommandLine -match 'gemini_paired\.py|execute_live\.py|end-to-end-diagnostic[\\/]live\.py'
}).Count
"""
    check = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                            process_check.replace("__PID__", str(os.getpid()))],
                           capture_output=True, text=True, timeout=20)
    if check.returncode or check.stdout.strip() != "0":
        raise SystemExit("Could not rule out another local evaluation process.")
    retrieve, identity = open_route()
    print("Check current AI Studio kpmg project tier, billing, usage and quota. Pause all other project traffic.")
    print("Confirm Free tier, billing disabled, at least 15 RPM / 250000 TPM / 500 RPD, and exclusive use for this run.")
    if input("Type FREE EXCLUSIVE to confirm, or press Enter to stop: ") != "FREE EXCLUSIVE":
        raise SystemExit("Billing or external usage not confirmed.")
    try:
        daily = int(input("Upper bound on other project requests in the preceding 24 hours: ").strip())
    except ValueError:
        raise SystemExit("A verified daily bound is required.")
    if not 0 <= daily <= 200:
        raise SystemExit("Insufficient or uncertain daily headroom for 90 calls and token checks.")
    print("Waiting 61 seconds to clear the previous minute's traffic.", flush=True)
    confirmed = time.time()
    time.sleep(61)
    out = ROOT / "data/processed/gemini-handoff-paired-v1"
    if args.resume_after_metadata_failure:
        from contextlib import closing
        import sqlite3
        with closing(sqlite3.connect((out / "attempts.sqlite3").as_uri() + "?mode=ro", uri=True)) as prior:
            kinds = prior.execute("SELECT kind FROM reservations ORDER BY id").fetchall()
        receipt = json.loads((out / "001-http.json").read_bytes())
        stop = json.loads((out / "completion.json").read_bytes())
        if kinds != [("metadata",)] or receipt.get("method") != "model" or receipt.get("status") != 400 or stop.get("status") != "stopped":
            raise SystemExit("Original metadata-only stop could not be verified.")
        out = out.with_name("gemini-handoff-paired-v1-recovery")
    max_attempts = 90
    if args.continue_f03_f10:
        prior_root = out.with_name("gemini-handoff-paired-v1-recovery")
        if (not all((prior_root / "F01" / arm / "result.json").is_file() for arm in ARMS)
                or not (prior_root / "F02/handoff/result.json").is_file()
                or (prior_root / "F02/current").exists()
                or any((prior_root / f"F{i:02d}").exists() for i in range(3, 11))
                or json.loads((prior_root / "completion.json").read_bytes()).get("provider_stop") != "HTTPStatusError HTTP 400"):
            raise SystemExit("Historical stop or unattempted schedule could not be verified.")
        out = out.with_name("gemini-handoff-paired-v1-f03-f10")
        questions = questions[2:]
        max_attempts = 72
    if args.simplified_v2:
        out = out.with_name("gemini-handoff-paired-v2-simplified")
    mode = next((name for name in STAGED if getattr(args, name)), None)
    staged = mode is not None
    grounding, selected, scoped, withhold = staged, (), False, False
    if staged:
        name, selected, scoped, withhold = STAGED[mode]
        out = out.with_name(name)
        max_attempts = len(selected) * 9
    simplified = args.simplified_v2 or staged
    out.mkdir()  # Atomic one-shot reservation. Never reuse or overwrite.
    quota = GeminiQuota(out / "attempts.sqlite3")
    quota.GENERATION_CAP = max_attempts
    quota.observe(minute_requests=0, minute_input_tokens=0, day_requests=daily,
                  valid_until=confirmed + 4 * 3600, exclusive=True)
    write(out / "preflight.json", {"model": MODEL, "confirmed_at": confirmed, "other_daily_upper_bound": daily, "generation_cap": max_attempts,
                                     "synthesis_wire": "simplified-v2" if simplified else "original",
                                     "quote_grounding": grounding, "scope_review": scoped,
                                     "withhold_interpretations": withhold,
                                     "transient_retries": RETRYING.get(mode, 0),
                                     "questions": list(selected) if staged else [q["id"] for q in questions]})
    try:
        with httpx.Client(headers={"x-goog-api-key": key}, timeout=60, follow_redirects=False,
                          transport=httpx.HTTPTransport(retries=0, trust_env=False), trust_env=False) as client:
            # The original evaluation labels are bound to the historical wire format.
            live = GeminiRun(client, quota, out, simplify_synthesis=simplified, transient_retries=RETRYING.get(mode, 0))
            model, _ = live.request("model", None)
            if "generateContent" not in model.get("supportedGenerationMethods", []):
                raise RuntimeError("Configured Gemini model is unavailable")
            for i, q in enumerate(questions):
                if staged and q["id"] not in selected:
                    continue  # i keeps the frozen alternating arm order of the full schedule
                folder = out / q["id"]
                folder.mkdir()
                print("Running", q["id"], flush=True)
                order = ("current", "handoff") if i % 2 == 0 else ("handoff", "current")
                replay_pair(folder, q["question"], retrieve, identity, live, order,
                            quote_grounding=grounding, scope_review=scoped,
                            withhold_interpretations=withhold)
    except Exception as exc:
        write(out / "completion.json", {"status": "stopped", "error": type(exc).__name__,
                                        "provider_stop": getattr(locals().get("live"), "stopped", None)})
        raise SystemExit(f"Paired run stopped. See {out / 'completion.json'}") from None
    write(out / "completion.json", {"status": "complete"})
    print(f"Paired run finished. Results: {out}")


if __name__ == "__main__":
    main()
