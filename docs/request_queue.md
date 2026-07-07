# Request Queue System Documentation

## Overview

The request queue system provides graceful handling of concurrent users for the Campus AI Assistant. It implements request queuing, backpressure handling, timeout management, and performance monitoring to ensure the system can handle 70 concurrent students without degradation.

## Architecture

### Components

1. **QueuedRequest**: Data structure representing a queued request with metadata
2. **QueueMetrics**: Metrics tracking for monitoring queue performance
3. **RequestQueue**: Thread-safe queue with backpressure and timeout handling
4. **Singleton Pattern**: Application-wide queue instance via `get_request_queue()`

### Key Features

- **Thread-safe operations**: Uses Python's `Queue` with locks for concurrent access
- **Backpressure handling**: Rejects requests when queue is full
- **Timeout management**: Automatically expires requests that wait too long
- **Fair FIFO processing**: First-in-first-out request handling
- **Performance metrics**: Tracks wait times, processing times, and success rates
- **Configurable limits**: Queue size, worker count, and timeouts are configurable

## Configuration

Add queue configuration to `config.json`:

```json
{
  "queue": {
    "max_queue_size": 100,
    "max_concurrent_workers": 10,
    "default_timeout": 30.0
  }
}
```

### Configuration Parameters

- **max_queue_size** (default: 100): Maximum number of requests that can be queued
- **max_concurrent_workers** (default: 10): Maximum number of concurrent processing workers
- **default_timeout** (default: 30.0): Default timeout for requests in seconds

## Usage

### Basic Usage in Streamlit App

```python
from request_queue import get_request_queue

# Get singleton queue instance
queue = get_request_queue(
    max_queue_size=100,
    max_concurrent_workers=10,
    default_timeout=30.0
)

# Submit a request
request_id = "unique_request_id"
query = "What is the placement process?"
success, error_msg = queue.submit(request_id, query)

if not success:
    # Handle backpressure
    print(f"Request rejected: {error_msg}")
else:
    # Define processing function
    def process_query(query_text):
        # Your processing logic here
        search_result = search_engine.search(query_text)
        response = llm_generator.generate_response(query_text, search_result)
        return {"search_result": search_result, "response": response}
    
    # Process the request
    result = queue.process_request(process_query, timeout_seconds=1.0)
    
    if result is not None:
        queued_request, processed_result = result
        
        if queued_request.error:
            print(f"Error: {queued_request.error}")
        else:
            # Use the result
            print(f"Result: {processed_result}")
```

### Monitoring Queue Metrics

```python
# Get current metrics
metrics = queue.get_metrics()

print(f"Queue size: {metrics['current_queue_size']}")
print(f"Active workers: {metrics['active_workers']}")
print(f"Total requests: {metrics['total_requests']}")
print(f"Completed: {metrics['completed_requests']}")
print(f"Failed: {metrics['failed_requests']}")
print(f"Timeout: {metrics['timeout_requests']}")
print(f"Rejected: {metrics['rejected_requests']}")
print(f"Avg wait time: {metrics['avg_wait_time_seconds']}s")
print(f"Avg processing time: {metrics['avg_processing_time_seconds']}s")
```

## Performance Characteristics

### Load Test Results (70 Concurrent Users)

Based on testing with 70 concurrent users making 2 queries each:

- **Total requests**: 140
- **Completed**: 110 (78.6%)
- **Rejected**: 30 (21.4%) - due to queue capacity
- **Average wait time**: ~6-7 seconds
- **Average processing time**: ~1.2 seconds
- **Success rate**: 100% (of accepted requests)

### Recommendations

1. **Queue Size**: Set to 100 for 70 concurrent users
   - Allows ~1.4 requests per user to be queued
   - Provides buffer for burst traffic

2. **Worker Count**: Set to 10 workers
   - Balances throughput with resource usage
   - Each worker processes ~1-2 second requests

3. **Timeout**: Set to 30 seconds
   - Prevents indefinite waiting
   - Reasonable for LLM generation times

## Error Handling

### Backpressure (Queue Full)

When the queue is full, new requests are rejected with a user-friendly message:

```
System is at capacity. Please try again in a moment. (Queue size: 100)
```

**User Experience**:
- Clear feedback that system is busy
- Encourages retry after a moment
- Prevents system overload

### Request Timeout

Requests that wait in queue longer than the timeout are automatically expired:

```
Request timed out in queue
```

**Handling**:
- Request is marked as completed with error
- Metrics track timeout count
- User receives timeout message

### Processing Failure

If processing raises an exception:

```
Error: <exception message>
```

**Handling**:
- Request is marked as completed with error
- Metrics track failure count
- Error is logged for debugging

## Integration with Streamlit

The queue is integrated into `app.py` with the following features:

1. **Queue Status Display**: Shows queue size and active workers in sidebar
2. **Position Feedback**: Informs users of their queue position
3. **Backpressure Messages**: Clear error messages when system is at capacity
4. **Request Tracking**: Each request gets a unique ID for monitoring
5. **Metrics Display**: Optional expandable metrics in sidebar

### User Experience Flow

1. User submits query
2. System generates unique request ID
3. Request is submitted to queue
4. If queue full: User sees error message and retry suggestion
5. If queued: User sees position and "Processing..." message
6. Request is processed when worker available
7. Results displayed with processing time

## Monitoring and Debugging

### Log Messages

The queue system logs important events:

```
INFO: Request req_001 queued (queue size: 5)
INFO: Request req_001 completed (wait: 0.5s, process: 1.2s)
WARNING: Request req_002 rejected - queue full
WARNING: Request req_003 expired before processing
ERROR: Request req_004 failed: <error message>
```

### Metrics Tracking

Metrics are tracked in real-time and can be accessed via `get_metrics()`:

- **Total requests**: Cumulative count of all submitted requests
- **Completed requests**: Successfully processed requests
- **Failed requests**: Requests that raised exceptions during processing
- **Timeout requests**: Requests that expired in queue
- **Rejected requests**: Requests rejected due to full queue
- **Current queue size**: Number of requests waiting
- **Active workers**: Number of workers currently processing
- **Average wait time**: Rolling average of last 100 requests
- **Average processing time**: Rolling average of last 100 requests

## Testing

Run the test suite to verify queue functionality:

```bash
python3 test_concurrent_queue.py
```

### Test Coverage

1. **Basic Operations**: Submit and process requests
2. **Backpressure**: Queue full rejection
3. **Timeout**: Request expiration
4. **Concurrent Processing**: Multiple workers
5. **Load Simulation**: 70 concurrent users
6. **Singleton Pattern**: Single instance verification

## Troubleshooting

### High Wait Times

**Symptom**: Average wait time > 10 seconds

**Solutions**:
- Increase `max_concurrent_workers` (more parallel processing)
- Increase `max_queue_size` (more buffer capacity)
- Optimize processing function (reduce processing time)

### High Rejection Rate

**Symptom**: Many requests rejected (> 20%)

**Solutions**:
- Increase `max_queue_size`
- Add rate limiting on client side
- Implement retry logic with exponential backoff

### Timeout Issues

**Symptom**: Many requests timing out

**Solutions**:
- Increase `default_timeout`
- Increase `max_concurrent_workers`
- Optimize processing function

### Memory Issues

**Symptom**: High memory usage with large queue

**Solutions**:
- Reduce `max_queue_size`
- Implement queue clearing on memory pressure
- Add garbage collection after processing

## Future Enhancements

Potential improvements for Phase 2:

1. **Priority Queue**: VIP users or urgent requests
2. **Rate Limiting**: Per-user request limits
3. **Retry Logic**: Automatic retry with exponential backoff
4. **Circuit Breaker**: Automatic queue clearing on system issues
5. **Distributed Queue**: Redis-based queue for multi-node deployment
6. **Advanced Metrics**: Prometheus/Grafana integration
7. **Request Batching**: Batch similar requests for efficiency
8. **Adaptive Sizing**: Dynamic queue size based on load

## References

- **Implementation**: `request_queue.py`
- **Integration**: `app.py`
- **Tests**: `test_concurrent_queue.py`
- **Configuration**: `config.json`
