"""
Performance Monitoring Middleware

Flask middleware for automatic performance monitoring, caching,
and optimization of all API requests.

Features:
- Automatic request/response time tracking
- Cache-Control header management
- Response compression
- Database query monitoring
- Error rate tracking
"""

import time
import gzip
from typing import Optional
from functools import wraps

from flask import (
    request, g, current_app, Response, 
    jsonify, after_this_request
)
import logging

logger = logging.getLogger(__name__)


def init_performance_middleware(app):
    """Initialize performance monitoring middleware for Flask app."""
    
    @app.before_request
    def before_request():
        """Set up request tracking before each request."""
        g.start_time = time.time()
        g.request_path = request.path
        g.request_method = request.method
        
        # Track in performance monitor if available
        if hasattr(current_app, 'performance_monitor'):
            g.endpoint_name = f"{request.method} {request.path}"
    
    @app.after_request
    def after_request(response):
        """Process response and collect metrics after each request."""
        try:
            # Calculate response time
            if hasattr(g, 'start_time'):
                response_time = (time.time() - g.start_time) * 1000  # Convert to ms
                
                # Add response time header
                response.headers['X-Response-Time'] = f"{response_time:.2f}ms"
                
                # Track in performance monitor
                if hasattr(current_app, 'performance_monitor') and hasattr(g, 'endpoint_name'):
                    monitor = current_app.performance_monitor
                    is_error = response.status_code >= 400
                    monitor.endpoint_metrics[g.endpoint_name].add_request(response_time, is_error)
            
            # Add cache headers for API responses
            if request.path.startswith('/api/'):
                add_cache_headers(response)
            
            # Add compression if enabled and beneficial
            if should_compress_response(response):
                response = compress_response(response)
            
            # Add performance headers
            add_performance_headers(response)
            
        except Exception as e:
            logger.error(f"Error in after_request middleware: {e}")
        
        return response
    
    @app.teardown_request
    def teardown_request(exception):
        """Clean up request-specific data."""
        # Clean up any request-specific caching or monitoring data
        pass


def add_cache_headers(response: Response) -> Response:
    """Add appropriate cache headers to API responses."""
    try:
        # Default cache settings
        if response.status_code == 200:
            # Cacheable responses
            if request.method == 'GET':
                # Different cache durations based on endpoint
                if '/api/v2/tasks' in request.path or '/api/v2/events' in request.path:
                    response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutes
                elif '/api/schedule' in request.path:
                    response.headers['Cache-Control'] = 'public, max-age=60'   # 1 minute
                elif '/api/weather' in request.path:
                    response.headers['Cache-Control'] = 'public, max-age=1800' # 30 minutes
                else:
                    response.headers['Cache-Control'] = 'public, max-age=300'
                
                # Add ETag for conditional requests
                if hasattr(response, 'data') and response.data:
                    import hashlib
                    etag = hashlib.md5(response.data).hexdigest()[:16]
                    response.headers['ETag'] = f'"{etag}"'
        
        elif response.status_code >= 400:
            # Don't cache error responses
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
    except Exception as e:
        logger.error(f"Error adding cache headers: {e}")
    
    return response


def should_compress_response(response: Response) -> bool:
    """Determine if response should be compressed."""
    try:
        # Only compress if:
        # 1. Content is text/json
        # 2. Content is large enough to benefit
        # 3. Client accepts gzip
        # 4. Not already compressed
        
        content_type = response.headers.get('Content-Type', '')
        content_length = len(response.data) if response.data else 0
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        return (
            'gzip' in accept_encoding and
            content_length > 1024 and  # Only compress if > 1KB
            ('json' in content_type or 'text' in content_type) and
            'Content-Encoding' not in response.headers
        )
        
    except Exception:
        return False


def compress_response(response: Response) -> Response:
    """Compress response data using gzip."""
    try:
        if response.data:
            compressed_data = gzip.compress(response.data)
            
            # Only use compression if it actually saves space
            if len(compressed_data) < len(response.data):
                response.data = compressed_data
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = str(len(compressed_data))
                
                # Track compression savings
                if hasattr(current_app, 'db_optimizer'):
                    savings = len(response.data) - len(compressed_data)
                    current_app.db_optimizer.stats['compression_savings'] += savings
        
    except Exception as e:
        logger.error(f"Error compressing response: {e}")
    
    return response


def add_performance_headers(response: Response) -> Response:
    """Add performance-related headers to response."""
    try:
        # Add server performance info
        response.headers['X-Powered-By'] = 'TaskMaster Performance Engine'
        
        # Add cache status if available
        if hasattr(current_app, 'cache_service'):
            cache_stats = current_app.cache_service.get_stats()
            response.headers['X-Cache-Hit-Rate'] = f"{cache_stats.get('hit_rate', 0):.1f}%"
        
        # Add database query info if monitoring is enabled
        if hasattr(g, 'db_query_count'):
            response.headers['X-DB-Queries'] = str(g.db_query_count)
        
    except Exception as e:
        logger.error(f"Error adding performance headers: {e}")
    
    return response


def cache_key_generator(*args, **kwargs):
    """Generate cache key for Flask-Caching."""
    try:
        # Include request path, method, and sorted query parameters
        key_parts = [
            request.method,
            request.path,
        ]
        
        # Add query parameters (sorted for consistency)
        if request.args:
            sorted_args = sorted(request.args.items())
            key_parts.append(str(sorted_args))
        
        # Add user context if available (for user-specific caching)
        if hasattr(g, 'user_id'):
            key_parts.append(f"user:{g.user_id}")
        
        cache_key = ':'.join(key_parts)
        
        # Ensure key length is reasonable
        if len(cache_key) > 250:
            import hashlib
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
        
        return cache_key
        
    except Exception as e:
        logger.error(f"Error generating cache key: {e}")
        return f"fallback:{int(time.time())}"


def performance_required(f):
    """Decorator to ensure performance services are available."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(current_app, 'performance_monitor'):
            return jsonify({
                'status': 'error',
                'message': 'Performance monitoring not available'
            }), 503
        
        return f(*args, **kwargs)
    
    return decorated_function


def monitor_db_queries(f):
    """Decorator to monitor database queries in a function."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(current_app, 'performance_monitor'):
            return f(*args, **kwargs)
        
        monitor = current_app.performance_monitor
        
        # Initialize query counter
        if not hasattr(g, 'db_query_count'):
            g.db_query_count = 0
        
        # Track query performance
        with monitor.track_db_query('api_endpoint', request.path.split('/')[-1]):
            result = f(*args, **kwargs)
        
        return result
    
    return decorated_function


def cached_api_response(timeout: int = 300, key_prefix: Optional[str] = None):
    """Decorator for caching API responses with automatic invalidation."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(current_app, 'cache_service'):
                return f(*args, **kwargs)
            
            cache_service = current_app.cache_service
            
            # Generate cache key
            prefix = key_prefix or f.__name__
            cache_key = cache_service.generate_key(
                prefix,
                cache_key_generator(),
                method=request.method,
                path=request.path
            )
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                # Add cache hit header
                response = jsonify(cached_result)
                response.headers['X-Cache'] = 'HIT'
                return response
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache successful responses
            if hasattr(result, 'status_code') and 200 <= result.status_code < 300:
                if hasattr(result, 'get_json'):
                    json_data = result.get_json()
                    if json_data:
                        # Determine dependencies for cache invalidation
                        dependencies = []
                        if '/tasks' in request.path:
                            dependencies.append('tasks')
                        elif '/events' in request.path:
                            dependencies.append('events')
                        elif '/initiatives' in request.path:
                            dependencies.append('initiatives')
                        
                        cache_service.set(cache_key, json_data, timeout, dependencies)
                        
                        # Add cache miss header
                        result.headers['X-Cache'] = 'MISS'
            
            return result
        
        return decorated_function
    return decorator