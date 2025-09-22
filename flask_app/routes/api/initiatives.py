"""
Initiatives API Routes

Handles all initiative-related endpoints including CRUD operations,
task creation, and completion tracking.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from models import db, Initiative, Task
from .utils import trigger_assignment_regeneration
import uuid

initiatives_bp = Blueprint('initiatives', __name__)


@initiatives_bp.route('/initiatives')
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


@initiatives_bp.route('/initiatives', methods=['POST'])
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


@initiatives_bp.route('/initiatives/<initiative_id>')
def get_initiative(initiative_id):
    """Get a specific initiative with its tasks"""
    initiative = Initiative.query.get_or_404(initiative_id)
    tasks = Task.query.filter_by(initiative_id=initiative_id, is_completed=False).all()
    
    initiative_data = initiative.to_dict()
    initiative_data['tasks'] = [task.to_dict() for task in tasks]
    
    return jsonify(initiative_data)


@initiatives_bp.route('/initiatives/<initiative_id>', methods=['PUT'])
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


@initiatives_bp.route('/initiatives/<initiative_id>', methods=['DELETE'])
def delete_initiative(initiative_id):
    """Delete an initiative"""
    initiative = Initiative.query.get_or_404(initiative_id)
    db.session.delete(initiative)
    db.session.commit()
    return jsonify({'status': 'success'})


@initiatives_bp.route('/initiatives/<initiative_id>/increment', methods=['POST'])
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


@initiatives_bp.route('/initiatives/<initiative_id>/create-task', methods=['POST'])
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
    trigger_assignment_regeneration()
    
    return jsonify(task.to_dict())