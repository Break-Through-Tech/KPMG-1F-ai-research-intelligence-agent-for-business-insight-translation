"""Try summarize() on the real index.

Run from the repo root:
    python3 try_summarize.py "your question"            # wiring check, fake model
    python3 try_summarize.py "your question" --real     # real model (needs GOOGLE_API_KEY; optional GOOGLE_MODEL)
"""

import argparse
import json
from src.retrieval import search
from src.summarization import summarize


def make_real_generate():
    from src.generation import create_generate

    generate, _ = create_generate()
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

    def generate(prompt, **kwargs):
        try:
            return inner(prompt, **kwargs)
        except Exception as exc:
            print("\nGENERATION ERROR:", exc)
            raise

    generate.supports_response_schema = getattr(inner, 'supports_response_schema', False) is True
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
