from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from models import db, Project, ProjectPhase, Task
import json
import uuid

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects')
def list_projects():
    """Display projects in tree view with phases and tasks"""
    projects = Project.query.all()
    
    # Build complete hierarchy with dependency logic
    for project in projects:
        project.phases = ProjectPhase.query.filter_by(project_id=project.id).order_by(ProjectPhase.order).all()
        
        for phase in project.phases:
            all_tasks = Task.query.filter_by(phase_id=phase.id).all()
            
            # Build dependency tree for tasks
            tasks_by_id = {task.id: task for task in all_tasks}
            
            # First, initialize all tasks with empty dependency lists
            for task in all_tasks:
                task.dependencies = []
                task.dependents = []
            
            # Then, build the relationships
            for task in all_tasks:
                if task.depends_on_task_ids:
                    try:
                        # Handle JSON string or null values
                        if task.depends_on_task_ids and task.depends_on_task_ids != 'null':
                            dep_ids = json.loads(task.depends_on_task_ids)
                            if isinstance(dep_ids, list):
                                for dep_id in dep_ids:
                                    if dep_id in tasks_by_id:
                                        dep_task = tasks_by_id[dep_id]
                                        task.dependencies.append(dep_task)
                                        dep_task.dependents.append(task)
                    except (json.JSONDecodeError, TypeError):
                        pass  # Keep empty lists on error
            
            # Separate root tasks (no dependencies OR dependencies are completed) from dependent tasks for rendering
            phase.root_tasks = []
            for task in all_tasks:
                if not task.is_completed:  # Only show active tasks
                    # Task is a root task if it has no dependencies OR all dependencies are completed
                    if not task.dependencies or all(dep.is_completed for dep in task.dependencies):
                        phase.root_tasks.append(task)
            phase.all_tasks = all_tasks
            
            # Calculate completion percentage
            completed_tasks = [t for t in all_tasks if t.is_completed]
            phase.completion_percentage = (len(completed_tasks) / len(all_tasks) * 100) if all_tasks else 0
            
            # Check if phase has dependencies
            # Parse the JSON string to check if it contains actual dependencies
            dependencies = []
            if phase.depends_on_phase_ids and phase.depends_on_phase_ids != 'null':
                try:
                    dependencies = json.loads(phase.depends_on_phase_ids)
                except (json.JSONDecodeError, TypeError):
                    dependencies = []
            
            phase.has_dependencies = bool(dependencies)
    
    return render_template('projects.html', projects=projects)

@projects_bp.route('/api/projects/<project_id>/tasks/<task_id>/complete', methods=['POST'])
def complete_project_task(project_id, task_id):
    """Mark a task as completed or snooze if recurring"""
    task = Task.query.get_or_404(task_id)
    
    # Record completion time
    task.last_completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    
    # Handle recurring vs non-recurring tasks differently
    if task.recurrence_days and task.recurrence_days > 0:
        # Recurring task: snooze until next occurrence (don't mark completed)
        from datetime import timedelta
        task.is_snoozed = True
        task.snoozed_until = datetime.utcnow() + timedelta(days=task.recurrence_days)
        task.status = 'snoozed'
        # Keep is_completed = False so task can reappear
        
        result = {
            'status': 'success',
            'task_snoozed': True,
            'snoozed_until': task.snoozed_until.isoformat()
        }
    else:
        # Non-recurring task: mark as completed normally
        task.is_completed = True
        task.status = 'completed'
        
        result = {
            'status': 'success', 
            'task_completed': True
        }
    
    db.session.commit()
    
    return jsonify(result)

@projects_bp.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a single project by ID"""
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())

@projects_bp.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    data = request.json
    
    # Parse dates if provided
    estimated_start_date = None
    estimated_end_date = None
    if data.get('estimated_start_date'):
        estimated_start_date = datetime.fromisoformat(data['estimated_start_date'])
    if data.get('estimated_end_date'):
        estimated_end_date = datetime.fromisoformat(data['estimated_end_date'])
    
    project = Project(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', 'PLANNING'),
        priority=data.get('priority', 'MEDIUM'),
        estimated_start_date=estimated_start_date,
        estimated_end_date=estimated_end_date,
        initiative_id=data.get('initiative_id'),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify(project.to_dict())

@projects_bp.route('/api/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update an existing project"""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    # Update fields if provided
    if 'title' in data:
        project.title = data['title']
    if 'description' in data:
        project.description = data['description']
    if 'status' in data:
        project.status = data['status']
    if 'priority' in data:
        project.priority = data['priority']
    if 'estimated_start_date' in data:
        if data['estimated_start_date']:
            project.estimated_start_date = datetime.fromisoformat(data['estimated_start_date'])
        else:
            project.estimated_start_date = None
    if 'estimated_end_date' in data:
        if data['estimated_end_date']:
            project.estimated_end_date = datetime.fromisoformat(data['estimated_end_date'])
        else:
            project.estimated_end_date = None
    
    project.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(project.to_dict())

@projects_bp.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'status': 'success'})

# Phase Management Endpoints
@projects_bp.route('/api/projects/<project_id>/phases', methods=['GET'])
def get_project_phases(project_id):
    """Get all phases for a project"""
    phases = ProjectPhase.query.filter_by(project_id=project_id).order_by(ProjectPhase.order).all()
    return jsonify([phase.to_dict() for phase in phases])

@projects_bp.route('/api/projects/<project_id>/phases', methods=['POST'])
def create_project_phase(project_id):
    """Create a new phase for a project"""
    data = request.json
    
    # Determine order based on dependencies
    depends_on_phase_ids = data.get('depends_on_phase_ids', [])
    
    # If no dependencies provided, treat as anytime phase (order 0)
    if not depends_on_phase_ids:
        phase_order = 0
    else:
        # Get the next sequential order number
        max_order = db.session.query(db.func.max(ProjectPhase.order)).filter_by(project_id=project_id).scalar() or 0
        phase_order = max_order + 1
    
    # Parse dates if provided
    estimated_start_date = None
    estimated_end_date = None
    if data.get('estimated_start_date'):
        estimated_start_date = datetime.fromisoformat(data['estimated_start_date'])
    if data.get('estimated_end_date'):
        estimated_end_date = datetime.fromisoformat(data['estimated_end_date'])
    
    phase = ProjectPhase(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        order=phase_order,
        status=data.get('status', 'PLANNING'),
        estimated_start_date=estimated_start_date,
        estimated_end_date=estimated_end_date,
        depends_on_phase_ids=json.dumps(depends_on_phase_ids),
        project_id=project_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(phase)
    db.session.commit()
    
    return jsonify(phase.to_dict())

@projects_bp.route('/api/projects/<project_id>/phases/<phase_id>', methods=['PUT'])
def update_project_phase(project_id, phase_id):
    """Update a project phase"""
    phase = ProjectPhase.query.filter_by(id=phase_id, project_id=project_id).first_or_404()
    data = request.json
    
    # Update fields if provided
    if 'title' in data:
        phase.title = data['title']
    if 'description' in data:
        phase.description = data['description']
    if 'status' in data:
        phase.status = data['status']
    if 'estimated_start_date' in data:
        if data['estimated_start_date']:
            phase.estimated_start_date = datetime.fromisoformat(data['estimated_start_date'])
        else:
            phase.estimated_start_date = None
    if 'estimated_end_date' in data:
        if data['estimated_end_date']:
            phase.estimated_end_date = datetime.fromisoformat(data['estimated_end_date'])
        else:
            phase.estimated_end_date = None
    if 'depends_on_phase_ids' in data:
        phase.depends_on_phase_ids = json.dumps(data['depends_on_phase_ids'])
    
    phase.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(phase.to_dict())

@projects_bp.route('/api/projects/<project_id>/phases/<phase_id>', methods=['DELETE'])
def delete_project_phase(project_id, phase_id):
    """Delete a project phase"""
    phase = ProjectPhase.query.filter_by(id=phase_id, project_id=project_id).first_or_404()
    
    # Also delete all tasks in this phase
    Task.query.filter_by(phase_id=phase_id).delete()
    
    db.session.delete(phase)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@projects_bp.route('/api/projects/<project_id>/phases/reorder', methods=['PUT'])
def reorder_project_phases(project_id):
    """Reorder phases in a project"""
    data = request.json
    phase_ids = data.get('phase_ids', [])
    
    # Update the order of each phase
    for index, phase_id in enumerate(phase_ids):
        phase = ProjectPhase.query.filter_by(id=phase_id, project_id=project_id).first()
        if phase:
            phase.order = index + 1
            phase.updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'status': 'success'})

# Phase-specific Task Management
@projects_bp.route('/api/projects/<project_id>/phases/<phase_id>/tasks', methods=['GET'])
def get_phase_tasks(project_id, phase_id):
    """Get available tasks for a specific phase with dependency information"""
    # Get tasks that are either not completed or snoozed but snooze has ended
    current_time = datetime.utcnow()
    tasks = Task.query.filter(
        (Task.phase_id == phase_id) & 
        (Task.project_id == project_id) &
        (Task.is_completed == False) &
        ((Task.is_snoozed.is_(None)) | (Task.is_snoozed == False) | (Task.snoozed_until <= current_time))
    ).order_by(Task.created_at).all()
    
    # Auto-unsnooze tasks whose snooze period has ended
    for task in tasks:
        if task.is_snoozed and task.snoozed_until and task.snoozed_until <= current_time:
            task.is_snoozed = False
            task.snoozed_until = None
            task.status = 'active'
    
    db.session.commit()
    
    # Build dependency information (include all project tasks for dependency resolution)
    all_tasks = Task.query.filter_by(project_id=project_id).all()
    tasks_by_id = {task.id: task for task in all_tasks}
    
    task_dicts = []
    for task in tasks:
        task_dict = task.to_dict()
        
        # Add dependencies information
        task_dict['dependencies'] = []
        task_dict['dependents'] = []
        
        if task.depends_on_task_ids:
            try:
                if task.depends_on_task_ids and task.depends_on_task_ids != 'null':
                    dep_ids = json.loads(task.depends_on_task_ids)
                    if isinstance(dep_ids, list):
                        for dep_id in dep_ids:
                            if dep_id in tasks_by_id:
                                dep_task = tasks_by_id[dep_id]
                                task_dict['dependencies'].append({
                                    'id': dep_task.id,
                                    'title': dep_task.title,
                                    'completed': dep_task.is_completed,
                                    'snoozed': dep_task.is_snoozed
                                })
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Find tasks that depend on this one
        for other_task in all_tasks:
            if other_task.depends_on_task_ids:
                try:
                    if other_task.depends_on_task_ids and other_task.depends_on_task_ids != 'null':
                        dep_ids = json.loads(other_task.depends_on_task_ids)
                        if isinstance(dep_ids, list) and task.id in dep_ids:
                            task_dict['dependents'].append({
                                'id': other_task.id,
                                'title': other_task.title,
                                'completed': other_task.is_completed,
                                'snoozed': other_task.is_snoozed
                            })
                except (json.JSONDecodeError, TypeError):
                    pass
        
        task_dicts.append(task_dict)
    
    return jsonify(task_dicts)

@projects_bp.route('/api/projects/<project_id>/phases/<phase_id>/tasks', methods=['POST'])
def create_phase_task(project_id, phase_id):
    """Create a new task in a specific phase"""
    data = request.json
    
    # Parse due_date if provided
    due_date = None
    if data.get('due_date'):
        due_date = datetime.fromisoformat(data['due_date']).date()
    
    task = Task(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        duration=data.get('duration', 30),
        urgency=data.get('urgency', 5),
        priority=data.get('priority', 'medium'),
        status='active',
        is_completed=False,
        project_id=project_id,
        phase_id=phase_id,
        depends_on_task_ids=json.dumps(data.get('depends_on_task_ids', [])),
        due_date=due_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(task)
    db.session.commit()
    
    return jsonify(task.to_dict())

@projects_bp.route('/api/projects/<project_id>/tasks/<task_id>', methods=['GET'])
def get_project_task(project_id, task_id):
    """Get a specific task within a project"""
    task = Task.query.filter_by(id=task_id, project_id=project_id).first_or_404()
    return jsonify(task.to_dict())

@projects_bp.route('/api/projects/<project_id>/tasks/<task_id>', methods=['PUT'])
def update_project_task(project_id, task_id):
    """Update a task within a project"""
    task = Task.query.filter_by(id=task_id, project_id=project_id).first_or_404()
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
    if 'phase_id' in data:
        task.phase_id = data['phase_id']  # Allow moving tasks between phases
    if 'depends_on_task_ids' in data:
        task.depends_on_task_ids = json.dumps(data['depends_on_task_ids'])
    if 'due_date' in data:
        if data['due_date']:
            task.due_date = datetime.fromisoformat(data['due_date']).date()
        else:
            task.due_date = None
    
    task.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(task.to_dict())

@projects_bp.route('/api/projects/<project_id>/tasks/<task_id>', methods=['DELETE'])
def delete_project_task(project_id, task_id):
    """Delete a task from a project"""
    task = Task.query.filter_by(id=task_id, project_id=project_id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({'status': 'success'})

@projects_bp.route('/api/projects/<project_id>/phases/<phase_id>/tasks/reorder', methods=['PUT'])
def reorder_phase_tasks(project_id, phase_id):
    """Reorder tasks within a phase by swapping positions"""
    data = request.json
    task_id_1 = data.get('task_id_1')
    task_id_2 = data.get('task_id_2')
    
    # Get both tasks
    task1 = Task.query.filter_by(id=task_id_1, project_id=project_id, phase_id=phase_id).first_or_404()
    task2 = Task.query.filter_by(id=task_id_2, project_id=project_id, phase_id=phase_id).first_or_404()
    
    # Swap their order positions (using a simple approach based on created_at)
    # Store original created_at values
    temp_created = task1.created_at
    task1.created_at = task2.created_at
    task2.created_at = temp_created
    
    # Update modified timestamps
    task1.updated_at = datetime.utcnow()
    task2.updated_at = datetime.utcnow()
    
    db.session.commit()
    return jsonify({'status': 'success'})