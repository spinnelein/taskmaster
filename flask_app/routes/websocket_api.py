"""
WebSocket API Integration Routes for TaskMaster YOLO Phase 2.2

Provides REST API endpoints that integrate with WebSocket broadcasting
to demonstrate real-time task and event synchronization capabilities.
"""

from flask import Blueprint, request, jsonify
from services.websocket_integration import get_websocket_integrator
import uuid
from datetime import datetime, timedelta

websocket_api_bp = Blueprint('websocket_api', __name__, url_prefix='/api/websocket')

@websocket_api_bp.route('/broadcast/task-created', methods=['POST'])
def broadcast_task_created():
    """Simulate task creation with WebSocket broadcasting"""
    try:
        data = request.get_json()
        
        # Create a sample task
        task_data = {
            'id': str(uuid.uuid4()),
            'title': data.get('title', 'Sample Task'),
            'description': data.get('description', 'This is a demo task for WebSocket testing'),
            'priority': data.get('priority', 3),
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'project_id': data.get('project_id'),
            'initiative_id': data.get('initiative_id'),
            'assigned_user_id': data.get('assigned_user_id')
        }
        
        # Broadcast the task creation
        integrator = get_websocket_integrator()
        integrator.on_task_created(task_data, data.get('user_id'))
        
        return jsonify({
            'success': True,
            'message': 'Task created and broadcasted',
            'task': task_data
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating task: {str(e)}'
        }), 500

@websocket_api_bp.route('/broadcast/task-completed', methods=['POST'])
def broadcast_task_completed():
    """Simulate task completion with WebSocket broadcasting"""
    try:
        data = request.get_json()
        
        # Simulate task completion
        task_data = {
            'id': data.get('task_id', str(uuid.uuid4())),
            'title': data.get('title', 'Completed Task'),
            'status': 'completed',
            'completed_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'completion_note': data.get('completion_note', 'Task completed via WebSocket demo')
        }
        
        # Broadcast the task completion
        integrator = get_websocket_integrator()
        integrator.on_task_completed(task_data, data.get('user_id'))
        
        return jsonify({
            'success': True,
            'message': 'Task completion broadcasted',
            'task': task_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error completing task: {str(e)}'
        }), 500

@websocket_api_bp.route('/broadcast/event-created', methods=['POST'])
def broadcast_event_created():
    """Simulate event creation with WebSocket broadcasting"""
    try:
        data = request.get_json()
        
        # Create a sample event
        start_time = datetime.utcnow() + timedelta(hours=1)
        event_data = {
            'id': str(uuid.uuid4()),
            'title': data.get('title', 'Sample Event'),
            'description': data.get('description', 'This is a demo event for WebSocket testing'),
            'start_time': start_time.isoformat(),
            'duration': data.get('duration', 60),
            'event_type': data.get('event_type', 'meeting'),
            'created_at': datetime.utcnow().isoformat(),
            'created_by': data.get('user_id'),
            'attendees': data.get('attendees', [])
        }
        
        # Broadcast the event creation
        integrator = get_websocket_integrator()
        integrator.on_event_created(event_data, data.get('user_id'))
        
        return jsonify({
            'success': True,
            'message': 'Event created and broadcasted',
            'event': event_data
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating event: {str(e)}'
        }), 500

@websocket_api_bp.route('/broadcast/schedule-updated', methods=['POST'])
def broadcast_schedule_updated():
    """Simulate schedule update with WebSocket broadcasting"""
    try:
        data = request.get_json()
        
        # Create schedule update data
        schedule_data = {
            'type': 'regeneration',
            'timestamp': datetime.utcnow().isoformat(),
            'affected_tasks': data.get('affected_tasks', []),
            'affected_time_pools': data.get('affected_time_pools', []),
            'user_id': data.get('user_id'),
            'reason': data.get('reason', 'Manual schedule regeneration via WebSocket demo')
        }
        
        # Broadcast the schedule update
        integrator = get_websocket_integrator()
        integrator.on_schedule_regenerated(schedule_data, data.get('user_id'))
        
        return jsonify({
            'success': True,
            'message': 'Schedule update broadcasted',
            'schedule': schedule_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating schedule: {str(e)}'
        }), 500

@websocket_api_bp.route('/broadcast/notification', methods=['POST'])
def broadcast_notification():
    """Send real-time notification via WebSocket"""
    try:
        data = request.get_json()
        
        message = data.get('message', 'Test notification')
        notification_type = data.get('type', 'info')
        target_user_id = data.get('target_user_id')
        
        # Send notification
        integrator = get_websocket_integrator()
        integrator.send_notification(message, notification_type, target_user_id)
        
        return jsonify({
            'success': True,
            'message': 'Notification sent',
            'notification': {
                'message': message,
                'type': notification_type,
                'target_user_id': target_user_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error sending notification: {str(e)}'
        }), 500

@websocket_api_bp.route('/broadcast/ai-insight', methods=['POST'])
def broadcast_ai_insight():
    """Simulate AI analysis completion with WebSocket broadcasting"""
    try:
        data = request.get_json()
        
        # Create AI insight data
        insight_data = {
            'analysis_id': str(uuid.uuid4()),
            'type': data.get('analysis_type', 'task_prioritization'),
            'results': {
                'priority_recommendations': data.get('recommendations', [
                    'Focus on overdue tasks first',
                    'Batch similar tasks together',
                    'Consider task dependencies'
                ]),
                'efficiency_score': data.get('efficiency_score', 85),
                'suggested_optimizations': data.get('optimizations', [
                    'Reduce context switching',
                    'Optimize time pool allocation'
                ])
            },
            'confidence': data.get('confidence', 0.92),
            'generated_at': datetime.utcnow().isoformat(),
            'target_user_id': data.get('target_user_id')
        }
        
        # Broadcast the AI insight
        integrator = get_websocket_integrator()
        integrator.on_ai_analysis_complete(insight_data, data.get('target_user_id'))
        
        return jsonify({
            'success': True,
            'message': 'AI insight broadcasted',
            'insight': insight_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error broadcasting AI insight: {str(e)}'
        }), 500

@websocket_api_bp.route('/stats', methods=['GET'])
def get_websocket_stats():
    """Get comprehensive WebSocket statistics"""
    try:
        integrator = get_websocket_integrator()
        stats = integrator.get_connection_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting WebSocket stats: {str(e)}'
        }), 500

@websocket_api_bp.route('/test-events', methods=['POST'])
def test_all_events():
    """Test all WebSocket event types in sequence"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'demo_user')
        
        integrator = get_websocket_integrator()
        events_sent = []
        
        # Test task events
        task_data = {
            'id': str(uuid.uuid4()),
            'title': 'WebSocket Test Task',
            'description': 'Comprehensive WebSocket event testing',
            'priority': 5,
            'status': 'active',
            'created_at': datetime.utcnow().isoformat()
        }
        
        integrator.on_task_created(task_data, user_id)
        events_sent.append('task_created')
        
        # Update task priority
        task_data['priority'] = 8
        integrator.on_task_priority_changed(task_data, 5, 8, user_id)
        events_sent.append('task_priority_changed')
        
        # Complete task
        task_data['status'] = 'completed'
        task_data['completed_at'] = datetime.utcnow().isoformat()
        integrator.on_task_completed(task_data, user_id)
        events_sent.append('task_completed')
        
        # Test event creation
        event_data = {
            'id': str(uuid.uuid4()),
            'title': 'WebSocket Test Event',
            'start_time': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            'duration': 30,
            'created_by': user_id
        }
        
        integrator.on_event_created(event_data, user_id)
        events_sent.append('event_created')
        
        # Test notification
        integrator.send_notification(
            'WebSocket test notification - all systems working!',
            'success',
            user_id
        )
        events_sent.append('notification_sent')
        
        # Test AI insight
        insight_data = {
            'analysis_id': str(uuid.uuid4()),
            'type': 'comprehensive_test',
            'results': {
                'message': 'WebSocket system is functioning correctly',
                'test_passed': True
            },
            'confidence': 1.0,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        integrator.on_ai_analysis_complete(insight_data, user_id)
        events_sent.append('ai_insight_sent')
        
        return jsonify({
            'success': True,
            'message': 'All WebSocket events tested successfully',
            'events_sent': events_sent,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing WebSocket events: {str(e)}'
        }), 500