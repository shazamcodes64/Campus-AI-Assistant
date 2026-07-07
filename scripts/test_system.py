#!/usr/bin/env python3
"""
System stress testing script
Tests real messy questions to find pain points
"""

import json
import time
from engines import SearchEngine
from llm import LLMGenerator

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Test queries - intentionally messy and varied
TEST_QUERIES = [
    # Vague queries
    "help",
    "what?",
    "tell me about stuff",
    "information",
    
    # Typos and bad grammar
    "wat is placemnt proces?",
    "how do i get gud grades",
    "sylabbus for cse",
    "requirments for graduaton",
    
    # Long complex queries
    "I need to understand the complete detailed step by step process for campus placement including all the eligibility criteria, documentation required, timeline, interview rounds, and what happens after selection",
    
    # Short keywords
    "gpa",
    "exam",
    "fee",
    "lab",
    
    # Unrelated stuff
    "weather today",
    "best pizza place",
    "how to cook pasta",
    "stock market prices",
    
    # Edge cases
    "",
    "a",
    "?" * 100,
    "placement " * 50,
    
    # Real academic questions (should work)
    "What is the minimum CGPA for placement?",
    "How many credits do I need to graduate?",
    "What are the lab requirements?",
    "When is the final exam?",
    "What subjects are in first year?",
    
    # Ambiguous questions
    "What about the process?",
    "How does it work?",
    "What are the rules?",
    "Can you explain?",
    
    # Multiple topics
    "Tell me about placement and syllabus and fees and everything",
    "I want to know about courses, exams, grades, and graduation requirements"
]

def test_search_engine():
    """Test search engine with messy queries"""
    print("🔍 Testing Search Engine...")
    
    try:
        engine = SearchEngine(config)
        print("✅ Search engine loaded")
    except Exception as e:
        print(f"❌ Failed to load search engine: {e}")
        return False
    
    failures = []
    slow_queries = []
    
    for i, query in enumerate(TEST_QUERIES):
        print(f"\n[{i+1}/{len(TEST_QUERIES)}] Testing: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        
        try:
            start_time = time.time()
            result = engine.search(query)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Check for slow responses
            if response_time > 5.0:
                slow_queries.append({
                    "query": query,
                    "time": response_time
                })
                print(f"  ⚠️  SLOW: {response_time:.2f}s")
            
            # Check result structure
            if not isinstance(result, dict) or "type" not in result:
                failures.append({
                    "query": query,
                    "error": "Invalid result structure",
                    "result": result
                })
                print(f"  ❌ Invalid result structure")
            else:
                print(f"  ✅ {result['type']} (conf: {result.get('confidence', 0):.2f}, time: {response_time:.2f}s)")
        
        except Exception as e:
            failures.append({
                "query": query,
                "error": str(e),
                "result": None
            })
            print(f"  ❌ ERROR: {e}")
    
    # Summary
    print(f"\n📊 SEARCH ENGINE RESULTS:")
    print(f"Total queries: {len(TEST_QUERIES)}")
    print(f"Failures: {len(failures)}")
    print(f"Slow queries (>5s): {len(slow_queries)}")
    
    if failures:
        print(f"\n❌ FAILURES:")
        for failure in failures[:5]:  # Show first 5
            print(f"  Query: '{failure['query'][:50]}'")
            print(f"  Error: {failure['error']}")
    
    if slow_queries:
        print(f"\n⚠️  SLOW QUERIES:")
        for slow in slow_queries[:5]:  # Show first 5
            print(f"  Query: '{slow['query'][:50]}' - {slow['time']:.2f}s")
    
    return len(failures) == 0

def test_llm_generator():
    """Test LLM generator with various contexts"""
    print("\n🤖 Testing LLM Generator...")
    
    try:
        generator = LLMGenerator(config)
        print("✅ LLM generator loaded")
    except Exception as e:
        print(f"❌ Failed to load LLM generator: {e}")
        return False
    
    # Test connection
    if not generator.test_connection():
        print("⚠️  Ollama not available - testing fallback behavior")
    
    # Test different result types
    test_cases = [
        {
            "type": "faq",
            "result": {
                "answer": "Test FAQ answer",
                "confidence": 0.9,
                "sources": ["FAQ: Test question"]
            },
            "confidence": 0.9
        },
        {
            "type": "document", 
            "result": {
                "chunks": [
                    {
                        "text": "This is a test document chunk with some content.",
                        "source": "test.pdf",
                        "page": 1,
                        "score": 0.9
                    }
                ],
                "confidence": 0.7,
                "sources": ["test.pdf (page 1)"]
            },
            "confidence": 0.7
        },
        {
            "type": "out_of_scope",
            "result": {
                "answer": "Out of scope message",
                "sources": []
            },
            "confidence": 0.0
        }
    ]
    
    failures = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n[{i+1}] Testing {test_case['type']} response...")
        
        try:
            start_time = time.time()
            result = generator.generate_response("test query", test_case)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if not isinstance(result, dict) or "answer" not in result:
                failures.append({
                    "type": test_case["type"],
                    "error": "Invalid result structure"
                })
                print(f"  ❌ Invalid result structure")
            else:
                print(f"  ✅ Generated response (time: {response_time:.2f}s)")
                print(f"     Method: {result.get('method', 'unknown')}")
                print(f"     Answer length: {len(result['answer'])} chars")
        
        except Exception as e:
            failures.append({
                "type": test_case["type"],
                "error": str(e)
            })
            print(f"  ❌ ERROR: {e}")
    
    print(f"\n📊 LLM GENERATOR RESULTS:")
    print(f"Test cases: {len(test_cases)}")
    print(f"Failures: {len(failures)}")
    
    if failures:
        print(f"\n❌ FAILURES:")
        for failure in failures:
            print(f"  Type: {failure['type']}")
            print(f"  Error: {failure['error']}")
    
    return len(failures) == 0

def main():
    """Run all tests"""
    print("🧪 CAMPUS AI ASSISTANT - STRESS TESTING")
    print("=" * 50)
    
    search_ok = test_search_engine()
    llm_ok = test_llm_generator()
    
    print("\n" + "=" * 50)
    print("📋 FINAL RESULTS:")
    print(f"Search Engine: {'✅ PASS' if search_ok else '❌ FAIL'}")
    print(f"LLM Generator: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    
    if search_ok and llm_ok:
        print("\n🎉 All tests passed! System is robust.")
    else:
        print("\n⚠️  Some tests failed. Fix issues before deployment.")
        
        print("\n🔧 DEBUGGING TIPS:")
        print("- Check that indices exist: ls data/indices/")
        print("- Verify Ollama is running: curl http://localhost:11434/api/tags")
        print("- Test with simple queries first")
        print("- Check logs for detailed error messages")

if __name__ == "__main__":
    main()