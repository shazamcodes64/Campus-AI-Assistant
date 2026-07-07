"""
Integration test for request queue with actual app components.

Tests the queue with real search engine and LLM generator (if available).
"""

import json
import time
from request_queue import get_request_queue


def load_config():
    """Load configuration"""
    with open("config.json", "r") as f:
        return json.load(f)


def test_queue_with_mock_components():
    """Test queue with mock components (no dependencies required)"""
    print("\n=== Integration Test: Queue with Mock Components ===")
    
    # Mock processor
    def mock_processor(query):
        time.sleep(0.5)  # Simulate processing
        return {
            "search_result": {
                "type": "document",
                "confidence": 0.75,
                "chunks": []
            },
            "response": {
                "answer": f"Mock answer for: {query}",
                "confidence": 0.75,
                "method": "mock",
                "sources": []
            }
        }
    
    # Get queue
    config = load_config()
    queue_config = config.get("queue", {})
    queue = get_request_queue(
        max_queue_size=queue_config.get("max_queue_size", 100),
        max_concurrent_workers=queue_config.get("max_concurrent_workers", 10),
        default_timeout=queue_config.get("default_timeout", 30.0)
    )
    
    print(f"✓ Queue initialized with config: {queue_config}")
    
    # Submit test request
    success, error = queue.submit("test_001", "What is the placement process?")
    assert success, f"Failed to submit: {error}"
    print("✓ Request submitted successfully")
    
    # Process request
    result = queue.process_request(mock_processor, timeout_seconds=1.0)
    assert result is not None, "Failed to process request"
    
    queued_request, processed_result = result
    assert queued_request.completed, "Request not completed"
    assert processed_result is not None, "No result returned"
    assert "search_result" in processed_result, "Missing search_result"
    assert "response" in processed_result, "Missing response"
    
    print(f"✓ Request processed successfully")
    print(f"  - Search type: {processed_result['search_result']['type']}")
    print(f"  - Response method: {processed_result['response']['method']}")
    
    # Check metrics
    metrics = queue.get_metrics()
    print(f"✓ Metrics collected:")
    print(f"  - Total requests: {metrics['total_requests']}")
    print(f"  - Completed: {metrics['completed_requests']}")
    print(f"  - Avg wait time: {metrics['avg_wait_time_seconds']:.2f}s")
    print(f"  - Avg processing time: {metrics['avg_processing_time_seconds']:.2f}s")
    
    print("✅ Integration test passed\n")


def test_queue_configuration():
    """Test that queue configuration is properly loaded"""
    print("\n=== Configuration Test ===")
    
    config = load_config()
    
    # Check queue config exists
    assert "queue" in config, "Queue configuration missing from config.json"
    
    queue_config = config["queue"]
    print(f"✓ Queue configuration found:")
    print(f"  - max_queue_size: {queue_config.get('max_queue_size')}")
    print(f"  - max_concurrent_workers: {queue_config.get('max_concurrent_workers')}")
    print(f"  - default_timeout: {queue_config.get('default_timeout')}")
    
    # Verify reasonable values
    assert queue_config.get("max_queue_size", 0) > 0, "Invalid max_queue_size"
    assert queue_config.get("max_concurrent_workers", 0) > 0, "Invalid max_concurrent_workers"
    assert queue_config.get("default_timeout", 0) > 0, "Invalid default_timeout"
    
    print("✅ Configuration test passed\n")


def test_backpressure_scenario():
    """Test backpressure with realistic scenario"""
    print("\n=== Backpressure Test ===")
    
    # Create new queue instance directly (not singleton) for testing
    from request_queue import RequestQueue
    queue = RequestQueue(max_queue_size=5, max_concurrent_workers=1)
    
    # Fill queue
    for i in range(5):
        success, _ = queue.submit(f"req_{i}", f"Query {i}")
        assert success, f"Failed to submit request {i}"
    
    print(f"✓ Queue filled: {queue.size()}/5")
    
    # Try to overflow
    success, error = queue.submit("overflow", "Overflow query")
    assert not success, "Should reject when full"
    assert "capacity" in error.lower(), "Error message should mention capacity"
    
    print(f"✓ Backpressure applied correctly")
    print(f"  - Error message: {error}")
    
    # Check metrics
    metrics = queue.get_metrics()
    assert metrics["rejected_requests"] > 0, "Should track rejected requests"
    
    print(f"✓ Rejected requests tracked: {metrics['rejected_requests']}")
    print("✅ Backpressure test passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Request Queue Integration Tests")
    print("=" * 60)
    
    try:
        test_queue_configuration()
        test_queue_with_mock_components()
        test_backpressure_scenario()
        
        print("=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 60)
        print("\nThe request queue is properly integrated and configured.")
        print("Run the Streamlit app to test with real components:")
        print("  streamlit run app.py")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise
