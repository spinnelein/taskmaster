"""
Analytics Service for Advanced API Features

Provides comprehensive API usage tracking, performance monitoring,
and rate limiting capabilities.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from datetime import datetime, timedelta
import hashlib
import secrets
import json
from typing import Dict, List, Any, Optional, Tuple
from flask import current_app, request, g
from functools import wraps
import time

from models import db, APIUsageMetric, SearchAnalytic, APIKey, RateLimitRecord, MetricType


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class AnalyticsService:
    """Main analytics service for tracking and monitoring"""
    
    def __init__(self):
        self.default_rate_limits = {
            'requests_per_hour': 1000,
            'requests_per_day': 10000
        }
    
    def track_api_request(self, endpoint: str, method: str, 
                         start_time: float, status_code: int = None,
                         response_size: int = None, error_info: Dict = None):
        """Track API request metrics"""
        try:
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Extract request information
            user_agent = request.headers.get('User-Agent', '')[:500]
            ip_address = self._get_client_ip()
            referrer = request.headers.get('Referer', '')[:500]
            
            # Process query parameters
            query_params = dict(request.args) if request.args else {}
            
            # Get request body size
            request_body_size = None
            if hasattr(request, 'content_length') and request.content_length:
                request_body_size = request.content_length
            
            # Create metric record
            metric = APIUsageMetric(
                request_id=getattr(g, 'request_id', None),
                session_id=getattr(g, 'session_id', None),
                user_id=getattr(g, 'user_id', None),
                method=method,
                endpoint=endpoint,
                route_pattern=getattr(g, 'route_pattern', endpoint),
                response_time_ms=response_time_ms,
                status_code=status_code,
                response_size_bytes=response_size,
                user_agent=user_agent,
                ip_address=ip_address,
                referrer=referrer,
                query_params=query_params,
                request_body_size=request_body_size,
                database_query_count=getattr(g, 'db_query_count', None),
                database_query_time_ms=getattr(g, 'db_query_time_ms', None),
                cache_hit=getattr(g, 'cache_hit', None),
                error_type=error_info.get('type') if error_info else None,
                error_message=error_info.get('message') if error_info else None
            )
            
            db.session.add(metric)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Failed to track API request: {e}")
            db.session.rollback()
    
    def track_search_query(self, query: str, entity_types: List[str], 
                          filters: Dict, result_count: int, 
                          search_time_ms: int, query_type: str = 'basic'):
        """Track search analytics"""
        try:
            analytic = SearchAnalytic(
                session_id=getattr(g, 'session_id', None),
                user_id=getattr(g, 'user_id', None),
                query=query,
                query_type=query_type,
                entity_types=entity_types,
                filters_used=filters,
                result_count=result_count,
                search_time_ms=search_time_ms
            )
            
            db.session.add(analytic)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Failed to track search query: {e}")
            db.session.rollback()
    
    def track_search_interaction(self, search_id: str, clicked_results: List[str], 
                                facets_used: List[str] = None):
        """Track user interaction with search results"""
        try:
            analytic = SearchAnalytic.query.filter_by(search_id=search_id).first()
            if analytic:
                analytic.clicked_results = clicked_results
                analytic.facets_used = facets_used or []
                db.session.commit()
                
        except Exception as e:
            current_app.logger.error(f"Failed to track search interaction: {e}")
            db.session.rollback()
    
    def check_rate_limit(self, api_key: str = None, ip_address: str = None) -> Tuple[bool, Dict]:
        """Check if request should be rate limited"""
        try:
            # Get API key limits if provided
            if api_key:
                key_record = APIKey.get_by_key_id(api_key)
                if not key_record:
                    return False, {'error': 'Invalid API key'}
                
                if not key_record.is_active or key_record.is_expired():
                    return False, {'error': 'API key is inactive or expired'}
                
                hourly_limit = key_record.rate_limit_per_hour
                daily_limit = key_record.rate_limit_per_day
                identifier = api_key
                
                # Update API key usage
                key_record.update_usage(ip_address)
                
            else:
                # Use default limits for IP-based rate limiting
                hourly_limit = self.default_rate_limits['requests_per_hour']
                daily_limit = self.default_rate_limits['requests_per_day']
                identifier = ip_address or 'unknown'
            
            # Get or create rate limit record
            rate_record = RateLimitRecord.get_current_usage(
                key_id=api_key if api_key else None,
                ip_address=ip_address if not api_key else None
            )
            
            if not rate_record:
                # Create new rate limit record
                rate_record = RateLimitRecord(
                    key_id=api_key if api_key else None,
                    ip_address=ip_address if not api_key else None
                )
                db.session.add(rate_record)
            
            # Check limits
            if rate_record.requests_in_hour >= hourly_limit:
                return False, {
                    'error': 'Hourly rate limit exceeded',
                    'limit': hourly_limit,
                    'reset_time': (rate_record.hour_window + timedelta(hours=1)).isoformat()
                }
            
            if rate_record.requests_in_day >= daily_limit:
                return False, {
                    'error': 'Daily rate limit exceeded',
                    'limit': daily_limit,
                    'reset_time': (rate_record.day_window + timedelta(days=1)).isoformat()
                }
            
            # Increment counters
            rate_record.increment_counters()
            db.session.commit()
            
            return True, {
                'remaining_hourly': hourly_limit - rate_record.requests_in_hour,
                'remaining_daily': daily_limit - rate_record.requests_in_day,
                'reset_hourly': (rate_record.hour_window + timedelta(hours=1)).isoformat(),
                'reset_daily': (rate_record.day_window + timedelta(days=1)).isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Rate limit check failed: {e}")
            db.session.rollback()
            return True, {}  # Allow request on error
    
    def create_api_key(self, name: str, description: str = None, 
                      permissions: List[str] = None, 
                      rate_limit_per_hour: int = None,
                      rate_limit_per_day: int = None,
                      expires_at: datetime = None) -> Tuple[APIKey, str]:
        """Create new API key and return the key record and actual key"""
        try:
            # Generate secure API key
            api_key = self._generate_api_key()
            key_hash = self._hash_api_key(api_key)
            
            # Create API key record
            key_record = APIKey(
                name=name,
                description=description,
                key_hash=key_hash,
                permissions=permissions or [],
                rate_limit_per_hour=rate_limit_per_hour or self.default_rate_limits['requests_per_hour'],
                rate_limit_per_day=rate_limit_per_day or self.default_rate_limits['requests_per_day'],
                expires_at=expires_at
            )
            
            db.session.add(key_record)
            db.session.commit()
            
            current_app.logger.info(f"Created API key: {name}")
            return key_record, api_key
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create API key: {e}")
            raise
    
    def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Validate API key and return key record if valid"""
        try:
            key_hash = self._hash_api_key(api_key)
            key_record = APIKey.query.filter_by(key_hash=key_hash).first()
            
            if not key_record:
                return None
            
            if not key_record.is_active or key_record.is_expired():
                return None
            
            return key_record
            
        except Exception as e:
            current_app.logger.error(f"API key validation failed: {e}")
            return None
    
    def get_usage_analytics(self, timeframe: str = '24h') -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        try:
            # Parse timeframe
            end_time = datetime.utcnow()
            if timeframe == '1h':
                start_time = end_time - timedelta(hours=1)
            elif timeframe == '24h':
                start_time = end_time - timedelta(hours=24)
            elif timeframe == '7d':
                start_time = end_time - timedelta(days=7)
            elif timeframe == '30d':
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=24)
            
            # Get metrics
            metrics = APIUsageMetric.get_metrics_by_timeframe(start_time, end_time)
            
            # Calculate analytics
            total_requests = len(metrics)
            successful_requests = len([m for m in metrics if m.status_code and m.status_code < 400])
            error_requests = len([m for m in metrics if m.status_code and m.status_code >= 400])
            
            # Response times
            response_times = [m.response_time_ms for m in metrics if m.response_time_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Endpoint analytics
            endpoint_counts = {}
            for metric in metrics:
                endpoint = metric.route_pattern or metric.endpoint
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
            
            # Error analytics
            error_counts = {}
            for metric in metrics:
                if metric.status_code and metric.status_code >= 400:
                    error_counts[metric.status_code] = error_counts.get(metric.status_code, 0) + 1
            
            # User agent analytics
            user_agents = {}
            for metric in metrics:
                if metric.user_agent:
                    # Simplified user agent (first part)
                    ua = metric.user_agent.split('/')[0] if '/' in metric.user_agent else metric.user_agent
                    user_agents[ua] = user_agents.get(ua, 0) + 1
            
            return {
                'timeframe': timeframe,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'error_requests': error_requests,
                'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                'avg_response_time_ms': round(avg_response_time, 2),
                'top_endpoints': sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                'error_breakdown': error_counts,
                'top_user_agents': sorted(user_agents.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to get usage analytics: {e}")
            return {}
    
    def get_search_analytics(self, timeframe: str = '24h') -> Dict[str, Any]:
        """Get search analytics"""
        try:
            # Parse timeframe
            hours = 24
            if timeframe == '1h':
                hours = 1
            elif timeframe == '7d':
                hours = 24 * 7
            elif timeframe == '30d':
                hours = 24 * 30
            
            # Get popular queries
            popular_queries = SearchAnalytic.get_popular_queries(limit=10, hours=hours)
            
            # Get zero result queries
            zero_result_queries = SearchAnalytic.get_zero_result_queries(hours=hours)
            
            # Get recent search analytics
            start_time = datetime.utcnow() - timedelta(hours=hours)
            recent_searches = SearchAnalytic.query.filter(
                SearchAnalytic.timestamp >= start_time
            ).all()
            
            # Calculate metrics
            total_searches = len(recent_searches)
            avg_results = sum(s.result_count for s in recent_searches) / total_searches if total_searches > 0 else 0
            zero_result_rate = (len(zero_result_queries) / total_searches * 100) if total_searches > 0 else 0
            
            # Search times
            search_times = [s.search_time_ms for s in recent_searches if s.search_time_ms]
            avg_search_time = sum(search_times) / len(search_times) if search_times else 0
            
            return {
                'timeframe': timeframe,
                'total_searches': total_searches,
                'avg_results_per_search': round(avg_results, 2),
                'zero_result_rate': round(zero_result_rate, 2),
                'avg_search_time_ms': round(avg_search_time, 2),
                'popular_queries': [{'query': q[0], 'count': q[1]} for q in popular_queries],
                'zero_result_queries': [q.query for q in zero_result_queries[:10]]
            }
            
        except Exception as e:
            current_app.logger.error(f"Failed to get search analytics: {e}")
            return {}
    
    def cleanup_old_analytics(self, days: int = 30):
        """Clean up old analytics data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Clean up API usage metrics
            old_metrics = APIUsageMetric.query.filter(
                APIUsageMetric.timestamp < cutoff_date
            ).all()
            
            metrics_count = len(old_metrics)
            for metric in old_metrics:
                db.session.delete(metric)
            
            # Clean up search analytics
            old_searches = SearchAnalytic.query.filter(
                SearchAnalytic.timestamp < cutoff_date
            ).all()
            
            searches_count = len(old_searches)
            for search in old_searches:
                db.session.delete(search)
            
            # Clean up rate limit records
            rate_limit_count = RateLimitRecord.cleanup_old_records(days=7)
            
            db.session.commit()
            
            current_app.logger.info(
                f"Cleaned up analytics: {metrics_count} metrics, "
                f"{searches_count} searches, {rate_limit_count} rate limits"
            )
            
            return {
                'metrics_cleaned': metrics_count,
                'searches_cleaned': searches_count,
                'rate_limits_cleaned': rate_limit_count
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to cleanup analytics: {e}")
            return {}
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"tm_{secrets.token_urlsafe(32)}"
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        # Check for forwarded IP first
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'


# Decorator for API key authentication
def require_api_key(permissions: List[str] = None):
    """Decorator to require API key authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract API key from header or query parameter
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'API key required',
                    'code': 'MISSING_API_KEY'
                }, 401
            
            # Validate API key
            key_record = analytics_service.validate_api_key(api_key)
            if not key_record:
                return {
                    'success': False,
                    'error': 'Invalid API key',
                    'code': 'INVALID_API_KEY'
                }, 401
            
            # Check permissions
            if permissions:
                for permission in permissions:
                    if not key_record.has_permission(permission):
                        return {
                            'success': False,
                            'error': f'Permission denied: {permission}',
                            'code': 'PERMISSION_DENIED'
                        }, 403
            
            # Store key info in g for use in the request
            g.api_key_id = key_record.key_id
            g.api_key_name = key_record.name
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Decorator for rate limiting
def rate_limit(per_hour: int = None, per_day: int = None):
    """Decorator to apply rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key or IP for rate limiting
            api_key = getattr(g, 'api_key_id', None)
            ip_address = analytics_service._get_client_ip()
            
            # Check rate limit
            allowed, limit_info = analytics_service.check_rate_limit(api_key, ip_address)
            
            if not allowed:
                response_data = {
                    'success': False,
                    'error': limit_info.get('error', 'Rate limit exceeded'),
                    'code': 'RATE_LIMIT_EXCEEDED'
                }
                
                if 'reset_time' in limit_info:
                    response_data['reset_time'] = limit_info['reset_time']
                
                return response_data, 429
            
            # Add rate limit headers to response
            g.rate_limit_info = limit_info
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Global analytics service instance
analytics_service = AnalyticsService()