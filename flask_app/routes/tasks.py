from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

def get_models():
    from app import db, Event, Task
    return db, Event, Task

@tasks_bp.route('/')
def list_tasks():
    """List all tasks"""
    db, Event, Task = get_models()
    tasks = Task.query.filter_by(is_completed=False).order_by(Task.urgency.desc()).all()
    completed_tasks = Task.query.filter_by(is_completed=True).order_by(Task.last_completed_at.desc()).limit(10).all()
    return render_template('tasks_list.html', tasks=tasks, completed_tasks=completed_tasks)

@tasks_bp.route('/new', methods=['GET', 'POST'])
def create_task():
    """Create a new task"""
    if request.method == 'POST':
        db, Event, Task = get_models()
        title = request.form['title']
        description = request.form.get('description', '')
        duration = int(request.form['duration'])
        urgency = int(request.form['urgency'])
        priority = request.form['priority']
        
        task = Task(
            title=title,
            description=description,
            duration=duration,
            urgency=urgency,
            priority=priority
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('tasks.list_tasks'))
    
    return render_template('task_form.html')

@tasks_bp.route('/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """Mark a task as completed"""
    db, Event, Task = get_models()
    task = Task.query.get_or_404(task_id)
    task.is_completed = True  # Fixed: use correct column name
    task.last_completed_at = datetime.utcnow()  # Fixed: use correct column name
    task.status = 'completed'
    
    db.session.commit()
    
    flash('Task completed!', 'success')
    return redirect(url_for('tasks.list_tasks'))