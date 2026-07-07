import csv
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines import SearchEngine
from llm import LLMGenerator

# -----------------
# LOAD FAILURES
# -----------------

print("🔍 Failure Hunter - Analyzing eval_results.csv\n")

try:
    with open("eval_results.csv", "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
except FileNotFoundError:
    print("❌ eval_results.csv not found. Run auto_eval.py first.")
    exit(1)

# -----------------
# IDENTIFY FAILURES
# -----------------

failures = []
for row in rows:
    missing = row["missing"].lower() == "true"
    has_sources = row["has_sources"].lower() == "true"
    confidence = float(row["confidence"])
    
    # Failure criteria
    if missing or not has_sources or confidence < 0.5:
        failures.append({
            "query": row["query"],
            "latency": float(row["latency"]),
            "confidence": confidence,
            "missing": missing,
            "has_sources": has_sources
        })

if not failures:
    print("✅ No failures found! All queries passed.")
    exit(0)

print(f"Found {len(failures)} failures:\n")

# -----------------
# DETAILED ANALYSIS
# -----------------

with open("config.json") as f:
    config = json.load(f)

engine = SearchEngine(config)
llm = LLMGenerator(config)

for idx, fail in enumerate(failures, 1):
    print(f"{'='*60}")
    print(f"FAILURE #{idx}: {fail['query']}")
    print(f"{'='*60}")
    print(f"Confidence: {fail['confidence']}")
    print(f"Has sources: {fail['has_sources']}")
    print(f"Missing response: {fail['missing']}")
    print()
    
    # Re-run to get detailed output
    search_result = engine.search(fail['query'])
    response = llm.generate_response(fail['query'], search_result)
    
    print("SEARCH RESULTS:")
    if search_result:
        for i, doc in enumerate(search_result[:3], 1):
            print(f"  {i}. {doc.get('text', '')[:100]}...")
    else:
        print("  (no results)")
    
    print("\nGENERATED RESPONSE:")
    print(f"  {response.get('answer', '')[:200]}...")
    
    print("\nSOURCES:")
    sources = response.get('sources', [])
    if sources:
        for src in sources:
            print(f"  - {src}")
    else:
        print("  (none)")
    
    print()

print(f"\n{'='*60}")
print(f"SUMMARY: {len(failures)} failures analyzed")
print(f"{'='*60}")
