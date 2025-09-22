"""
Performance Monitoring Service

Comprehensive performance monitoring for TaskMaster API including response time tracking,
database query analysis, memory monitoring, and real-time metrics collection.

Features:
- Response time tracking per endpoint
- Database query performance monitoring
- Memory usage analysis
- Cache hit rate monitoring
- Error rate tracking
- Real-time metrics collection
- Performance alerts and thresholds
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from contextlib import contextmanager
from functools import wraps

from flask import request, g, current_app
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'tags': self.tags
        }


@dataclass
class EndpointMetrics:
    """Metrics for a specific API endpoint."""
    total_requests: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    error_count: int = 0
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def avg_response_time(self) -> float:
        return self.total_response_time / self.total_requests if self.total_requests > 0 else 0
    
    @property
    def error_rate(self) -> float:
        return (self.error_count / self.total_requests * 100) if self.total_requests > 0 else 0
    
    def add_request(self, response_time: float, is_error: bool = False):
        """Add a request measurement."""
        self.total_requests += 1
        self.total_response_time += response_time
        self.min_response_time = min(self.min_response_time, response_time)
        self.max_response_time = max(self.max_response_time, response_time)
        self.recent_response_times.append(response_time)
        
        if is_error:
            self.error_count += 1
    
    def get_percentile(self, percentile: float) -> float:
        """Calculate response time percentile."""
        if not self.recent_response_times:
            return 0
        
        sorted_times = sorted(self.recent_response_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_requests': self.total_requests,
            'avg_response_time': round(self.avg_response_time, 3),
            'min_response_time': round(self.min_response_time, 3) if self.min_response_time != float('inf') else 0,
            'max_response_time': round(self.max_response_time, 3),
            'error_count': self.error_count,
            'error_rate': round(self.error_rate, 2),
            'p50': round(self.get_percentile(50), 3),
            'p95': round(self.get_percentile(95), 3),
            'p99': round(self.get_percentile(99), 3)
        }


class PerformanceMonitor:
    """Main performance monitoring service."""
    
    def __init__(self, enable_db_monitoring: bool = True, enable_memory_monitoring: bool = True):
        self.enable_db_monitoring = enable_db_monitoring
        self.enable_memory_monitoring = enable_memory_monitoring
        
        # Metrics storage
        self.endpoint_metrics: Dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self.db_query_metrics: List[MetricPoint] = []
        self.memory_metrics: List[MetricPoint] = []
        self.cache_metrics: List[MetricPoint] = []
        
        # Configuration
        self.max_metric_points = 10000
        self.performance_thresholds = {
            'response_time_warning': 1000,  # ms
            'response_time_critical': 5000,  # ms
            'error_rate_warning': 5,  # %
            'error_rate_critical': 10,  # %
            'memory_warning': 500,  # MB
            'memory_critical': 1000,  # MB
        }
        
        # Alerts
        self.alert_callbacks: List[Callable] = []
        self._monitoring_active = False
        self._monitor_thread = None
        
        # Database query tracking
        self._db_query_start_times = {}
        
        logger.info("Performance monitor initialized")
    
    def start_monitoring(self):
        """Start background monitoring thread."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self._monitoring_active:
            try:
                # Collect system metrics
                if self.enable_memory_monitoring:
                    self._collect_memory_metrics()
                
                # Collect cache metrics
                self._collect_cache_metrics()
                
                # Trim old metrics
                self._trim_metrics()
                
                # Check thresholds and send alerts
                self._check_alerts()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(30)  # Monitor every 30 seconds
    
    @contextmanager
    def track_request(self, endpoint: str):
        """Context manager for tracking request performance."""
        start_time = time.time()
        error_occurred = False
        
        # Store start time in request context
        g.request_start_time = start_time
        g.endpoint = endpoint
        
        try:
            yield
        except Exception as e:
            error_occurred = True
            logger.error(f"Request error on {endpoint}: {e}")
            raise
        finally:
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Record metrics
            self.endpoint_metrics[endpoint].add_request(response_time, error_occurred)
            
            # Log slow requests
            if response_time > self.performance_thresholds['response_time_warning']:
                logger.warning(f"Slow request: {endpoint} took {response_time:.2f}ms")
    
    @contextmanager
    def track_db_query(self, query_type: str, table: str = ""):
        """Context manager for tracking database query performance."""
        if not self.enable_db_monitoring:
            yield
            return
        
        start_time = time.time()
        query_id = f"{query_type}_{table}_{int(start_time * 1000000)}"
        
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            metric = MetricPoint(
                timestamp=datetime.now(),
                value=duration,
                tags={
                    'query_type': query_type,
                    'table': table,
                    'query_id': query_id
                }
            )
            
            self.db_query_metrics.append(metric)
            
            # Log slow queries
            if duration > 100:  # Log queries taking more than 100ms
                logger.warning(f"Slow query: {query_type} on {table} took {duration:.2f}ms")
    
    def record_cache_hit(self, cache_type: str, hit: bool):
        """Record cache hit/miss."""
        metric = MetricPoint(
            timestamp=datetime.now(),
            value=1 if hit else 0,
            tags={
                'cache_type': cache_type,
                'result': 'hit' if hit else 'miss'
            }
        )
        self.cache_metrics.append(metric)
    
    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for specific endpoint or all endpoints."""
        if endpoint:
            if endpoint in self.endpoint_metrics:
                return {endpoint: self.endpoint_metrics[endpoint].to_dict()}
            return {}
        
        return {ep: metrics.to_dict() for ep, metrics in self.endpoint_metrics.items()}
    
    def get_db_query_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """Get database query statistics for the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_queries = [m for m in self.db_query_metrics if m.timestamp >= cutoff_time]
        
        if not recent_queries:
            return {'total_queries': 0}
        
        query_times = [m.value for m in recent_queries]
        query_types = defaultdict(list)
        
        for metric in recent_queries:
            query_type = metric.tags.get('query_type', 'unknown')
            query_types[query_type].append(metric.value)
        
        stats = {
            'total_queries': len(recent_queries),
            'avg_query_time': round(sum(query_times) / len(query_times), 3),
            'min_query_time': round(min(query_times), 3),
            'max_query_time': round(max(query_times), 3),
            'slow_queries': len([t for t in query_times if t > 100]),
            'by_type': {}
        }
        
        for query_type, times in query_types.items():
            stats['by_type'][query_type] = {
                'count': len(times),
                'avg_time': round(sum(times) / len(times), 3),
                'max_time': round(max(times), 3)
            }
        
        return stats
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'percent': round(process.memory_percent(), 2),
                'available_mb': round(psutil.virtual_memory().available / 1024 / 1024, 2),
                'total_mb': round(psutil.virtual_memory().total / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {}
    
    def get_cache_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """Get cache statistics for the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.cache_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {'total_requests': 0, 'hit_rate': 0}
        
        hits = len([m for m in recent_metrics if m.value == 1])
        total = len(recent_metrics)
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        cache_types = defaultdict(lambda: {'hits': 0, 'misses': 0})
        for metric in recent_metrics:
            cache_type = metric.tags.get('cache_type', 'unknown')
            if metric.value == 1:
                cache_types[cache_type]['hits'] += 1
            else:
                cache_types[cache_type]['misses'] += 1
        
        return {
            'total_requests': total,
            'hits': hits,
            'misses': total - hits,
            'hit_rate': round(hit_rate, 2),
            'by_type': {
                cache_type: {
                    **stats,
                    'hit_rate': round((stats['hits'] / (stats['hits'] + stats['misses']) * 100) if (stats['hits'] + stats['misses']) > 0 else 0, 2)
                }
                for cache_type, stats in cache_types.items()
            }
        }
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        return {
            'endpoints': self.get_endpoint_stats(),
            'database': self.get_db_query_stats(),
            'memory': self.get_memory_stats(),
            'cache': self.get_cache_stats(),
            'monitoring_active': self._monitoring_active,
            'uptime_minutes': self._get_uptime_minutes()
        }
    
    def _collect_memory_metrics(self):
        """Collect memory usage metrics."""
        try:
            memory_stats = self.get_memory_stats()
            if memory_stats:
                metric = MetricPoint(
                    timestamp=datetime.now(),
                    value=memory_stats['rss_mb'],
                    tags={'metric_type': 'memory_usage'}
                )
                self.memory_metrics.append(metric)
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
    
    def _collect_cache_metrics(self):
        """Collect cache performance metrics."""
        try:
            # Skip if not in application context
            from flask import has_app_context
            if not has_app_context():
                return
                
            if hasattr(current_app, 'cache_service'):
                cache_stats = current_app.cache_service.get_stats()
                
                metric = MetricPoint(
                    timestamp=datetime.now(),
                    value=cache_stats.get('hit_rate', 0),
                    tags={'metric_type': 'cache_hit_rate'}
                )
                self.cache_metrics.append(metric)
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
    
    def _trim_metrics(self):
        """Remove old metrics to prevent memory buildup."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        self.db_query_metrics = [m for m in self.db_query_metrics if m.timestamp >= cutoff_time]
        self.memory_metrics = [m for m in self.memory_metrics if m.timestamp >= cutoff_time]
        self.cache_metrics = [m for m in self.cache_metrics if m.timestamp >= cutoff_time]
        
        # Keep only recent metrics if we have too many
        for metric_list in [self.db_query_metrics, self.memory_metrics, self.cache_metrics]:
            if len(metric_list) > self.max_metric_points:
                metric_list[:] = metric_list[-self.max_metric_points:]
    
    def _check_alerts(self):
        """Check performance thresholds and trigger alerts."""
        # Check endpoint response times
        for endpoint, metrics in self.endpoint_metrics.items():
            if metrics.total_requests > 0:
                if metrics.avg_response_time > self.performance_thresholds['response_time_critical']:
                    self._trigger_alert('critical', f"Endpoint {endpoint} average response time is {metrics.avg_response_time:.2f}ms")
                elif metrics.avg_response_time > self.performance_thresholds['response_time_warning']:
                    self._trigger_alert('warning', f"Endpoint {endpoint} average response time is {metrics.avg_response_time:.2f}ms")
                
                if metrics.error_rate > self.performance_thresholds['error_rate_critical']:
                    self._trigger_alert('critical', f"Endpoint {endpoint} error rate is {metrics.error_rate:.2f}%")
                elif metrics.error_rate > self.performance_thresholds['error_rate_warning']:
                    self._trigger_alert('warning', f"Endpoint {endpoint} error rate is {metrics.error_rate:.2f}%")
        
        # Check memory usage
        memory_stats = self.get_memory_stats()
        if memory_stats:
            memory_mb = memory_stats.get('rss_mb', 0)
            if memory_mb > self.performance_thresholds['memory_critical']:
                self._trigger_alert('critical', f"Memory usage is {memory_mb:.2f}MB")
            elif memory_mb > self.performance_thresholds['memory_warning']:
                self._trigger_alert('warning', f"Memory usage is {memory_mb:.2f}MB")
    
    def _trigger_alert(self, level: str, message: str):
        """Trigger performance alert."""
        logger.warning(f"Performance alert ({level}): {message}")
        
        for callback in self.alert_callbacks:
            try:
                callback(level, message)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for performance alerts."""
        self.alert_callbacks.append(callback)
    
    def _get_uptime_minutes(self) -> int:
        """Get application uptime in minutes."""
        if hasattr(self, '_start_time'):
            return int((time.time() - self._start_time) / 60)
        return 0


def monitor_performance(func):
    """Decorator for monitoring function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(current_app, 'performance_monitor'):
            return func(*args, **kwargs)
        
        monitor = current_app.performance_monitor
        endpoint = f"{func.__module__}.{func.__name__}"
        
        with monitor.track_request(endpoint):
            return func(*args, **kwargs)
    
    return wrapper


# Global performance monitor instance
performance_monitor: Optional[PerformanceMonitor] = None


def init_performance_monitor(app):
    """Initialize performance monitor with Flask app."""
    global performance_monitor
    
    performance_monitor = PerformanceMonitor()
    performance_monitor._start_time = time.time()
    app.performance_monitor = performance_monitor
    
    # Start monitoring
    performance_monitor.start_monitoring()
    
    return performance_monitor