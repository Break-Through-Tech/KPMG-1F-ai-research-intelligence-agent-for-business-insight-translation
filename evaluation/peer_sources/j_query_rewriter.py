from __future__ import annotations

import re

# Replace business-style phrases with research terms before retrieval.
PHRASE_REPLACEMENTS = {
    "carry out the plans they say they will follow": "plan execution adherence",
    "how confident an ai model is in its own answer": "language model confidence uncertainty calibration",
    "memory and compute cost": "memory compute efficiency",
    "step-by-step reasoning": "chain-of-thought reasoning trace faithfulness",
    "different ai language models": "large language model comparison",
    "how should a company check for it": "organizational bias auditing",
    "simulated users": "user simulators",
    "simulated user": "user simulator",
    "ai agent benchmark": "llm agent benchmark evaluation",
    "ai agents": "llm agents",
    "ai agent": "llm agent",
    "gender bias": "gender bias evaluation",
    "long-context language models": "long-context llm inference",
    "without losing accuracy": "accuracy preservation",
}

# Remove common words that add little value to the search query.
STOP_WORDS = {
    "a", "an", "the", "what", "how", "can", "could", "does", "do", "did",
    "is", "are", "was", "were", "be", "been", "being", "to", "of", "in",
    "on", "for", "and", "or", "it", "its", "they", "their", "should",
}


def _normalize(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("query must be a string")

    text = re.sub(r"\s+", " ", text.strip())

    if not text:
        raise ValueError("query cannot be empty")

    return text


def rewrite_query(question: str) -> str:
    text = _normalize(question).lower()

    # Use longest phrase first so shorter replacements do not interfere.
    for source, target in sorted(
        PHRASE_REPLACEMENTS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        text = text.replace(source, target)

    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)

    tokens = [
        token
        for token in text.split()
        if token not in STOP_WORDS
    ]

    # Keep the first occurrence of each term to make the query compact.
    seen: set[str] = set()
    compact: list[str] = []

    for token in tokens:
        if token not in seen:
            compact.append(token)
            seen.add(token)

    return " ".join(compact)


if __name__ == "__main__":
    benchmark_questions = [
        (
            "How much can the choice of simulated user change the results "
            "of an AI agent benchmark, and what mistake do simulated users "
            "make most often?"
        ),
        (
            "Can an AI model's step-by-step reasoning be trusted as a "
            "record of how it reached its answer?"
        ),
        (
            "Do AI agents actually carry out the plans they say they "
            "will follow?"
        ),
        (
            "How consistent is gender bias across different AI language "
            "models, and how should a company check for it?"
        ),
        (
            "How can a company estimate how confident an AI model is "
            "in its own answer?"
        ),
        (
            "How can the memory and compute cost of running long-context "
            "language models be reduced without losing accuracy?"
        ),
    ]

    for number, question in enumerate(benchmark_questions, start=1):
        print(f"\nQ{number}")
        print("Original:")
        print(question)
        print("\nRewritten:")
        print(rewrite_query(question))
        print("-" * 70)
