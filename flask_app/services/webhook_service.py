"""
Webhook Service for Advanced API Features

Handles webhook delivery, retry logic, and event dispatching for
external system integrations.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
import asyncio
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import current_app
import threading
import time
from dataclasses import dataclass

from models import db, WebhookSubscription, WebhookDelivery, WebhookEvent, WebhookStatus, DeliveryStatus


@dataclass
class WebhookPayload:
    """Webhook payload structure"""
    event_type: str
    event_id: str
    timestamp: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class WebhookDeliveryWorker:
    """Background worker for webhook deliveries"""
    
    def __init__(self):
        self.running = False
        self.worker_thread = None
        self.delivery_session = requests.Session()
        self.delivery_session.timeout = 30
        
        # Configure session with reasonable defaults
        self.delivery_session.headers.update({
            'User-Agent': 'TaskMaster-Webhook/1.0',
            'Content-Type': 'application/json'
        })
    
    def start(self):
        """Start the webhook delivery worker"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            current_app.logger.info("Webhook delivery worker started")
    
    def stop(self):
        """Stop the webhook delivery worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        current_app.logger.info("Webhook delivery worker stopped")
    
    def _worker_loop(self):
        """Main worker loop for processing webhook deliveries"""
        while self.running:
            try:
                # Get pending deliveries
                pending_deliveries = WebhookDelivery.get_pending_deliveries(limit=10)
                
                if not pending_deliveries:
                    time.sleep(5)  # Wait 5 seconds if no deliveries
                    continue
                
                # Process each delivery
                for delivery in pending_deliveries:
                    if not self.running:
                        break
                    
                    try:
                        self._process_delivery(delivery)
                        db.session.commit()
                    except Exception as e:
                        current_app.logger.error(f"Failed to process delivery {delivery.id}: {e}")
                        db.session.rollback()
                        
                        # Mark delivery as failed if too many errors
                        if delivery.attempt_count >= delivery.max_attempts:
                            delivery.status = DeliveryStatus.FAILED
                            db.session.commit()
                
            except Exception as e:
                current_app.logger.error(f"Webhook worker error: {e}")
                time.sleep(10)  # Wait longer on errors
    
    def _process_delivery(self, delivery: WebhookDelivery):
        """Process individual webhook delivery"""
        subscription = delivery.subscription
        
        if not subscription or subscription.status != WebhookStatus.ACTIVE:
            delivery.status = DeliveryStatus.CANCELLED
            return
        
        # Prepare headers
        headers = {
            'X-Webhook-Event': delivery.event_type.value,
            'X-Webhook-Signature': f'sha256={delivery.signature}',
            'X-Webhook-Delivery': delivery.id,
            'X-Webhook-Timestamp': delivery.scheduled_at.isoformat()
        }
        
        # Add custom headers from subscription
        if subscription.headers:
            headers.update(subscription.headers)
        
        try:
            # Make HTTP request
            response = self.delivery_session.post(
                subscription.url,
                data=delivery.payload,
                headers=headers,
                timeout=subscription.timeout_seconds
            )
            
            # Process response
            delivery.mark_attempt(
                status_code=response.status_code,
                response_body=response.text[:1000],  # Limit response body size
                response_headers=dict(response.headers)
            )
            
            # Update subscription stats
            subscription.update_delivery_stats(response.status_code < 400)
            
            current_app.logger.info(
                f"Webhook delivered to {subscription.url}: {response.status_code}"
            )
            
        except requests.exceptions.Timeout:
            delivery.mark_attempt(error_message="Request timeout")
            subscription.update_delivery_stats(False)
            current_app.logger.warning(f"Webhook timeout for {subscription.url}")
            
        except requests.exceptions.ConnectionError as e:
            delivery.mark_attempt(error_message=f"Connection error: {str(e)}")
            subscription.update_delivery_stats(False)
            current_app.logger.warning(f"Webhook connection error for {subscription.url}: {e}")
            
        except Exception as e:
            delivery.mark_attempt(error_message=f"Delivery error: {str(e)}")
            subscription.update_delivery_stats(False)
            current_app.logger.error(f"Webhook delivery error for {subscription.url}: {e}")


class WebhookEventDispatcher:
    """Dispatches events to webhook subscriptions"""
    
    def __init__(self):
        self.worker = WebhookDeliveryWorker()
    
    def start(self):
        """Start the webhook system"""
        self.worker.start()
    
    def stop(self):
        """Stop the webhook system"""
        self.worker.stop()
    
    def dispatch_event(self, event_type: WebhookEvent, event_id: str, 
                      event_data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Dispatch event to all relevant webhook subscriptions"""
        try:
            # Get subscriptions for this event type
            subscriptions = WebhookSubscription.get_subscriptions_for_event(event_type)
            
            if not subscriptions:
                return
            
            # Create webhook payload
            payload = WebhookPayload(
                event_type=event_type.value,
                event_id=event_id,
                timestamp=datetime.utcnow().isoformat(),
                data=event_data,
                metadata=metadata or {}
            )
            
            payload_dict = {
                'event_type': payload.event_type,
                'event_id': payload.event_id,
                'timestamp': payload.timestamp,
                'data': payload.data,
                'metadata': payload.metadata
            }
            
            # Create deliveries for matching subscriptions
            deliveries_created = 0
            for subscription in subscriptions:
                if subscription.should_deliver_event(event_type, payload_dict):
                    delivery = WebhookDelivery.create_delivery(
                        subscription=subscription,
                        event_type=event_type,
                        event_id=event_id,
                        payload_data=payload_dict
                    )
                    
                    db.session.add(delivery)
                    deliveries_created += 1
            
            if deliveries_created > 0:
                db.session.commit()
                current_app.logger.info(
                    f"Created {deliveries_created} webhook deliveries for event {event_type.value}"
                )
            
        except Exception as e:
            current_app.logger.error(f"Failed to dispatch webhook event: {e}")
            db.session.rollback()


class WebhookService:
    """Main webhook service coordinating all webhook functionality"""
    
    def __init__(self):
        self.dispatcher = WebhookEventDispatcher()
        self._initialized = False
    
    def initialize(self):
        """Initialize the webhook service"""
        if not self._initialized:
            self.dispatcher.start()
            self._initialized = True
            current_app.logger.info("Webhook service initialized")
    
    def shutdown(self):
        """Shutdown the webhook service"""
        if self._initialized:
            self.dispatcher.stop()
            self._initialized = False
            current_app.logger.info("Webhook service shutdown")
    
    def create_subscription(self, name: str, url: str, events: List[str], 
                          description: str = None, filters: Dict = None,
                          headers: Dict = None, retry_count: int = 3,
                          timeout_seconds: int = 30) -> WebhookSubscription:
        """Create new webhook subscription"""
        try:
            # Validate events
            valid_events = [e.value for e in WebhookEvent]
            invalid_events = [e for e in events if e not in valid_events]
            if invalid_events:
                raise ValueError(f"Invalid webhook events: {', '.join(invalid_events)}")
            
            # Create subscription
            subscription = WebhookSubscription(
                name=name,
                url=url,
                description=description,
                events=events,
                filters=filters or {},
                headers=headers or {},
                retry_count=retry_count,
                timeout_seconds=timeout_seconds
            )
            
            db.session.add(subscription)
            db.session.commit()
            
            current_app.logger.info(f"Created webhook subscription: {name}")
            return subscription
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create webhook subscription: {e}")
            raise
    
    def update_subscription(self, subscription_id: str, **updates) -> WebhookSubscription:
        """Update webhook subscription"""
        try:
            subscription = WebhookSubscription.query.get(subscription_id)
            if not subscription:
                raise ValueError("Webhook subscription not found")
            
            # Update allowed fields
            updatable_fields = [
                'name', 'url', 'description', 'events', 'filters', 
                'headers', 'status', 'retry_count', 'timeout_seconds'
            ]
            
            for field, value in updates.items():
                if field in updatable_fields and hasattr(subscription, field):
                    setattr(subscription, field, value)
            
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Updated webhook subscription: {subscription.name}")
            return subscription
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to update webhook subscription: {e}")
            raise
    
    def delete_subscription(self, subscription_id: str):
        """Delete webhook subscription"""
        try:
            subscription = WebhookSubscription.query.get(subscription_id)
            if not subscription:
                raise ValueError("Webhook subscription not found")
            
            db.session.delete(subscription)
            db.session.commit()
            
            current_app.logger.info(f"Deleted webhook subscription: {subscription.name}")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to delete webhook subscription: {e}")
            raise
    
    def trigger_event(self, event_type: WebhookEvent, entity_id: str, 
                     entity_data: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Trigger webhook event for entity change"""
        if not self._initialized:
            current_app.logger.warning("Webhook service not initialized, skipping event")
            return
        
        self.dispatcher.dispatch_event(event_type, entity_id, entity_data, metadata)
    
    def get_subscription_analytics(self, subscription_id: str) -> Dict[str, Any]:
        """Get analytics for webhook subscription"""
        subscription = WebhookSubscription.query.get(subscription_id)
        if not subscription:
            raise ValueError("Webhook subscription not found")
        
        # Get recent deliveries for analytics
        recent_deliveries = WebhookDelivery.get_deliveries_for_subscription(
            subscription_id, limit=100
        )
        
        # Calculate metrics
        total_deliveries = len(recent_deliveries)
        successful_deliveries = sum(1 for d in recent_deliveries if d.status == DeliveryStatus.DELIVERED)
        failed_deliveries = sum(1 for d in recent_deliveries if d.status == DeliveryStatus.FAILED)
        avg_response_time = 0
        
        if recent_deliveries:
            response_times = []
            for delivery in recent_deliveries:
                if delivery.first_attempted_at and delivery.delivered_at:
                    response_time = (delivery.delivered_at - delivery.first_attempted_at).total_seconds()
                    response_times.append(response_time)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'subscription_id': subscription_id,
            'name': subscription.name,
            'status': subscription.status.value,
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'failed_deliveries': failed_deliveries,
            'success_rate': subscription.get_success_rate(),
            'avg_response_time_seconds': round(avg_response_time, 2),
            'last_delivery_at': subscription.last_delivery_at.isoformat() if subscription.last_delivery_at else None,
            'last_success_at': subscription.last_success_at.isoformat() if subscription.last_success_at else None,
            'last_failure_at': subscription.last_failure_at.isoformat() if subscription.last_failure_at else None
        }
    
    def test_webhook(self, subscription_id: str) -> Dict[str, Any]:
        """Send test webhook to verify connectivity"""
        subscription = WebhookSubscription.query.get(subscription_id)
        if not subscription:
            raise ValueError("Webhook subscription not found")
        
        # Create test payload
        test_payload = {
            'event_type': 'webhook.test',
            'event_id': f'test_{datetime.utcnow().isoformat()}',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'test': True,
                'subscription_id': subscription_id,
                'message': 'This is a test webhook from TaskMaster'
            },
            'metadata': {
                'test_webhook': True
            }
        }
        
        # Create temporary delivery for testing
        test_delivery = WebhookDelivery(
            subscription_id=subscription_id,
            event_type=WebhookEvent.TASK_CREATED,  # Use any event type for test
            event_id='test',
            payload=json.dumps(test_payload),
            signature=subscription.generate_signature(json.dumps(test_payload)),
            max_attempts=1
        )
        
        # Process delivery immediately
        worker = WebhookDeliveryWorker()
        worker._process_delivery(test_delivery)
        
        return {
            'success': test_delivery.status == DeliveryStatus.DELIVERED,
            'status_code': test_delivery.response_status_code,
            'response_body': test_delivery.response_body,
            'error_message': test_delivery.error_message,
            'attempt_count': test_delivery.attempt_count
        }
    
    def cleanup_old_deliveries(self, max_age_days: int = 30):
        """Clean up old webhook deliveries"""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        old_deliveries = WebhookDelivery.query.filter(
            WebhookDelivery.created_at < cutoff_date
        ).all()
        
        count = len(old_deliveries)
        for delivery in old_deliveries:
            db.session.delete(delivery)
        
        db.session.commit()
        current_app.logger.info(f"Cleaned up {count} old webhook deliveries")
        
        return count


# Global webhook service instance
webhook_service = WebhookService()