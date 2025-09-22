"""
Events API Routes

Handles all event-related endpoints including CRUD operations,
recurring event management, and calendar integration.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, date, timedelta
from models import db, Event, Meal
from recurring_service import recurring_service
from .utils import trigger_pool_regeneration, parse_date_range, parse_datetime_with_timezone
import uuid

events_bp = Blueprint('events', __name__)


@events_bp.route('/events')
def get_events():
    """Get events - supports two modes via query parameter"""
    mode = request.args.get('mode', 'list')  # 'list' or 'calendar'
    
    if mode == 'calendar':
        # Calendar mode: expand recurring events for display
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        start_date, end_date = parse_date_range(start_str, end_str)
        
        # Get all events and expand recurring ones
        all_events = Event.query.all()
        expanded_events = recurring_service.expand_events_for_period(all_events, start_date, end_date)
        return jsonify(expanded_events)
    
    else:
        # List mode: only master events (for events list page)
        all_events = Event.query.all()
        master_events = recurring_service.get_master_events_only(all_events)
        return jsonify([e.to_dict() for e in master_events])


@events_bp.route('/events', methods=['POST'])
def create_event():
    """Create a new event from FullCalendar"""
    data = request.json
    
    # Parse datetime strings
    start_time = parse_datetime_with_timezone(data['start'])
    end_time = parse_datetime_with_timezone(data['end'])
    
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
    trigger_pool_regeneration()
    
    # Return event with meal data if it's a dinner event
    if event.meal_id:
        return jsonify(event.to_dict_with_meal())
    else:
        return jsonify(event.to_dict())


@events_bp.route('/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an event from form or FullCalendar drag/resize"""
    event = Event.query.get_or_404(event_id)
    data = request.json
    
    # Handle datetime fields
    if 'start' in data:
        start_time = parse_datetime_with_timezone(data['start'])
        event.start_time = start_time.replace(tzinfo=None)
        # Update dtstart for recurring events
        if event.is_recurring:
            event.dtstart = event.start_time
    
    if 'end' in data:
        end_time = parse_datetime_with_timezone(data['end'])
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
    trigger_pool_regeneration()
    
    # Return event with meal data if it's a dinner event
    if event.meal_id:
        return jsonify(event.to_dict_with_meal())
    else:
        return jsonify(event.to_dict())


@events_bp.route('/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event"""
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    # Trigger time pool regeneration
    trigger_pool_regeneration()
    
    return jsonify({'status': 'success'})


@events_bp.route('/events/<event_id>/recurring-info')
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


@events_bp.route('/events/dinner', methods=['GET'])
def get_dinner_events():
    """Get all dinner events"""
    dinner_events = Event.query.filter(Event.meal_id.isnot(None)).all()
    return jsonify([event.to_dict_with_meal() for event in dinner_events])