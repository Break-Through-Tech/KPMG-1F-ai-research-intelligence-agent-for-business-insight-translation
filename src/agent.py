from dotenv import load_dotenv
load_dotenv()

import os
from google import genai
from google.genai import types

from retrieval import search_chunks


MODEL_NAME = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = (
    "You are a research assistant that answers business questions using only "
    "the provided research excerpts. Always cite the specific source "
    "(paper title and page number) for each claim you make. "
    "If the excerpts don't contain enough information to answer, "
    "say so clearly rather than guessing."
)


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def format_context(hits):
    """Turn search results into a labeled context block for the prompt."""
    blocks = []

    for hit in hits:
        blocks.append(
            f"[Source: {hit['title']} "
            f"(arXiv:{hit['arxiv_id']}, p.{hit['page_number']})]\n"
            f"{hit['text']}"
        )

    return "\n\n".join(blocks)


def ask_question(question: str, top_k: int = 5) -> dict:
    hits = search_chunks(question, top_k=top_k)

    if not hits:
        return {
            "answer": "No relevant research found in the indexed papers for this question.",
            "sources": []
        }

    context = format_context(hits)

    user_prompt = (
        f"Question: {question}\n\n"
        f"Relevant research excerpts:\n{context}\n\n"
        "Answer the question, translating the findings into clear "
        "business implications. Cite the paper title and page number "
        "for every claim."
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )

    return {
        "answer": response.text,
        "sources": [
            {
                "title": h["title"],
                "pdf_url": h["pdf_url"],
                "page": h["page_number"]
            }
            for h in hits
        ]
    }

if __name__ == "__main__":
    questions = [
        "What capabilities and limitations does MCP-Atlas identify when evaluating LLM tool use with real MCP servers?",
        "What risks or failure modes of AI agents are identified in research on agentic misalignment?",
        "How does multi-turn interaction affect the robustness of LLM unlearning?",
        "What approaches are used to improve the interpretability of neural network representations?",
        "How does Continuous-Utility Direct Preference Optimization use continuous utility scores during preference optimization?",        "How do single-agent and multi-agent approaches compare in agentic trip-planning tasks?",
        "What are the different approaches used to evaluate safety and reliability in LLM agents?",
        "What should a company evaluate before giving an AI system access to external tools or MCP servers?",
        "What risks should a business consider when deploying autonomous AI agents in workflows where the system can take actions on its own?",
        'If a vendor claims that its AI system is safe or reliable, what evidence should a business look for before trusting that claim?',
    ]

    for i, question in enumerate(questions, start=1):
        print("\n" + "=" * 80)
        print(f"QUESTION {i}")
        print("=" * 80)
        print(question)

        result = ask_question(question)

        print("\nANSWER:")
        print(result["answer"])

        print("\nSOURCES:")

        for source in result["sources"]:
            print(
                f"- {source['title']} "
                f"(p.{source['page']}) — {source['pdf_url']}"
            )