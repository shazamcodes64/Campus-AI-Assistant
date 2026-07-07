#!/usr/bin/env python3
"""
Load testing script for Campus AI Assistant
Tests concurrent user scenarios and measures performance
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import threading
import statistics
from datetime import datetime
from engines import SearchEngine
from llm import LLMGenerator

# Test queries representing typical student usage
TEST_QUERIES = [
    "What is the syllabus?",
    "How many credits is this course?",
    "What is the exam pattern?",
    "What is the attendance policy?",
    "What is the placement process?",
    "How are internal marks calculated?",
    "What are the lab requirements?",
    "When is the project deadline?",
    "What is the grading system?",
    "How do I apply for revaluation?",
]

class LoadTester:
    def __init__(self, config_path="config.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.results = []
        self.errors = []
        self.lock = threading.Lock()
        
    def single_query_test(self, query, user_id):
        """Execute a single query and record metrics"""
        start_time = time.time()
        
        try:
            # Initialize components (simulates user session)
            engine = SearchEngine(self.config)
            llm = LLMGenerator(self.config)
            
            # Execute query
            search_result = engine.search(query)
            response = llm.generate_response(query, search_result)
            
            end_time = time.time()
            latency = end_time - start_time
            
            # Record result
            with self.lock:
                self.results.append({
                    "user_id": user_id,
                    "query": query,
                    "latency": latency,
                    "confidence": response.get("confidence", 0),
                    "method": response.get("method", "unknown"),
                    "has_sources": bool(response.get("sources")),
                    "timestamp": datetime.now().isoformat()
                })
            
            return True
            
        except Exception as e:
            with self.lock:
                self.errors.append({
                    "user_id": user_id,
                    "query": query,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            return False
    
    def user_session(self, user_id, num_queries=5):
        """Simulate a user session with multiple queries"""
        print(f"[User {user_id}] Starting session...")
        
        for i in range(num_queries):
            query = TEST_QUERIES[i % len(TEST_QUERIES)]
            success = self.single_query_test(query, user_id)
            
            if success:
                print(f"[User {user_id}] Query {i+1}/{num_queries} completed")
            else:
                print(f"[User {user_id}] Query {i+1}/{num_queries} FAILED")
            
            # Small delay between queries (realistic user behavior)
            time.sleep(1)
        
        print(f"[User {user_id}] Session complete")
    
    def concurrent_load_test(self, num_users=10, queries_per_user=5):
        """Test with concurrent users"""
        print(f"\n{'='*60}")
        print(f"LOAD TEST: {num_users} concurrent users, {queries_per_user} queries each")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Create threads for concurrent users
        threads = []
        for user_id in range(1, num_users + 1):
            thread = threading.Thread(
                target=self.user_session,
                args=(user_id, queries_per_user)
            )
            threads.append(thread)
        
        # Start all threads
        print(f"Starting {num_users} concurrent user sessions...\n")
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print(f"LOAD TEST COMPLETE")
        print(f"{'='*60}\n")
        
        return total_time
    
    def analyze_results(self):
        """Analyze and display test results"""
        if not self.results:
            print("❌ No results to analyze")
            return
        
        # Calculate metrics
        latencies = [r["latency"] for r in self.results]
        confidences = [r["confidence"] for r in self.results]
        
        total_queries = len(self.results)
        total_errors = len(self.errors)
        success_rate = (total_queries / (total_queries + total_errors)) * 100 if (total_queries + total_errors) > 0 else 0
        
        # Latency statistics
        avg_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]
        
        # Confidence statistics
        avg_confidence = statistics.mean(confidences)
        
        # Method distribution
        methods = {}
        for r in self.results:
            method = r["method"]
            methods[method] = methods.get(method, 0) + 1
        
        # Sources statistics
        with_sources = sum(1 for r in self.results if r["has_sources"])
        source_rate = (with_sources / total_queries) * 100
        
        # Print report
        print("\n" + "="*60)
        print("PERFORMANCE REPORT")
        print("="*60)
        
        print(f"\n📊 Overall Statistics:")
        print(f"  Total queries: {total_queries}")
        print(f"  Successful: {total_queries}")
        print(f"  Failed: {total_errors}")
        print(f"  Success rate: {success_rate:.1f}%")
        
        print(f"\n⏱️  Latency (seconds):")
        print(f"  Average: {avg_latency:.2f}s")
        print(f"  Median: {median_latency:.2f}s")
        print(f"  Min: {min_latency:.2f}s")
        print(f"  Max: {max_latency:.2f}s")
        print(f"  P95: {p95_latency:.2f}s")
        print(f"  P99: {p99_latency:.2f}s")
        
        print(f"\n🎯 Confidence:")
        print(f"  Average: {avg_confidence:.2f}")
        
        print(f"\n📚 Sources:")
        print(f"  Queries with sources: {with_sources}/{total_queries} ({source_rate:.1f}%)")
        
        print(f"\n🔧 Response Methods:")
        for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_queries) * 100
            print(f"  {method}: {count} ({percentage:.1f}%)")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  User {error['user_id']}: {error['error'][:80]}")
        
        # Performance assessment
        print(f"\n{'='*60}")
        print("ASSESSMENT")
        print("="*60)
        
        issues = []
        
        if p95_latency > 10:
            issues.append(f"⚠️  P95 latency ({p95_latency:.2f}s) exceeds 10s target")
        else:
            print(f"✅ P95 latency ({p95_latency:.2f}s) meets <10s target")
        
        if avg_latency > 5:
            issues.append(f"⚠️  Average latency ({avg_latency:.2f}s) exceeds 5s target")
        else:
            print(f"✅ Average latency ({avg_latency:.2f}s) is acceptable")
        
        if success_rate < 95:
            issues.append(f"⚠️  Success rate ({success_rate:.1f}%) below 95% target")
        else:
            print(f"✅ Success rate ({success_rate:.1f}%) meets target")
        
        if source_rate < 80:
            issues.append(f"⚠️  Source rate ({source_rate:.1f}%) below 80% target")
        else:
            print(f"✅ Source rate ({source_rate:.1f}%) is good")
        
        if issues:
            print(f"\n⚠️  Issues Found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"\n🎉 All performance targets met!")
        
        print()
    
    def save_results(self, filename="load_test_results.json"):
        """Save detailed results to file"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "errors": self.errors,
            "summary": {
                "total_queries": len(self.results),
                "total_errors": len(self.errors),
                "success_rate": (len(self.results) / (len(self.results) + len(self.errors))) * 100 if (len(self.results) + len(self.errors)) > 0 else 0
            }
        }
        
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"📁 Detailed results saved to {filename}")

def main():
    """Run load tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test Campus AI Assistant")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users (default: 10)")
    parser.add_argument("--queries", type=int, default=5, help="Queries per user (default: 5)")
    parser.add_argument("--output", type=str, default="load_test_results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    print("🚀 Campus AI Assistant - Load Testing")
    print(f"Configuration: {args.users} users, {args.queries} queries each")
    print()
    
    # Initialize tester
    tester = LoadTester()
    
    # Run load test
    total_time = tester.concurrent_load_test(
        num_users=args.users,
        queries_per_user=args.queries
    )
    
    print(f"Total test duration: {total_time:.2f}s")
    
    # Analyze results
    tester.analyze_results()
    
    # Save results
    tester.save_results(args.output)
    
    # Exit code based on success
    if len(tester.errors) > 0:
        print("\n⚠️  Test completed with errors")
        sys.exit(1)
    else:
        print("\n✅ Test completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
