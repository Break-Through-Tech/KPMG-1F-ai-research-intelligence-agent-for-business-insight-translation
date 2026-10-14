from retrieval import search_chunks


QUESTIONS = [
    "What capabilities and limitations does MCP-Atlas identify when evaluating LLM tool use with real MCP servers?",
    "What risks or failure modes of AI agents are identified in research on agentic misalignment?",
    "How does multi-turn interaction affect the robustness of LLM unlearning?",
    "What approaches are used to improve the interpretability of neural network representations?",
    "How does Continuous-Utility Direct Preference Optimization use continuous utility scores during preference optimization?",
    "How do single-agent and multi-agent approaches compare in agentic trip-planning tasks?",
    "What are the different approaches used to evaluate safety and reliability in LLM agents?",
    "What should a company evaluate before giving an AI system access to external tools or MCP servers?",
    "What risks should a business consider when deploying autonomous AI agents in workflows where the system can take actions on its own?",
    "If a vendor claims that its AI system is safe or reliable, what evidence should a business look for before trusting that claim?",
]


for i, question in enumerate(QUESTIONS, start=1):
    print("\n" + "=" * 100)
    print(f"QUESTION {i}")
    print("=" * 100)
    print(question)

    hits = search_chunks(question, top_k=5)

    for rank, hit in enumerate(hits, start=1):
        print("\n" + "-" * 80)
        print(f"CHUNK {rank}")
        print(f"Title: {hit['title']}")
        print(f"Page: {hit['page_number']}")
        print(f"arXiv ID: {hit['arxiv_id']}")
        print("-" * 80)
        print(hit["text"])