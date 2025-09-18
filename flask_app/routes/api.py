from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from models import db, Event, Task, Initiative, TimePool, WeatherForecast, TaskAssignment, Dish, Recipe, Meal, MealDish
from recurring_service import recurring_service
from weather_service import get_flask_weather_service
from task_queue_service import get_task_queue_service
from assignment_service import get_assignment_service
import uuid
import json
import asyncio
import logging
import time

logger = logging.getLogger(__name__)

def _trigger_pool_regeneration():
    """Trigger time pool regeneration when events change"""
    try:
        from background_service import background_service
        if background_service and background_service.is_running:
            background_service.regenerate_time_pools()
    except Exception as e:
        print(f"Could not trigger pool regeneration: {e}")

def _trigger_assignment_regeneration():
    """Trigger task assignment regeneration when tasks change"""
    try:
        from background_service import background_service
        if background_service and background_service.is_running:
            # Use a fixed job ID so we don't create multiple pending jobs
            job_id = 'task_change_assignment_regen'
            
            # Check if there's already a pending job
            existing_job = background_service.scheduler.get_job(job_id)
            if existing_job:
                # Remove existing job and create a new one with updated time
                background_service.scheduler.remove_job(job_id)
            
            # Schedule assignment regeneration with a small delay
            background_service.scheduler.add_job(
                func=background_service._regenerate_task_assignments,
                args=['task_change'],
                trigger='date',
                run_date=datetime.now() + timedelta(seconds=5),  # Reduced delay
                id=job_id,
                name='Task Change Assignment Regeneration',
                max_instances=1
            )
        else:
            # If background service isn't running, try direct assignment
            assignment_service = get_assignment_service()
            assignment_service.bulk_assign_tasks_to_pools(
                clear_existing=True,
                max_days_ahead=7,
                assigned_by='task_change_direct'
            )
    except Exception as e:
        print(f"Could not trigger assignment regeneration: {e}")

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/events')
def get_events():
    """Get events - supports two modes via query parameter"""
    mode = request.args.get('mode', 'list')  # 'list' or 'calendar'
    
    if mode == 'calendar':
        # Calendar mode: expand recurring events for display
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        
        if start_str and end_str:
            start_date = datetime.fromisoformat(start_str.replace('Z', '')).date()
            end_date = datetime.fromisoformat(end_str.replace('Z', '')).date()
        else:
            # Default to current month
            today = date.today()
            start_date = today.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Get all events and expand recurring ones
        all_events = Event.query.all()
        expanded_events = recurring_service.expand_events_for_period(all_events, start_date, end_date)
        return jsonify(expanded_events)
    
    else:
        # List mode: only master events (for events list page)
        all_events = Event.query.all()
        master_events = recurring_service.get_master_events_only(all_events)
        return jsonify([e.to_dict() for e in master_events])

@api_bp.route('/events', methods=['POST'])
def create_event():
    """Create a new event from FullCalendar"""
    data = request.json
    
    # Parse datetime strings
    start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    
    # Remove timezone info to store as local time
    start_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)
    
    # Handle all-day events - ensure proper timestamps
    event_type = data.get('event_type', 'timed')
    if event_type == 'all_day':
        # For all-day events, set start time to 00:00:00 and end time to 23:59:59
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Validate meal_id if provided
    meal_id = data.get('meal_id')
    if meal_id:
        meal = Meal.query.get(meal_id)
        if not meal:
            return jsonify({'error': 'Invalid meal_id - meal does not exist'}), 400

    event = Event(
        id=str(uuid.uuid4()),  # Generate UUID for ID
        title=data['title'],
        start_time=start_time,
        end_time=end_time,
        is_blocking=data.get('is_blocking', True),
        description=data.get('description', ''),
        location=data.get('location', ''),
        event_type=event_type,
        meal_id=meal_id,
        notifications_enabled=data.get('notifications_enabled', True),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Handle recurring event fields
    if data.get('is_recurring', False):
        event.is_recurring = True
        event.is_recurrence_master = True  # Mark as master event
        event.recurrence_pattern = data.get('recurrence_pattern', '')
        event.recurrence_rrule = data.get('recurrence_rrule', '')
        
        # Set dtstart/dtend for RRULE processing
        event.dtstart = start_time
        event.dtend = end_time
        
        # Handle recurrence end date if provided
        if data.get('recurrence_end'):
            event.recurrence_end = datetime.fromisoformat(data['recurrence_end'].replace('Z', '+00:00')).replace(tzinfo=None)
    
    db.session.add(event)
    db.session.commit()
    
    # Trigger time pool regeneration
    _trigger_pool_regeneration()
    
    # Return event with meal data if it's a dinner event
    if event.meal_id:
        return jsonify(event.to_dict_with_meal())
    else:
        return jsonify(event.to_dict())

@api_bp.route('/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an event from form or FullCalendar drag/resize"""
    event = Event.query.get_or_404(event_id)
    data = request.json
    
    # Handle datetime fields
    if 'start' in data:
        start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
        event.start_time = start_time.replace(tzinfo=None)
        # Update dtstart for recurring events
        if event.is_recurring:
            event.dtstart = event.start_time
    
    if 'end' in data:
        end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
        event.end_time = end_time.replace(tzinfo=None)
        # Update dtend for recurring events
        if event.is_recurring:
            event.dtend = event.end_time
    
    # Handle basic fields
    if 'title' in data:
        event.title = data['title']
    
    if 'description' in data:
        event.description = data['description']
    
    if 'location' in data:
        event.location = data['location']
    
    if 'event_type' in data:
        event.event_type = data['event_type']
    
    # Handle boolean fields
    if 'is_blocking' in data:
        event.is_blocking = data['is_blocking']
    
    if 'notifications_enabled' in data:
        event.notifications_enabled = data['notifications_enabled']
    
    # Handle meal_id for dinner events
    if 'meal_id' in data:
        meal_id = data['meal_id']
        if meal_id:
            # Validate that the meal exists
            meal = Meal.query.get(meal_id)
            if not meal:
                return jsonify({'error': 'Invalid meal_id - meal does not exist'}), 400
        event.meal_id = meal_id
    
    # Handle recurring event fields
    if 'is_recurring' in data:
        event.is_recurring = data['is_recurring']
        if data['is_recurring']:
            event.is_recurrence_master = True
            
            # Handle recurrence pattern
            if 'recurrence_pattern' in data:
                event.recurrence_pattern = data['recurrence_pattern']
            
            if 'recurrence_rrule' in data:
                event.recurrence_rrule = data['recurrence_rrule']
            
            # Handle recurrence end date
            if 'recurrence_end' in data and data['recurrence_end']:
                event.recurrence_end = datetime.fromisoformat(data['recurrence_end']).replace(tzinfo=None)
            elif 'recurrence_end' in data and not data['recurrence_end']:
                event.recurrence_end = None
        else:
            # If no longer recurring, clear recurring fields
            event.is_recurrence_master = False
            event.recurrence_pattern = None
            event.recurrence_rrule = None
            event.recurrence_end = None
    
    event.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Trigger time pool regeneration
    _trigger_pool_regeneration()
    
    # Return event with meal data if it's a dinner event
    if event.meal_id:
        return jsonify(event.to_dict_with_meal())
    else:
        return jsonify(event.to_dict())

@api_bp.route('/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event"""
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    # Trigger time pool regeneration
    _trigger_pool_regeneration()
    
    return jsonify({'status': 'success'})

@api_bp.route('/tasks')
def get_tasks():
    """Get all root tasks including snoozed ones (accounting for dependencies)"""
    # Get all incomplete tasks (including snoozed ones)
    current_time = datetime.utcnow()
    available_tasks = Task.query.filter(Task.is_completed == False).all()
    
    # Auto-unsnooze tasks whose snooze period has ended
    for task in available_tasks:
        if task.is_snoozed and task.snoozed_until and task.snoozed_until <= current_time:
            task.is_snoozed = False
            task.snoozed_until = None
            task.status = 'active'
    
    db.session.commit()
    
    # Build task lookup for dependency checking (include completed tasks for dependency resolution)
    all_tasks_by_id = {task.id: task for task in Task.query.all()}
    
    # Filter to only include root tasks (no dependencies OR all dependencies completed)
    root_tasks = []
    for task in available_tasks:
        is_root_task = True
        
        if task.depends_on_task_ids:
            try:
                # Handle JSON string or null values
                if task.depends_on_task_ids and task.depends_on_task_ids != 'null':
                    dep_ids = json.loads(task.depends_on_task_ids)
                    if isinstance(dep_ids, list) and dep_ids:
                        # Check if all dependencies are completed
                        for dep_id in dep_ids:
                            if dep_id in all_tasks_by_id:
                                dep_task = all_tasks_by_id[dep_id]
                                # Task is blocked if dependency is not completed AND not snoozed
                                if not dep_task.is_completed and not dep_task.is_snoozed:
                                    is_root_task = False
                                    break
            except (json.JSONDecodeError, TypeError):
                # If dependency parsing fails, treat as root task
                pass
        
        if is_root_task:
            root_tasks.append(task)
    
    return jsonify([t.to_dict() for t in root_tasks])

@api_bp.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.json
    
    # Parse due_date if provided
    due_date = None
    if data.get('due_date'):
        due_date = datetime.fromisoformat(data['due_date']).date()
    
    # Parse start_date (snoozed_until) if provided
    start_datetime = None
    is_snoozed = False
    if data.get('start_date') or data.get('snoozed_until'):
        start_date_str = data.get('start_date') or data.get('snoozed_until')
        start_datetime = datetime.fromisoformat(start_date_str)
        is_snoozed = True  # If user sets a start date, treat as snoozed until then
    
    # Validate start_date <= due_date if both provided
    if start_datetime and due_date:
        if start_datetime.date() > due_date:
            return jsonify({'error': 'Start date cannot be after due date'}), 400
    
    task = Task(
        id=str(uuid.uuid4()),  # Generate UUID for ID
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
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(task)
    db.session.commit()
    
    # Trigger assignment regeneration
    _trigger_assignment_regeneration()
    
    return jsonify(task.to_dict())

@api_bp.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update an existing task"""
    task = Task.query.get_or_404(task_id)
    data = request.json
    
    # Update fields if provided
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'duration' in data:
        task.duration = data['duration']
    if 'urgency' in data:
        task.urgency = data['urgency']
    if 'priority' in data:
        task.priority = data['priority']
    if 'recurrence_days' in data:
        task.recurrence_days = data['recurrence_days']
    if 'required_weather' in data:
        task.required_weather = data['required_weather']
    if 'due_date' in data:
        if data['due_date']:
            task.due_date = datetime.fromisoformat(data['due_date']).date()
        else:
            task.due_date = None
    
    # Handle start_date (snoozed_until) updates
    if 'start_date' in data:
        if data['start_date']:
            start_datetime = datetime.fromisoformat(data['start_date'])
            task.snoozed_until = start_datetime
            task.is_snoozed = True
            task.status = 'snoozed'
            
            # Validate start_date <= due_date if both exist
            if task.due_date and start_datetime.date() > task.due_date:
                return jsonify({'error': 'Start date cannot be after due date'}), 400
        else:
            # Clear start date
            task.snoozed_until = None
            task.is_snoozed = False
            task.status = 'active'
    
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Trigger assignment regeneration
    _trigger_assignment_regeneration()
    
    return jsonify(task.to_dict())

@api_bp.route('/tasks/<task_id>')
def get_task(task_id):
    """Get a specific task"""
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@api_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    
    # Trigger assignment regeneration
    _trigger_assignment_regeneration()
    
    return jsonify({'status': 'success'})

@api_bp.route('/tasks/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed or snooze if recurring"""
    task = Task.query.get_or_404(task_id)
    
    # Record completion time
    task.last_completed_at = datetime.now()
    task.updated_at = datetime.now()
    
    # Handle recurring vs non-recurring tasks differently
    if task.recurrence_days and task.recurrence_days > 0:
        # Recurring task: snooze until next occurrence (don't mark completed)
        from datetime import timedelta
        task.is_snoozed = True
        task.snoozed_until = datetime.now() + timedelta(days=task.recurrence_days)
        task.status = 'snoozed'
        # Keep is_completed = False so task can reappear
        
        result = {
            'task_snoozed': True,
            'snoozed_until': task.snoozed_until.isoformat(),
            'task': task.to_dict()
        }
    else:
        # Non-recurring task: mark as completed normally
        task.is_completed = True
        task.status = 'completed'
        
        result = {
            'task_completed': True,
            'task': task.to_dict()
        }
    
    db.session.commit()
    
    # Trigger assignment regeneration
    _trigger_assignment_regeneration()
    
    return jsonify(result)

@api_bp.route('/events/<event_id>/recurring-info')
def get_recurring_info(event_id):
    """Get recurring event information"""
    event = Event.query.get_or_404(event_id)
    
    if not event.is_recurring:
        return jsonify({'is_recurring': False})
    
    return jsonify({
        'is_recurring': True,
        'is_recurrence_master': bool(event.is_recurrence_master),
        'recurrence_rrule': event.recurrence_rrule,
        'recurrence_pattern': event.recurrence_pattern,
        'recurrence_end': event.recurrence_end.isoformat() if event.recurrence_end else None,
        'master_event_id': event.recurrence_master_id if event.recurrence_master_id else event.id
    })

# Initiative endpoints
@api_bp.route('/initiatives')
def get_initiatives():
    """Get all initiatives with active tasks details"""
    initiatives = Initiative.query.all()
    
    # Get active tasks for each initiative
    current_time = datetime.utcnow()
    initiatives_data = []
    
    for initiative in initiatives:
        initiative_data = initiative.to_dict()
        
        # Get all non-completed tasks (including snoozed)
        active_tasks = Task.query.filter(
            (Task.initiative_id == initiative.id) &
            (Task.is_completed == False)
        ).all()
        
        # Auto-unsnooze expired tasks
        for task in active_tasks:
            if task.is_snoozed and task.snoozed_until and task.snoozed_until <= current_time:
                task.is_snoozed = False
                task.snoozed_until = None
                task.status = 'active'
        
        db.session.commit()
        
        # Add task details to initiative data
        task_details = []
        for task in active_tasks:
            task_dict = task.to_dict()
            # Add frequency info for display
            if task.recurrence_days and task.recurrence_days > 0:
                task_dict['frequency_display'] = f"Every {task.recurrence_days} day{'s' if task.recurrence_days > 1 else ''}"
            else:
                task_dict['frequency_display'] = "One-time"
            
            # Add last completed info
            if task.last_completed_at:
                task_dict['last_completed_display'] = task.last_completed_at.strftime('%Y-%m-%d')
            else:
                task_dict['last_completed_display'] = "Never"
            
            # Add snooze status for display
            if task.is_snoozed and task.snoozed_until:
                if task.snoozed_until > current_time:
                    task_dict['is_sleeping'] = True
                    task_dict['wake_up_time'] = task.snoozed_until.strftime('%Y-%m-%d %H:%M')
                    task_dict['status_display'] = f"Sleeping until {task.snoozed_until.strftime('%m/%d %H:%M')}"
                else:
                    task_dict['is_sleeping'] = False
                    task_dict['status_display'] = "Active"
            else:
                task_dict['is_sleeping'] = False
                task_dict['status_display'] = "Active"
            
            task_details.append(task_dict)
        
        initiative_data['active_tasks'] = task_details
        initiatives_data.append(initiative_data)
    
    return jsonify(initiatives_data)

@api_bp.route('/initiatives', methods=['POST'])
def create_initiative():
    """Create a new initiative"""
    data = request.json
    
    initiative = Initiative(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', 'ACTIVE'),
        is_template=data.get('is_template', False),
        target_completion_count=data.get('target_completion_count', 0),
        current_completion_count=data.get('current_completion_count', 0),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(initiative)
    db.session.commit()
    
    return jsonify(initiative.to_dict())

@api_bp.route('/initiatives/<initiative_id>')
def get_initiative(initiative_id):
    """Get a specific initiative with its tasks"""
    initiative = Initiative.query.get_or_404(initiative_id)
    tasks = Task.query.filter_by(initiative_id=initiative_id, is_completed=False).all()
    
    initiative_data = initiative.to_dict()
    initiative_data['tasks'] = [task.to_dict() for task in tasks]
    
    return jsonify(initiative_data)

@api_bp.route('/initiatives/<initiative_id>', methods=['PUT'])
def update_initiative(initiative_id):
    """Update an initiative"""
    initiative = Initiative.query.get_or_404(initiative_id)
    data = request.json
    
    if 'title' in data:
        initiative.title = data['title']
    if 'description' in data:
        initiative.description = data['description']
    if 'status' in data:
        initiative.status = data['status']
    if 'target_completion_count' in data:
        initiative.target_completion_count = data['target_completion_count']
    if 'current_completion_count' in data:
        initiative.current_completion_count = data['current_completion_count']
    
    initiative.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(initiative.to_dict())

@api_bp.route('/initiatives/<initiative_id>', methods=['DELETE'])
def delete_initiative(initiative_id):
    """Delete an initiative"""
    initiative = Initiative.query.get_or_404(initiative_id)
    db.session.delete(initiative)
    db.session.commit()
    return jsonify({'status': 'success'})

@api_bp.route('/initiatives/<initiative_id>/increment', methods=['POST'])
def increment_initiative(initiative_id):
    """Increment the completion count of an initiative"""
    initiative = Initiative.query.get_or_404(initiative_id)
    initiative.current_completion_count = (initiative.current_completion_count or 0) + 1
    initiative.updated_at = datetime.utcnow()
    
    # Auto-complete if target reached
    if (initiative.target_completion_count and 
        initiative.current_completion_count >= initiative.target_completion_count):
        initiative.status = 'COMPLETED'
    
    db.session.commit()
    return jsonify(initiative.to_dict())

@api_bp.route('/initiatives/<initiative_id>/create-task', methods=['POST'])
def create_task_from_initiative(initiative_id):
    """Create a recurring task for an initiative"""
    initiative = Initiative.query.get_or_404(initiative_id)
    data = request.json
    
    # Calculate due date
    due_date = None
    if data.get('due_date'):
        # Use provided due date
        due_date = datetime.fromisoformat(data['due_date']).date()
    elif data.get('recurrence_days'):
        # If no due date provided, calculate based on recurrence_days
        from datetime import date, timedelta
        due_date = date.today() + timedelta(days=int(data['recurrence_days']))
    
    task = Task(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        duration=data.get('duration', 30),
        urgency=data.get('urgency', 5),
        priority=data.get('priority', 'medium'),
        status='active',
        is_completed=False,
        initiative_id=initiative_id,
        recurrence_days=data.get('recurrence_days'),
        due_date=due_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(task)
    db.session.commit()
    
    # Trigger assignment regeneration
    _trigger_assignment_regeneration()
    
    return jsonify(task.to_dict())

# Task Queue endpoints
@api_bp.route('/task-queue/all')
def get_all_tasks_queue():
    """Get all tasks ordered by priority score"""
    limit = int(request.args.get('limit', 100))
    
    try:
        queue_service = get_task_queue_service()
        task_queue = queue_service.get_all_tasks_queue(limit)
        
        return jsonify({
            'task_queue': task_queue,
            'task_queue_detailed': task_queue,  # For backward compatibility
            'count': len(task_queue)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'task_queue': [],
            'count': 0
        }), 500

@api_bp.route('/task-queue/available')
def get_available_tasks_queue():
    """Get available (unassigned/partially assigned) tasks ordered by priority"""
    limit = int(request.args.get('limit', 100))
    
    try:
        queue_service = get_task_queue_service()
        available_queue = queue_service.get_available_tasks_queue(limit)
        
        return jsonify({
            'available_tasks': available_queue,
            'available_tasks_detailed': available_queue,  # For backward compatibility
            'count': len(available_queue)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'available_tasks': [],
            'count': 0
        }), 500

@api_bp.route('/task-queue/statistics')
def get_queue_statistics():
    """Get task queue statistics"""
    try:
        queue_service = get_task_queue_service()
        stats = queue_service.get_queue_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

# Task Assignment endpoints
@api_bp.route('/task-assignments', methods=['POST'])
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

@api_bp.route('/task-assignments')
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

@api_bp.route('/task-assignments/<assignment_id>', methods=['DELETE'])
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

# Assignment Suggestions endpoints
@api_bp.route('/task-assignments/suggest-pools/<task_id>')
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

@api_bp.route('/task-assignments/suggest-tasks/<time_pool_id>')
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

@api_bp.route('/task-assignments/auto-assign/<task_id>', methods=['POST'])
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
                'status': 'error',
                'message': message,
                'assignments': [],
                'assignment_count': 0
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f"Auto-assignment failed: {str(e)}",
            'assignments': [],
            'assignment_count': 0
        }), 500

@api_bp.route('/time-pools/regenerate', methods=['POST'])
def regenerate_time_pools():
    """Manually trigger time pool regeneration"""
    try:
        from background_service import background_service
        if background_service and background_service.is_running:
            background_service.regenerate_time_pools()
            return jsonify({'status': 'success', 'message': 'Time pool regeneration scheduled'})
        else:
            # If background service isn't running, regenerate directly
            pools_created, pools_updated = background_service.regenerate_all_time_pools(max_days_ahead=30)
            return jsonify({
                'status': 'success', 
                'message': 'Time pools regenerated directly',
                'pools_created': pools_created,
                'pools_updated': pools_updated
            })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api_bp.route('/debug/task-queue', methods=['GET'])
def debug_task_queue():
    """Debug endpoint to check task queue filtering"""
    try:
        from task_queue_service import get_task_queue_service
        queue_service = get_task_queue_service()
        
        all_tasks = queue_service.get_all_tasks_queue(limit=10)
        available_tasks = queue_service.get_available_tasks_queue(limit=10)
        
        debug_info = {
            'all_tasks_count': len(all_tasks),
            'available_tasks_count': len(available_tasks),
            'all_tasks': [
                {
                    'title': task.get('title'),
                    'status': task.get('status'),
                    'can_be_scheduled': task.get('can_be_scheduled'),
                    'blocking_reasons': task.get('blocking_reasons'),
                    'is_assigned': task.get('is_assigned'),
                    'is_fully_assigned': task.get('is_fully_assigned'),
                    'remaining_minutes': task.get('remaining_minutes'),
                    'priority_score': task.get('priority_score')
                }
                for task in all_tasks
            ],
            'available_tasks': [
                {
                    'title': task.get('title'),
                    'can_be_scheduled': task.get('can_be_scheduled'),
                    'is_fully_assigned': task.get('is_fully_assigned'),
                    'priority_score': task.get('priority_score')
                }
                for task in available_tasks
            ]
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/time-pools', methods=['GET'])
def get_time_pools():
    """Get time pools with optional date filtering and weather data"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        include_weather = request.args.get('include_weather', 'false').lower() == 'true'
        
        # Import here to avoid circular imports
        from models import TimePool, db, WeatherForecast, TaskAssignment, Task
        from weather_service import get_flask_weather_service
        
        # Base query for TimePool
        query = TimePool.query
        
        # Apply date filters
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
        
        # Order by date and start time
        pools = query.order_by(TimePool.pool_date, TimePool.start_time).all()
        
        # Convert to dictionaries
        pools_data = []
        total_minutes = 0
        outdoor_suitable_count = 0
        
        # Get weather service if needed
        weather_service = get_flask_weather_service() if include_weather else None
        
        for pool in pools:
            pool_dict = pool.to_dict()
            
            # Add assignment information
            try:
                # Query task assignments for this pool
                assignments = TaskAssignment.query.filter_by(time_pool_id=pool.id).all()
                pool_dict['assignments'] = []
                allocated_minutes = 0
                
                for assignment in assignments:
                    # Get the task details
                    task = Task.query.get(assignment.task_id)
                    if task:
                        task_info = {
                            'task_id': assignment.task_id,
                            'task_title': task.title,
                            'allocated_minutes': assignment.allocated_minutes,
                            'status': assignment.status
                        }
                        pool_dict['assignments'].append(task_info)
                        allocated_minutes += assignment.allocated_minutes or 0
                
                # Calculate utilization
                pool_dict['allocated_minutes'] = allocated_minutes
                pool_dict['available_minutes'] = max(0, (pool.total_minutes or 0) - allocated_minutes)
                
            except Exception as e:
                logger.warning(f"Error getting assignments for pool {pool.id}: {e}")
                pool_dict['assignments'] = []
                pool_dict['allocated_minutes'] = 0
                pool_dict['available_minutes'] = pool.total_minutes or 0
            
            # Add weather information if requested
            if include_weather and weather_service:
                try:
                    weather_forecast = weather_service.get_by_date(pool.pool_date)
                    if weather_forecast:
                        weather_data = {
                            'weather_condition': weather_forecast.weather_condition,
                            'temp_high': weather_forecast.temp_high,
                            'temp_low': weather_forecast.temp_low,
                            'precipitation_probability': weather_forecast.precipitation_probability,
                            'suitable_for_outdoor_work': weather_forecast.is_suitable_for_outdoor_work()
                        }
                        pool_dict['weather'] = weather_data
                        
                        if weather_forecast.is_suitable_for_outdoor_work():
                            outdoor_suitable_count += 1
                    else:
                        pool_dict['weather'] = {
                            'weather_condition': 'Unknown',
                            'suitable_for_outdoor_work': False
                        }
                except Exception as e:
                    logger.warning(f"Error getting weather for pool {pool.id}: {e}")
                    pool_dict['weather'] = {
                        'weather_condition': 'Unknown',
                        'suitable_for_outdoor_work': False
                    }
            
            pools_data.append(pool_dict)
            total_minutes += pool.total_minutes or 0
        
        return jsonify({
            'pools': pools_data,
            'total_minutes': total_minutes,
            'pool_count': len(pools_data),
            'outdoor_suitable': outdoor_suitable_count if include_weather else None
        })
        
    except Exception as e:
        logger.error(f"Error retrieving time pools: {e}")
        return jsonify({
            'error': f"Failed to retrieve time pools: {str(e)}",
            'pools': [],
            'total_minutes': 0,
            'pool_count': 0
        }), 500

# Bulk Assignment endpoints
@api_bp.route('/assignments/bulk-assign', methods=['POST'])
def bulk_assign_tasks():
    """Bulk assign available tasks to time pools"""
    try:
        from assignment_service import get_assignment_service
        
        # Get request parameters
        data = request.get_json() or {}
        clear_existing = data.get('clear_existing', True)
        max_days_ahead = data.get('max_days_ahead', 7)
        assigned_by = data.get('assigned_by', 'api_bulk')
        
        # Run bulk assignment
        assignment_service = get_assignment_service()
        result = assignment_service.bulk_assign_tasks_to_pools(
            clear_existing=clear_existing,
            max_days_ahead=max_days_ahead,
            assigned_by=assigned_by
        )
        
        # Return results
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error in bulk assignment API: {e}")
        return jsonify({
            'success': False,
            'message': f"Bulk assignment API error: {str(e)}",
            'assignments_made': [],
            'tasks_processed': 0,
            'pools_used': 0,
            'unassigned_tasks': []
        }), 500

@api_bp.route('/assignments/regenerate', methods=['POST'])
def regenerate_assignments():
    """Alias for bulk-assign with clear_existing=True (regenerates all assignments)"""
    try:
        from assignment_service import get_assignment_service
        
        data = request.get_json() or {}
        max_days_ahead = data.get('max_days_ahead', 7)
        
        assignment_service = get_assignment_service()
        result = assignment_service.bulk_assign_tasks_to_pools(
            clear_existing=True,  # Always clear for regeneration
            max_days_ahead=max_days_ahead,
            assigned_by='api_regenerate'
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error in regenerate assignments API: {e}")
        return jsonify({
            'success': False,
            'message': f"Regenerate assignments API error: {str(e)}",
            'assignments_made': [],
            'tasks_processed': 0,
            'pools_used': 0,
            'unassigned_tasks': []
        }), 500

# Time Pool API Endpoints
@api_bp.route('/time_pools_api', methods=['GET'])
def get_time_pools_api():
    """Get time pools, optionally filtered by date range"""
    from datetime import datetime, date, timedelta
    from models import TimePool
    
    try:
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Default to today and next 7 days if no dates provided
        if not start_date_str:
            start_date = date.today()
        else:
            start_date = datetime.fromisoformat(start_date_str).date()
            
        if not end_date_str:
            end_date = start_date + timedelta(days=7)
        else:
            end_date = datetime.fromisoformat(end_date_str).date()
        
        # Query time pools
        pools = TimePool.query.filter(
            TimePool.pool_date >= start_date,
            TimePool.pool_date <= end_date
        ).order_by(TimePool.pool_date, TimePool.start_time).all()
        
        return jsonify([pool.to_dict() for pool in pools])
        
    except Exception as e:
        logger.error(f"Error getting time pools: {e}")
        return jsonify({'error': f"Failed to get time pools: {str(e)}"}), 500

@api_bp.route('/assignments_api', methods=['GET'])
def get_assignments_api():
    """Get task assignments, optionally filtered by date range or task"""
    from datetime import datetime, date, timedelta
    from models import TaskAssignment, TimePool, Task
    
    try:
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        task_id = request.args.get('task_id')
        pool_id = request.args.get('pool_id')
        
        # Start with base query
        query = TaskAssignment.query
        
        # Filter by task if specified
        if task_id:
            query = query.filter(TaskAssignment.task_id == task_id)
            
        # Filter by pool if specified
        if pool_id:
            query = query.filter(TaskAssignment.time_pool_id == pool_id)
        
        # Filter by date range if specified
        if start_date_str or end_date_str:
            # Default date range
            if not start_date_str:
                start_date = date.today()
            else:
                start_date = datetime.fromisoformat(start_date_str).date()
                
            if not end_date_str:
                end_date = start_date + timedelta(days=7)
            else:
                end_date = datetime.fromisoformat(end_date_str).date()
            
            # Join with TimePool to filter by date
            query = query.join(TimePool).filter(
                TimePool.pool_date >= start_date,
                TimePool.pool_date <= end_date
            )
        
        # Execute query
        assignments = query.order_by(TaskAssignment.assigned_at.desc()).all()
        
        # Convert to dict with additional details
        result = []
        for assignment in assignments:
            assignment_dict = assignment.to_dict()
            
            # Add task details
            task = Task.query.get(assignment.task_id)
            if task:
                assignment_dict['task_title'] = task.title
                assignment_dict['task_status'] = task.status
                
            # Add pool details
            pool = TimePool.query.get(assignment.time_pool_id)
            if pool:
                assignment_dict['pool_date'] = pool.pool_date.isoformat()
                assignment_dict['pool_start_time'] = pool.start_time.isoformat() if pool.start_time else None
                
            result.append(assignment_dict)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting assignments: {e}")
        return jsonify({'error': f"Failed to get assignments: {str(e)}"}), 500

@api_bp.route('/assignments/bulk_api', methods=['POST'])
def bulk_assign_tasks_api():
    """Trigger bulk assignment of tasks to time pools"""
    from assignment_service import get_assignment_service
    
    try:
        data = request.json if request.json else {}
        
        # Get parameters
        clear_existing = data.get('clear_existing', True)
        max_days_ahead = data.get('max_days_ahead', 7)
        assigned_by = data.get('assigned_by', 'api_bulk')
        
        # Get assignment service and run bulk assignment
        assignment_service = get_assignment_service()
        result = assignment_service.bulk_assign_tasks_to_pools(
            clear_existing=clear_existing,
            max_days_ahead=max_days_ahead,
            assigned_by=assigned_by
        )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error in bulk assignment: {e}")
        return jsonify({
            'success': False,
            'message': f"Bulk assignment failed: {str(e)}",
            'assignments_made': [],
            'tasks_processed': 0,
            'pools_used': 0,
            'unassigned_tasks': []
        }), 500

# Dishes API endpoints
@api_bp.route('/dishes', methods=['GET'])
def get_dishes():
    """Get all dishes with recipe data"""
    try:
        dishes = Dish.query.order_by(Dish.title).all()
        return jsonify([dish.to_dict_with_recipe() for dish in dishes])
    except Exception as e:
        logger.error(f"Error getting dishes: {e}")
        return jsonify({'error': f"Failed to get dishes: {str(e)}"}), 500

@api_bp.route('/dishes/<dish_id>', methods=['GET'])
def get_dish(dish_id):
    """Get a specific dish with recipe data"""
    try:
        dish = Dish.query.get_or_404(dish_id)
        return jsonify(dish.to_dict_with_recipe())
    except Exception as e:
        logger.error(f"Error getting dish {dish_id}: {e}")
        return jsonify({'error': f"Failed to get dish: {str(e)}"}), 500

@api_bp.route('/dishes', methods=['POST'])
def create_dish():
    """Create a new dish"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        if not data.get('dish_type'):
            return jsonify({'error': 'Dish type is required'}), 400
        if not data.get('difficulty'):
            return jsonify({'error': 'Difficulty is required'}), 400
        if not data.get('ingredients') or len(data.get('ingredients', [])) == 0:
            return jsonify({'error': 'Ingredients are required'}), 400
        if not data.get('instructions') or len(data.get('instructions', [])) == 0:
            return jsonify({'error': 'Instructions are required'}), 400
        
        # Handle dietary tags
        dietary_tags = data.get('dietary_tags', [])
        if isinstance(dietary_tags, list):
            dietary_tags_json = json.dumps(dietary_tags)
        else:
            dietary_tags_json = None
        
        # Create recipe first
        recipe_id = str(uuid.uuid4())
        recipe = Recipe(
            id=recipe_id,
            title=data['title'] + " Recipe",
            description=data.get('description', ''),
            ingredients=json.dumps(data['ingredients']),
            instructions=json.dumps(data['instructions']),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        dish = Dish(
            id=str(uuid.uuid4()),
            title=data['title'],
            description=data.get('description'),
            dish_type=data['dish_type'],
            difficulty=data['difficulty'],
            cuisine=data.get('cuisine'),
            prep_time_minutes=data.get('prep_time_minutes'),
            cook_time_minutes=data.get('cook_time_minutes'),
            total_time_minutes=data.get('total_time_minutes'),
            advance_prep_hours=data.get('advance_prep_hours'),
            advance_prep_description=data.get('advance_prep_description'),
            default_servings=data.get('default_servings'),
            calories_per_serving=data.get('calories_per_serving'),
            estimated_cost_per_serving=data.get('estimated_cost_per_serving'),
            dietary_tags=dietary_tags_json,
            recipe_id=recipe_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(recipe)
        db.session.add(dish)
        db.session.commit()
        
        return jsonify(dish.to_dict_with_recipe()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating dish: {e}")
        return jsonify({'error': f"Failed to create dish: {str(e)}"}), 500

@api_bp.route('/dishes/<dish_id>', methods=['PUT'])
def update_dish(dish_id):
    """Update a dish"""
    try:
        dish = Dish.query.get_or_404(dish_id)
        data = request.json
        
        # Update fields if provided
        if 'title' in data:
            dish.title = data['title']
        if 'description' in data:
            dish.description = data['description']
        if 'dish_type' in data:
            dish.dish_type = data['dish_type']
        if 'difficulty' in data:
            dish.difficulty = data['difficulty']
        if 'cuisine' in data:
            dish.cuisine = data['cuisine']
        if 'prep_time_minutes' in data:
            dish.prep_time_minutes = data['prep_time_minutes']
        if 'cook_time_minutes' in data:
            dish.cook_time_minutes = data['cook_time_minutes']
        if 'total_time_minutes' in data:
            dish.total_time_minutes = data['total_time_minutes']
        if 'advance_prep_hours' in data:
            dish.advance_prep_hours = data['advance_prep_hours']
        if 'advance_prep_description' in data:
            dish.advance_prep_description = data['advance_prep_description']
        if 'default_servings' in data:
            dish.default_servings = data['default_servings']
        if 'calories_per_serving' in data:
            dish.calories_per_serving = data['calories_per_serving']
        if 'estimated_cost_per_serving' in data:
            dish.estimated_cost_per_serving = data['estimated_cost_per_serving']
        if 'dietary_tags' in data:
            dietary_tags = data['dietary_tags']
            if isinstance(dietary_tags, list):
                dish.dietary_tags = json.dumps(dietary_tags)
            else:
                dish.dietary_tags = None
        if 'recipe_id' in data:
            dish.recipe_id = data['recipe_id']
        
        # Handle recipe updates
        if 'ingredients' in data or 'instructions' in data:
            recipe = dish.get_recipe()
            if recipe:
                # Update existing recipe
                if 'ingredients' in data:
                    recipe.ingredients = json.dumps(data['ingredients'])
                if 'instructions' in data:
                    recipe.instructions = json.dumps(data['instructions'])
                recipe.updated_at = datetime.utcnow()
            else:
                # Create new recipe if none exists
                recipe_id = str(uuid.uuid4())
                recipe = Recipe(
                    id=recipe_id,
                    title=dish.title + " Recipe",
                    description=dish.description or '',
                    ingredients=json.dumps(data.get('ingredients', [])),
                    instructions=json.dumps(data.get('instructions', [])),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                dish.recipe_id = recipe_id
                db.session.add(recipe)
        
        dish.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(dish.to_dict_with_recipe())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating dish {dish_id}: {e}")
        return jsonify({'error': f"Failed to update dish: {str(e)}"}), 500

@api_bp.route('/dishes/<dish_id>', methods=['DELETE'])
def delete_dish(dish_id):
    """Delete a dish"""
    try:
        dish = Dish.query.get_or_404(dish_id)
        db.session.delete(dish)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Dish deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting dish {dish_id}: {e}")
        return jsonify({'error': f"Failed to delete dish: {str(e)}"}), 500

# Meals endpoints
@api_bp.route('/meals', methods=['GET'])
def get_meals():
    """Get all meals"""
    try:
        meals = Meal.query.all()
        return jsonify([meal.to_dict_with_dishes() for meal in meals])
    except Exception as e:
        logger.error(f"Error fetching meals: {e}")
        return jsonify({'error': f"Failed to fetch meals: {str(e)}"}), 500

@api_bp.route('/meals/<meal_id>', methods=['GET'])
def get_meal(meal_id):
    """Get a specific meal with dishes"""
    try:
        meal = Meal.query.get_or_404(meal_id)
        return jsonify(meal.to_dict_with_dishes())
    except Exception as e:
        logger.error(f"Error fetching meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to fetch meal: {str(e)}"}), 500

@api_bp.route('/meals', methods=['POST'])
def create_meal():
    """Create a new meal"""
    try:
        data = request.get_json()
        
        # Create meal
        meal_id = str(uuid.uuid4())
        meal = Meal(
            id=meal_id,
            title=data['title'],
            description=data.get('description', ''),
            meal_type=data['meal_type'],
            status=data.get('status', 'planned'),
            serves_count=data.get('serves_count'),
            planned_date=datetime.fromisoformat(data['planned_date']) if data.get('planned_date') else None,
            prep_start_time=datetime.fromisoformat(data['prep_start_time']) if data.get('prep_start_time') else None,
            cook_start_time=datetime.fromisoformat(data['cook_start_time']) if data.get('cook_start_time') else None,
            serve_time=datetime.fromisoformat(data['serve_time']) if data.get('serve_time') else None,
            estimated_calories_per_serving=data.get('estimated_calories_per_serving'),
            dietary_tags=json.dumps(data.get('dietary_tags', [])) if data.get('dietary_tags') else None,
            estimated_cost=data.get('estimated_cost'),
            actual_cost=data.get('actual_cost'),
            event_id=data.get('event_id'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(meal)
        
        # Add dishes to meal if provided
        if 'dish_ids' in data and data['dish_ids']:
            for dish_id in data['dish_ids']:
                meal_dish = MealDish(
                    id=str(uuid.uuid4()),
                    meal_id=meal_id,
                    dish_id=dish_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(meal_dish)
        
        db.session.commit()
        return jsonify(meal.to_dict_with_dishes()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating meal: {e}")
        return jsonify({'error': f"Failed to create meal: {str(e)}"}), 500

@api_bp.route('/meals/<meal_id>', methods=['PUT'])
def update_meal(meal_id):
    """Update a meal"""
    try:
        meal = Meal.query.get_or_404(meal_id)
        data = request.get_json()
        
        # Update meal fields
        if 'title' in data:
            meal.title = data['title']
        if 'description' in data:
            meal.description = data['description']
        if 'meal_type' in data:
            meal.meal_type = data['meal_type']
        if 'status' in data:
            meal.status = data['status']
        if 'serves_count' in data:
            meal.serves_count = data['serves_count']
        if 'planned_date' in data:
            meal.planned_date = datetime.fromisoformat(data['planned_date']) if data['planned_date'] else None
        if 'prep_start_time' in data:
            meal.prep_start_time = datetime.fromisoformat(data['prep_start_time']) if data['prep_start_time'] else None
        if 'cook_start_time' in data:
            meal.cook_start_time = datetime.fromisoformat(data['cook_start_time']) if data['cook_start_time'] else None
        if 'serve_time' in data:
            meal.serve_time = datetime.fromisoformat(data['serve_time']) if data['serve_time'] else None
        if 'estimated_calories_per_serving' in data:
            meal.estimated_calories_per_serving = data['estimated_calories_per_serving']
        if 'dietary_tags' in data:
            meal.dietary_tags = json.dumps(data['dietary_tags']) if data['dietary_tags'] else None
        if 'estimated_cost' in data:
            meal.estimated_cost = data['estimated_cost']
        if 'actual_cost' in data:
            meal.actual_cost = data['actual_cost']
        if 'event_id' in data:
            meal.event_id = data['event_id']
        
        meal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(meal.to_dict_with_dishes())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to update meal: {str(e)}"}), 500

@api_bp.route('/meals/<meal_id>', methods=['DELETE'])
def delete_meal(meal_id):
    """Delete a meal"""
    try:
        meal = Meal.query.get_or_404(meal_id)
        
        # Delete associated meal_dishes records
        MealDish.query.filter_by(meal_id=meal_id).delete()
        
        # Delete the meal
        db.session.delete(meal)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Meal deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to delete meal: {str(e)}"}), 500

@api_bp.route('/meals/<meal_id>/dishes', methods=['POST'])
def add_dish_to_meal(meal_id):
    """Add a dish to a meal"""
    try:
        meal = Meal.query.get_or_404(meal_id)
        data = request.get_json()
        dish_id = data['dish_id']
        
        # Check if dish exists
        dish = Dish.query.get_or_404(dish_id)
        
        # Check if dish is already in meal
        existing = MealDish.query.filter_by(meal_id=meal_id, dish_id=dish_id).first()
        if existing:
            return jsonify({'error': 'Dish is already in this meal'}), 400
        
        # Add dish to meal
        meal_dish = MealDish(
            id=str(uuid.uuid4()),
            meal_id=meal_id,
            dish_id=dish_id,
            notes=data.get('notes', ''),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(meal_dish)
        db.session.commit()
        
        return jsonify(meal.to_dict_with_dishes())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding dish to meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to add dish to meal: {str(e)}"}), 500

@api_bp.route('/meals/<meal_id>/dishes/<dish_id>', methods=['DELETE'])
def remove_dish_from_meal(meal_id, dish_id):
    """Remove a dish from a meal"""
    try:
        meal_dish = MealDish.query.filter_by(meal_id=meal_id, dish_id=dish_id).first_or_404()
        
        db.session.delete(meal_dish)
        db.session.commit()
        
        meal = Meal.query.get(meal_id)
        return jsonify(meal.to_dict_with_dishes())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing dish from meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to remove dish from meal: {str(e)}"}), 500

# Dinner Event convenience endpoints
@api_bp.route('/events/dinner', methods=['GET'])
def get_dinner_events():
    """Get all dinner events (events with meals)"""
    try:
        dinner_events = Event.query.filter(Event.meal_id.isnot(None)).all()
        return jsonify([event.to_dict_with_meal() for event in dinner_events])
    except Exception as e:
        logger.error(f"Error fetching dinner events: {e}")
        return jsonify({'error': f"Failed to fetch dinner events: {str(e)}"}), 500

@api_bp.route('/meals/<meal_id>/events', methods=['GET'])
def get_meal_events(meal_id):
    """Get all events using a specific meal"""
    try:
        meal = Meal.query.get_or_404(meal_id)
        events = meal.get_events()
        return jsonify([event.to_dict() for event in events])
    except Exception as e:
        logger.error(f"Error fetching events for meal {meal_id}: {e}")
        return jsonify({'error': f"Failed to fetch events for meal: {str(e)}"}), 500