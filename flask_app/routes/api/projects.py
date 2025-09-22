"""
Projects API Routes

Handles all project-related endpoints including CRUD operations for projects,
project phases, and project templates. Also includes template instantiation logic.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from models import db, Project, ProjectPhase, ProjectTemplate, Task
from .utils import trigger_assignment_regeneration
import uuid
import json

projects_bp = Blueprint('projects', __name__)


# PROJECT ENDPOINTS

@projects_bp.route('/projects')
def get_projects():
    """Get all projects with phase and task details"""
    projects = Project.query.all()
    
    projects_data = []
    for project in projects:
        project_data = project.to_dict()
        
        # Get project phases
        phases = ProjectPhase.query.filter_by(project_id=project.id).order_by(ProjectPhase.order).all()
        project_data['phases'] = [phase.to_dict() for phase in phases]
        
        # Get project tasks
        tasks = Task.query.filter_by(project_id=project.id, is_completed=False).all()
        project_data['active_tasks'] = [task.to_dict() for task in tasks]
        project_data['task_count'] = len(tasks)
        
        projects_data.append(project_data)
    
    return jsonify(projects_data)


@projects_bp.route('/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    data = request.json
    
    project = Project(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        status=data.get('status', 'PLANNING'),
        priority=data.get('priority', 'MEDIUM'),
        estimated_start_date=datetime.fromisoformat(data['estimated_start_date']) if data.get('estimated_start_date') else None,
        estimated_end_date=datetime.fromisoformat(data['estimated_end_date']) if data.get('estimated_end_date') else None,
        initiative_id=data.get('initiative_id'),
        template_id=data.get('template_id'),
        tags=data.get('tags'),
        custom_fields=data.get('custom_fields'),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify(project.to_dict())


@projects_bp.route('/projects/<project_id>')
def get_project(project_id):
    """Get a specific project with its phases and tasks"""
    project = Project.query.get_or_404(project_id)
    
    project_data = project.to_dict()
    
    # Get project phases
    phases = ProjectPhase.query.filter_by(project_id=project_id).order_by(ProjectPhase.order).all()
    project_data['phases'] = [phase.to_dict() for phase in phases]
    
    # Get project tasks
    tasks = Task.query.filter_by(project_id=project_id).all()
    project_data['tasks'] = [task.to_dict() for task in tasks]
    
    return jsonify(project_data)


@projects_bp.route('/projects/<project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project"""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    if 'title' in data:
        project.title = data['title']
    if 'description' in data:
        project.description = data['description']
    if 'status' in data:
        project.status = data['status']
    if 'priority' in data:
        project.priority = data['priority']
    if 'estimated_start_date' in data:
        project.estimated_start_date = datetime.fromisoformat(data['estimated_start_date']) if data['estimated_start_date'] else None
    if 'estimated_end_date' in data:
        project.estimated_end_date = datetime.fromisoformat(data['estimated_end_date']) if data['estimated_end_date'] else None
    if 'initiative_id' in data:
        project.initiative_id = data['initiative_id']
    if 'tags' in data:
        project.tags = data['tags']
    if 'custom_fields' in data:
        project.custom_fields = data['custom_fields']
    
    project.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(project.to_dict())


@projects_bp.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project and its phases"""
    project = Project.query.get_or_404(project_id)
    
    # Delete associated phases
    ProjectPhase.query.filter_by(project_id=project_id).delete()
    
    # Note: Tasks are not automatically deleted, just unlinked
    Task.query.filter_by(project_id=project_id).update({'project_id': None, 'phase_id': None})
    
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({'status': 'success'})


# PROJECT TEMPLATE ENDPOINTS

@projects_bp.route('/project-templates')
def get_project_templates():
    """Get all project templates with summary information"""
    templates = ProjectTemplate.query.filter_by(is_active=True).all()
    
    templates_data = []
    for template in templates:
        template_data = template.to_dict()
        template_data['summary'] = template.get_summary()
        templates_data.append(template_data)
    
    return jsonify(templates_data)


@projects_bp.route('/project-templates', methods=['POST'])
def create_project_template():
    """Create a new project template"""
    data = request.json
    
    # Validate template_data structure
    template_data = data.get('template_data', {})
    if not template_data.get('project') or not template_data.get('phases'):
        return jsonify({'error': 'Template data must include project and phases'}), 400
    
    template = ProjectTemplate(
        id=str(uuid.uuid4()),
        name=data['name'],
        description=data.get('description', ''),
        category=data.get('category', 'General'),
        estimated_duration_days=data.get('estimated_duration_days'),
        is_active=data.get('is_active', True),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    template.set_template_data(template_data)
    
    db.session.add(template)
    db.session.commit()
    
    return jsonify(template.to_dict())


@projects_bp.route('/project-templates/<template_id>')
def get_project_template(template_id):
    """Get a specific project template"""
    template = ProjectTemplate.query.get_or_404(template_id)
    return jsonify(template.to_dict())


@projects_bp.route('/project-templates/<template_id>', methods=['PUT'])
def update_project_template(template_id):
    """Update a project template"""
    template = ProjectTemplate.query.get_or_404(template_id)
    data = request.json
    
    if 'name' in data:
        template.name = data['name']
    if 'description' in data:
        template.description = data['description']
    if 'category' in data:
        template.category = data['category']
    if 'estimated_duration_days' in data:
        template.estimated_duration_days = data['estimated_duration_days']
    if 'is_active' in data:
        template.is_active = data['is_active']
    if 'template_data' in data:
        template.set_template_data(data['template_data'])
    
    template.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(template.to_dict())


@projects_bp.route('/project-templates/<template_id>', methods=['DELETE'])
def delete_project_template(template_id):
    """Delete a project template"""
    template = ProjectTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    return jsonify({'status': 'success'})


@projects_bp.route('/project-templates/<template_id>/instantiate', methods=['POST'])
def instantiate_project_template(template_id):
    """Create a project from a template with specified due date"""
    template = ProjectTemplate.query.get_or_404(template_id)
    data = request.json
    
    if not data.get('due_date'):
        return jsonify({'error': 'due_date is required for template instantiation'}), 400
    
    try:
        due_date = datetime.fromisoformat(data['due_date']).date()
    except ValueError:
        return jsonify({'error': 'Invalid due_date format. Use ISO format (YYYY-MM-DD)'}), 400
    
    # Get template data
    template_data = template.get_template_data()
    project_template = template_data.get('project', {})
    phases_template = template_data.get('phases', [])
    
    # Calculate project dates working backwards from due date
    estimated_duration = template.estimated_duration_days or 30
    estimated_start_date = due_date - timedelta(days=estimated_duration)
    
    # Create the project
    project = Project(
        id=str(uuid.uuid4()),
        title=data.get('project_name', project_template.get('title', template.name)),
        description=project_template.get('description', template.description),
        status='PLANNING',
        priority=project_template.get('priority', 'MEDIUM'),
        estimated_start_date=datetime.combine(estimated_start_date, datetime.min.time()),
        estimated_end_date=datetime.combine(due_date, datetime.min.time()),
        initiative_id=data.get('initiative_id'),
        template_id=template.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(project)
    db.session.flush()  # Get the project ID
    
    # Create phases and tasks
    phase_id_mapping = {}  # Map template phase names to actual IDs
    
    for phase_template in phases_template:
        # Calculate phase dates
        start_offset = phase_template.get('start_offset_days', 0)
        duration = phase_template.get('duration_days', 7)
        
        phase_start = estimated_start_date + timedelta(days=start_offset)
        phase_end = phase_start + timedelta(days=duration)
        
        # Create the phase
        phase = ProjectPhase(
            id=str(uuid.uuid4()),
            title=phase_template['title'],
            description=phase_template.get('description', ''),
            order=phase_template.get('order', 1),
            status='PLANNING',
            estimated_start_date=datetime.combine(phase_start, datetime.min.time()),
            estimated_end_date=datetime.combine(phase_end, datetime.min.time()),
            project_id=project.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(phase)
        db.session.flush()  # Get the phase ID
        
        # Store mapping for tasks
        phase_id_mapping[phase_template['title']] = phase.id
        
        # Create tasks for this phase
        for task_template in phase_template.get('tasks', []):
            # Calculate task due date
            task_start_offset = task_template.get('start_offset_days', 0)
            task_due_date = phase_start + timedelta(days=task_start_offset)
            
            task = Task(
                id=str(uuid.uuid4()),
                title=task_template['title'],
                description=task_template.get('description', ''),
                duration=task_template.get('estimated_hours', 1) * 60,  # Convert hours to minutes
                priority=task_template.get('priority', 'medium'),
                status='active',
                is_completed=False,
                due_date=task_due_date,
                project_id=project.id,
                phase_id=phase.id,
                is_divisible=task_template.get('is_divisible', False),
                min_chunk_size=task_template.get('min_chunk_size', 30),
                required_context=json.dumps(task_template.get('required_context', [])),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(task)
    
    # Increment template usage count
    template.increment_usage()
    
    db.session.commit()
    
    # Trigger assignment regeneration for new tasks
    trigger_assignment_regeneration()
    
    # Return the created project with all details
    project_data = project.to_dict()
    phases = ProjectPhase.query.filter_by(project_id=project.id).order_by(ProjectPhase.order).all()
    project_data['phases'] = [phase.to_dict() for phase in phases]
    
    tasks = Task.query.filter_by(project_id=project.id).all()
    project_data['tasks'] = [task.to_dict() for task in tasks]
    
    return jsonify({
        'status': 'success',
        'project': project_data,
        'template_name': template.name,
        'phases_created': len(phases),
        'tasks_created': len(tasks)
    })




# PROJECT PHASE ENDPOINTS

@projects_bp.route('/projects/<project_id>/phases', methods=['POST'])
def create_project_phase(project_id):
    """Create a new phase for a project"""
    project = Project.query.get_or_404(project_id)
    data = request.json
    
    phase = ProjectPhase(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        order=data.get('order', 1),
        status=data.get('status', 'PLANNING'),
        estimated_start_date=datetime.fromisoformat(data['estimated_start_date']) if data.get('estimated_start_date') else None,
        estimated_end_date=datetime.fromisoformat(data['estimated_end_date']) if data.get('estimated_end_date') else None,
        depends_on_phase_ids=data.get('depends_on_phase_ids'),
        project_id=project_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(phase)
    db.session.commit()
    
    return jsonify(phase.to_dict())


@projects_bp.route('/project-phases/<phase_id>', methods=['PUT'])
def update_project_phase(phase_id):
    """Update a project phase"""
    phase = ProjectPhase.query.get_or_404(phase_id)
    data = request.json
    
    if 'title' in data:
        phase.title = data['title']
    if 'description' in data:
        phase.description = data['description']
    if 'order' in data:
        phase.order = data['order']
    if 'status' in data:
        phase.status = data['status']
    if 'estimated_start_date' in data:
        phase.estimated_start_date = datetime.fromisoformat(data['estimated_start_date']) if data['estimated_start_date'] else None
    if 'estimated_end_date' in data:
        phase.estimated_end_date = datetime.fromisoformat(data['estimated_end_date']) if data['estimated_end_date'] else None
    if 'depends_on_phase_ids' in data:
        phase.depends_on_phase_ids = data['depends_on_phase_ids']
    
    phase.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(phase.to_dict())


@projects_bp.route('/project-phases/<phase_id>', methods=['DELETE'])
def delete_project_phase(phase_id):
    """Delete a project phase"""
    phase = ProjectPhase.query.get_or_404(phase_id)
    
    # Unlink tasks from this phase
    Task.query.filter_by(phase_id=phase_id).update({'phase_id': None})
    
    db.session.delete(phase)
    db.session.commit()
    
    return jsonify({'status': 'success'})