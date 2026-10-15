"""Synthetic ResearchResult fixture for review bridge tests."""
def demo_request():
    return {"query": "agents", "top_k": 5, "industry": "banking", "jurisdiction": "US"}
def demo_result():
    return {
        "schema_version": "1.0", "request": demo_request(),
        "evidence": [{"chunk_id": "c1", "text": "Passage one", "source_url": "https://example.org/1", "page_number": 1}],
        "summary": {"status": "ok", "query": "agents", "claims": [{"text": "Claim A", "chunk_ids": ["c1"]}], "limitations": []},
        "business_insight": {"status": "ok", "industry": "banking", "implications": [{"text": "Implication A", "chunk_ids": ["c1"], "suggested_action": "Investigate", "assumptions": []}], "risks": [], "limitations": []},
        "provenance": {}, "regulatory_checkpoint": None,
        "human_review": {"status": "pending", "reviewer": None, "notes": None}, "approved": False,
    }
