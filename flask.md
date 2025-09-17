Flask Migration Plan for Claude Code
CRITICAL INSTRUCTIONS FOR CLAUDE CODE
markdown# Flask Migration from FastAPI + React

## CRITICAL REMINDERS
- NO EMOJIS in code or comments!
- Use only ASCII characters
- DO NOT DELETE existing domain/data layer code - we're reusing it!
- Keep Flask app simple - no unnecessary complexity
- This is a Windows environment

## IMPORTANT: Finding Existing Code

Claude Code has trouble finding existing code. Here's what to look for:

### Domain Layer (KEEP THESE - DO NOT DELETE):
Look in these locations:
- src/domain/*.py
- backend/src/domain/*.py
- domain/*.py

Files to preserve:
- task.py (Task class with can_start(), complete(), etc.)
- event.py (Event class with blocks_time_period(), etc.)
- project.py, phase.py, initiative.py (if they exist)
- meal.py, dish.py (if they exist)

### Data Layer (KEEP THESE - DO NOT DELETE):
Look in these locations:
- src/data/repositories/*.py
- backend/src/data/repositories/*.py
- src/data/models/*.py
- backend/src/data/models/*.py

### Command Layer (KEEP FOR LATER):
- src/commands/*.py
- backend/src/commands/*.py
(We'll integrate these into Flask routes later)

## Phase 1: Create Flask Foundation (DO THIS FIRST)

### Step 1: Create New Flask Directory Structure
Create a new 'flask_app' directory at project root level:

flask_app/
├── app.py                 # Main Flask application
├── models.py             # Database models (simplified)
├── routes/
│   ├── __init__.py
│   ├── events.py         # Event routes
│   ├── tasks.py          # Task routes
│   └── schedule.py       # Schedule routes
├── templates/
│   ├── base.html         # Base template
│   ├── schedule.html     # Main schedule view
│   ├── events.html       # Events list
│   ├── event_form.html   # Create/edit event
│   ├── tasks.html        # Tasks list
│   └── task_form.html    # Create/edit task
├── static/
│   └── style.css         # Simple CSS
├── domain_adapter.py     # Adapter to use existing domain classes
└── requirements.txt      # Flask dependencies

### Step 2: Create app.py
```python
# flask_app/app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
import uuid
import os
import sys

# Add parent directory to path to import existing domain code
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scheduler.db'
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Import models after db is initialized
from models import Event, Task, Project

@app.route('/')
def index():
    """Main schedule view"""
    # Get today's events
    today = date.today()
    events = Event.query.filter(
        db.func.date(Event.start_time) == today
    ).order_by(Event.start_time).all()
    
    # Get pending tasks
    tasks = Task.query.filter_by(completion_status='pending').all()
    
    # Calculate time pools (gaps between blocking events)
    time_pools = calculate_time_pools(events)
    
    return render_template('schedule.html', 
                         events=events, 
                         tasks=tasks,
                         time_pools=time_pools,
                         today=today)

def calculate_time_pools(events):
    """Calculate available time slots between blocking events"""
    pools = []
    blocking_events = [e for e in events if e.is_blocking]
    blocking_events.sort(key=lambda x: x.start_time)
    
    # Simple time pool calculation
    work_start = datetime.combine(date.today(), datetime.min.time()).replace(hour=8)
    work_end = datetime.combine(date.today(), datetime.min.time()).replace(hour=17)
    
    if not blocking_events:
        pools.append({
            'start': work_start,
            'end': work_end,
            'duration': 9 * 60  # 9 hours in minutes
        })
        return pools
    
    # Check time before first event
    if blocking_events[0].start_time > work_start:
        duration = int((blocking_events[0].start_time - work_start).total_seconds() / 60)
        if duration > 30:  # Only show pools > 30 minutes
            pools.append({
                'start': work_start,
                'end': blocking_events[0].start_time,
                'duration': duration
            })
    
    # Check time between events
    for i in range(len(blocking_events) - 1):
        gap_start = blocking_events[i].end_time
        gap_end = blocking_events[i + 1].start_time
        duration = int((gap_end - gap_start).total_seconds() / 60)
        if duration > 30:
            pools.append({
                'start': gap_start,
                'end': gap_end,
                'duration': duration
            })
    
    # Check time after last event
    if blocking_events[-1].end_time < work_end:
        duration = int((work_end - blocking_events[-1].end_time).total_seconds() / 60)
        if duration > 30:
            pools.append({
                'start': blocking_events[-1].end_time,
                'end': work_end,
                'duration': duration
            })
    
    return pools

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
Step 3: Create models.py
python# flask_app/models.py
from app import db
from datetime import datetime
import uuid

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_blocking = db.Column(db.Boolean, default=True)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def duration_minutes(self):
        return int((self.end_time - self.start_time).total_seconds() / 60)

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    urgency = db.Column(db.Integer, default=5)  # 1-10
    completion_status = db.Column(db.String(20), default='pending')
    due_date = db.Column(db.Date)
    due_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='planning')
    start_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
Step 4: Create Event Routes
python# flask_app/routes/events.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from models import Event
from datetime import datetime

events_bp = Blueprint('events', __name__, url_prefix='/events')

@events_bp.route('/')
def list_events():
    events = Event.query.order_by(Event.start_time.desc()).all()
    return render_template('events.html', events=events)

@events_bp.route('/new', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        event = Event(
            title=request.form['title'],
            start_time=datetime.fromisoformat(request.form['start_time']),
            end_time=datetime.fromisoformat(request.form['end_time']),
            is_blocking='is_blocking' in request.form,
            location=request.form.get('location', '')
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('event_form.html')

@events_bp.route('/<string:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted', 'info')
    return redirect(url_for('index'))
Step 5: Create Templates
html<!-- flask_app/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}TaskMaster{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; background: #f4f4f4; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 10px; border-bottom: 2px solid #333; }
        nav a { margin: 0 10px; text-decoration: none; color: #333; }
        nav a:hover { color: #007bff; }
        .schedule-grid { display: grid; grid-template-columns: 100px 1fr; gap: 0; }
        .time-slot { padding: 10px; border-bottom: 1px solid #ddd; }
        .event { background: #ffcccc; padding: 10px; margin: 2px; border-radius: 5px; }
        .event.non-blocking { background: #cce5ff; }
        .time-pool { background: #ccffcc; padding: 10px; margin: 2px; border-radius: 5px; }
        .task-card { background: #fffacd; padding: 10px; margin: 5px 0; border-radius: 5px; }
        form { margin: 20px 0; }
        input, select, textarea { width: 100%; padding: 8px; margin: 5px 0; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .flash { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .flash.success { background: #d4edda; color: #155724; }
        .flash.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>TaskMaster</h1>
            <nav>
                <a href="{{ url_for('index') }}">Schedule</a>
                <a href="{{ url_for('events.list_events') }}">Events</a>
                <a href="{{ url_for('tasks.list_tasks') }}">Tasks</a>
            </nav>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
html<!-- flask_app/templates/schedule.html -->
{% extends "base.html" %}
{% block title %}Schedule - {{ today }}{% endblock %}
{% block content %}
<h2>Schedule for {{ today.strftime('%A, %B %d, %Y') }}</h2>

<div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
    <div>
        <h3>Timeline</h3>
        <div class="schedule-grid">
            {% for hour in range(7, 22) %}
                <div class="time-slot">{{ '%02d:00'|format(hour) }}</div>
                <div>
                    {% for event in events %}
                        {% if event.start_time.hour <= hour < event.end_time.hour %}
                            <div class="event {% if not event.is_blocking %}non-blocking{% endif %}">
                                <strong>{{ event.title }}</strong><br>
                                {{ event.start_time.strftime('%I:%M %p') }} - {{ event.end_time.strftime('%I:%M %p') }}
                            </div>
                        {% endif %}
                    {% endfor %}
                    
                    {% for pool in time_pools %}
                        {% if pool.start.hour <= hour < pool.end.hour %}
                            <div class="time-pool">
                                Available: {{ pool.duration }} minutes
                            </div>
                        {% endif %}
                    {% endfor %}
                </div>
            {% endfor %}
        </div>
        
        <a href="{{ url_for('events.create_event') }}">
            <button style="margin-top: 20px;">Add Event</button>
        </a>
    </div>
    
    <div>
        <h3>Pending Tasks</h3>
        {% for task in tasks %}
            <div class="task-card">
                <strong>{{ task.title }}</strong><br>
                Duration: {{ task.duration }} min<br>
                Urgency: {{ task.urgency }}/10
                {% if task.due_date %}
                    <br>Due: {{ task.due_date }}
                {% endif %}
            </div>
        {% endfor %}
        
        <a href="{{ url_for('tasks.create_task') }}">
            <button style="margin-top: 20px;">Add Task</button>
        </a>
    </div>
</div>
{% endblock %}
Step 6: Register Blueprints
Update app.py to register the blueprints:
python# Add to app.py after db initialization
from routes.events import events_bp
from routes.tasks import tasks_bp

app.register_blueprint(events_bp)
app.register_blueprint(tasks_bp)
Phase 2: Data Migration
Step 1: Check for Existing Database
Look for existing SQLite database files:

scheduler.db
test.db
taskmaster.db
Any .db files in backend/ or project root

If found, we'll migrate the data. If not, we'll start fresh.
Step 2: Create Migration Script (if database exists)
python# flask_app/migrate_data.py
import sqlite3
import sys
import os

# Add paths to find existing code
sys.path.append('..')
sys.path.append('../backend')

def migrate_data():
    # Find existing database
    old_db_path = None
    for path in ['../scheduler.db', '../backend/scheduler.db', '../test.db']:
        if os.path.exists(path):
            old_db_path = path
            break
    
    if not old_db_path:
        print("No existing database found. Starting fresh.")
        return
    
    print(f"Migrating from {old_db_path}")
    
    old_conn = sqlite3.connect(old_db_path)
    new_conn = sqlite3.connect('scheduler.db')
    
    # Copy events
    events = old_conn.execute('SELECT * FROM events').fetchall()
    for event in events:
        # Insert into new database
        pass  # Map fields appropriately
    
    print("Migration complete!")

if __name__ == '__main__':
    migrate_data()
Phase 3: Testing and Cleanup
Step 1: Run Flask App
bashcd flask_app
pip install flask flask-sqlalchemy
python app.py
# Visit http://localhost:5000
Step 2: Test Core Functions

Create an event - should appear immediately
Create a task - should show in sidebar
Check time pools - should show gaps between events
Delete an event - should update immediately

Step 3: Archive Old Code
bash# Create archive of old architecture
mkdir _archive
mv frontend/ _archive/
mv backend/app/ _archive/  # Keep backend/src for domain code
CRITICAL NOTES FOR CLAUDE CODE

DO NOT DELETE src/domain or backend/src/domain - We need those classes!
Find existing code first - Use 'dir', 'ls', 'find' commands to locate files
Start with Phase 1 - Get basic Flask working before migration
Test each step - Run the app after each major change
Keep it simple - No fancy features, just working basics

Success Criteria

Flask app runs on http://localhost:5000
Can create events and they show immediately
Can create tasks and they show in sidebar
Time pools display correctly
No React, no npm, no CORS errors
Everything in one codebase

DO NOT

Delete domain layer code
Add complex JavaScript
Use React or any frontend framework
Create API endpoints (use Flask routes)
Add authentication (yet)
Use emojis in code


## Instructions for Claude Code:
We're migrating from the overcomplicated FastAPI + React architecture to simple Flask with server-side rendering.
CRITICAL:

NO EMOJIS! Only ASCII characters
DO NOT DELETE existing domain/data layer code
Find existing code BEFORE creating new files

Follow the migration plan above:

First, find and list all existing domain and data layer files
Create the new flask_app directory structure
Implement Phase 1 (Flask foundation) completely
Test that the Flask app runs
Only then proceed to data migration if needed

Start by showing me what domain/data files you can find, then create the Flask foundation.
The goal is a SIMPLE, WORKING app with no frontend/backend separation.

This migration plan gives Claude Code clear, step-by-step instructions while warning about its tendency to not find existing code. The Flask app will be much simpler and actually work!