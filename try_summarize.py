"""Try summarize() on the real index.

Run from the repo root:
    python3 try_summarize.py "your question"            # wiring check, fake model
    python3 try_summarize.py "your question" --real     # real model (needs GEMINI_API_KEY)
"""

import argparse
import json
import os

try:  # optional: load GEMINI_API_KEY from a git-ignored .env file
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


from src.retrieval import search
from src.summarization import summarize


def make_real_generate():
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["LLM_API_KEY"],
        base_url=os.environ["LLM_BASE_URL"],
    )
    model = os.environ["LLM_MODEL"]

    def generate(prompt):
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return resp.choices[0].message.content

    return generate


def make_fake_generate(passages):
    def generate(prompt):
        return json.dumps({
            "status": "ok",
            "claims": [{"text": "Top passage (wiring check only).",
                        "chunk_ids": [passages[0]["chunk_id"]]}],
            "limitations": [],
        })

    return generate


def with_error_print(inner):
    """Local debugging only: summarize() hides exception text on purpose."""

    def generate(prompt):
        try:
            return inner(prompt)
        except Exception as exc:
            print("\nGENERATION ERROR:", exc)
            raise

    return generate


def describe_location(p):
    if p.get("page_number"):
        return f"p.{p['page_number']}"
    return p.get("html_url") or "html"


parser = argparse.ArgumentParser()
parser.add_argument("query")
parser.add_argument("--top-k", type=int, default=5)
parser.add_argument("--real", action="store_true", help="use Gemini instead of the fake model")
args = parser.parse_args()

passages = search(args.query, args.top_k)
print(f"Retrieved {len(passages)} passages")
if not passages:
    raise SystemExit("Index returned nothing; rebuild it first.")

if args.real:
    if not os.environ.get("LLM_API_KEY"):
        raise SystemExit("Set LLM_API_KEY, LLM_BASE_URL and LLM_MODEL first.")
    generate = with_error_print(make_real_generate())
else:
    generate = make_fake_generate(passages)

result = summarize(args.query, passages, generate=generate)
by_id = {p["chunk_id"]: p for p in passages}

print(f"\nstatus: {result['status']}   error: {result['error']}")
for i, claim in enumerate(result["claims"], 1):
    print(f"\nCLAIM {i}: {claim['text']}")
    for cid in claim["chunk_ids"]:
        p = by_id[cid]
        print(f"  cites {cid} ({p['title']}, {describe_location(p)}):")
        print(f"    {p['text'][:1500]}")
print("\nlimitations:")
for note in result["limitations"]:
    print(f"  - {note}")
print("\nomitted by size limit:", result["omitted_chunk_ids"])