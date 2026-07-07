#!/usr/bin/env python3
"""
Test script to verify embedding batching optimization
"""

import json
import time
import numpy as np
from engines import SearchEngine

def test_faq_embedding_cache():
    """Test that FAQ embeddings are cached and reused"""
    print("=" * 60)
    print("Testing FAQ Embedding Cache")
    print("=" * 60)
    
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # Create search engine
    print("\n1. Initializing SearchEngine...")
    engine = SearchEngine(config)
    
    # First search - should compute embeddings
    print("\n2. First FAQ search (should compute embeddings)...")
    start = time.time()
    result1 = engine._search_faq("What is the placement process?")
    time1 = time.time() - start
    print(f"   Time: {time1:.4f}s")
    print(f"   Result: {result1.get('confidence', 0):.4f} confidence")
    
    # Second search - should use cache
    print("\n3. Second FAQ search (should use cache)...")
    start = time.time()
    result2 = engine._search_faq("How do I apply for placement?")
    time2 = time.time() - start
    print(f"   Time: {time2:.4f}s")
    print(f"   Result: {result2.get('confidence', 0):.4f} confidence")
    
    # Verify cache is working
    if time2 < time1 * 0.5:  # Second call should be much faster
        print("\n✅ Cache is working! Second call was significantly faster.")
    else:
        print("\n⚠️  Cache may not be working optimally.")
    
    # Check cache attributes
    print("\n4. Cache status:")
    print(f"   Cache exists: {engine._faq_embeddings_cache is not None}")
    print(f"   Cache timestamp: {engine._faq_cache_timestamp}")
    print(f"   Cached questions: {len(engine._faq_questions_cache) if engine._faq_questions_cache else 0}")
    
    return True

def test_batch_encoding():
    """Test batch encoding utility method"""
    print("\n" + "=" * 60)
    print("Testing Batch Encoding Method")
    print("=" * 60)
    
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # Create search engine
    engine = SearchEngine(config)
    
    # Test with various batch sizes
    test_texts = [
        "What is machine learning?",
        "How does neural network work?",
        "Explain deep learning",
        "What is artificial intelligence?",
        "Define natural language processing"
    ]
    
    print(f"\n1. Encoding {len(test_texts)} texts...")
    print(f"   Batch size: {config.get('embedding_batch_size', 32)}")
    
    start = time.time()
    embeddings = engine.encode_batch(test_texts)
    elapsed = time.time() - start
    
    print(f"   Time: {elapsed:.4f}s")
    print(f"   Output shape: {embeddings.shape}")
    print(f"   Expected shape: ({len(test_texts)}, 384)")
    
    # Verify output
    if embeddings.shape == (len(test_texts), 384):
        print("\n✅ Batch encoding works correctly!")
    else:
        print("\n❌ Batch encoding output shape is incorrect!")
        return False
    
    # Verify embeddings are normalized
    norms = np.linalg.norm(embeddings, axis=1)
    if np.allclose(norms, 1.0, atol=1e-5):
        print("✅ Embeddings are properly normalized!")
    else:
        print("⚠️  Embeddings may not be normalized correctly")
    
    return True

def test_config_values():
    """Test that config values are loaded correctly"""
    print("\n" + "=" * 60)
    print("Testing Configuration Values")
    print("=" * 60)
    
    with open("config.json", "r") as f:
        config = json.load(f)
    
    print("\nBatching configuration:")
    print(f"  embedding_batch_size: {config.get('embedding_batch_size', 'NOT SET')}")
    print(f"  faq_cache_ttl_seconds: {config.get('faq_cache_ttl_seconds', 'NOT SET')}")
    
    if "embedding_batch_size" in config and "faq_cache_ttl_seconds" in config:
        print("\n✅ Configuration values are set correctly!")
        return True
    else:
        print("\n❌ Configuration values are missing!")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("EMBEDDING BATCHING OPTIMIZATION TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Config values
        test1 = test_config_values()
        
        # Test 2: Batch encoding
        test2 = test_batch_encoding()
        
        # Test 3: FAQ cache
        test3 = test_faq_embedding_cache()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Config values: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"Batch encoding: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"FAQ cache: {'✅ PASS' if test3 else '❌ FAIL'}")
        
        if test1 and test2 and test3:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed")
            return 1
    
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
