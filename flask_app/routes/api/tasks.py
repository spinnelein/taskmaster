"""
Tasks API Routes

Handles all task-related endpoints including CRUD operations,
task completion, dependency management, and snoozing functionality.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from models import db, Task
from models.projects import ProjectPhase
from .utils import trigger_assignment_regeneration
from services.claude_task_analyzer import get_claude_task_analyzer
import uuid
import json
import logging

logger = logging.getLogger(__name__)

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/tasks')
def get_tasks():
    """Get all root tasks including snoozed ones (accounting for dependencies)"""
    # Check if we should return completed tasks
    completed = request.args.get('completed', 'false').lower() == 'true'
    
    current_time = datetime.utcnow()
    
    if completed:
        # Return completed tasks, sorted by completion date (most recent first)
        completed_tasks = Task.query.filter(Task.is_completed == True).order_by(Task.last_completed_at.desc().nullslast(), Task.updated_at.desc()).limit(50).all()
        return jsonify([t.to_dict() for t in completed_tasks])
    
    # Get all incomplete tasks (including snoozed ones)
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
        
        # Check phase dependencies if task has a phase
        if is_root_task and task.phase_id:
            # Get the task's phase and check if it has dependencies
            phase = db.session.get(ProjectPhase, task.phase_id)
            if phase and phase.depends_on_phase_ids:
                try:
                    phase_dep_ids = json.loads(phase.depends_on_phase_ids)
                    if isinstance(phase_dep_ids, list) and phase_dep_ids:
                        # Check if all dependent phases are completed
                        for phase_dep_id in phase_dep_ids:
                            dep_phase = db.session.get(ProjectPhase, phase_dep_id)
                            if dep_phase and dep_phase.status != 'COMPLETED':
                                # Phase dependency not satisfied - task is blocked
                                is_root_task = False
                                break
                except (json.JSONDecodeError, TypeError):
                    # If phase dependency parsing fails, allow task through
                    pass
        
        if is_root_task:
            root_tasks.append(task)
    
    return jsonify([t.to_dict() for t in root_tasks])


@tasks_bp.route('/tasks', methods=['POST'])
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
    
    # YOLO.md Implementation: Automatic AI Analysis on Task Creation
    task_dict = task.to_dict()
    try:
        logger.info(f"Auto-analyzing new task: {task.title}")
        
        # Get Claude analyzer
        analyzer = get_claude_task_analyzer()
        
        # Build context if project/initiative IDs provided
        context = {}
        if data.get('project_id'):
            task.project_id = data['project_id']
        if data.get('initiative_id'):  
            task.initiative_id = data['initiative_id']
        if data.get('meal_id'):
            task.meal_id = data['meal_id']
        
        # Get comprehensive context
        if task.project_id or task.initiative_id:
            context = analyzer.get_task_context(task.id)
        
        # Perform analysis and save to database YOLO fields
        analysis_result = analyzer.analyze_task_comprehensive(
            task_dict, 
            context, 
            save_to_db=True
        )
        
        # Commit the analysis updates
        db.session.commit()
        
        # Add analysis info to response
        task_dict['ai_analysis_status'] = {
            'analyzed': True,
            'cognitive_load': task.cognitive_load,
            'energy_level': task.energy_level,
            'analysis_source': analysis_result.get('analysis_source', 'unknown'),
            'complexity_score': analysis_result.get('complexity_assessment', {}).get('complexity_score'),
            'analyzed_at': task.last_analyzed.isoformat() if task.last_analyzed else None
        }
        
        logger.info(f"Auto-analysis completed for task {task.id}: "
                   f"cognitive_load={task.cognitive_load}, energy_level={task.energy_level}")
        
    except Exception as e:
        logger.warning(f"Auto-analysis failed for task {task.id}: {e}")
        # Don't fail task creation if analysis fails
        task_dict['ai_analysis_status'] = {
            'analyzed': False,
            'error': str(e)
        }
    
    # Trigger assignment regeneration
    trigger_assignment_regeneration()
    
    return jsonify(task_dict)


@tasks_bp.route('/tasks/<task_id>', methods=['PUT'])
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
    trigger_assignment_regeneration()
    
    return jsonify(task.to_dict())


@tasks_bp.route('/tasks/<task_id>')
def get_task(task_id):
    """Get a specific task"""
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())


@tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    
    # Trigger assignment regeneration
    trigger_assignment_regeneration()
    
    return jsonify({'status': 'success'})


@tasks_bp.route('/tasks/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed or snooze if recurring"""
    task = Task.query.get_or_404(task_id)
    
    # Record completion time
    task.last_completed_at = datetime.now()
    task.updated_at = datetime.now()
    
    # Handle recurring vs non-recurring tasks differently
    if task.recurrence_days and task.recurrence_days > 0:
        # Recurring task: snooze until next occurrence (don't mark completed)
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
    trigger_assignment_regeneration()
    
    return jsonify(result)