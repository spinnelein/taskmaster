"""
Webhook API Routes for Advanced API Features

Provides webhook subscription management, delivery tracking, and
analytics for event-driven integrations.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json
from typing import Dict, List, Any

from services.webhook_service import webhook_service
from models import WebhookSubscription, WebhookDelivery, WebhookEvent, WebhookStatus, DeliveryStatus, db
from routes.api.response_utils import APIResponse


# Create webhook blueprint
webhook_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')


@webhook_bp.route('/subscriptions', methods=['GET'])
def get_webhook_subscriptions():
    """
    Get webhook subscriptions
    
    Query Parameters:
    - status: Filter by status (active|paused|disabled|failed)
    - event_type: Filter by event type
    - limit: Maximum results (default: 20)
    - offset: Pagination offset (default: 0)
    
    Returns:
    {
        "success": true,
        "data": {
            "subscriptions": [...],
            "total_count": 5
        }
    }
    """
    try:
        # Parse query parameters
        status_filter = request.args.get('status')
        event_type_filter = request.args.get('event_type')
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = max(int(request.args.get('offset', 0)), 0)
        
        # Build query
        query = WebhookSubscription.query
        
        if status_filter:
            try:
                status_enum = WebhookStatus(status_filter.lower())
                query = query.filter(WebhookSubscription.status == status_enum)
            except ValueError:
                return create_error_response(
                    f"Invalid status filter: {status_filter}",
                    400,
                    {'code': 'INVALID_STATUS', 'valid_statuses': [s.value for s in WebhookStatus]}
                )
        
        if event_type_filter:
            # Check if it's a valid event type
            valid_events = [e.value for e in WebhookEvent]
            if event_type_filter not in valid_events:
                return create_error_response(
                    f"Invalid event type: {event_type_filter}",
                    400,
                    {'code': 'INVALID_EVENT_TYPE', 'valid_events': valid_events}
                )
            
            query = query.filter(WebhookSubscription.events.contains([event_type_filter]))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and fetch
        subscriptions = query.order_by(WebhookSubscription.created_at.desc()).offset(offset).limit(limit).all()
        
        response_data = {
            'subscriptions': [sub.to_dict() for sub in subscriptions],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get webhook subscriptions failed: {e}")
        return create_error_response(
            "Failed to get webhook subscriptions",
            500,
            {'code': 'GET_SUBSCRIPTIONS_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/subscriptions', methods=['POST'])
def create_webhook_subscription():
    """
    Create new webhook subscription
    
    Request Body:
    {
        "name": "My Webhook",
        "url": "https://example.com/webhook",
        "description": "Webhook description",
        "events": ["task.created", "task.updated"],
        "filters": {
            "data.status": "active"
        },
        "headers": {
            "Authorization": "Bearer token"
        },
        "retry_count": 3,
        "timeout_seconds": 30
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
        required_fields = ['name', 'url', 'events']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(
                    f"Field '{field}' is required",
                    400,
                    {'code': 'MISSING_FIELD', 'field': field}
                )
        
        # Validate URL format
        url = data['url']
        if not (url.startswith('http://') or url.startswith('https://')):
            return create_error_response(
                "URL must start with http:// or https://",
                400,
                {'code': 'INVALID_URL'}
            )
        
        # Validate events
        events = data['events']
        if not isinstance(events, list) or not events:
            return create_error_response(
                "Events must be a non-empty list",
                400,
                {'code': 'INVALID_EVENTS'}
            )
        
        valid_events = [e.value for e in WebhookEvent]
        invalid_events = [e for e in events if e not in valid_events]
        if invalid_events:
            return create_error_response(
                f"Invalid webhook events: {', '.join(invalid_events)}",
                400,
                {'code': 'INVALID_EVENT_TYPES', 'valid_events': valid_events}
            )
        
        # Create subscription
        subscription = webhook_service.create_subscription(
            name=data['name'],
            url=data['url'],
            events=data['events'],
            description=data.get('description'),
            filters=data.get('filters'),
            headers=data.get('headers'),
            retry_count=data.get('retry_count', 3),
            timeout_seconds=data.get('timeout_seconds', 30)
        )
        
        return create_response(
            subscription.to_dict(),
            message="Webhook subscription created successfully"
        )
        
    except ValueError as e:
        return create_error_response(
            str(e),
            400,
            {'code': 'VALIDATION_ERROR'}
        )
    except Exception as e:
        current_app.logger.error(f"Create webhook subscription failed: {e}")
        return create_error_response(
            "Failed to create webhook subscription",
            500,
            {'code': 'CREATE_SUBSCRIPTION_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/subscriptions/<subscription_id>', methods=['GET'])
def get_webhook_subscription(subscription_id):
    """Get specific webhook subscription by ID"""
    try:
        subscription = WebhookSubscription.query.get(subscription_id)
        if not subscription:
            return create_error_response(
                "Webhook subscription not found",
                404,
                {'code': 'SUBSCRIPTION_NOT_FOUND'}
            )
        
        return create_response(subscription.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"Get webhook subscription failed: {e}")
        return create_error_response(
            "Failed to get webhook subscription",
            500,
            {'code': 'GET_SUBSCRIPTION_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/subscriptions/<subscription_id>', methods=['PUT'])
def update_webhook_subscription(subscription_id):
    """Update webhook subscription"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response(
                "Request body is required",
                400,
                {'code': 'MISSING_REQUEST_BODY'}
            )
        
        # Validate events if provided
        if 'events' in data:
            events = data['events']
            if not isinstance(events, list):
                return create_error_response(
                    "Events must be a list",
                    400,
                    {'code': 'INVALID_EVENTS'}
                )
            
            valid_events = [e.value for e in WebhookEvent]
            invalid_events = [e for e in events if e not in valid_events]
            if invalid_events:
                return create_error_response(
                    f"Invalid webhook events: {', '.join(invalid_events)}",
                    400,
                    {'code': 'INVALID_EVENT_TYPES', 'valid_events': valid_events}
                )
        
        # Validate status if provided
        if 'status' in data:
            try:
                WebhookStatus(data['status'].lower())
            except ValueError:
                return create_error_response(
                    f"Invalid status: {data['status']}",
                    400,
                    {'code': 'INVALID_STATUS', 'valid_statuses': [s.value for s in WebhookStatus]}
                )
        
        # Update subscription
        subscription = webhook_service.update_subscription(subscription_id, **data)
        
        return create_response(
            subscription.to_dict(),
            message="Webhook subscription updated successfully"
        )
        
    except ValueError as e:
        return create_error_response(
            str(e),
            400,
            {'code': 'VALIDATION_ERROR'}
        )
    except Exception as e:
        current_app.logger.error(f"Update webhook subscription failed: {e}")
        return create_error_response(
            "Failed to update webhook subscription",
            500,
            {'code': 'UPDATE_SUBSCRIPTION_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/subscriptions/<subscription_id>', methods=['DELETE'])
def delete_webhook_subscription(subscription_id):
    """Delete webhook subscription"""
    try:
        webhook_service.delete_subscription(subscription_id)
        
        return create_response(
            {},
            message="Webhook subscription deleted successfully"
        )
        
    except ValueError as e:
        return create_error_response(
            str(e),
            404,
            {'code': 'SUBSCRIPTION_NOT_FOUND'}
        )
    except Exception as e:
        current_app.logger.error(f"Delete webhook subscription failed: {e}")
        return create_error_response(
            "Failed to delete webhook subscription",
            500,
            {'code': 'DELETE_SUBSCRIPTION_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/subscriptions/<subscription_id>/test', methods=['POST'])
def test_webhook_subscription(subscription_id):
    """
    Test webhook subscription by sending a test payload
    
    Returns:
    {
        "success": true,
        "data": {
            "test_successful": true,
            "status_code": 200,
            "response_body": "OK",
            "error_message": null
        }
    }
    """
    try:
        result = webhook_service.test_webhook(subscription_id)
        
        response_data = {
            'test_successful': result['success'],
            'status_code': result['status_code'],
            'response_body': result['response_body'],
            'error_message': result['error_message'],
            'attempt_count': result['attempt_count']
        }
        
        return create_response(response_data)
        
    except ValueError as e:
        return create_error_response(
            str(e),
            404,
            {'code': 'SUBSCRIPTION_NOT_FOUND'}
        )
    except Exception as e:
        current_app.logger.error(f"Test webhook subscription failed: {e}")
        return create_error_response(
            "Failed to test webhook subscription",
            500,
            {'code': 'TEST_WEBHOOK_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/subscriptions/<subscription_id>/analytics', methods=['GET'])
def get_webhook_analytics(subscription_id):
    """
    Get analytics for webhook subscription
    
    Returns:
    {
        "success": true,
        "data": {
            "subscription_id": "uuid",
            "name": "My Webhook",
            "total_deliveries": 100,
            "successful_deliveries": 95,
            "failed_deliveries": 5,
            "success_rate": 95.0,
            "avg_response_time_seconds": 0.45
        }
    }
    """
    try:
        analytics = webhook_service.get_subscription_analytics(subscription_id)
        return create_response(analytics)
        
    except ValueError as e:
        return create_error_response(
            str(e),
            404,
            {'code': 'SUBSCRIPTION_NOT_FOUND'}
        )
    except Exception as e:
        current_app.logger.error(f"Get webhook analytics failed: {e}")
        return create_error_response(
            "Failed to get webhook analytics",
            500,
            {'code': 'GET_ANALYTICS_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/deliveries', methods=['GET'])
def get_webhook_deliveries():
    """
    Get webhook deliveries
    
    Query Parameters:
    - subscription_id: Filter by subscription
    - status: Filter by delivery status
    - event_type: Filter by event type
    - limit: Maximum results (default: 20)
    - offset: Pagination offset (default: 0)
    """
    try:
        # Parse query parameters
        subscription_id = request.args.get('subscription_id')
        status_filter = request.args.get('status')
        event_type_filter = request.args.get('event_type')
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = max(int(request.args.get('offset', 0)), 0)
        
        # Build query
        query = WebhookDelivery.query
        
        if subscription_id:
            query = query.filter(WebhookDelivery.subscription_id == subscription_id)
        
        if status_filter:
            try:
                status_enum = DeliveryStatus(status_filter.lower())
                query = query.filter(WebhookDelivery.status == status_enum)
            except ValueError:
                return create_error_response(
                    f"Invalid status filter: {status_filter}",
                    400,
                    {'code': 'INVALID_STATUS', 'valid_statuses': [s.value for s in DeliveryStatus]}
                )
        
        if event_type_filter:
            try:
                event_enum = WebhookEvent(event_type_filter)
                query = query.filter(WebhookDelivery.event_type == event_enum)
            except ValueError:
                return create_error_response(
                    f"Invalid event type: {event_type_filter}",
                    400,
                    {'code': 'INVALID_EVENT_TYPE', 'valid_events': [e.value for e in WebhookEvent]}
                )
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and fetch
        deliveries = query.order_by(WebhookDelivery.created_at.desc()).offset(offset).limit(limit).all()
        
        response_data = {
            'deliveries': [delivery.to_dict() for delivery in deliveries],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get webhook deliveries failed: {e}")
        return create_error_response(
            "Failed to get webhook deliveries",
            500,
            {'code': 'GET_DELIVERIES_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/deliveries/<delivery_id>', methods=['GET'])
def get_webhook_delivery(delivery_id):
    """Get specific webhook delivery by ID"""
    try:
        delivery = WebhookDelivery.query.get(delivery_id)
        if not delivery:
            return create_error_response(
                "Webhook delivery not found",
                404,
                {'code': 'DELIVERY_NOT_FOUND'}
            )
        
        return create_response(delivery.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"Get webhook delivery failed: {e}")
        return create_error_response(
            "Failed to get webhook delivery",
            500,
            {'code': 'GET_DELIVERY_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/events', methods=['GET'])
def get_webhook_events():
    """
    Get list of available webhook events
    
    Returns:
    {
        "success": true,
        "data": {
            "events": [
                {
                    "event_type": "task.created",
                    "description": "Triggered when a new task is created"
                }
            ]
        }
    }
    """
    try:
        event_descriptions = {
            WebhookEvent.TASK_CREATED: "Triggered when a new task is created",
            WebhookEvent.TASK_UPDATED: "Triggered when a task is updated",
            WebhookEvent.TASK_COMPLETED: "Triggered when a task is completed",
            WebhookEvent.TASK_DELETED: "Triggered when a task is deleted",
            WebhookEvent.EVENT_CREATED: "Triggered when a new event is created",
            WebhookEvent.EVENT_UPDATED: "Triggered when an event is updated",
            WebhookEvent.EVENT_DELETED: "Triggered when an event is deleted",
            WebhookEvent.INITIATIVE_CREATED: "Triggered when a new initiative is created",
            WebhookEvent.INITIATIVE_UPDATED: "Triggered when an initiative is updated",
            WebhookEvent.INITIATIVE_DELETED: "Triggered when an initiative is deleted",
            WebhookEvent.PROJECT_CREATED: "Triggered when a new project is created",
            WebhookEvent.PROJECT_UPDATED: "Triggered when a project is updated",
            WebhookEvent.PROJECT_DELETED: "Triggered when a project is deleted",
            WebhookEvent.EXPORT_COMPLETED: "Triggered when an export operation completes",
            WebhookEvent.EXPORT_FAILED: "Triggered when an export operation fails"
        }
        
        events_data = []
        for event, description in event_descriptions.items():
            events_data.append({
                'event_type': event.value,
                'description': description,
                'category': event.value.split('.')[0]  # Extract category (task, event, etc.)
            })
        
        response_data = {'events': events_data}
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get webhook events failed: {e}")
        return create_error_response(
            "Failed to get webhook events",
            500,
            {'code': 'GET_EVENTS_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/cleanup', methods=['POST'])
def cleanup_webhook_deliveries():
    """
    Clean up old webhook deliveries (admin operation)
    
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
        
        count = webhook_service.cleanup_old_deliveries(max_age_days)
        
        response_data = {
            'message': 'Cleanup completed successfully',
            'deliveries_cleaned': count,
            'max_age_days': max_age_days
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Cleanup webhook deliveries failed: {e}")
        return create_error_response(
            "Failed to cleanup webhook deliveries",
            500,
            {'code': 'CLEANUP_ERROR', 'details': str(e)}
        )


@webhook_bp.route('/health', methods=['GET'])
def webhook_health():
    """
    Check webhook service health and status
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "active_subscriptions": 5,
            "pending_deliveries": 2,
            "worker_running": true
        }
    }
    """
    try:
        # Get counts
        active_subscriptions = WebhookSubscription.query.filter(
            WebhookSubscription.status == WebhookStatus.ACTIVE
        ).count()
        
        pending_deliveries = WebhookDelivery.query.filter(
            WebhookDelivery.status.in_([DeliveryStatus.PENDING, DeliveryStatus.RETRYING])
        ).count()
        
        response_data = {
            'status': 'healthy',
            'active_subscriptions': active_subscriptions,
            'pending_deliveries': pending_deliveries,
            'worker_running': webhook_service._initialized,
            'capabilities': [
                'subscription_management',
                'event_filtering',
                'retry_logic',
                'hmac_verification',
                'delivery_analytics',
                'webhook_testing'
            ]
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Webhook health check failed: {e}")
        return create_error_response(
            "Webhook health check failed",
            500,
            {'code': 'HEALTH_CHECK_ERROR', 'details': str(e)}
        )


# Register error handlers
@webhook_bp.errorhandler(404)
def not_found(error):
    return create_error_response(
        "Webhook endpoint not found",
        404,
        {'code': 'ENDPOINT_NOT_FOUND'}
    )


@webhook_bp.errorhandler(405)
def method_not_allowed(error):
    return create_error_response(
        "Method not allowed for this webhook endpoint",
        405,
        {'code': 'METHOD_NOT_ALLOWED'}
    )