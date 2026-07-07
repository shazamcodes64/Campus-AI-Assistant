#!/usr/bin/env python3
"""
Comprehensive Performance Testing Script
Tests concurrent sessions, response times, and memory usage

Tasks covered:
- 9.6: Test with 10 concurrent sessions
- 9.7: Measure and optimize response time (<5-10s target)
- 9.8: Validate memory usage (<4GB typical, <8GB peak)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import threading
import statistics
from datetime import datetime
from typing import List, Dict, Any
from memory_monitor import MemoryMonitor, get_monitor, trigger_gc_with_logging
from engines import SearchEngine
from llm import LLMGenerator

# Test queries representing realistic student usage patterns
TEST_QUERIES = [
    "What is the placement process?",
    "How do I register for courses?",
    "What are the graduation requirements?",
    "When is the academic calendar?",
    "How do I apply for scholarships?",
    "What is the refund policy?",
    "How do I change my major?",
    "What are the library hours?",
    "How do I access online resources?",
    "What is the grading system?",
    "What is the attendance policy?",
    "How are internal marks calculated?",
    "What are the lab requirements?",
    "When is the project deadline?",
    "How do I apply for revaluation?",
]


class PerformanceTester:
    """Comprehensive performance testing with memory monitoring"""
    
    def __init__(self, config_path="config.json"):
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.results = []
        self.errors = []
        self.memory_snapshots = []
        self.lock = threading.Lock()
        self.monitor = get_monitor()
        
        # Set memory baseline
        self.monitor.set_baseline()
    
    def take_memory_snapshot(self, label: str):
        """Take a memory snapshot with label"""
        mem = self.monitor.get_memory_usage()
        delta = self.monitor.get_memory_delta()
        
        snapshot = {
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "rss_mb": mem["rss_mb"],
            "vms_mb": mem["vms_mb"],
            "percent": mem["percent"],
            "delta_mb": delta["rss_delta_mb"] if delta else 0
        }
        
        with self.lock:
            self.memory_snapshots.append(snapshot)
        
        return snapshot
    
    def single_query_test(self, query: str, user_id: int) -> bool:
        """Execute a single query and record all metrics"""
        start_time = time.time()
        mem_before = self.monitor.get_memory_usage()
        
        try:
            # Initialize components (simulates user session)
            engine = SearchEngine(self.config)
            llm = LLMGenerator(self.config)
            
            # Execute query
            search_start = time.time()
            search_result = engine.search(query)
            search_time = time.time() - search_start
            
            llm_start = time.time()
            response = llm.generate_response(query, search_result)
            llm_time = time.time() - llm_start
            
            end_time = time.time()
            total_latency = end_time - start_time
            
            mem_after = self.monitor.get_memory_usage()
            mem_delta = mem_after["rss_mb"] - mem_before["rss_mb"]
            
            # Record result
            with self.lock:
                self.results.append({
                    "user_id": user_id,
                    "query": query,
                    "total_latency": total_latency,
                    "search_time": search_time,
                    "llm_time": llm_time,
                    "confidence": response.get("confidence", 0),
                    "method": response.get("method", "unknown"),
                    "route": search_result.get("type", "unknown"),
                    "has_sources": bool(response.get("sources")),
                    "mem_before_mb": mem_before["rss_mb"],
                    "mem_after_mb": mem_after["rss_mb"],
                    "mem_delta_mb": mem_delta,
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
    
    def user_session(self, user_id: int, num_queries: int = 5):
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
            time.sleep(0.5)
        
        print(f"[User {user_id}] Session complete")
    
    def concurrent_load_test(self, num_users: int = 10, queries_per_user: int = 5):
        """Test with concurrent users and monitor memory"""
        print(f"\n{'='*70}")
        print(f"PERFORMANCE TEST: {num_users} concurrent users, {queries_per_user} queries each")
        print(f"{'='*70}\n")
        
        # Take initial memory snapshot
        self.take_memory_snapshot("test_start")
        
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
        
        # Monitor memory during test
        monitoring_thread = threading.Thread(target=self._monitor_during_test, args=(threads,))
        monitoring_thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        monitoring_thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Take final memory snapshot
        self.take_memory_snapshot("test_end")
        
        # Trigger garbage collection
        print("\n🗑️  Running garbage collection...")
        trigger_gc_with_logging("post-test cleanup")
        self.take_memory_snapshot("after_gc")
        
        print(f"\n{'='*70}")
        print(f"PERFORMANCE TEST COMPLETE")
        print(f"{'='*70}\n")
        
        return total_time
    
    def _monitor_during_test(self, threads: List[threading.Thread]):
        """Monitor memory usage during test execution"""
        while any(t.is_alive() for t in threads):
            time.sleep(2)  # Check every 2 seconds
            self.take_memory_snapshot("during_test")
    
    def analyze_results(self):
        """Comprehensive analysis of test results"""
        if not self.results:
            print("❌ No results to analyze")
            return
        
        print("\n" + "="*70)
        print("📊 PERFORMANCE ANALYSIS")
        print("="*70)
        
        # Basic statistics
        total_queries = len(self.results)
        total_errors = len(self.errors)
        success_rate = (total_queries / (total_queries + total_errors)) * 100 if (total_queries + total_errors) > 0 else 0
        
        print(f"\n📈 Overall Statistics:")
        print(f"  Total queries: {total_queries}")
        print(f"  Successful: {total_queries}")
        print(f"  Failed: {total_errors}")
        print(f"  Success rate: {success_rate:.1f}%")
        
        # Response time analysis
        self._analyze_response_times()
        
        # Memory analysis
        self._analyze_memory_usage()
        
        # Route distribution
        self._analyze_routes()
        
        # Performance assessment
        self._assess_performance()
        
        # Show errors if any
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  User {error['user_id']}: {error['error'][:80]}")
    
    def _analyze_response_times(self):
        """Analyze response time metrics"""
        total_latencies = [r["total_latency"] for r in self.results]
        search_times = [r["search_time"] for r in self.results]
        llm_times = [r["llm_time"] for r in self.results]
        
        print(f"\n⏱️  Response Time Analysis:")
        print(f"\n  Total Latency:")
        self._print_time_stats(total_latencies)
        
        print(f"\n  Search Time:")
        self._print_time_stats(search_times)
        
        print(f"\n  LLM Generation Time:")
        self._print_time_stats(llm_times)
    
    def _print_time_stats(self, times: List[float]):
        """Print time statistics"""
        avg = statistics.mean(times)
        median = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        p50 = sorted(times)[int(len(times) * 0.50)]
        p95 = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0]
        p99 = sorted(times)[int(len(times) * 0.99)] if len(times) > 1 else times[0]
        
        print(f"    Average: {avg:.2f}s")
        print(f"    Median (P50): {median:.2f}s")
        print(f"    P95: {p95:.2f}s")
        print(f"    P99: {p99:.2f}s")
        print(f"    Min: {min_time:.2f}s")
        print(f"    Max: {max_time:.2f}s")
    
    def _analyze_memory_usage(self):
        """Analyze memory usage patterns"""
        print(f"\n💾 Memory Usage Analysis:")
        
        # Memory deltas per query
        mem_deltas = [r["mem_delta_mb"] for r in self.results]
        avg_delta = statistics.mean(mem_deltas)
        max_delta = max(mem_deltas)
        min_delta = min(mem_deltas)
        total_growth = sum(mem_deltas)
        
        print(f"\n  Per-Query Memory Impact:")
        print(f"    Average delta: {avg_delta:+.2f} MB")
        print(f"    Max delta: {max_delta:+.2f} MB")
        print(f"    Min delta: {min_delta:+.2f} MB")
        print(f"    Total growth: {total_growth:+.2f} MB")
        
        # Memory snapshots
        if self.memory_snapshots:
            print(f"\n  Memory Snapshots:")
            start_snapshot = self.memory_snapshots[0]
            end_snapshot = self.memory_snapshots[-1]
            peak_snapshot = max(self.memory_snapshots, key=lambda x: x["rss_mb"])
            
            print(f"    Start: {start_snapshot['rss_mb']:.2f} MB")
            print(f"    End: {end_snapshot['rss_mb']:.2f} MB")
            print(f"    Peak: {peak_snapshot['rss_mb']:.2f} MB")
            print(f"    Growth: {end_snapshot['rss_mb'] - start_snapshot['rss_mb']:+.2f} MB")
        
        # GC summary
        gc_summary = self.monitor.get_gc_summary()
        print(f"\n  Garbage Collection:")
        print(f"    Collections: {gc_summary['total_collections']}")
        print(f"    Total freed: {gc_summary['total_freed_mb']:.2f} MB")
        if gc_summary['total_collections'] > 0:
            print(f"    Avg freed: {gc_summary['avg_freed_mb']:.2f} MB")
    
    def _analyze_routes(self):
        """Analyze query routing distribution"""
        print(f"\n🔀 Route Distribution:")
        
        routes = {}
        methods = {}
        
        for r in self.results:
            route = r["route"]
            method = r["method"]
            routes[route] = routes.get(route, 0) + 1
            methods[method] = methods.get(method, 0) + 1
        
        total = len(self.results)
        
        print(f"\n  Routes:")
        for route, count in sorted(routes.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"    {route}: {count} ({percentage:.1f}%)")
        
        print(f"\n  Methods:")
        for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"    {method}: {count} ({percentage:.1f}%)")
        
        # Confidence statistics
        confidences = [r["confidence"] for r in self.results]
        avg_confidence = statistics.mean(confidences)
        print(f"\n  Average Confidence: {avg_confidence:.2f}")
        
        # Sources statistics
        with_sources = sum(1 for r in self.results if r["has_sources"])
        source_rate = (with_sources / total) * 100
        print(f"  Queries with sources: {with_sources}/{total} ({source_rate:.1f}%)")
    
    def _assess_performance(self):
        """Assess performance against targets"""
        print(f"\n{'='*70}")
        print("🎯 PERFORMANCE ASSESSMENT")
        print("="*70)
        
        issues = []
        passes = []
        
        # Response time targets
        total_latencies = [r["total_latency"] for r in self.results]
        p95_latency = sorted(total_latencies)[int(len(total_latencies) * 0.95)]
        avg_latency = statistics.mean(total_latencies)
        
        # Task 9.7: Response time targets
        if p95_latency <= 10:
            passes.append(f"✅ P95 latency ({p95_latency:.2f}s) meets <10s target")
        else:
            issues.append(f"❌ P95 latency ({p95_latency:.2f}s) exceeds 10s target")
        
        if avg_latency <= 5:
            passes.append(f"✅ Average latency ({avg_latency:.2f}s) meets <5s target")
        else:
            issues.append(f"⚠️  Average latency ({avg_latency:.2f}s) exceeds 5s target")
        
        # Task 9.8: Memory usage targets
        if self.memory_snapshots:
            peak_mem = max(s["rss_mb"] for s in self.memory_snapshots)
            end_mem = self.memory_snapshots[-1]["rss_mb"]
            
            # Convert MB to GB for comparison
            peak_gb = peak_mem / 1024
            end_gb = end_mem / 1024
            
            if end_gb <= 4:
                passes.append(f"✅ Typical memory ({end_gb:.2f} GB) meets <4GB target")
            else:
                issues.append(f"⚠️  Typical memory ({end_gb:.2f} GB) exceeds 4GB target")
            
            if peak_gb <= 8:
                passes.append(f"✅ Peak memory ({peak_gb:.2f} GB) meets <8GB target")
            else:
                issues.append(f"❌ Peak memory ({peak_gb:.2f} GB) exceeds 8GB target")
        
        # Task 9.6: Concurrent sessions
        total_queries = len(self.results)
        total_errors = len(self.errors)
        success_rate = (total_queries / (total_queries + total_errors)) * 100 if (total_queries + total_errors) > 0 else 0
        
        if success_rate >= 95:
            passes.append(f"✅ Success rate ({success_rate:.1f}%) meets 95% target")
        else:
            issues.append(f"❌ Success rate ({success_rate:.1f}%) below 95% target")
        
        # Print results
        for p in passes:
            print(p)
        
        if issues:
            print(f"\n⚠️  Issues Found:")
            for issue in issues:
                print(issue)
        else:
            print(f"\n🎉 All performance targets met!")
        
        return len(issues) == 0
    
    def save_results(self, filename="performance_test_results.json"):
        """Save detailed results to file"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "results": self.results,
            "errors": self.errors,
            "memory_snapshots": self.memory_snapshots,
            "gc_summary": self.monitor.get_gc_summary(),
            "summary": {
                "total_queries": len(self.results),
                "total_errors": len(self.errors),
                "success_rate": (len(self.results) / (len(self.results) + len(self.errors))) * 100 if (len(self.results) + len(self.errors)) > 0 else 0
            }
        }
        
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\n📁 Detailed results saved to {filename}")


def main():
    """Run comprehensive performance tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive performance test for Campus AI Assistant")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users (default: 10)")
    parser.add_argument("--queries", type=int, default=5, help="Queries per user (default: 5)")
    parser.add_argument("--output", type=str, default="performance_test_results.json", help="Output file for results")
    
    args = parser.parse_args()
    
    print("🚀 Campus AI Assistant - Comprehensive Performance Testing")
    print(f"Configuration: {args.users} users, {args.queries} queries each")
    print(f"Total queries: {args.users * args.queries}")
    print()
    
    # Initialize tester
    tester = PerformanceTester()
    
    # Run performance test
    total_time = tester.concurrent_load_test(
        num_users=args.users,
        queries_per_user=args.queries
    )
    
    print(f"Total test duration: {total_time:.2f}s")
    
    # Analyze results
    tester.analyze_results()
    
    # Save results
    tester.save_results(args.output)
    
    # Print final memory summary
    tester.monitor.print_summary()
    
    # Exit code based on performance targets
    all_passed = tester._assess_performance()
    
    if all_passed:
        print("\n✅ All performance tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some performance targets not met - see assessment above")
        sys.exit(1)


if __name__ == "__main__":
    main()
