"""
Cache Service

Provides multi-level caching infrastructure with Redis backend and intelligent
cache invalidation for TaskMaster API performance optimization.

Features:
- Redis-based distributed caching
- Application-level memory caching
- Intelligent cache key generation
- Dependency-based cache invalidation
- TTL management and cache warming
- Performance metrics integration
"""

import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from functools import wraps
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from flask import current_app, request
import logging

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration settings."""
    
    # Redis settings
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None
    REDIS_SOCKET_TIMEOUT = 30
    REDIS_CONNECTION_POOL_MAX_CONNECTIONS = 50
    
    # Cache TTL settings (seconds)
    DEFAULT_TTL = 300  # 5 minutes
    LONG_TTL = 3600    # 1 hour
    SHORT_TTL = 60     # 1 minute
    
    # TTL by resource type
    RESOURCE_TTL = {
        'tasks': 300,
        'events': 300,
        'initiatives': 600,
        'projects': 600,
        'meals': 1800,
        'dishes': 3600,
        'weather': 10800,  # 3 hours
        'analysis': 1800,
        'schedule': 300,
        'assignments': 600
    }
    
    # Memory cache settings
    MEMORY_CACHE_SIZE = 1000
    MEMORY_CACHE_TTL = 60
    
    # Performance settings
    MAX_KEY_SIZE = 250
    ENABLE_COMPRESSION = True
    COMPRESSION_THRESHOLD = 1024  # bytes


class MemoryCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 60):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        value, expires_at = self._cache[key]
        current_time = time.time()
        
        if current_time > expires_at:
            self.delete(key)
            return None
        
        self._access_times[key] = current_time
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        current_time = time.time()
        ttl = ttl or self.default_ttl
        expires_at = current_time + ttl
        
        # Evict if at max size
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()
        
        self._cache[key] = (value, expires_at)
        self._access_times[key] = current_time
        return True
    
    def delete(self, key: str) -> bool:
        """Remove key from cache."""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
        return True
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_times.clear()
        return True
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        self.delete(lru_key)


class CacheService:
    """Multi-level cache service with Redis and memory caching."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.redis_client = None
        self.memory_cache = MemoryCache(
            max_size=self.config.MEMORY_CACHE_SIZE,
            default_ttl=self.config.MEMORY_CACHE_TTL
        )
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'redis_hits': 0,
            'memory_hits': 0,
            'errors': 0
        }
        self._dependency_map: Dict[str, Set[str]] = {}
        
        # Initialize Redis if available
        if REDIS_AVAILABLE:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            pool = redis.ConnectionPool(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                password=self.config.REDIS_PASSWORD,
                socket_timeout=self.config.REDIS_SOCKET_TIMEOUT,
                max_connections=self.config.REDIS_CONNECTION_POOL_MAX_CONNECTIONS,
                decode_responses=True
            )
            self.redis_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            self.redis_client = None
    
    def generate_key(self, prefix: str, identifier: str, **kwargs) -> str:
        """Generate standardized cache key."""
        key_parts = [prefix, identifier]
        
        # Add sorted kwargs for consistency
        if kwargs:
            sorted_params = sorted(kwargs.items())
            param_str = '&'.join(f"{k}={v}" for k, v in sorted_params)
            key_parts.append(hashlib.md5(param_str.encode()).hexdigest()[:8])
        
        key = ':'.join(str(part) for part in key_parts)
        
        # Ensure key doesn't exceed max size
        if len(key) > self.config.MAX_KEY_SIZE:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            key = f"{prefix}:{key_hash}"
        
        return key
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then Redis)."""
        try:
            # Try memory cache first
            value = self.memory_cache.get(key)
            if value is not None:
                self._cache_stats['hits'] += 1
                self._cache_stats['memory_hits'] += 1
                return value
            
            # Try Redis if available
            if self.redis_client:
                redis_value = self.redis_client.get(key)
                if redis_value is not None:
                    # Store in memory cache for faster access
                    parsed_value = json.loads(redis_value)
                    self.memory_cache.set(key, parsed_value)
                    
                    self._cache_stats['hits'] += 1
                    self._cache_stats['redis_hits'] += 1
                    return parsed_value
            
            self._cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._cache_stats['errors'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            dependencies: Optional[List[str]] = None) -> bool:
        """Set value in cache with TTL and dependency tracking."""
        try:
            ttl = ttl or self.config.DEFAULT_TTL
            
            # Set in memory cache
            self.memory_cache.set(key, value, min(ttl, self.config.MEMORY_CACHE_TTL))
            
            # Set in Redis if available
            if self.redis_client:
                serialized_value = json.dumps(value, default=str)
                
                # Apply compression if enabled and value is large enough
                if (self.config.ENABLE_COMPRESSION and 
                    len(serialized_value) > self.config.COMPRESSION_THRESHOLD):
                    import gzip
                    serialized_value = gzip.compress(serialized_value.encode()).decode('latin1')
                    key = f"gz:{key}"
                
                self.redis_client.setex(key, ttl, serialized_value)
            
            # Track dependencies
            if dependencies:
                self._track_dependencies(key, dependencies)
            
            self._cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._cache_stats['errors'] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from all cache levels."""
        try:
            success = True
            
            # Delete from memory cache
            self.memory_cache.delete(key)
            
            # Delete from Redis
            if self.redis_client:
                self.redis_client.delete(key)
                # Also try compressed version
                self.redis_client.delete(f"gz:{key}")
            
            # Remove from dependency tracking
            self._remove_from_dependencies(key)
            
            self._cache_stats['deletes'] += 1
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._cache_stats['errors'] += 1
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        try:
            count = 0
            
            # For Redis, use SCAN for efficiency
            if self.redis_client:
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
            
            # For memory cache, iterate over keys
            memory_keys = list(self.memory_cache._cache.keys())
            for key in memory_keys:
                if self._match_pattern(key, pattern):
                    self.memory_cache.delete(key)
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error for {pattern}: {e}")
            self._cache_stats['errors'] += 1
            return 0
    
    def invalidate_dependencies(self, dependency: str) -> int:
        """Invalidate all cache keys that depend on the given dependency."""
        if dependency not in self._dependency_map:
            return 0
        
        dependent_keys = self._dependency_map[dependency].copy()
        count = 0
        
        for key in dependent_keys:
            if self.delete(key):
                count += 1
        
        # Clean up the dependency mapping
        del self._dependency_map[dependency]
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            **self._cache_stats,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'redis_available': self.redis_client is not None,
            'memory_cache_size': len(self.memory_cache._cache),
            'dependency_mappings': len(self._dependency_map)
        }
        
        if self.redis_client:
            try:
                redis_info = self.redis_client.info('memory')
                stats['redis_memory_used'] = redis_info.get('used_memory_human', 'Unknown')
                stats['redis_connected_clients'] = self.redis_client.info('clients')['connected_clients']
            except Exception:
                pass
        
        return stats
    
    def clear_all(self) -> bool:
        """Clear all caches."""
        try:
            self.memory_cache.clear()
            
            if self.redis_client:
                self.redis_client.flushdb()
            
            self._dependency_map.clear()
            return True
            
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")
            return False
    
    def _track_dependencies(self, key: str, dependencies: List[str]):
        """Track cache key dependencies for invalidation."""
        for dep in dependencies:
            if dep not in self._dependency_map:
                self._dependency_map[dep] = set()
            self._dependency_map[dep].add(key)
    
    def _remove_from_dependencies(self, key: str):
        """Remove key from all dependency mappings."""
        for dep_set in self._dependency_map.values():
            dep_set.discard(key)
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for cache keys."""
        if '*' not in pattern:
            return key == pattern
        
        # Convert glob pattern to regex-like matching
        import re
        regex_pattern = pattern.replace('*', '.*')
        return re.match(f"^{regex_pattern}$", key) is not None


def cache_response(ttl: Optional[int] = None, dependencies: Optional[List[str]] = None):
    """Decorator for caching API responses."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not hasattr(current_app, 'cache_service'):
                return func(*args, **kwargs)
            
            cache_service = current_app.cache_service
            
            # Generate cache key from function name, args, and request params
            func_name = f"{func.__module__}.{func.__name__}"
            request_key = ""
            
            if hasattr(request, 'args'):
                sorted_params = sorted(request.args.items())
                request_key = hashlib.md5(str(sorted_params).encode()).hexdigest()[:8]
            
            cache_key = cache_service.generate_key(func_name, request_key)
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Determine TTL based on function or default
            effective_ttl = ttl
            if effective_ttl is None:
                # Try to infer from function name
                for resource, resource_ttl in cache_service.config.RESOURCE_TTL.items():
                    if resource in func_name.lower():
                        effective_ttl = resource_ttl
                        break
                else:
                    effective_ttl = cache_service.config.DEFAULT_TTL
            
            cache_service.set(cache_key, result, effective_ttl, dependencies)
            return result
            
        return wrapper
    return decorator


# Global cache manager instance
cache_manager: Optional[CacheService] = None


def init_cache_service(app):
    """Initialize cache service with Flask app."""
    global cache_manager
    
    config = CacheConfig()
    cache_manager = CacheService(config)
    app.cache_service = cache_manager
    
    return cache_manager