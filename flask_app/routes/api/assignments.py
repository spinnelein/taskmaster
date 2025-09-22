"""
Task Assignments API Routes

Handles task assignment operations including assignment creation,
suggestions, auto-assignment, and assignment management.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
from models import db, Task, TimePool, TaskAssignment
from assignment_service import get_assignment_service
import uuid

assignments_bp = Blueprint('assignments', __name__)


@assignments_bp.route('/task-assignments', methods=['POST'])
def assign_task_to_pool():
    """Assign a task to a time pool"""
    data = request.json
    
    # Validate required fields
    required_fields = ['task_id', 'time_pool_id', 'allocated_minutes']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Validate task exists
        task = Task.query.get(data['task_id'])
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Validate time pool exists
        time_pool = TimePool.query.get(data['time_pool_id'])
        if not time_pool:
            return jsonify({'error': 'Time pool not found'}), 404
        
        # Check if pool has enough available time
        allocated_minutes = int(data['allocated_minutes'])
        if time_pool.available_minutes < allocated_minutes:
            return jsonify({
                'error': f'Time pool only has {time_pool.available_minutes} minutes available, requested {allocated_minutes}'
            }), 400
        
        # Create assignment
        assignment = TaskAssignment(
            id=str(uuid.uuid4()),
            task_id=data['task_id'],
            time_pool_id=data['time_pool_id'],
            allocated_minutes=allocated_minutes,
            scheduled_start=datetime.fromisoformat(data['scheduled_start']) if data.get('scheduled_start') else None,
            scheduled_end=datetime.fromisoformat(data['scheduled_end']) if data.get('scheduled_end') else None,
            assigned_at=datetime.utcnow(),
            assigned_by=data.get('assigned_by', 'user'),
            notes=data.get('notes'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Update time pool allocation
        time_pool.allocated_minutes = (time_pool.allocated_minutes or 0) + allocated_minutes
        time_pool.available_minutes = time_pool.total_minutes - time_pool.allocated_minutes
        time_pool.updated_at = datetime.utcnow()
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'assignment': assignment.to_dict(),
            'message': f'Task assigned {allocated_minutes} minutes in time pool'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@assignments_bp.route('/task-assignments')
def get_task_assignments():
    """Get task assignments with optional filtering"""
    task_id = request.args.get('task_id')
    time_pool_id = request.args.get('time_pool_id')
    status = request.args.get('status')
    
    try:
        query = TaskAssignment.query
        
        # Apply filters
        if task_id:
            query = query.filter_by(task_id=task_id)
        if time_pool_id:
            query = query.filter_by(time_pool_id=time_pool_id)
        if status:
            query = query.filter_by(status=status)
        
        assignments = query.order_by(TaskAssignment.assigned_at.desc()).all()
        
        return jsonify({
            'assignments': [a.to_dict() for a in assignments],
            'count': len(assignments)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'assignments': [],
            'count': 0
        }), 500


@assignments_bp.route('/task-assignments/<assignment_id>', methods=['DELETE'])
def cancel_task_assignment(assignment_id):
    """Cancel/remove a task assignment"""
    reason = request.args.get('reason', 'Manual cancellation')
    
    try:
        assignment = TaskAssignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Cancel the assignment (this also updates the time pool)
        assignment.cancel_assignment(reason)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Assignment cancelled'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@assignments_bp.route('/task-assignments/suggest-pools/<task_id>')
def suggest_pools_for_task(task_id):
    """Get suggested time pools for a task"""
    limit = int(request.args.get('limit', 5))
    
    try:
        assignment_service = get_assignment_service()
        suggestions = assignment_service.suggest_pools_for_task(task_id, limit)
        
        return jsonify({
            'task_id': task_id,
            'pool_suggestions': suggestions,
            'count': len(suggestions)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'pool_suggestions': [],
            'count': 0
        }), 500


@assignments_bp.route('/task-assignments/suggest-tasks/<time_pool_id>')
def suggest_tasks_for_pool(time_pool_id):
    """Get suggested tasks for a time pool"""
    limit = int(request.args.get('limit', 5))
    
    try:
        assignment_service = get_assignment_service()
        suggestions = assignment_service.suggest_tasks_for_pool(time_pool_id, limit)
        
        return jsonify({
            'time_pool_id': time_pool_id,
            'task_suggestions': suggestions,
            'count': len(suggestions)
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'task_suggestions': [],
            'count': 0
        }), 500


@assignments_bp.route('/task-assignments/auto-assign/<task_id>', methods=['POST'])
def auto_assign_task(task_id):
    """Automatically assign a task to the best available time pools"""
    max_pools = int(request.args.get('max_pools', 3))
    
    try:
        assignment_service = get_assignment_service()
        success, message, assignments = assignment_service.auto_assign_task(task_id, max_pools)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'assignments': assignments,
                'assignment_count': len(assignments)
            })
        else:
            return jsonify({
                'status': 'partial_success',
                'message': message,
                'assignments': [],
                'assignment_count': 0
            }), 206
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'assignments': [],
            'assignment_count': 0
        }), 500


@assignments_bp.route('/assignments/bulk-assign', methods=['POST'])
def bulk_assign_tasks():
    """Bulk assign multiple tasks to time pools"""
    data = request.json
    clear_existing = data.get('clear_existing', False)
    max_days_ahead = data.get('max_days_ahead', 7)
    
    try:
        assignment_service = get_assignment_service()
        
        results = assignment_service.bulk_assign_tasks_to_pools(
            clear_existing=clear_existing,
            max_days_ahead=max_days_ahead,
            assigned_by='bulk_api_assign'
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Bulk assignment completed. Made {len(results)} assignments.',
            'assignments_made': results,
            'assignment_count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Bulk assignment failed: {str(e)}',
            'assignments_made': [],
            'assignment_count': 0
        }), 500


@assignments_bp.route('/assignments/regenerate', methods=['POST'])
def regenerate_assignments():
    """Alias for bulk-assign with clear_existing=True (regenerates all assignments)"""
    try:
        assignment_service = get_assignment_service()
        
        results = assignment_service.bulk_assign_tasks_to_pools(
            clear_existing=True,
            max_days_ahead=7,
            assigned_by='api_regenerate'
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Assignments regenerated. Made {len(results)} new assignments.',
            'assignments_made': results,
            'assignment_count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Regenerate assignments API error: {str(e)}",
            'assignments_made': [],
            'assignment_count': 0
        }), 500