from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime

events_bp = Blueprint('events', __name__, url_prefix='/events')

def get_models():
    from app import db, Event, Task
    return db, Event, Task

@events_bp.route('/')
def list_events():
    """List all events"""
    db, Event, Task = get_models()
    events = Event.query.order_by(Event.start_time.desc()).all()
    return render_template('events_list.html', events=events)

@events_bp.route('/new', methods=['GET', 'POST'])
def create_event():
    """Create a new event"""
    if request.method == 'POST':
        db, Event, Task = get_models()
        title = request.form['title']
        start_time = datetime.fromisoformat(request.form['start_time'])
        end_time = datetime.fromisoformat(request.form['end_time'])
        is_blocking = 'is_blocking' in request.form
        location = request.form.get('location', '')
        description = request.form.get('description', '')
        
        event = Event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            is_blocking=is_blocking,
            location=location,
            description=description
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('event_form.html')

@events_bp.route('/<event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """Delete an event"""
    db, Event, Task = get_models()
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    flash('Event deleted', 'info')
    return redirect(url_for('index'))