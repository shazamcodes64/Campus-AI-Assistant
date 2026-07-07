#!/usr/bin/env python3
"""Ultra-fast smoke test - no heavy model loading"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json

print("🚀 Quick System Test\n")

# Test 1: Config exists
print("[1/5] Checking config...", end=" ")
try:
    with open("config.json") as f:
        config = json.load(f)
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

# Test 2: Indices exist
print("[2/5] Checking indices...", end=" ")
import os
required_files = [
    "data/indices/faiss.index",
    "data/indices/bm25_index.pkl",
    "data/indices/metadata.json"
]
missing = [f for f in required_files if not os.path.exists(f)]
if missing:
    print(f"✗ Missing: {missing}")
    sys.exit(1)
print("✓")

# Test 3: Ollama connection
print("[3/5] Testing Ollama...", end=" ")
import requests
try:
    response = requests.get(f"{config['ollama_url']}/api/tags", timeout=2)
    if response.status_code == 200:
        print("✓")
    else:
        print(f"⚠ Status {response.status_code}")
except Exception as e:
    print(f"✗ {str(e)[:40]}")

# Test 4: Import modules
print("[4/5] Importing modules...", end=" ")
try:
    from engines import SearchEngine
    from llm import LLMGenerator
    print("✓")
except Exception as e:
    print(f"✗ {e}")
    sys.exit(1)

# Test 5: Single query test
print("[5/5] Running single query test...")
print("    Loading models (this takes ~10-15s)...", end=" ", flush=True)
start = time.time()
try:
    engine = SearchEngine(config)
    llm = LLMGenerator(config)
    load_time = round(time.time() - start, 1)
    print(f"✓ ({load_time}s)")
    
    # Test query
    test_query = "What is the syllabus?"
    print(f"    Testing: '{test_query}'...", end=" ", flush=True)
    
    start = time.time()
    search_result = engine.search(test_query)
    response = llm.generate_response(test_query, search_result)
    query_time = round(time.time() - start, 2)
    
    has_answer = bool(response.get("answer"))
    has_sources = bool(response.get("sources"))
    confidence = response.get("confidence", 0)
    
    print(f"✓ ({query_time}s)")
    print(f"    Confidence: {confidence:.2f}")
    print(f"    Sources: {len(response.get('sources', []))}")
    print(f"    Answer preview: {response.get('answer', '')[:100]}...")
    
except Exception as e:
    print(f"✗ {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed!")
print(f"\nEstimated time for 50 queries: ~{50 * query_time}s ({round(50 * query_time / 60, 1)}min)")
