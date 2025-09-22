"""
Performance API Routes

Provides API endpoints for performance monitoring, caching control,
database optimization, and benchmarking capabilities.

Endpoints:
- GET /api/performance/stats - Get overall performance statistics
- GET /api/performance/monitoring - Get monitoring metrics
- GET/POST/DELETE /api/performance/cache - Cache management
- GET /api/performance/database - Database optimization analysis
- POST /api/performance/benchmark - Run performance benchmarks
- GET /api/performance/history - Get benchmark history
"""

from flask import Blueprint, request, jsonify, current_app, g
from datetime import datetime
import logging

from services.performance import (
    cache_manager, performance_monitor, db_optimizer, benchmark_manager
)
from .response_utils import APIResponse

logger = logging.getLogger(__name__)

performance_bp = Blueprint('performance', __name__, url_prefix='/performance')


@performance_bp.route('/stats', methods=['GET'])
def get_performance_stats():
    """Get comprehensive performance statistics."""
    try:
        stats = {}
        
        # Cache statistics
        if hasattr(current_app, 'cache_service'):
            stats['cache'] = current_app.cache_service.get_stats()
        
        # Monitoring statistics
        if hasattr(current_app, 'performance_monitor'):
            stats['monitoring'] = current_app.performance_monitor.get_overall_stats()
        
        # Database optimization statistics
        if hasattr(current_app, 'db_optimizer'):
            stats['database'] = current_app.db_optimizer.get_optimization_stats()
        
        # System statistics
        stats['system'] = {
            'timestamp': datetime.now().isoformat(),
            'services_active': {
                'cache': hasattr(current_app, 'cache_service'),
                'monitoring': hasattr(current_app, 'performance_monitor'),
                'optimization': hasattr(current_app, 'db_optimizer'),
                'benchmarking': benchmark_manager is not None
            }
        }
        
        return APIResponse.success(stats, "Performance statistics retrieved")
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        return APIResponse.error(f"Failed to get performance statistics: {str(e)}", status_code=500)


@performance_bp.route('/monitoring', methods=['GET'])
def get_monitoring_metrics():
    """Get detailed monitoring metrics."""
    try:
        if not hasattr(current_app, 'performance_monitor'):
            return APIResponse.error("Performance monitoring not available", status_code=503)
        
        monitor = current_app.performance_monitor
        
        # Get query parameters
        endpoint = request.args.get('endpoint')
        minutes = int(request.args.get('minutes', 60))
        
        metrics = {
            'endpoints': monitor.get_endpoint_stats(endpoint),
            'database': monitor.get_db_query_stats(minutes),
            'memory': monitor.get_memory_stats(),
            'cache': monitor.get_cache_stats(minutes),
            'monitoring_active': monitor._monitoring_active
        }
        
        return APIResponse.success(metrics, "Monitoring metrics retrieved")
        
    except Exception as e:
        logger.error(f"Error getting monitoring metrics: {e}")
        return APIResponse.error(f"Failed to get monitoring metrics: {str(e)}", status_code=500)


@performance_bp.route('/cache', methods=['GET'])
def get_cache_stats():
    """Get cache statistics and configuration."""
    try:
        if not hasattr(current_app, 'cache_service'):
            return APIResponse.error("Cache service not available", status_code=503)
        
        cache_service = current_app.cache_service
        
        stats = cache_service.get_stats()
        stats['config'] = {
            'redis_available': cache_service.redis_client is not None,
            'default_ttl': cache_service.config.DEFAULT_TTL,
            'memory_cache_size': cache_service.config.MEMORY_CACHE_SIZE,
            'compression_enabled': cache_service.config.ENABLE_COMPRESSION
        }
        
        return APIResponse.success(stats, "Cache statistics retrieved")
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return APIResponse.error(f"Failed to get cache statistics: {str(e)}", status_code=500)


@performance_bp.route('/cache', methods=['POST'])
def manage_cache():
    """Manage cache operations (warm, invalidate, clear)."""
    try:
        if not hasattr(current_app, 'cache_service'):
            return APIResponse.error("Cache service not available", status_code=503)
        
        cache_service = current_app.cache_service
        data = request.get_json() or {}
        operation = data.get('operation')
        
        if operation == 'clear':
            success = cache_service.clear_all()
            return APIResponse.success(
                {'success': success}, 
                "Cache cleared successfully" if success else "Failed to clear cache"
            )
        
        elif operation == 'invalidate_pattern':
            pattern = data.get('pattern')
            if not pattern:
                return APIResponse.error("Pattern is required for invalidation", status_code=400)
            
            count = cache_service.invalidate_pattern(pattern)
            return APIResponse.success(
                {'invalidated_keys': count}, 
                f"Invalidated {count} cache keys matching pattern '{pattern}'"
            )
        
        elif operation == 'invalidate_dependencies':
            dependency = data.get('dependency')
            if not dependency:
                return APIResponse.error("Dependency is required for invalidation", status_code=400)
            
            count = cache_service.invalidate_dependencies(dependency)
            return APIResponse.success(
                {'invalidated_keys': count}, 
                f"Invalidated {count} cache keys dependent on '{dependency}'"
            )
        
        else:
            return APIResponse.error("Invalid operation. Supported: clear, invalidate_pattern, invalidate_dependencies", status_code=400)
        
    except Exception as e:
        logger.error(f"Error managing cache: {e}")
        return APIResponse.error(f"Failed to manage cache: {str(e)}", status_code=500)


@performance_bp.route('/database', methods=['GET'])
def get_database_analysis():
    """Get database optimization analysis."""
    try:
        if not hasattr(current_app, 'db_optimizer'):
            return APIResponse.error("Database optimizer not available", status_code=503)
        
        optimizer = current_app.db_optimizer
        action = request.args.get('action', 'stats')
        
        if action == 'analyze':
            from models import db
            analysis = optimizer.analyze_database_schema(db)
            return APIResponse.success(analysis, "Database schema analysis completed")
        
        elif action == 'slow_queries':
            min_time = float(request.args.get('min_time', 100))
            slow_queries = optimizer.get_slow_queries(min_time)
            return APIResponse.success(
                {'slow_queries': slow_queries}, 
                f"Found {len(slow_queries)} slow queries"
            )
        
        else:  # Default to stats
            stats = optimizer.get_optimization_stats()
            return APIResponse.success(stats, "Database optimization statistics retrieved")
        
    except Exception as e:
        logger.error(f"Error getting database analysis: {e}")
        return APIResponse.error(f"Failed to get database analysis: {str(e)}", status_code=500)


@performance_bp.route('/database/optimize', methods=['POST'])
def optimize_database():
    """Apply database optimizations."""
    try:
        if not hasattr(current_app, 'db_optimizer'):
            return APIResponse.error("Database optimizer not available", status_code=503)
        
        optimizer = current_app.db_optimizer
        data = request.get_json() or {}
        operation = data.get('operation')
        
        if operation == 'create_indexes':
            from models import db
            max_indexes = int(data.get('max_indexes', 5))
            results = optimizer.create_recommended_indexes(db, max_indexes)
            return APIResponse.success(results, "Index creation completed")
        
        elif operation == 'analyze_schema':
            from models import db
            analysis = optimizer.analyze_database_schema(db)
            return APIResponse.success(analysis, "Database schema analysis completed")
        
        elif operation == 'clear_query_log':
            optimizer.clear_query_log()
            return APIResponse.success({}, "Query performance log cleared")
        
        else:
            return APIResponse.error("Invalid operation. Supported: create_indexes, analyze_schema, clear_query_log", status_code=400)
        
    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        return APIResponse.error(f"Failed to optimize database: {str(e)}", status_code=500)


@performance_bp.route('/benchmark', methods=['POST'])
def run_benchmark():
    """Run performance benchmark test."""
    try:
        if not benchmark_manager:
            return APIResponse.error("Benchmarking service not available", status_code=503)
        
        data = request.get_json() or {}
        test_name = data.get('test_name', f"benchmark_{int(datetime.now().timestamp())}")
        test_type = data.get('test_type', 'load')
        endpoints = data.get('endpoints')
        
        # Custom configuration
        config_data = data.get('config', {})
        from services.performance.benchmarking_service import BenchmarkConfig
        
        config = BenchmarkConfig(
            base_url=config_data.get('base_url', 'http://localhost:5000'),
            concurrent_users=config_data.get('concurrent_users', 10),
            requests_per_user=config_data.get('requests_per_user', 20),
            ramp_up_time=config_data.get('ramp_up_time', 5),
            timeout=config_data.get('timeout', 30)
        )
        
        if test_type == 'load':
            result = benchmark_manager.run_load_test(test_name, endpoints, config)
            return APIResponse.success(result.to_dict(), f"Load test '{test_name}' completed")
        
        elif test_type == 'stress':
            max_users = data.get('max_users', 50)
            step_size = data.get('step_size', 10)
            step_duration = data.get('step_duration', 30)
            
            results = benchmark_manager.run_stress_test(test_name, max_users, step_size, step_duration)
            return APIResponse.success(
                [r.to_dict() for r in results], 
                f"Stress test '{test_name}' completed"
            )
        
        else:
            return APIResponse.error("Invalid test_type. Supported: load, stress", status_code=400)
        
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        return APIResponse.error(f"Failed to run benchmark: {str(e)}", status_code=500)


@performance_bp.route('/benchmark/history', methods=['GET'])
def get_benchmark_history():
    """Get benchmark test history."""
    try:
        if not benchmark_manager:
            return APIResponse.error("Benchmarking service not available", status_code=503)
        
        limit = request.args.get('limit', type=int)
        history = benchmark_manager.get_benchmark_history(limit)
        
        return APIResponse.success(
            {'benchmarks': history}, 
            f"Retrieved {len(history)} benchmark results"
        )
        
    except Exception as e:
        logger.error(f"Error getting benchmark history: {e}")
        return APIResponse.error(f"Failed to get benchmark history: {str(e)}", status_code=500)


@performance_bp.route('/benchmark/compare', methods=['POST'])
def compare_benchmarks():
    """Compare two benchmark results."""
    try:
        if not benchmark_manager:
            return APIResponse.error("Benchmarking service not available", status_code=503)
        
        data = request.get_json() or {}
        baseline_name = data.get('baseline')
        comparison_name = data.get('comparison')
        
        if not baseline_name or not comparison_name:
            return APIResponse.error("Both baseline and comparison test names are required", status_code=400)
        
        comparison = benchmark_manager.compare_benchmarks(baseline_name, comparison_name)
        
        if 'error' in comparison:
            return APIResponse.error(comparison['error'], status_code=404)
        
        return APIResponse.success(comparison, "Benchmark comparison completed")
        
    except Exception as e:
        logger.error(f"Error comparing benchmarks: {e}")
        return APIResponse.error(f"Failed to compare benchmarks: {str(e)}", status_code=500)


@performance_bp.route('/health', methods=['GET'])
def performance_health():
    """Performance services health check."""
    try:
        health = {
            'timestamp': datetime.now().isoformat(),
            'services': {
                'cache': hasattr(current_app, 'cache_service'),
                'monitoring': hasattr(current_app, 'performance_monitor'),
                'optimization': hasattr(current_app, 'db_optimizer'),
                'benchmarking': benchmark_manager is not None
            },
            'status': 'healthy'
        }
        
        # Check Redis connectivity if cache service is available
        if hasattr(current_app, 'cache_service'):
            cache_service = current_app.cache_service
            health['cache_redis_available'] = cache_service.redis_client is not None
            
            if cache_service.redis_client:
                try:
                    cache_service.redis_client.ping()
                    health['cache_redis_status'] = 'connected'
                except Exception:
                    health['cache_redis_status'] = 'disconnected'
        
        return APIResponse.success(health, "Performance services are healthy")
        
    except Exception as e:
        logger.error(f"Error checking performance health: {e}")
        return APIResponse.error(f"Health check failed: {str(e)}", status_code=500)