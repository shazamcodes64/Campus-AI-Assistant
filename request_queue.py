"""
Request Queue System for Concurrent User Management

Handles request queuing, backpressure, and timeout management for the Campus AI Assistant.
Designed to gracefully handle 70 concurrent students with fair resource allocation.
"""

import time
import threading
from queue import Queue, Full, Empty
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, Dict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueuedRequest:
    """Represents a queued request with metadata"""
    request_id: str
    query: str
    timestamp: float = field(default_factory=time.time)
    timeout: float = 30.0  # Default 30 second timeout
    result: Optional[Any] = None
    error: Optional[str] = None
    completed: bool = False
    
    def is_expired(self) -> bool:
        """Check if request has exceeded timeout"""
        return (time.time() - self.timestamp) > self.timeout


@dataclass
class QueueMetrics:
    """Metrics for monitoring queue performance"""
    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    rejected_requests: int = 0
    current_queue_size: int = 0
    avg_wait_time: float = 0.0
    avg_processing_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "total_requests": self.total_requests,
            "completed_requests": self.completed_requests,
            "failed_requests": self.failed_requests,
            "timeout_requests": self.timeout_requests,
            "rejected_requests": self.rejected_requests,
            "current_queue_size": self.current_queue_size,
            "avg_wait_time_seconds": round(self.avg_wait_time, 2),
            "avg_processing_time_seconds": round(self.avg_processing_time, 2)
        }


class RequestQueue:
    """
    Thread-safe request queue with backpressure handling and timeout management.
    
    Features:
    - Configurable queue size limits
    - Request timeout handling
    - Backpressure (reject when full)
    - Queue monitoring and metrics
    - Fair FIFO processing
    """
    
    def __init__(
        self,
        max_queue_size: int = 100,
        max_concurrent_workers: int = 10,
        default_timeout: float = 30.0
    ):
        """
        Initialize request queue.
        
        Args:
            max_queue_size: Maximum number of queued requests
            max_concurrent_workers: Maximum concurrent processing workers
            default_timeout: Default timeout for requests in seconds
        """
        self.max_queue_size = max_queue_size
        self.max_concurrent_workers = max_concurrent_workers
        self.default_timeout = default_timeout
        
        # Thread-safe queue
        self.queue = Queue(maxsize=max_queue_size)
        
        # Metrics tracking
        self.metrics = QueueMetrics()
        self.metrics_lock = threading.Lock()
        
        # Processing state
        self.active_workers = 0
        self.workers_lock = threading.Lock()
        
        # Wait time tracking
        self.wait_times = []
        self.processing_times = []
        
        logger.info(
            f"RequestQueue initialized: max_queue_size={max_queue_size}, "
            f"max_workers={max_concurrent_workers}, timeout={default_timeout}s"
        )
    
    def submit(
        self,
        request_id: str,
        query: str,
        timeout: Optional[float] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Submit a request to the queue.
        
        Args:
            request_id: Unique identifier for the request
            query: User query string
            timeout: Optional custom timeout (uses default if None)
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if timeout is None:
            timeout = self.default_timeout
        
        request = QueuedRequest(
            request_id=request_id,
            query=query,
            timeout=timeout
        )
        
        try:
            # Try to add to queue (non-blocking)
            self.queue.put(request, block=False)
            
            with self.metrics_lock:
                self.metrics.total_requests += 1
                self.metrics.current_queue_size = self.queue.qsize()
            
            logger.info(f"Request {request_id} queued (queue size: {self.queue.qsize()})")
            return True, None
            
        except Full:
            # Queue is full - apply backpressure
            with self.metrics_lock:
                self.metrics.rejected_requests += 1
            
            error_msg = (
                f"System is at capacity. Please try again in a moment. "
                f"(Queue size: {self.max_queue_size})"
            )
            logger.warning(f"Request {request_id} rejected - queue full")
            return False, error_msg
    
    def process_request(
        self,
        processor_func: Callable[[str], Any],
        timeout_seconds: float = 1.0
    ) -> Optional[tuple[QueuedRequest, Any]]:
        """
        Process next request from queue.
        
        Args:
            processor_func: Function to process the query (takes query string, returns result)
            timeout_seconds: How long to wait for a request from queue
        
        Returns:
            Tuple of (request, result) if processed, None if no request available
        """
        try:
            # Get next request from queue
            request = self.queue.get(timeout=timeout_seconds)
            
            # Track worker count
            with self.workers_lock:
                self.active_workers += 1
            
            try:
                # Check if request has already timed out
                if request.is_expired():
                    with self.metrics_lock:
                        self.metrics.timeout_requests += 1
                        self.metrics.current_queue_size = self.queue.qsize()
                    
                    logger.warning(f"Request {request.request_id} expired before processing")
                    request.error = "Request timed out in queue"
                    request.completed = True
                    return request, None
                
                # Calculate wait time
                wait_time = time.time() - request.timestamp
                self.wait_times.append(wait_time)
                
                # Process the request
                start_time = time.time()
                result = processor_func(request.query)
                processing_time = time.time() - start_time
                
                self.processing_times.append(processing_time)
                
                # Update request
                request.result = result
                request.completed = True
                
                # Update metrics
                with self.metrics_lock:
                    self.metrics.completed_requests += 1
                    self.metrics.current_queue_size = self.queue.qsize()
                    
                    # Update averages (rolling average of last 100)
                    if len(self.wait_times) > 100:
                        self.wait_times = self.wait_times[-100:]
                    if len(self.processing_times) > 100:
                        self.processing_times = self.processing_times[-100:]
                    
                    self.metrics.avg_wait_time = sum(self.wait_times) / len(self.wait_times)
                    self.metrics.avg_processing_time = sum(self.processing_times) / len(self.processing_times)
                
                logger.info(
                    f"Request {request.request_id} completed "
                    f"(wait: {wait_time:.2f}s, process: {processing_time:.2f}s)"
                )
                
                return request, result
                
            except Exception as e:
                # Processing failed
                request.error = str(e)
                request.completed = True
                
                with self.metrics_lock:
                    self.metrics.failed_requests += 1
                    self.metrics.current_queue_size = self.queue.qsize()
                
                logger.error(f"Request {request.request_id} failed: {e}")
                return request, None
                
            finally:
                # Always decrement worker count
                with self.workers_lock:
                    self.active_workers -= 1
                
                # Mark task as done
                self.queue.task_done()
        
        except Empty:
            # No requests in queue
            return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current queue metrics"""
        with self.metrics_lock:
            metrics_dict = self.metrics.to_dict()
            metrics_dict["active_workers"] = self.active_workers
            return metrics_dict
    
    def is_full(self) -> bool:
        """Check if queue is at capacity"""
        return self.queue.full()
    
    def size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def clear(self):
        """Clear all pending requests from queue"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except Empty:
                break
        
        logger.info("Queue cleared")


# Singleton instance for application-wide use
_queue_instance: Optional[RequestQueue] = None
_queue_lock = threading.Lock()


def get_request_queue(
    max_queue_size: int = 100,
    max_concurrent_workers: int = 10,
    default_timeout: float = 30.0
) -> RequestQueue:
    """
    Get or create singleton request queue instance.
    
    Args:
        max_queue_size: Maximum number of queued requests
        max_concurrent_workers: Maximum concurrent processing workers
        default_timeout: Default timeout for requests in seconds
    
    Returns:
        RequestQueue instance
    """
    global _queue_instance
    
    if _queue_instance is None:
        with _queue_lock:
            if _queue_instance is None:
                _queue_instance = RequestQueue(
                    max_queue_size=max_queue_size,
                    max_concurrent_workers=max_concurrent_workers,
                    default_timeout=default_timeout
                )
    
    return _queue_instance
