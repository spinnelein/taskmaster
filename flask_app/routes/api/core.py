"""
Core API Routes

Handles miscellaneous core endpoints including health checks,
enhanced task queue, event-aware assignments, and smart scheduling.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from models import db, TaskAssignment, Task, TimePool
from task_queue_service import get_task_queue_service
from services.event_aware_assignment_service import get_event_aware_assignment_service
import logging

logger = logging.getLogger(__name__)
core_bp = Blueprint('core', __name__)


@core_bp.route('/health')
def health_check():
    """API health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 500


@core_bp.route('/task-queue/enhanced')
def get_enhanced_task_queue():
    """Get enhanced task queue with additional metadata"""
    limit = int(request.args.get('limit', 50))
    
    try:
        queue_service = get_task_queue_service()
        enhanced_queue = queue_service.get_enhanced_task_queue(limit)
        
        return jsonify({
            'enhanced_queue': enhanced_queue,
            'count': len(enhanced_queue),
            'queue_type': 'enhanced'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'enhanced_queue': [],
            'count': 0
        }), 500


@core_bp.route('/task-queue/enhanced/available')
def get_enhanced_available_queue():
    """Get enhanced available task queue"""
    limit = int(request.args.get('limit', 50))
    
    try:
        queue_service = get_task_queue_service()
        available_enhanced = queue_service.get_enhanced_available_queue(limit)
        
        return jsonify({
            'available_enhanced': available_enhanced,
            'count': len(available_enhanced),
            'queue_type': 'enhanced_available'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'available_enhanced': [],
            'count': 0
        }), 500


@core_bp.route('/task-queue/enhanced/context/<task_id>')
def get_enhanced_task_context(task_id):
    """Get enhanced context for a specific task"""
    try:
        queue_service = get_task_queue_service()
        context = queue_service.get_task_context(task_id)
        
        return jsonify({
            'task_id': task_id,
            'context': context
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'task_id': task_id,
            'context': None
        }), 500


@core_bp.route('/task-queue/enhanced/compare', methods=['POST'])
def compare_enhanced_task_priorities():
    """Compare priority scores between multiple tasks"""
    try:
        data = request.json or {}
        task_ids = data.get('task_ids', [])
        
        if not task_ids or len(task_ids) < 2:
            return jsonify({'error': 'At least 2 task_ids required for comparison'}), 400
        
        queue_service = get_task_queue_service()
        comparison = queue_service.compare_task_priorities(task_ids)
        
        return jsonify({
            'comparison': comparison,
            'task_count': len(task_ids)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'comparison': None
        }), 500


@core_bp.route('/assignments/event-aware/pools', methods=['GET'])
def get_available_pools_with_events():
    """Get available time pools with event awareness"""
    try:
        event_aware_service = get_event_aware_assignment_service()
        pools = event_aware_service.get_available_pools_with_events()
        
        return jsonify({
            'pools': pools,
            'count': len(pools)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'pools': [],
            'count': 0
        }), 500


@core_bp.route('/assignments/event-aware/project/<project_id>', methods=['POST'])
def assign_project_tasks_smart(project_id):
    """Smart assignment of project tasks with event awareness"""
    try:
        event_aware_service = get_event_aware_assignment_service()
        result = event_aware_service.assign_project_tasks(project_id)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@core_bp.route('/assignments/event-aware/recurring', methods=['POST'])
def handle_recurring_tasks():
    """Handle recurring task assignments with event awareness"""
    try:
        event_aware_service = get_event_aware_assignment_service()
        result = event_aware_service.handle_recurring_tasks()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@core_bp.route('/assignments/event-aware/meal-tasks', methods=['POST'])
def prepare_meal_tasks():
    """Prepare meal-related tasks with event awareness"""
    try:
        event_aware_service = get_event_aware_assignment_service()
        result = event_aware_service.prepare_meal_tasks()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@core_bp.route('/assignments/event-aware/bulk', methods=['POST'])
def bulk_assign_with_events():
    """Bulk assignment with event awareness"""
    try:
        data = request.json or {}
        max_days_ahead = data.get('max_days_ahead', 7)
        
        event_aware_service = get_event_aware_assignment_service()
        result = event_aware_service.bulk_assign_with_events(max_days_ahead)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@core_bp.route('/time_pools_api', methods=['GET'])
def get_time_pools_api():
    """Legacy API endpoint for time pools (backward compatibility)"""
    try:
        # Delegate to the main time pools endpoint
        from .schedule import get_time_pools
        return get_time_pools()
    except Exception as e:
        return jsonify({
            'error': str(e),
            'pools': [],
            'total_minutes': 0
        }), 500


@core_bp.route('/assignments_api', methods=['GET'])
def get_assignments_api():
    """Legacy API endpoint for assignments (backward compatibility)"""
    try:
        # Get task assignments, optionally filtered by date range or task
        task_id = request.args.get('task_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = TaskAssignment.query
        
        # Apply filters
        if task_id:
            query = query.filter_by(task_id=task_id)
        
        # Handle date filtering with a single join
        need_time_pool_join = start_date or end_date
        if need_time_pool_join:
            query = query.join(TimePool)
            
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(TimePool.pool_date >= start_date_obj)
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
            
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(TimePool.pool_date <= end_date_obj)
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        assignments = query.order_by(TaskAssignment.assigned_at.desc()).all()
        
        # Build response with task and pool details
        assignments_data = []
        for assignment in assignments:
            assignment_dict = assignment.to_dict()
            
            # Add task details using the get_task() method
            task = assignment.get_task()
            if task:
                assignment_dict['task_title'] = task.title
                assignment_dict['task_priority'] = task.priority
            
            # Add time pool details using the get_time_pool() method
            time_pool = assignment.get_time_pool()
            if time_pool:
                assignment_dict['pool_date'] = time_pool.pool_date.isoformat()
                assignment_dict['pool_start_time'] = time_pool.start_time.strftime('%H:%M')
                assignment_dict['pool_end_time'] = time_pool.end_time.strftime('%H:%M')
            
            assignments_data.append(assignment_dict)
        
        return jsonify({
            'assignments': assignments_data,
            'count': len(assignments_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting assignments: {e}")
        return jsonify({'error': f"Failed to get assignments: {str(e)}"}), 500


@core_bp.route('/assignments/bulk_api', methods=['POST'])
def bulk_assign_tasks_api():
    """Legacy bulk assignment API endpoint"""
    try:
        # Delegate to the main bulk assignment endpoint
        from .assignments import bulk_assign_tasks
        return bulk_assign_tasks()
    except Exception as e:
        return jsonify({
            'error': str(e),
            'assignments_made': [],
            'assignment_count': 0
        }), 500


@core_bp.route('/admin/regenerate-pools', methods=['POST'])
def regenerate_time_pools():
    """Manual time pool regeneration endpoint for testing/admin"""
    try:
        from .utils import trigger_pool_regeneration
        
        # Log the manual trigger
        logger.info("Manual time pool regeneration requested via API")
        
        # Trigger regeneration using the same method as event changes
        trigger_pool_regeneration()
        
        return jsonify({
            'status': 'success',
            'message': 'Time pool regeneration triggered',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error triggering manual pool regeneration: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to trigger regeneration: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500