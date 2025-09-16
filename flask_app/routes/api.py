from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from models import db, Event, Task, Initiative
from recurring_service import recurring_service
import uuid

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
    
    event = Event(
        id=str(uuid.uuid4()),  # Generate UUID for ID
        title=data['title'],
        start_time=start_time,
        end_time=end_time,
        is_blocking=data.get('is_blocking', True),
        description=data.get('description', ''),
        location=data.get('location', ''),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify(event.to_dict())

@api_bp.route('/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an event from FullCalendar drag/resize"""
    event = Event.query.get_or_404(event_id)
    data = request.json
    
    if 'start' in data:
        start_time = datetime.fromisoformat(data['start'].replace('Z', '+00:00'))
        event.start_time = start_time.replace(tzinfo=None)
    
    if 'end' in data:
        end_time = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
        event.end_time = end_time.replace(tzinfo=None)
    
    if 'title' in data:
        event.title = data['title']
    
    db.session.commit()
    return jsonify(event.to_dict())

@api_bp.route('/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event"""
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'status': 'success'})

@api_bp.route('/tasks')
def get_tasks():
    """Get all tasks"""
    tasks = Task.query.filter_by(is_completed=False).all()
    return jsonify([t.to_dict() for t in tasks])

@api_bp.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.json
    
    # Parse due_date if provided
    due_date = None
    if data.get('due_date'):
        due_date = datetime.fromisoformat(data['due_date']).date()
    
    task = Task(
        id=str(uuid.uuid4()),  # Generate UUID for ID
        title=data['title'],
        description=data.get('description', ''),
        duration=data.get('duration', 30),
        urgency=data.get('urgency', 5),
        priority=data.get('priority', 'medium'),
        status='active',
        is_completed=False,
        due_date=due_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(task)
    db.session.commit()
    
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
    if 'due_date' in data:
        if data['due_date']:
            task.due_date = datetime.fromisoformat(data['due_date']).date()
        else:
            task.due_date = None
    
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
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
    return jsonify({'status': 'success'})

@api_bp.route('/tasks/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed and create next recurring instance if applicable"""
    task = Task.query.get_or_404(task_id)
    
    # Mark current task as completed
    task.is_completed = True
    task.last_completed_at = datetime.utcnow()
    task.status = 'completed'
    
    # Check if this is a recurring task that should generate a new instance
    if task.initiative_id and task.recurrence_days and task.recurrence_days > 0:
        from datetime import date, timedelta
        
        # Calculate next due date
        next_due_date = date.today() + timedelta(days=task.recurrence_days)
        
        # Create new task instance
        new_task = Task(
            id=str(uuid.uuid4()),
            title=task.title,
            description=task.description,
            duration=task.duration,
            urgency=task.urgency,
            priority=task.priority,
            status='active',
            is_completed=False,
            initiative_id=task.initiative_id,
            recurrence_days=task.recurrence_days,
            parent_task_id=task.id,  # Link to completed task
            due_date=next_due_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_task)
    
    db.session.commit()
    
    # Return both completed task and new task (if created)
    result = {'completed_task': task.to_dict()}
    if task.initiative_id and task.recurrence_days and task.recurrence_days > 0:
        result['next_task'] = new_task.to_dict()
    
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
    """Get all initiatives with task counts"""
    initiatives = Initiative.query.all()
    return jsonify([i.to_dict() for i in initiatives])

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
    
    return jsonify(task.to_dict())