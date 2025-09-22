"""
Analytics API Routes for Advanced API Features

Provides API usage analytics, performance monitoring, and API key
management for comprehensive system insights.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from flask import Blueprint, request, jsonify, current_app, g
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any

from services.analytics_service import analytics_service, require_api_key, rate_limit
from models import APIKey, APIUsageMetric, SearchAnalytic, RateLimitRecord, db
from routes.api.response_utils import APIResponse


# Create analytics blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/usage', methods=['GET'])
@require_api_key(['analytics.read'])
@rate_limit(per_hour=100)
def get_usage_analytics():
    """
    Get API usage analytics
    
    Query Parameters:
    - timeframe: 1h|24h|7d|30d (default: 24h)
    - format: summary|detailed (default: summary)
    
    Returns:
    {
        "success": true,
        "data": {
            "timeframe": "24h",
            "total_requests": 1000,
            "successful_requests": 950,
            "error_requests": 50,
            "success_rate": 95.0,
            "avg_response_time_ms": 245.5,
            "top_endpoints": [...],
            "error_breakdown": {...}
        }
    }
    """
    try:
        timeframe = request.args.get('timeframe', '24h')
        format_type = request.args.get('format', 'summary')
        
        # Validate timeframe
        valid_timeframes = ['1h', '24h', '7d', '30d']
        if timeframe not in valid_timeframes:
            return create_error_response(
                f"Invalid timeframe: {timeframe}",
                400,
                {'code': 'INVALID_TIMEFRAME', 'valid_timeframes': valid_timeframes}
            )
        
        # Get analytics
        analytics = analytics_service.get_usage_analytics(timeframe)
        
        if format_type == 'detailed':
            # Add detailed breakdown by hour/day
            end_time = datetime.utcnow()
            if timeframe == '1h':
                start_time = end_time - timedelta(hours=1)
                bucket_size = timedelta(minutes=5)
            elif timeframe == '24h':
                start_time = end_time - timedelta(hours=24)
                bucket_size = timedelta(hours=1)
            elif timeframe == '7d':
                start_time = end_time - timedelta(days=7)
                bucket_size = timedelta(hours=6)
            else:  # 30d
                start_time = end_time - timedelta(days=30)
                bucket_size = timedelta(days=1)
            
            # Get detailed metrics
            metrics = APIUsageMetric.get_metrics_by_timeframe(start_time, end_time)
            
            # Create time series data
            time_series = []
            current_bucket = start_time
            while current_bucket < end_time:
                bucket_end = current_bucket + bucket_size
                bucket_metrics = [
                    m for m in metrics 
                    if current_bucket <= m.timestamp < bucket_end
                ]
                
                time_series.append({
                    'timestamp': current_bucket.isoformat(),
                    'requests': len(bucket_metrics),
                    'errors': len([m for m in bucket_metrics if m.status_code >= 400]),
                    'avg_response_time': sum(m.response_time_ms for m in bucket_metrics if m.response_time_ms) / len(bucket_metrics) if bucket_metrics else 0
                })
                
                current_bucket = bucket_end
            
            analytics['time_series'] = time_series
        
        return create_response(analytics)
        
    except Exception as e:
        current_app.logger.error(f"Get usage analytics failed: {e}")
        return create_error_response(
            "Failed to get usage analytics",
            500,
            {'code': 'GET_ANALYTICS_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/search', methods=['GET'])
@require_api_key(['analytics.read'])
@rate_limit(per_hour=100)
def get_search_analytics():
    """
    Get search analytics
    
    Query Parameters:
    - timeframe: 1h|24h|7d|30d (default: 24h)
    
    Returns:
    {
        "success": true,
        "data": {
            "timeframe": "24h",
            "total_searches": 500,
            "avg_results_per_search": 15.2,
            "zero_result_rate": 5.0,
            "popular_queries": [...],
            "zero_result_queries": [...]
        }
    }
    """
    try:
        timeframe = request.args.get('timeframe', '24h')
        
        # Validate timeframe
        valid_timeframes = ['1h', '24h', '7d', '30d']
        if timeframe not in valid_timeframes:
            return create_error_response(
                f"Invalid timeframe: {timeframe}",
                400,
                {'code': 'INVALID_TIMEFRAME', 'valid_timeframes': valid_timeframes}
            )
        
        # Get search analytics
        analytics = analytics_service.get_search_analytics(timeframe)
        
        return create_response(analytics)
        
    except Exception as e:
        current_app.logger.error(f"Get search analytics failed: {e}")
        return create_error_response(
            "Failed to get search analytics",
            500,
            {'code': 'GET_SEARCH_ANALYTICS_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/endpoints', methods=['GET'])
@require_api_key(['analytics.read'])
@rate_limit(per_hour=100)
def get_endpoint_analytics():
    """
    Get per-endpoint analytics
    
    Query Parameters:
    - timeframe: 1h|24h|7d|30d (default: 24h)
    - endpoint: Filter by specific endpoint pattern
    
    Returns:
    {
        "success": true,
        "data": {
            "endpoints": [
                {
                    "endpoint": "/api/tasks",
                    "total_requests": 100,
                    "avg_response_time": 150.5,
                    "error_rate": 2.0
                }
            ]
        }
    }
    """
    try:
        timeframe = request.args.get('timeframe', '24h')
        endpoint_filter = request.args.get('endpoint')
        
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
            return create_error_response(
                f"Invalid timeframe: {timeframe}",
                400,
                {'code': 'INVALID_TIMEFRAME'}
            )
        
        # Get metrics
        query = APIUsageMetric.query.filter(
            APIUsageMetric.timestamp >= start_time,
            APIUsageMetric.timestamp <= end_time
        )
        
        if endpoint_filter:
            query = query.filter(APIUsageMetric.route_pattern.like(f'%{endpoint_filter}%'))
        
        metrics = query.all()
        
        # Group by endpoint
        endpoint_stats = {}
        for metric in metrics:
            endpoint = metric.route_pattern or metric.endpoint
            
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    'total_requests': 0,
                    'response_times': [],
                    'errors': 0,
                    'status_codes': {}
                }
            
            stats = endpoint_stats[endpoint]
            stats['total_requests'] += 1
            
            if metric.response_time_ms:
                stats['response_times'].append(metric.response_time_ms)
            
            if metric.status_code:
                if metric.status_code >= 400:
                    stats['errors'] += 1
                
                status_key = str(metric.status_code)
                stats['status_codes'][status_key] = stats['status_codes'].get(status_key, 0) + 1
        
        # Calculate final stats
        endpoint_analytics = []
        for endpoint, stats in endpoint_stats.items():
            avg_response_time = sum(stats['response_times']) / len(stats['response_times']) if stats['response_times'] else 0
            error_rate = (stats['errors'] / stats['total_requests'] * 100) if stats['total_requests'] > 0 else 0
            
            endpoint_analytics.append({
                'endpoint': endpoint,
                'total_requests': stats['total_requests'],
                'avg_response_time_ms': round(avg_response_time, 2),
                'error_rate': round(error_rate, 2),
                'status_codes': stats['status_codes']
            })
        
        # Sort by request count
        endpoint_analytics.sort(key=lambda x: x['total_requests'], reverse=True)
        
        response_data = {
            'timeframe': timeframe,
            'endpoints': endpoint_analytics
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get endpoint analytics failed: {e}")
        return create_error_response(
            "Failed to get endpoint analytics",
            500,
            {'code': 'GET_ENDPOINT_ANALYTICS_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/api-keys', methods=['GET'])
@require_api_key(['admin'])
@rate_limit(per_hour=50)
def get_api_keys():
    """
    Get API keys (admin only)
    
    Query Parameters:
    - active: true|false (filter by active status)
    - limit: Maximum results (default: 20)
    - offset: Pagination offset (default: 0)
    
    Returns list of API keys (without sensitive data)
    """
    try:
        active_filter = request.args.get('active')
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = max(int(request.args.get('offset', 0)), 0)
        
        # Build query
        query = APIKey.query
        
        if active_filter is not None:
            is_active = active_filter.lower() == 'true'
            query = query.filter(APIKey.is_active == is_active)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        api_keys = query.order_by(APIKey.created_at.desc()).offset(offset).limit(limit).all()
        
        response_data = {
            'api_keys': [key.to_dict(include_sensitive=False) for key in api_keys],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get API keys failed: {e}")
        return create_error_response(
            "Failed to get API keys",
            500,
            {'code': 'GET_API_KEYS_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/api-keys', methods=['POST'])
@require_api_key(['admin'])
@rate_limit(per_hour=10)
def create_api_key():
    """
    Create new API key (admin only)
    
    Request Body:
    {
        "name": "Integration Key",
        "description": "For external system integration",
        "permissions": ["tasks.read", "events.read"],
        "rate_limit_per_hour": 1000,
        "rate_limit_per_day": 10000,
        "expires_at": "2024-12-31T23:59:59Z"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "api_key": "tm_xxxxxxxxxx",
            "key_record": {...}
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return create_error_response(
                "Request body is required",
                400,
                {'code': 'MISSING_REQUEST_BODY'}
            )
        
        # Validate required fields
        if not data.get('name'):
            return create_error_response(
                "Name is required",
                400,
                {'code': 'MISSING_NAME'}
            )
        
        # Parse expires_at if provided
        expires_at = None
        if data.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
            except ValueError:
                return create_error_response(
                    "Invalid expires_at format. Use ISO format",
                    400,
                    {'code': 'INVALID_EXPIRES_AT'}
                )
        
        # Create API key
        key_record, api_key = analytics_service.create_api_key(
            name=data['name'],
            description=data.get('description'),
            permissions=data.get('permissions', []),
            rate_limit_per_hour=data.get('rate_limit_per_hour'),
            rate_limit_per_day=data.get('rate_limit_per_day'),
            expires_at=expires_at
        )
        
        response_data = {
            'api_key': api_key,
            'key_record': key_record.to_dict(include_sensitive=False),
            'warning': 'Store this API key securely. It will not be shown again.'
        }
        
        return create_response(
            response_data,
            message="API key created successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"Create API key failed: {e}")
        return create_error_response(
            "Failed to create API key",
            500,
            {'code': 'CREATE_API_KEY_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/api-keys/<key_id>', methods=['PUT'])
@require_api_key(['admin'])
@rate_limit(per_hour=50)
def update_api_key(key_id):
    """
    Update API key (admin only)
    
    Request Body:
    {
        "name": "Updated Name",
        "description": "Updated description",
        "is_active": false,
        "permissions": ["tasks.read"],
        "rate_limit_per_hour": 500
    }
    """
    try:
        api_key = APIKey.query.filter_by(key_id=key_id).first()
        if not api_key:
            return create_error_response(
                "API key not found",
                404,
                {'code': 'API_KEY_NOT_FOUND'}
            )
        
        data = request.get_json()
        if not data:
            return create_error_response(
                "Request body is required",
                400,
                {'code': 'MISSING_REQUEST_BODY'}
            )
        
        # Update allowed fields
        updatable_fields = [
            'name', 'description', 'is_active', 'permissions',
            'rate_limit_per_hour', 'rate_limit_per_day', 'expires_at'
        ]
        
        for field, value in data.items():
            if field in updatable_fields and hasattr(api_key, field):
                if field == 'expires_at' and value:
                    try:
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        return create_error_response(
                            "Invalid expires_at format",
                            400,
                            {'code': 'INVALID_EXPIRES_AT'}
                        )
                
                setattr(api_key, field, value)
        
        api_key.updated_at = datetime.utcnow()
        db.session.commit()
        
        return create_response(
            api_key.to_dict(include_sensitive=False),
            message="API key updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update API key failed: {e}")
        return create_error_response(
            "Failed to update API key",
            500,
            {'code': 'UPDATE_API_KEY_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/api-keys/<key_id>', methods=['DELETE'])
@require_api_key(['admin'])
@rate_limit(per_hour=50)
def delete_api_key(key_id):
    """Delete API key (admin only)"""
    try:
        api_key = APIKey.query.filter_by(key_id=key_id).first()
        if not api_key:
            return create_error_response(
                "API key not found",
                404,
                {'code': 'API_KEY_NOT_FOUND'}
            )
        
        db.session.delete(api_key)
        db.session.commit()
        
        return create_response(
            {},
            message="API key deleted successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete API key failed: {e}")
        return create_error_response(
            "Failed to delete API key",
            500,
            {'code': 'DELETE_API_KEY_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/rate-limits', methods=['GET'])
@require_api_key(['analytics.read'])
@rate_limit(per_hour=100)
def get_rate_limit_status():
    """
    Get current rate limit status
    
    Returns:
    {
        "success": true,
        "data": {
            "current_key": {
                "remaining_hourly": 950,
                "remaining_daily": 9500,
                "reset_hourly": "2024-01-01T14:00:00Z",
                "reset_daily": "2024-01-02T00:00:00Z"
            }
        }
    }
    """
    try:
        # Get current API key info
        api_key_id = getattr(g, 'api_key_id', None)
        ip_address = analytics_service._get_client_ip()
        
        # Check current rate limit status
        allowed, limit_info = analytics_service.check_rate_limit(api_key_id, ip_address)
        
        response_data = {
            'api_key_id': api_key_id,
            'ip_address': ip_address,
            'status': 'within_limits' if allowed else 'rate_limited',
            'limits': limit_info
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get rate limit status failed: {e}")
        return create_error_response(
            "Failed to get rate limit status",
            500,
            {'code': 'GET_RATE_LIMIT_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/cleanup', methods=['POST'])
@require_api_key(['admin'])
@rate_limit(per_hour=5)
def cleanup_analytics():
    """
    Clean up old analytics data (admin only)
    
    Request Body (optional):
    {
        "max_age_days": 30
    }
    """
    try:
        data = request.get_json() or {}
        max_age_days = data.get('max_age_days', 30)
        
        if not isinstance(max_age_days, (int, float)) or max_age_days <= 0:
            return create_error_response(
                "max_age_days must be a positive number",
                400,
                {'code': 'INVALID_MAX_AGE'}
            )
        
        # Perform cleanup
        cleanup_results = analytics_service.cleanup_old_analytics(max_age_days)
        
        return create_response(
            cleanup_results,
            message="Analytics cleanup completed successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"Analytics cleanup failed: {e}")
        return create_error_response(
            "Failed to cleanup analytics",
            500,
            {'code': 'CLEANUP_ERROR', 'details': str(e)}
        )


@analytics_bp.route('/health', methods=['GET'])
def analytics_health():
    """
    Check analytics service health
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "total_metrics": 1000,
            "active_api_keys": 5,
            "rate_limit_records": 50
        }
    }
    """
    try:
        # Get counts
        total_metrics = APIUsageMetric.query.count()
        total_searches = SearchAnalytic.query.count()
        active_api_keys = APIKey.query.filter_by(is_active=True).count()
        rate_limit_records = RateLimitRecord.query.count()
        
        response_data = {
            'status': 'healthy',
            'total_metrics': total_metrics,
            'total_searches': total_searches,
            'active_api_keys': active_api_keys,
            'rate_limit_records': rate_limit_records,
            'capabilities': [
                'usage_analytics',
                'search_analytics',
                'api_key_management',
                'rate_limiting',
                'endpoint_monitoring',
                'performance_tracking'
            ]
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Analytics health check failed: {e}")
        return create_error_response(
            "Analytics health check failed",
            500,
            {'code': 'HEALTH_CHECK_ERROR', 'details': str(e)}
        )


# Add rate limit headers to all responses
@analytics_bp.after_request
def add_rate_limit_headers(response):
    """Add rate limit headers to response"""
    if hasattr(g, 'rate_limit_info') and g.rate_limit_info:
        headers = {
            'X-RateLimit-Remaining-Hourly': str(g.rate_limit_info.get('remaining_hourly', '')),
            'X-RateLimit-Remaining-Daily': str(g.rate_limit_info.get('remaining_daily', '')),
            'X-RateLimit-Reset-Hourly': g.rate_limit_info.get('reset_hourly', ''),
            'X-RateLimit-Reset-Daily': g.rate_limit_info.get('reset_daily', '')
        }
        
        for header, value in headers.items():
            if value:
                response.headers[header] = value
    
    return response


# Register error handlers
@analytics_bp.errorhandler(404)
def not_found(error):
    return create_error_response(
        "Analytics endpoint not found",
        404,
        {'code': 'ENDPOINT_NOT_FOUND'}
    )


@analytics_bp.errorhandler(405)
def method_not_allowed(error):
    return create_error_response(
        "Method not allowed for this analytics endpoint",
        405,
        {'code': 'METHOD_NOT_ALLOWED'}
    )