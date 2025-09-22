"""
Performance Services Package

This package contains performance optimization services for the TaskMaster application.

Modules:
- cache_service: Redis and memory caching with intelligent invalidation
- monitoring_service: Performance monitoring and metrics collection
- optimization_service: Database query optimization and response optimization
- benchmarking_service: Performance testing and benchmarking tools
"""

from .cache_service import CacheService, cache_manager, init_cache_service
from .monitoring_service import PerformanceMonitor, performance_monitor, init_performance_monitor
from .optimization_service import OptimizationService, db_optimizer, init_optimization_service
from .benchmarking_service import BenchmarkingService, benchmark_manager, init_benchmarking_service

__all__ = [
    'CacheService', 'cache_manager', 'init_cache_service',
    'PerformanceMonitor', 'performance_monitor', 'init_performance_monitor',
    'OptimizationService', 'db_optimizer', 'init_optimization_service',
    'BenchmarkingService', 'benchmark_manager', 'init_benchmarking_service'
]