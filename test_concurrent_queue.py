"""
Test script for request queue with simulated concurrent users.

Tests:
1. Queue submission and processing
2. Backpressure handling (queue full)
3. Timeout handling
4. Concurrent request processing
5. Metrics collection
"""

import time
import threading
from request_queue import RequestQueue, get_request_queue
import random


def mock_processor(query: str) -> dict:
    """Mock processor that simulates search + LLM generation"""
    # Simulate processing time (0.5-2 seconds)
    processing_time = random.uniform(0.5, 2.0)
    time.sleep(processing_time)
    
    return {
        "query": query,
        "answer": f"Mock answer for: {query}",
        "confidence": random.uniform(0.6, 0.95),
        "processing_time": processing_time
    }


def test_basic_queue():
    """Test basic queue submission and processing"""
    print("\n=== Test 1: Basic Queue Operations ===")
    
    queue = RequestQueue(max_queue_size=10, max_concurrent_workers=2)
    
    # Submit a request
    success, error = queue.submit("req_001", "What is the placement process?")
    assert success, f"Failed to submit request: {error}"
    print("✓ Request submitted successfully")
    
    # Process the request
    result = queue.process_request(mock_processor, timeout_seconds=1.0)
    assert result is not None, "Failed to process request"
    
    request, processed = result
    assert request.completed, "Request not marked as completed"
    assert processed is not None, "No result returned"
    print(f"✓ Request processed: {processed['query']}")
    
    # Check metrics
    metrics = queue.get_metrics()
    print(f"✓ Metrics: {metrics}")
    assert metrics["completed_requests"] == 1
    
    print("✅ Basic queue test passed\n")


def test_backpressure():
    """Test queue backpressure when full"""
    print("\n=== Test 2: Backpressure Handling ===")
    
    queue = RequestQueue(max_queue_size=5, max_concurrent_workers=1)
    
    # Fill the queue
    for i in range(5):
        success, _ = queue.submit(f"req_{i}", f"Query {i}")
        assert success, f"Failed to submit request {i}"
    
    print(f"✓ Queue filled: {queue.size()}/5")
    
    # Try to submit when full
    success, error = queue.submit("req_overflow", "Overflow query")
    assert not success, "Should have rejected request when full"
    assert error is not None, "Should have error message"
    print(f"✓ Backpressure applied: {error}")
    
    # Check metrics
    metrics = queue.get_metrics()
    assert metrics["rejected_requests"] == 1
    print(f"✓ Rejected requests tracked: {metrics['rejected_requests']}")
    
    print("✅ Backpressure test passed\n")


def test_timeout():
    """Test request timeout handling"""
    print("\n=== Test 3: Timeout Handling ===")
    
    queue = RequestQueue(max_queue_size=10, default_timeout=1.0)
    
    # Submit request with short timeout
    success, _ = queue.submit("req_timeout", "Timeout query", timeout=0.5)
    assert success
    
    # Wait for timeout
    time.sleep(1.0)
    
    # Try to process (should be expired)
    result = queue.process_request(mock_processor, timeout_seconds=1.0)
    assert result is not None
    
    request, processed = result
    assert request.error is not None, "Should have timeout error"
    assert processed is None, "Should not have result for timed out request"
    print(f"✓ Timeout detected: {request.error}")
    
    # Check metrics
    metrics = queue.get_metrics()
    assert metrics["timeout_requests"] == 1
    print(f"✓ Timeout requests tracked: {metrics['timeout_requests']}")
    
    print("✅ Timeout test passed\n")


def test_concurrent_processing():
    """Test concurrent request processing"""
    print("\n=== Test 4: Concurrent Processing ===")
    
    queue = RequestQueue(max_queue_size=50, max_concurrent_workers=5)
    
    # Submit multiple requests
    num_requests = 20
    for i in range(num_requests):
        success, _ = queue.submit(f"req_{i}", f"Concurrent query {i}")
        assert success
    
    print(f"✓ Submitted {num_requests} requests")
    
    # Process requests concurrently
    results = []
    
    def worker():
        while True:
            result = queue.process_request(mock_processor, timeout_seconds=0.5)
            if result is None:
                break
            results.append(result)
    
    # Start worker threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    print(f"✓ Processed {len(results)} requests")
    
    # Check metrics
    metrics = queue.get_metrics()
    print(f"✓ Metrics: completed={metrics['completed_requests']}, "
          f"avg_wait={metrics['avg_wait_time_seconds']}s, "
          f"avg_process={metrics['avg_processing_time_seconds']}s")
    
    assert metrics["completed_requests"] == num_requests
    
    print("✅ Concurrent processing test passed\n")


def test_load_simulation():
    """Simulate realistic load with 70 concurrent users"""
    print("\n=== Test 5: Load Simulation (70 Users) ===")
    
    queue = RequestQueue(max_queue_size=100, max_concurrent_workers=10)
    
    num_users = 70
    queries_per_user = 2
    
    results = []
    rejected = []
    
    def user_simulation(user_id: int):
        """Simulate a user making queries"""
        for q in range(queries_per_user):
            query = f"User {user_id} query {q}"
            request_id = f"user_{user_id}_q_{q}"
            
            # Submit request
            success, error = queue.submit(request_id, query)
            
            if not success:
                rejected.append((request_id, error))
            else:
                # Simulate some delay between queries
                time.sleep(random.uniform(0.1, 0.5))
    
    def worker():
        """Process requests from queue"""
        while True:
            result = queue.process_request(mock_processor, timeout_seconds=0.5)
            if result is None:
                # Check if queue is empty and all users done
                time.sleep(0.1)
                if queue.size() == 0:
                    break
            else:
                results.append(result)
    
    # Start user threads
    print(f"Starting {num_users} user threads...")
    user_threads = []
    for i in range(num_users):
        t = threading.Thread(target=user_simulation, args=(i,))
        t.start()
        user_threads.append(t)
    
    # Start worker threads
    print(f"Starting {queue.max_concurrent_workers} worker threads...")
    worker_threads = []
    for i in range(queue.max_concurrent_workers):
        t = threading.Thread(target=worker)
        t.start()
        worker_threads.append(t)
    
    # Wait for all users to finish
    for t in user_threads:
        t.join()
    
    print("✓ All users completed")
    
    # Wait for all workers to finish
    for t in worker_threads:
        t.join()
    
    print("✓ All workers completed")
    
    # Report results
    metrics = queue.get_metrics()
    print(f"\n📊 Load Test Results:")
    print(f"  Total requests: {metrics['total_requests']}")
    print(f"  Completed: {metrics['completed_requests']}")
    print(f"  Failed: {metrics['failed_requests']}")
    print(f"  Timeout: {metrics['timeout_requests']}")
    print(f"  Rejected: {metrics['rejected_requests']}")
    print(f"  Avg wait time: {metrics['avg_wait_time_seconds']:.2f}s")
    print(f"  Avg processing time: {metrics['avg_processing_time_seconds']:.2f}s")
    
    if rejected:
        print(f"\n⚠️  {len(rejected)} requests were rejected due to queue capacity")
    
    # Success criteria
    success_rate = metrics['completed_requests'] / metrics['total_requests'] * 100
    print(f"\n✓ Success rate: {success_rate:.1f}%")
    
    # Adjusted criteria for realistic load
    assert success_rate >= 90, f"Success rate too low: {success_rate}%"
    # With 70 concurrent users and 10 workers, some wait time is expected
    assert metrics['avg_wait_time_seconds'] < 10.0, "Average wait time too high"
    
    print("✅ Load simulation test passed\n")


def test_singleton():
    """Test singleton pattern for queue"""
    print("\n=== Test 6: Singleton Pattern ===")
    
    queue1 = get_request_queue()
    queue2 = get_request_queue()
    
    assert queue1 is queue2, "Should return same instance"
    print("✓ Singleton pattern working correctly")
    
    print("✅ Singleton test passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Request Queue Test Suite")
    print("=" * 60)
    
    try:
        test_basic_queue()
        test_backpressure()
        test_timeout()
        test_concurrent_processing()
        test_load_simulation()
        test_singleton()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
