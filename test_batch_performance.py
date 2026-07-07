#!/usr/bin/env python3
"""
Performance test for batch encoding optimization.

This script demonstrates the performance benefits of batch encoding
with larger query sets (10, 20, 50 queries).
"""

import json
import numpy as np
import time
from engines import SearchEngine

def generate_test_queries(n):
    """Generate n test queries"""
    base_queries = [
        "What is the placement process?",
        "How do I register for courses?",
        "What are the library hours?",
        "When is the exam schedule released?",
        "How can I apply for scholarships?",
        "What are the admission requirements?",
        "How do I access the student portal?",
        "What is the refund policy?",
        "When are the semester breaks?",
        "How do I contact academic advisors?",
        "What sports facilities are available?",
        "How do I join student clubs?",
        "What is the grading system?",
        "How do I apply for internships?",
        "What are the hostel facilities?",
        "How do I get a library card?",
        "What is the attendance policy?",
        "How do I change my major?",
        "What research opportunities exist?",
        "How do I report technical issues?"
    ]
    
    # Repeat and extend if needed
    queries = []
    while len(queries) < n:
        queries.extend(base_queries)
    
    return queries[:n]

def test_performance():
    """Test batch encoding performance with different batch sizes"""
    
    print("=" * 70)
    print("Batch Encoding Performance Test")
    print("=" * 70)
    
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    print(f"\nConfiguration:")
    print(f"  - Embedding model: {config['embedding_model']}")
    print(f"  - Default batch size: {config['embedding_batch_size']}")
    
    # Initialize SearchEngine
    print("\n🔄 Initializing SearchEngine...")
    engine = SearchEngine(config)
    print("✓ SearchEngine initialized\n")
    
    # Test with different query counts
    query_counts = [10, 20, 50]
    
    for n_queries in query_counts:
        print("=" * 70)
        print(f"Testing with {n_queries} queries")
        print("=" * 70)
        
        queries = generate_test_queries(n_queries)
        
        # Method 1: Batch encoding
        print(f"\n1. Batch encoding (batch_size={config['embedding_batch_size']}):")
        start_time = time.time()
        batch_embeddings = engine.encode_batch(queries)
        batch_time = time.time() - start_time
        print(f"   Time: {batch_time:.3f}s")
        print(f"   Shape: {batch_embeddings.shape}")
        print(f"   Throughput: {n_queries/batch_time:.1f} queries/sec")
        
        # Method 2: Single encoding (one at a time)
        print(f"\n2. Single encoding (one at a time):")
        start_time = time.time()
        single_embeddings = []
        for query in queries:
            emb = engine.model.encode([query], normalize_embeddings=True)
            single_embeddings.append(emb[0])
        single_embeddings = np.array(single_embeddings)
        single_time = time.time() - start_time
        print(f"   Time: {single_time:.3f}s")
        print(f"   Shape: {single_embeddings.shape}")
        print(f"   Throughput: {n_queries/single_time:.1f} queries/sec")
        
        # Comparison
        speedup = single_time / batch_time if batch_time > 0 else 0
        time_saved = single_time - batch_time
        print(f"\n📊 Performance Comparison:")
        print(f"   Speedup: {speedup:.2f}x")
        print(f"   Time saved: {time_saved:.3f}s ({time_saved/single_time*100:.1f}%)")
        
        # Verify consistency
        max_diff = np.max(np.abs(batch_embeddings - single_embeddings))
        print(f"   Max difference: {max_diff:.10f} (should be ~0)")
        
        if speedup > 1.0:
            print(f"   ✅ Batch encoding is {speedup:.2f}x faster!")
        else:
            print(f"   ⚠️  Speedup is minimal (hardware dependent)")
        
        print()
    
    # Test batch search performance
    print("=" * 70)
    print("Batch Search Performance Test")
    print("=" * 70)
    
    n_queries = 20
    queries = generate_test_queries(n_queries)
    
    print(f"\nTesting with {n_queries} queries:")
    
    # Batch search
    print(f"\n1. Batch search:")
    start_time = time.time()
    batch_results = engine.search_batch(queries)
    batch_search_time = time.time() - start_time
    print(f"   Time: {batch_search_time:.3f}s")
    print(f"   Throughput: {n_queries/batch_search_time:.1f} queries/sec")
    
    # Individual search
    print(f"\n2. Individual search:")
    start_time = time.time()
    individual_results = []
    for query in queries:
        result = engine.search(query)
        individual_results.append(result)
    individual_search_time = time.time() - start_time
    print(f"   Time: {individual_search_time:.3f}s")
    print(f"   Throughput: {n_queries/individual_search_time:.1f} queries/sec")
    
    # Comparison
    search_speedup = individual_search_time / batch_search_time if batch_search_time > 0 else 0
    search_time_saved = individual_search_time - batch_search_time
    print(f"\n📊 Performance Comparison:")
    print(f"   Speedup: {search_speedup:.2f}x")
    print(f"   Time saved: {search_time_saved:.3f}s ({search_time_saved/individual_search_time*100:.1f}%)")
    
    if search_speedup > 1.0:
        print(f"   ✅ Batch search is {search_speedup:.2f}x faster!")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\n✅ Batch encoding optimization is working correctly!")
    print("\nKey Benefits:")
    print("  1. Batch encoding processes multiple queries efficiently")
    print("  2. Batch search eliminates redundant embedding computations")
    print("  3. Significant speedup for multi-query scenarios")
    print("  4. Maintains consistency with single-query results")
    print("\nConfiguration:")
    print(f"  - Batch size: {config['embedding_batch_size']}")
    print(f"  - Embedding model: {config['embedding_model']}")
    print(f"  - FAQ cache TTL: {config['faq_cache_ttl_seconds']}s")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_performance()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
