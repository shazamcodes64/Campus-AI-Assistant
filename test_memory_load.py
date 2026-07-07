"""Test memory behavior under load with multiple queries"""

import json
import time
from memory_monitor import get_monitor, log_memory, trigger_gc_with_logging

print("="*60)
print("Memory Load Test - Multiple Queries")
print("="*60)

# Initialize
with open("config.json", "r") as f:
    config = json.load(f)

from engines import SearchEngine
from llm import LLMGenerator

monitor = get_monitor()
monitor.set_baseline()

# Load engines
print("\n📦 Loading engines...")
log_memory("before loading")
search_engine = SearchEngine(config)
llm_gen = LLMGenerator(config)
log_memory("after loading")

# Test queries
test_queries = [
    "What is the placement process?",
    "How do I register for courses?",
    "What are the graduation requirements?",
    "When is the academic calendar?",
    "How do I apply for scholarships?",
    "What is the refund policy?",
    "How do I change my major?",
    "What are the library hours?",
    "How do I access online resources?",
    "What is the grading system?"
]

print(f"\n🔄 Running {len(test_queries)} queries...")
print("-"*60)

results = []
for i, query in enumerate(test_queries, 1):
    print(f"\nQuery {i}/{len(test_queries)}: {query[:50]}...")
    
    # Log memory before
    mem_before = monitor.get_memory_usage()
    
    # Search
    search_result = search_engine.search(query)
    
    # Generate response
    response = llm_gen.generate_response(query, search_result)
    
    # Log memory after
    mem_after = monitor.get_memory_usage()
    mem_delta = mem_after["rss_mb"] - mem_before["rss_mb"]
    
    results.append({
        "query": query,
        "type": search_result["type"],
        "confidence": search_result["confidence"],
        "mem_before": mem_before["rss_mb"],
        "mem_after": mem_after["rss_mb"],
        "mem_delta": mem_delta
    })
    
    print(f"  Type: {search_result['type']}, Confidence: {search_result['confidence']:.2f}")
    print(f"  Memory: {mem_before['rss_mb']:.2f} MB → {mem_after['rss_mb']:.2f} MB (Δ {mem_delta:+.2f} MB)")
    
    # Periodic GC every 3 queries
    if i % 3 == 0:
        print(f"  🗑️  Periodic GC trigger...")
        trigger_gc_with_logging(f"after query {i}")

print("\n" + "="*60)
print("LOAD TEST RESULTS")
print("="*60)

# Calculate statistics
total_delta = sum(r["mem_delta"] for r in results)
avg_delta = total_delta / len(results)
max_delta = max(r["mem_delta"] for r in results)
min_delta = min(r["mem_delta"] for r in results)

print(f"\nQueries processed: {len(results)}")
print(f"Total memory growth: {total_delta:+.2f} MB")
print(f"Average per query: {avg_delta:+.2f} MB")
print(f"Max delta: {max_delta:+.2f} MB")
print(f"Min delta: {min_delta:+.2f} MB")

# Route distribution
route_counts = {}
for r in results:
    route_counts[r["type"]] = route_counts.get(r["type"], 0) + 1

print(f"\nRoute distribution:")
for route, count in route_counts.items():
    print(f"  {route}: {count} ({count/len(results)*100:.1f}%)")

# Final GC and summary
print("\n🗑️  Final garbage collection...")
trigger_gc_with_logging("final cleanup")

print("\n")
monitor.print_summary()

# Memory growth check
final_mem = monitor.get_memory_usage()
delta = monitor.get_memory_delta()

print("="*60)
print("MEMORY HEALTH CHECK")
print("="*60)

if delta["rss_delta_mb"] < 100:
    print("✅ Memory growth is healthy (<100 MB)")
elif delta["rss_delta_mb"] < 200:
    print("⚠️  Memory growth is moderate (100-200 MB)")
else:
    print("❌ Memory growth is high (>200 MB)")

print(f"\nFinal memory: {final_mem['rss_mb']:.2f} MB")
print(f"Peak memory: {monitor.peak_memory:.2f} MB")
print(f"Total growth: {delta['rss_delta_mb']:+.2f} MB")

print("\n✅ Load test completed!")
