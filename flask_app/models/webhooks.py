"""
Webhook Models for Advanced API Features

Manages webhook subscriptions, deliveries, and analytics for event-driven
integrations with external systems.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from datetime import datetime
import uuid
import json
import hashlib
import hmac
from enum import Enum

from .base import db, BaseModel


class WebhookEvent(Enum):
    """Supported webhook event types"""
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"
    
    INITIATIVE_CREATED = "initiative.created"
    INITIATIVE_UPDATED = "initiative.updated"
    INITIATIVE_DELETED = "initiative.deleted"
    
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    
    EXPORT_COMPLETED = "export.completed"
    EXPORT_FAILED = "export.failed"


class WebhookStatus(Enum):
    """Webhook subscription status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    FAILED = "failed"


class DeliveryStatus(Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class WebhookSubscription(BaseModel):
    """Model for webhook subscriptions"""
    
    __tablename__ = 'webhook_subscriptions'
    
    # Core fields
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Event configuration
    events = db.Column(db.JSON, nullable=False)  # List of WebhookEvent values
    filters = db.Column(db.JSON, nullable=True)  # Event filtering criteria
    
    # Security
    secret = db.Column(db.String(128), nullable=False)  # HMAC secret
    headers = db.Column(db.JSON, nullable=True)  # Custom headers
    
    # Configuration
    status = db.Column(db.Enum(WebhookStatus), default=WebhookStatus.ACTIVE, nullable=False)
    retry_count = db.Column(db.Integer, default=3, nullable=False)
    timeout_seconds = db.Column(db.Integer, default=30, nullable=False)
    
    # Statistics
    total_deliveries = db.Column(db.Integer, default=0, nullable=False)
    successful_deliveries = db.Column(db.Integer, default=0, nullable=False)
    failed_deliveries = db.Column(db.Integer, default=0, nullable=False)
    last_delivery_at = db.Column(db.DateTime, nullable=True)
    last_success_at = db.Column(db.DateTime, nullable=True)
    last_failure_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    deliveries = db.relationship('WebhookDelivery', backref='subscription', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.secret:
            self.secret = self._generate_secret()
        if not self.events:
            self.events = []
        if not self.headers:
            self.headers = {}
        if not self.filters:
            self.filters = {}
    
    def _generate_secret(self) -> str:
        """Generate secure webhook secret"""
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
    
    def to_dict(self):
        """Convert webhook subscription to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'name': self.name,
            'url': self.url,
            'description': self.description,
            'events': self.events or [],
            'filters': self.filters or {},
            'secret': self.secret,
            'headers': self.headers or {},
            'status': self.status.value if self.status else None,
            'retry_count': self.retry_count,
            'timeout_seconds': self.timeout_seconds,
            'total_deliveries': self.total_deliveries,
            'successful_deliveries': self.successful_deliveries,
            'failed_deliveries': self.failed_deliveries,
            'success_rate': self.get_success_rate(),
            'last_delivery_at': self.last_delivery_at.isoformat() if self.last_delivery_at else None,
            'last_success_at': self.last_success_at.isoformat() if self.last_success_at else None,
            'last_failure_at': self.last_failure_at.isoformat() if self.last_failure_at else None
        })
        return base_dict
    
    def get_success_rate(self) -> float:
        """Calculate delivery success rate"""
        if self.total_deliveries == 0:
            return 0.0
        return (self.successful_deliveries / self.total_deliveries) * 100.0
    
    def should_deliver_event(self, event_type: WebhookEvent, event_data: dict) -> bool:
        """Check if event should be delivered to this subscription"""
        # Check if event type is subscribed
        if event_type.value not in self.events:
            return False
        
        # Check subscription status
        if self.status != WebhookStatus.ACTIVE:
            return False
        
        # Apply filters if defined
        if self.filters:
            return self._matches_filters(event_data, self.filters)
        
        return True
    
    def _matches_filters(self, event_data: dict, filters: dict) -> bool:
        """Check if event data matches subscription filters"""
        for filter_key, filter_value in filters.items():
            if '.' in filter_key:
                # Handle nested keys (e.g., "data.status")
                keys = filter_key.split('.')
                data_value = event_data
                for key in keys:
                    if isinstance(data_value, dict) and key in data_value:
                        data_value = data_value[key]
                    else:
                        data_value = None
                        break
            else:
                data_value = event_data.get(filter_key)
            
            # Check filter match
            if isinstance(filter_value, list):
                if data_value not in filter_value:
                    return False
            elif isinstance(filter_value, dict):
                # Handle operator-based filters
                operator = filter_value.get('operator', 'eq')
                expected_value = filter_value.get('value')
                
                if operator == 'eq' and data_value != expected_value:
                    return False
                elif operator == 'ne' and data_value == expected_value:
                    return False
                elif operator == 'in' and data_value not in expected_value:
                    return False
                elif operator == 'contains' and expected_value not in str(data_value):
                    return False
            else:
                if data_value != filter_value:
                    return False
        
        return True
    
    def generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for payload"""
        return hmac.new(
            self.secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def update_delivery_stats(self, success: bool):
        """Update delivery statistics"""
        self.total_deliveries += 1
        self.last_delivery_at = datetime.utcnow()
        
        if success:
            self.successful_deliveries += 1
            self.last_success_at = datetime.utcnow()
        else:
            self.failed_deliveries += 1
            self.last_failure_at = datetime.utcnow()
    
    @classmethod
    def get_active_subscriptions(cls):
        """Get all active webhook subscriptions"""
        return cls.query.filter(cls.status == WebhookStatus.ACTIVE).all()
    
    @classmethod
    def get_subscriptions_for_event(cls, event_type: WebhookEvent):
        """Get subscriptions that listen for specific event type"""
        return cls.query.filter(
            cls.status == WebhookStatus.ACTIVE,
            cls.events.contains([event_type.value])
        ).all()


class WebhookDelivery(BaseModel):
    """Model for webhook delivery attempts"""
    
    __tablename__ = 'webhook_deliveries'
    
    # Core fields
    subscription_id = db.Column(db.String(36), db.ForeignKey('webhook_subscriptions.id'), nullable=False)
    event_type = db.Column(db.Enum(WebhookEvent), nullable=False)
    event_id = db.Column(db.String(36), nullable=False)  # ID of the event that triggered webhook
    
    # Payload
    payload = db.Column(db.Text, nullable=False)  # JSON payload
    signature = db.Column(db.String(128), nullable=False)  # HMAC signature
    
    # Delivery tracking
    status = db.Column(db.Enum(DeliveryStatus), default=DeliveryStatus.PENDING, nullable=False)
    attempt_count = db.Column(db.Integer, default=0, nullable=False)
    max_attempts = db.Column(db.Integer, default=3, nullable=False)
    
    # Response tracking
    response_status_code = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, nullable=True)
    response_headers = db.Column(db.JSON, nullable=True)
    
    # Timing
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    first_attempted_at = db.Column(db.DateTime, nullable=True)
    last_attempted_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Error tracking
    error_message = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.JSON, nullable=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.response_headers:
            self.response_headers = {}
        if not self.error_details:
            self.error_details = {}
    
    def to_dict(self):
        """Convert webhook delivery to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'subscription_id': self.subscription_id,
            'event_type': self.event_type.value if self.event_type else None,
            'event_id': self.event_id,
            'payload': json.loads(self.payload) if self.payload else None,
            'signature': self.signature,
            'status': self.status.value if self.status else None,
            'attempt_count': self.attempt_count,
            'max_attempts': self.max_attempts,
            'response_status_code': self.response_status_code,
            'response_body': self.response_body,
            'response_headers': self.response_headers or {},
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'first_attempted_at': self.first_attempted_at.isoformat() if self.first_attempted_at else None,
            'last_attempted_at': self.last_attempted_at.isoformat() if self.last_attempted_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'error_message': self.error_message,
            'error_details': self.error_details or {}
        })
        return base_dict
    
    def can_retry(self) -> bool:
        """Check if delivery can be retried"""
        return (
            self.status in [DeliveryStatus.FAILED, DeliveryStatus.RETRYING] and
            self.attempt_count < self.max_attempts
        )
    
    def mark_attempt(self, status_code: int = None, response_body: str = None, 
                    response_headers: dict = None, error_message: str = None):
        """Mark delivery attempt with response details"""
        now = datetime.utcnow()
        
        self.attempt_count += 1
        self.last_attempted_at = now
        
        if not self.first_attempted_at:
            self.first_attempted_at = now
        
        # Update response details
        if status_code is not None:
            self.response_status_code = status_code
        if response_body is not None:
            self.response_body = response_body
        if response_headers is not None:
            self.response_headers = response_headers
        if error_message is not None:
            self.error_message = error_message
        
        # Determine status based on response
        if status_code and 200 <= status_code < 300:
            self.status = DeliveryStatus.DELIVERED
            self.delivered_at = now
        elif self.can_retry():
            self.status = DeliveryStatus.RETRYING
        else:
            self.status = DeliveryStatus.FAILED
    
    @classmethod
    def get_pending_deliveries(cls, limit: int = 100):
        """Get pending webhook deliveries"""
        return cls.query.filter(
            cls.status.in_([DeliveryStatus.PENDING, DeliveryStatus.RETRYING]),
            cls.scheduled_at <= datetime.utcnow()
        ).order_by(cls.scheduled_at.asc()).limit(limit).all()
    
    @classmethod
    def get_deliveries_for_subscription(cls, subscription_id: str, limit: int = 50):
        """Get deliveries for specific subscription"""
        return cls.query.filter(
            cls.subscription_id == subscription_id
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def create_delivery(cls, subscription: WebhookSubscription, event_type: WebhookEvent, 
                       event_id: str, payload_data: dict):
        """Create new webhook delivery"""
        # Serialize payload
        payload_json = json.dumps(payload_data, default=str)
        
        # Generate signature
        signature = subscription.generate_signature(payload_json)
        
        # Create delivery record
        delivery = cls(
            subscription_id=subscription.id,
            event_type=event_type,
            event_id=event_id,
            payload=payload_json,
            signature=signature,
            max_attempts=subscription.retry_count
        )
        
        return delivery