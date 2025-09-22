"""
Analytics Models for Advanced API Features

Tracks API usage, performance metrics, and provides insights for
optimization and monitoring.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from datetime import datetime, timedelta
import uuid
import json
from enum import Enum

from .base import db, BaseModel


class MetricType(Enum):
    """Types of metrics collected"""
    API_REQUEST = "api_request"
    API_RESPONSE = "api_response"
    SEARCH_QUERY = "search_query"
    EXPORT_REQUEST = "export_request"
    WEBHOOK_DELIVERY = "webhook_delivery"
    ERROR_OCCURRED = "error_occurred"


class APIUsageMetric(BaseModel):
    """Model for tracking API usage metrics"""
    
    __tablename__ = 'api_usage_metrics'
    
    # Request identification
    request_id = db.Column(db.String(36), nullable=False, index=True)
    session_id = db.Column(db.String(36), nullable=True, index=True)
    user_id = db.Column(db.String(36), nullable=True, index=True)
    
    # Request details
    method = db.Column(db.String(10), nullable=False)  # GET, POST, etc.
    endpoint = db.Column(db.String(500), nullable=False, index=True)
    route_pattern = db.Column(db.String(500), nullable=True, index=True)  # /api/tasks/{id}
    
    # Timing
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    response_time_ms = db.Column(db.Integer, nullable=True)  # Response time in milliseconds
    
    # Response details
    status_code = db.Column(db.Integer, nullable=True, index=True)
    response_size_bytes = db.Column(db.Integer, nullable=True)
    
    # Request metadata
    user_agent = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    referrer = db.Column(db.String(500), nullable=True)
    
    # Query parameters and filters
    query_params = db.Column(db.JSON, nullable=True)
    request_body_size = db.Column(db.Integer, nullable=True)
    
    # Performance metrics
    database_query_count = db.Column(db.Integer, nullable=True)
    database_query_time_ms = db.Column(db.Integer, nullable=True)
    cache_hit = db.Column(db.Boolean, nullable=True)
    
    # Error tracking
    error_type = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
        if not self.query_params:
            self.query_params = {}
    
    def to_dict(self):
        """Convert API usage metric to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'request_id': self.request_id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'method': self.method,
            'endpoint': self.endpoint,
            'route_pattern': self.route_pattern,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'response_time_ms': self.response_time_ms,
            'status_code': self.status_code,
            'response_size_bytes': self.response_size_bytes,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'referrer': self.referrer,
            'query_params': self.query_params or {},
            'request_body_size': self.request_body_size,
            'database_query_count': self.database_query_count,
            'database_query_time_ms': self.database_query_time_ms,
            'cache_hit': self.cache_hit,
            'error_type': self.error_type,
            'error_message': self.error_message
        })
        return base_dict
    
    @classmethod
    def get_metrics_by_timeframe(cls, start_time: datetime, end_time: datetime):
        """Get metrics within specific timeframe"""
        return cls.query.filter(
            cls.timestamp >= start_time,
            cls.timestamp <= end_time
        ).all()
    
    @classmethod
    def get_endpoint_metrics(cls, endpoint_pattern: str, hours: int = 24):
        """Get metrics for specific endpoint in last N hours"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.route_pattern == endpoint_pattern,
            cls.timestamp >= start_time
        ).all()
    
    @classmethod
    def get_error_metrics(cls, hours: int = 24):
        """Get error metrics in last N hours"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.status_code >= 400,
            cls.timestamp >= start_time
        ).all()


class SearchAnalytic(BaseModel):
    """Model for tracking search analytics"""
    
    __tablename__ = 'search_analytics'
    
    # Search identification
    search_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), nullable=True, index=True)
    user_id = db.Column(db.String(36), nullable=True, index=True)
    
    # Search details
    query = db.Column(db.Text, nullable=False)
    query_type = db.Column(db.String(50), nullable=True)  # basic, advanced, faceted
    entity_types = db.Column(db.JSON, nullable=True)  # Types searched
    filters_used = db.Column(db.JSON, nullable=True)  # Filters applied
    
    # Results
    result_count = db.Column(db.Integer, nullable=False)
    facets_used = db.Column(db.JSON, nullable=True)  # Facets clicked
    
    # Performance
    search_time_ms = db.Column(db.Integer, nullable=True)
    
    # User interaction
    clicked_results = db.Column(db.JSON, nullable=True)  # Which results were clicked
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.entity_types:
            self.entity_types = []
        if not self.filters_used:
            self.filters_used = {}
        if not self.facets_used:
            self.facets_used = []
        if not self.clicked_results:
            self.clicked_results = []
    
    def to_dict(self):
        """Convert search analytic to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'search_id': self.search_id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'query': self.query,
            'query_type': self.query_type,
            'entity_types': self.entity_types or [],
            'filters_used': self.filters_used or {},
            'result_count': self.result_count,
            'facets_used': self.facets_used or [],
            'search_time_ms': self.search_time_ms,
            'clicked_results': self.clicked_results or [],
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        })
        return base_dict
    
    @classmethod
    def get_popular_queries(cls, limit: int = 10, hours: int = 24):
        """Get most popular search queries"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return db.session.query(
            cls.query.label('search_query'),
            db.func.count(cls.id).label('count')
        ).filter(
            cls.timestamp >= start_time
        ).group_by(cls.query).order_by(db.func.count(cls.id).desc()).limit(limit).all()
    
    @classmethod
    def get_zero_result_queries(cls, hours: int = 24):
        """Get queries that returned no results"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.result_count == 0,
            cls.timestamp >= start_time
        ).all()


class APIKey(BaseModel):
    """Model for API key management"""
    
    __tablename__ = 'api_keys'
    
    # Key details
    key_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    key_hash = db.Column(db.String(128), nullable=False)  # Hashed API key
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Permissions
    permissions = db.Column(db.JSON, nullable=False)  # List of allowed operations
    rate_limit_per_hour = db.Column(db.Integer, default=1000, nullable=False)
    rate_limit_per_day = db.Column(db.Integer, default=10000, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Usage tracking
    total_requests = db.Column(db.Integer, default=0, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)
    last_ip_address = db.Column(db.String(45), nullable=True)
    
    # Security
    allowed_origins = db.Column(db.JSON, nullable=True)  # CORS origins
    allowed_ips = db.Column(db.JSON, nullable=True)  # IP whitelist
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.permissions:
            self.permissions = []
        if not self.allowed_origins:
            self.allowed_origins = []
        if not self.allowed_ips:
            self.allowed_ips = []
    
    def to_dict(self, include_sensitive=False):
        """Convert API key to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'key_id': self.key_id,
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions or [],
            'rate_limit_per_hour': self.rate_limit_per_hour,
            'rate_limit_per_day': self.rate_limit_per_day,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'total_requests': self.total_requests,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'last_ip_address': self.last_ip_address,
            'allowed_origins': self.allowed_origins or [],
            'allowed_ips': self.allowed_ips or []
        })
        
        if include_sensitive:
            base_dict['key_hash'] = self.key_hash
        
        return base_dict
    
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def has_permission(self, operation: str) -> bool:
        """Check if API key has specific permission"""
        if not self.is_active or self.is_expired():
            return False
        
        # Allow all if permissions list is empty or contains "*"
        if not self.permissions or "*" in self.permissions:
            return True
        
        return operation in self.permissions
    
    def update_usage(self, ip_address: str = None):
        """Update usage statistics"""
        self.total_requests += 1
        self.last_used_at = datetime.utcnow()
        if ip_address:
            self.last_ip_address = ip_address
    
    @classmethod
    def get_by_key_id(cls, key_id: str):
        """Get API key by key ID"""
        return cls.query.filter(cls.key_id == key_id, cls.is_active == True).first()


class RateLimitRecord(BaseModel):
    """Model for tracking rate limiting"""
    
    __tablename__ = 'rate_limit_records'
    
    # Identification
    key_id = db.Column(db.String(36), nullable=True, index=True)  # API key or None for IP-based
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    endpoint = db.Column(db.String(500), nullable=True, index=True)
    
    # Time windows
    hour_window = db.Column(db.DateTime, nullable=False, index=True)  # Hour bucket
    day_window = db.Column(db.DateTime, nullable=False, index=True)   # Day bucket
    
    # Counters
    requests_in_hour = db.Column(db.Integer, default=0, nullable=False)
    requests_in_day = db.Column(db.Integer, default=0, nullable=False)
    
    # Last activity
    last_request_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.hour_window:
            now = datetime.utcnow()
            self.hour_window = now.replace(minute=0, second=0, microsecond=0)
        if not self.day_window:
            now = datetime.utcnow()
            self.day_window = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def to_dict(self):
        """Convert rate limit record to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'key_id': self.key_id,
            'ip_address': self.ip_address,
            'endpoint': self.endpoint,
            'hour_window': self.hour_window.isoformat() if self.hour_window else None,
            'day_window': self.day_window.isoformat() if self.day_window else None,
            'requests_in_hour': self.requests_in_hour,
            'requests_in_day': self.requests_in_day,
            'last_request_at': self.last_request_at.isoformat() if self.last_request_at else None
        })
        return base_dict
    
    def increment_counters(self):
        """Increment request counters"""
        self.requests_in_hour += 1
        self.requests_in_day += 1
        self.last_request_at = datetime.utcnow()
    
    @classmethod
    def get_current_usage(cls, key_id: str = None, ip_address: str = None):
        """Get current rate limit usage"""
        now = datetime.utcnow()
        hour_window = now.replace(minute=0, second=0, microsecond=0)
        day_window = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = cls.query.filter(
            cls.hour_window == hour_window,
            cls.day_window == day_window
        )
        
        if key_id:
            query = query.filter(cls.key_id == key_id)
        if ip_address:
            query = query.filter(cls.ip_address == ip_address)
        
        return query.first()
    
    @classmethod
    def cleanup_old_records(cls, days: int = 7):
        """Clean up old rate limit records"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_records = cls.query.filter(cls.day_window < cutoff_date).all()
        
        count = len(old_records)
        for record in old_records:
            db.session.delete(record)
        
        db.session.commit()
        return count