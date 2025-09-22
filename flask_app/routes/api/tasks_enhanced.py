"""
Enhanced Tasks API Routes

Handles all task-related endpoints with pagination, filtering, sorting,
and advanced query capabilities. Follows CODING_STANDARDS.md compliance.
"""
from flask import Blueprint, request, url_for
from datetime import datetime, timedelta
from models import db, Task
from .utils import trigger_assignment_regeneration
from .query_utils import apply_standard_enhancements, create_filter_config
from .response_utils import APIResponse, handle_api_errors, validate_request_data
import uuid
import json

tasks_enhanced_bp = Blueprint('tasks_enhanced', __name__)


# Configuration for task queries
TASK_QUERY_CONFIG = {
    'filters': create_filter_config(Task, {
        # Status filters
        'status': {'column': 'status', 'type': 'exact'},
        'priority': {'column': 'priority', 'type': 'in'},
        'is_completed': {'column': 'is_completed', 'type': 'boolean'},
        'is_snoozed': {'column': 'is_snoozed', 'type': 'boolean'},
        
        # Date range filters
        'due_date_from': {'column': 'due_date', 'type': 'date_range'},
        'due_date_to': {'column': 'due_date', 'type': 'date_range'},
        'created_from': {'column': 'created_at', 'type': 'date_range'},
        'created_to': {'column': 'created_at', 'type': 'date_range'},
        
        # Numeric range filters
        'duration_min': {'column': 'duration', 'type': 'numeric_range'},
        'duration_max': {'column': 'duration', 'type': 'numeric_range'},
        'urgency_min': {'column': 'urgency', 'type': 'numeric_range'},
        'urgency_max': {'column': 'urgency', 'type': 'numeric_range'},
        
        # Relationship filters
        'initiative_id': {'column': 'initiative_id', 'type': 'exact'},
        'project_id': {'column': 'project_id', 'type': 'exact'},
        'parent_task_id': {'column': 'parent_task_id', 'type': 'exact'},
    }),
    'search_fields': ['title', 'description'],
    'sortable_fields': [
        'title', 'created_at', 'updated_at', 'due_date', 
        'urgency', 'priority', 'duration', 'status'
    ],
    'default_sort': 'created_at:desc',
    'default_limit': 20,
    'max_limit': 100
}


@tasks_enhanced_bp.route('/v2/tasks')
@handle_api_errors
def get_tasks_enhanced():
    """Get tasks with enhanced query capabilities"""
    # Base query - include all incomplete tasks by default
    query = Task.query
    
    # Apply special root task logic if requested
    if request.args.get('root_only', '').lower() == 'true':
        query = _get_root_tasks_query()
    
    # Apply standard enhancements
    enhancer = apply_standard_enhancements(query, Task, TASK_QUERY_CONFIG)
    
    # Get and serialize results
    return enhancer.serialize_results()


@tasks_enhanced_bp.route('/v2/tasks/<task_id>')
@handle_api_errors
def get_task_enhanced(task_id):
    """Get a specific task with enhanced response"""
    task = Task.query.get(task_id)
    
    if not task:
        return APIResponse.not_found("Task not found")
    
    # Include related data if requested
    include = request.args.get('include', '').split(',')
    task_data = task.to_dict()
    
    if 'dependencies' in include:
        task_data['dependencies'] = _get_task_dependencies(task)
    
    if 'subtasks' in include:
        task_data['subtasks'] = _get_subtasks(task)
    
    return APIResponse.success(data=task_data)


@tasks_enhanced_bp.route('/v2/tasks', methods=['POST'])
@handle_api_errors
@validate_request_data(required_fields=['title'])
def create_task_enhanced(validated_data=None):
    """Create a new task with validation"""
    data = validated_data
    
    # Validate dates
    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.fromisoformat(data['due_date']).date()
        except ValueError:
            return APIResponse.validation_error({
                'due_date': 'Invalid date format. Use ISO format (YYYY-MM-DD)'
            })
    
    # Handle start date/snoozing
    start_datetime = None
    is_snoozed = False
    if data.get('start_date') or data.get('snoozed_until'):
        start_date_str = data.get('start_date') or data.get('snoozed_until')
        try:
            start_datetime = datetime.fromisoformat(start_date_str)
            is_snoozed = True
        except ValueError:
            return APIResponse.validation_error({
                'start_date': 'Invalid datetime format. Use ISO format'
            })
    
    # Validate date logic
    if start_datetime and due_date:
        if start_datetime.date() > due_date:
            return APIResponse.validation_error({
                'dates': 'Start date cannot be after due date'
            })
    
    # Create task
    task = Task(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        duration=data.get('duration', 30),
        urgency=data.get('urgency', 5),
        priority=data.get('priority', 'medium'),
        status='snoozed' if is_snoozed else 'active',
        is_completed=False,
        is_snoozed=is_snoozed,
        snoozed_until=start_datetime,
        due_date=due_date,
        required_weather=data.get('required_weather'),
        initiative_id=data.get('initiative_id'),
        project_id=data.get('project_id'),
        parent_task_id=data.get('parent_task_id'),
        recurrence_days=data.get('recurrence_days'),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(task)
    db.session.commit()
    
    # Trigger assignment regeneration
    trigger_assignment_regeneration()
    
    # Return created response with location header
    location = url_for('tasks_enhanced.get_task_enhanced', task_id=task.id, _external=True)
    return APIResponse.created(data=task.to_dict(), location=location)


@tasks_enhanced_bp.route('/v2/tasks/batch', methods=['POST'])
@handle_api_errors
def create_tasks_batch():
    """Batch create multiple tasks"""
    if not request.is_json:
        return APIResponse.error("Request must be JSON", status_code=415)
    
    data = request.get_json()
    if not isinstance(data, dict) or 'tasks' not in data:
        return APIResponse.validation_error({
            'tasks': 'Request must contain a "tasks" array'
        })
    
    tasks_data = data['tasks']
    if not isinstance(tasks_data, list):
        return APIResponse.validation_error({
            'tasks': 'Tasks must be an array'
        })
    
    created_tasks = []
    errors = []
    
    for idx, task_data in enumerate(tasks_data):
        if 'title' not in task_data:
            errors.append({
                'index': idx,
                'error': 'Title is required'
            })
            continue
        
        try:
            task = Task(
                id=str(uuid.uuid4()),
                title=task_data['title'],
                description=task_data.get('description', ''),
                duration=task_data.get('duration', 30),
                urgency=task_data.get('urgency', 5),
                priority=task_data.get('priority', 'medium'),
                status=task_data.get('status', 'active'),
                is_completed=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(task)
            created_tasks.append(task)
        except Exception as e:
            errors.append({
                'index': idx,
                'error': str(e)
            })
    
    if created_tasks:
        db.session.commit()
        trigger_assignment_regeneration()
    
    response_data = {
        'created': [task.to_dict() for task in created_tasks],
        'errors': errors
    }
    
    status_code = 201 if not errors else 207  # 207 Multi-Status
    
    return APIResponse.success(
        data=response_data,
        message=f"Created {len(created_tasks)} tasks",
        status_code=status_code
    )


@tasks_enhanced_bp.route('/v2/tasks/<task_id>', methods=['PUT'])
@handle_api_errors
def update_task_enhanced(task_id):
    """Update a task with validation"""
    task = Task.query.get(task_id)
    if not task:
        return APIResponse.not_found("Task not found")
    
    if not request.is_json:
        return APIResponse.error("Request must be JSON", status_code=415)
    
    data = request.get_json()
    
    # Track if any changes were made
    changes_made = False
    
    # Update allowed fields
    update_fields = [
        'title', 'description', 'duration', 'urgency', 'priority',
        'recurrence_days', 'required_weather'
    ]
    
    for field in update_fields:
        if field in data and getattr(task, field) != data[field]:
            setattr(task, field, data[field])
            changes_made = True
    
    # Handle date updates
    if 'due_date' in data:
        if data['due_date']:
            try:
                new_due_date = datetime.fromisoformat(data['due_date']).date()
                if task.due_date != new_due_date:
                    task.due_date = new_due_date
                    changes_made = True
            except ValueError:
                return APIResponse.validation_error({
                    'due_date': 'Invalid date format'
                })
        else:
            task.due_date = None
            changes_made = True
    
    # Handle start date/snoozing
    if 'start_date' in data:
        if data['start_date']:
            try:
                start_datetime = datetime.fromisoformat(data['start_date'])
                task.snoozed_until = start_datetime
                task.is_snoozed = True
                task.status = 'snoozed'
                changes_made = True
            except ValueError:
                return APIResponse.validation_error({
                    'start_date': 'Invalid datetime format'
                })
        else:
            task.snoozed_until = None
            task.is_snoozed = False
            task.status = 'active'
            changes_made = True
    
    if changes_made:
        task.updated_at = datetime.utcnow()
        db.session.commit()
        trigger_assignment_regeneration()
    
    return APIResponse.success(data=task.to_dict())


@tasks_enhanced_bp.route('/v2/tasks/<task_id>', methods=['DELETE'])
@handle_api_errors
def delete_task_enhanced(task_id):
    """Delete a task"""
    task = Task.query.get(task_id)
    if not task:
        return APIResponse.not_found("Task not found")
    
    db.session.delete(task)
    db.session.commit()
    
    trigger_assignment_regeneration()
    
    return APIResponse.no_content()


# Helper functions
def _get_root_tasks_query():
    """Get query for root tasks only"""
    current_time = datetime.utcnow()
    
    # Start with incomplete tasks
    query = Task.query.filter(Task.is_completed == False)
    
    # Auto-unsnooze tasks (this would be better in a background job)
    tasks_to_unsnooze = query.filter(
        Task.is_snoozed == True,
        Task.snoozed_until <= current_time
    ).all()
    
    for task in tasks_to_unsnooze:
        task.is_snoozed = False
        task.snoozed_until = None
        task.status = 'active'
    
    if tasks_to_unsnooze:
        db.session.commit()
    
    # Filter to root tasks (no dependencies or all deps completed)
    # This is complex to do in SQL, so we'll handle in post-processing
    return query


def _get_task_dependencies(task):
    """Get task dependency information"""
    dependencies = []
    
    if task.depends_on_task_ids:
        try:
            dep_ids = json.loads(task.depends_on_task_ids)
            if isinstance(dep_ids, list):
                dep_tasks = Task.query.filter(Task.id.in_(dep_ids)).all()
                dependencies = [
                    {
                        'id': dep.id,
                        'title': dep.title,
                        'completed': dep.is_completed,
                        'status': dep.status
                    }
                    for dep in dep_tasks
                ]
        except (json.JSONDecodeError, TypeError):
            pass
    
    return dependencies


def _get_subtasks(task):
    """Get subtasks of a task"""
    subtasks = Task.query.filter_by(parent_task_id=task.id).all()
    return [
        {
            'id': st.id,
            'title': st.title,
            'completed': st.is_completed,
            'status': st.status
        }
        for st in subtasks
    ]