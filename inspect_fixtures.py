import json
from pathlib import Path
from src.summarization import summarize

fixture_dir = Path("tests/fixtures/summarization")

for fixture_path in sorted(fixture_dir.glob("*.json")):
    print(f"\n==========================================")
    print(f" Fixture: {fixture_path.name}")
    print(f"==========================================")
    
    fx = json.loads(fixture_path.read_text(encoding="utf-8"))
    
    # Run summarize with the fixture's fake model response
    result = summarize(
        fx["query"], 
        fx["passages"], 
        generate=lambda prompt: json.dumps(fx["model_response"])
    )
    
    print(f"Query:  {result['query']}")
    print(f"Status: {result['status']}")
    if result.get("error"):
        print(f"Error:  {result['error']}")
        
    print("\nClaims:")
    if result["claims"]:
        for i, claim in enumerate(result["claims"], 1):
            print(f"  {i}. {claim['text']}")
            print(f"     Cited Chunks: {claim['chunk_ids']}")
    else:
        print("  (No claims generated)")
        
    print("\nLimitations:")
    if result["limitations"]:
        for lim in result["limitations"]:
            print(f"  - {lim}")
    else:
        print("  (None)")