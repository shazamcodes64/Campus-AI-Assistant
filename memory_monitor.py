"""Memory monitoring utilities for tracking memory usage and GC behavior"""

import gc
import psutil
import os
from typing import Dict, Optional
from datetime import datetime


class MemoryMonitor:
    """Monitor memory usage and garbage collection statistics"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.baseline_memory = None
        self.peak_memory = 0
        self.gc_stats = []
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage in MB
        
        Returns:
            Dictionary with memory metrics:
            - rss: Resident Set Size (physical memory)
            - vms: Virtual Memory Size
            - percent: Memory usage as percentage of total
        """
        mem_info = self.process.memory_info()
        mem_percent = self.process.memory_percent()
        
        return {
            "rss_mb": mem_info.rss / (1024 * 1024),
            "vms_mb": mem_info.vms / (1024 * 1024),
            "percent": mem_percent
        }
    
    def set_baseline(self):
        """Set baseline memory usage for comparison"""
        self.baseline_memory = self.get_memory_usage()
        print(f"📊 Memory baseline set: {self.baseline_memory['rss_mb']:.2f} MB")
    
    def get_memory_delta(self) -> Optional[Dict[str, float]]:
        """Get memory usage change since baseline
        
        Returns:
            Dictionary with memory deltas or None if baseline not set
        """
        if self.baseline_memory is None:
            return None
        
        current = self.get_memory_usage()
        return {
            "rss_delta_mb": current["rss_mb"] - self.baseline_memory["rss_mb"],
            "vms_delta_mb": current["vms_mb"] - self.baseline_memory["vms_mb"],
            "percent_delta": current["percent"] - self.baseline_memory["percent"]
        }
    
    def trigger_gc_with_stats(self) -> Dict[str, any]:
        """Trigger garbage collection and return statistics
        
        Returns:
            Dictionary with GC statistics:
            - collected: Number of objects collected
            - before_mb: Memory before GC
            - after_mb: Memory after GC
            - freed_mb: Memory freed by GC
            - timestamp: When GC was triggered
        """
        before = self.get_memory_usage()
        
        # Trigger full garbage collection
        collected = gc.collect()
        
        after = self.get_memory_usage()
        freed = before["rss_mb"] - after["rss_mb"]
        
        stats = {
            "collected": collected,
            "before_mb": before["rss_mb"],
            "after_mb": after["rss_mb"],
            "freed_mb": freed,
            "timestamp": datetime.now().isoformat()
        }
        
        # Track peak memory
        if after["rss_mb"] > self.peak_memory:
            self.peak_memory = after["rss_mb"]
        
        # Store stats
        self.gc_stats.append(stats)
        
        return stats
    
    def log_memory_status(self, label: str = ""):
        """Log current memory status with optional label"""
        mem = self.get_memory_usage()
        delta = self.get_memory_delta()
        
        status = f"💾 Memory {label}: {mem['rss_mb']:.2f} MB ({mem['percent']:.1f}%)"
        
        if delta:
            status += f" | Delta: {delta['rss_delta_mb']:+.2f} MB"
        
        print(status)
    
    def get_gc_summary(self) -> Dict[str, any]:
        """Get summary of garbage collection statistics
        
        Returns:
            Dictionary with GC summary:
            - total_collections: Total number of GC runs
            - total_freed_mb: Total memory freed
            - avg_freed_mb: Average memory freed per GC
            - peak_memory_mb: Peak memory usage observed
        """
        if not self.gc_stats:
            return {
                "total_collections": 0,
                "total_freed_mb": 0.0,
                "avg_freed_mb": 0.0,
                "peak_memory_mb": self.peak_memory
            }
        
        total_freed = sum(stat["freed_mb"] for stat in self.gc_stats)
        
        return {
            "total_collections": len(self.gc_stats),
            "total_freed_mb": total_freed,
            "avg_freed_mb": total_freed / len(self.gc_stats),
            "peak_memory_mb": self.peak_memory
        }
    
    def print_summary(self):
        """Print a formatted summary of memory and GC statistics"""
        summary = self.get_gc_summary()
        current = self.get_memory_usage()
        
        print("\n" + "="*60)
        print("📊 MEMORY MONITORING SUMMARY")
        print("="*60)
        print(f"Current Memory: {current['rss_mb']:.2f} MB ({current['percent']:.1f}%)")
        print(f"Peak Memory: {summary['peak_memory_mb']:.2f} MB")
        
        if self.baseline_memory:
            delta = self.get_memory_delta()
            print(f"Memory Growth: {delta['rss_delta_mb']:+.2f} MB")
        
        print(f"\nGarbage Collections: {summary['total_collections']}")
        print(f"Total Memory Freed: {summary['total_freed_mb']:.2f} MB")
        
        if summary['total_collections'] > 0:
            print(f"Avg Memory Freed: {summary['avg_freed_mb']:.2f} MB")
        
        print("="*60 + "\n")


# Global singleton instance
_monitor = None


def get_monitor() -> MemoryMonitor:
    """Get or create the global memory monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = MemoryMonitor()
    return _monitor


def log_memory(label: str = ""):
    """Convenience function to log memory status"""
    get_monitor().log_memory_status(label)


def trigger_gc_with_logging(label: str = "") -> int:
    """Trigger GC and log the results
    
    Args:
        label: Optional label for logging context
        
    Returns:
        Number of objects collected
    """
    monitor = get_monitor()
    stats = monitor.trigger_gc_with_stats()
    
    log_msg = f"🗑️  GC {label}: Collected {stats['collected']} objects, freed {stats['freed_mb']:.2f} MB"
    print(log_msg)
    
    return stats['collected']
