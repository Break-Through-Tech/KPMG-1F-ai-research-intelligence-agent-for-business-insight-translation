"""One-shot subscription pilot. Use --offline to exercise recording with a fixture."""
import argparse
import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import time
from unittest.mock import patch

os.environ["LITELLM_OFFLINE_MODE"] = "True"

import httpx
from lmi import LLMResult
from paperqa import Docs
from paperqa.utils import get_citation_ids
from adapter import MODEL, PIN, ask, settings

QUESTIONS = {
    "travelplanner": "How was the TravelPlanner benchmark designed, and what final pass rate did GPT-4-Turbo achieve in the two-stage setting?",
    "accuraterag": "With fine-tuned Llama-2-7B, what score ranges did AccurateRAG and RAFT with GPT-4 CoT achieve across the three APIBench subsets? Give the exact Table 2 values for each subset and method.",
}
COPY_SHA = "8f1d2f1329017f3d9450b203048fb7f7b3ff6832cec8430cbf9e11c8d425c6f6"


async def run_one(question, rows, path, offline):
    record = {
        "question": question, "provider": MODEL, "fixture": offline,
        "copy_sha256": COPY_SHA, "parent_sha256": PIN, "retrieved": [],
        "http_attempts": 0, "model_invocations": 0, "project_publication": False,
    }

    def save():
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    gather = Docs.aget_evidence
    send = httpx.AsyncClient._send_single_request

    async def observe(docs, *args, **kwargs):
        result = await gather(docs, *args, **kwargs)
        record["retrieved"] = [
            {"citation_id": c.id, "marker": c.text.name, "arxiv_id": c.text.doc.dockey,
             "chunk_id": by_text[(c.text.doc.dockey, c.text.text)]["chunk_id"],
             "source_url": by_text[(c.text.doc.dockey, c.text.text)]["source_url"],
             "text": c.text.text, "context_summary": c.context}
            for c in result.contexts
        ]
        save()
        return result

    async def capped_send(client, request):
        if (offline or request.method != "POST" or request.url.scheme != "https"
                or request.url.host != "chatgpt.com"
                or request.url.path != "/backend-api/codex/responses"
                or record["http_attempts"]):
            record["blocked_outbound_request"] = True
            raise RuntimeError("Pilot blocked unexpected or repeated outbound request")
        record["http_attempts"] = 1
        save()
        response = await send(client, request)
        record["http_status"] = response.status_code
        save()
        return response

    def block_sync(*args, **kwargs):
        record["blocked_synchronous_request"] = True
        raise RuntimeError("Pilot blocked synchronous HTTP including renewed authentication")

    class SingleAnswer:
        async def call_single(self, *, messages, name, **kwargs):
            if name != "answer" or record["model_invocations"]:
                raise RuntimeError("Pilot blocked unexpected or repeated model invocation")
            record["model_invocations"] = 1
            record["answer_prompt"] = messages[-1].content
            save()
            if offline:
                key = get_citation_ids(messages[-1].content)[0]
                result = LLMResult(model="offline-fixture", text=f"Fixture ({key}).")
            else:
                model = settings().get_llm()
                model.config["router_kwargs"].update(num_retries=0, fallbacks=[])
                deployments = model.config["model_list"]
                if len(deployments) != 1 or deployments[0]["litellm_params"]["model"] != MODEL:
                    raise RuntimeError("Unexpected subscription deployment")
                deployments[0]["litellm_params"]["max_retries"] = 0
                result = await model.call_single(messages=messages, name=name, **kwargs)
            record["provider_draft"] = result.text
            record["usage"] = {
                key: getattr(result, key) for key in
                ("model", "prompt_count", "completion_count", "cache_read_tokens")
            }
            save()
            return result

    by_text = {(row["arxiv_id"], row["text"]): row for row in rows}
    started = time.perf_counter()
    save()
    try:
        with (
            patch.object(Docs, "aget_evidence", observe),
            patch.object(httpx.AsyncClient, "_send_single_request", capped_send),
            patch.object(httpx.Client, "_send_single_request", block_sync),
        ):
            record["adapter_result"] = await ask(question, rows, llm_model=SingleAnswer())
    except Exception as exc:
        record["error"] = {"type": type(exc).__name__}
        if isinstance(exc, (KeyError, AttributeError)):
            record["error"]["field"] = str(exc)
        if getattr(exc, "status_code", None) is not None:
            record["error"]["status_code"] = exc.status_code
    finally:
        record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        save()
    print(path.name, {key: record.get(key) for key in
                     ("elapsed_seconds", "model_invocations", "http_attempts", "http_status", "error")}, flush=True)
    return record


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    src = Path(__file__).with_name("pilot-copy.json")
    data = src.read_bytes()
    packet = json.loads(data)
    if sha256(data).hexdigest() != COPY_SHA or packet["parent_sha256"] != PIN:
        raise ValueError("Unexpected copied corpus")
    if args.offline:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            result = await run_one(next(iter(QUESTIONS.values())), packet["records"],
                                   Path(directory) / "fixture.json", True)
            assert result["adapter_result"]["status"] == "ok", result.get("error")
            assert result["retrieved"] and result["http_attempts"] == 0
        return
    auth = Path(os.environ["CHATGPT_TOKEN_DIR"]) / "auth.json"
    if not auth.is_file():
        raise ValueError("Pilot device authentication file is missing")
    output = src.with_name("live-results")
    output.mkdir()  # Prevent a second live invocation of this pilot.
    for key, question in QUESTIONS.items():
        result = await run_one(question, packet["records"], output / f"{key}.json", False)
        if (result.get("blocked_synchronous_request") or result.get("http_status") in (401, 403)
                or result.get("error", {}).get("status_code") in (401, 403)):
            break


if __name__ == "__main__":
    asyncio.run(main())
