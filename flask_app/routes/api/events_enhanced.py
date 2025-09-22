"""
Enhanced Events API Routes

Handles all event-related endpoints with pagination, filtering, sorting,
recurring event management, and calendar integration.
Follows CODING_STANDARDS.md compliance.
"""
from flask import Blueprint, request, url_for
from datetime import datetime, date, timedelta
from sqlalchemy import and_
from models import db, Event, Meal
from recurring_service import recurring_service
from .utils import trigger_pool_regeneration, parse_date_range, parse_datetime_with_timezone
from .query_utils import apply_standard_enhancements, create_filter_config
from .response_utils import APIResponse, handle_api_errors, validate_request_data
import uuid

events_enhanced_bp = Blueprint('events_enhanced', __name__)


# Configuration for event queries
EVENT_QUERY_CONFIG = {
    'filters': create_filter_config(Event, {
        # Basic filters
        'event_type': {'column': 'event_type', 'type': 'in'},
        'status': {'column': 'status', 'type': 'exact'},
        'is_blocking': {'column': 'is_blocking', 'type': 'boolean'},
        'is_recurring': {'column': 'is_recurring', 'type': 'boolean'},
        'notifications_enabled': {'column': 'notifications_enabled', 'type': 'boolean'},
        
        # Date range filters
        'start_from': {'column': 'start_time', 'type': 'date_range'},
        'start_to': {'column': 'start_time', 'type': 'date_range'},
        'end_from': {'column': 'end_time', 'type': 'date_range'},
        'end_to': {'column': 'end_time', 'type': 'date_range'},
        
        # Relationship filters
        'project_id': {'column': 'project_id', 'type': 'exact'},
        'meal_id': {'column': 'meal_id', 'type': 'exact'},
        'location': {'column': 'location', 'type': 'like'},
    }),
    'search_fields': ['title', 'description', 'location'],
    'sortable_fields': [
        'title', 'start_time', 'end_time', 'created_at',
        'updated_at', 'event_type', 'status', 'priority'
    ],
    'default_sort': 'start_time:asc',
    'default_limit': 50,
    'max_limit': 200
}


@events_enhanced_bp.route('/v2/events')
@handle_api_errors
def get_events_enhanced():
    """Get events with enhanced query capabilities"""
    mode = request.args.get('mode', 'list')
    
    if mode == 'calendar':
        # Calendar mode with expansion
        return _get_calendar_events()
    
    # List mode with advanced filtering
    query = Event.query
    
    # Apply master events filter for list mode
    if request.args.get('master_only', 'true').lower() == 'true':
        all_events = query.all()
        master_events = recurring_service.get_master_events_only(all_events)
        # Convert back to query-like result
        master_ids = [e.id for e in master_events]
        query = Event.query.filter(Event.id.in_(master_ids))
    
    # Apply standard enhancements
    enhancer = apply_standard_enhancements(query, Event, EVENT_QUERY_CONFIG)
    
    # Get results
    results = enhancer.serialize_results()
    
    # Add expansion info to recurring events if requested
    if request.args.get('include_expansion_info', '').lower() == 'true':
        for event_data in results['data']:
            if event_data.get('is_recurring'):
                event_data['expansion_info'] = _get_expansion_info(event_data['id'])
    
    return results


@events_enhanced_bp.route('/v2/events/calendar')
@handle_api_errors
def get_calendar_events_enhanced():
    """Get expanded events specifically for calendar display"""
    return _get_calendar_events()


@events_enhanced_bp.route('/v2/events/<event_id>')
@handle_api_errors
def get_event_enhanced(event_id):
    """Get a specific event with enhanced response"""
    event = Event.query.get(event_id)
    
    if not event:
        return APIResponse.not_found("Event not found")
    
    # Get event data
    include = request.args.get('include', '').split(',')
    
    if 'meal' in include and event.meal_id:
        event_data = event.to_dict_with_meal()
    else:
        event_data = event.to_dict()
    
    # Add recurring info if requested
    if 'recurring_info' in include and event.is_recurring:
        event_data['recurring_info'] = {
            'is_recurring': True,
            'is_recurrence_master': bool(event.is_recurrence_master),
            'recurrence_rrule': event.recurrence_rrule,
            'recurrence_pattern': event.recurrence_pattern,
            'recurrence_end': event.recurrence_end.isoformat() if event.recurrence_end else None,
            'master_event_id': event.recurrence_master_id or event.id
        }
    
    return APIResponse.success(data=event_data)


@events_enhanced_bp.route('/v2/events', methods=['POST'])
@handle_api_errors
@validate_request_data(required_fields=['title', 'start', 'end'])
def create_event_enhanced(validated_data=None):
    """Create a new event with validation"""
    data = validated_data
    
    # Parse and validate datetime fields
    try:
        start_time = parse_datetime_with_timezone(data['start'])
        end_time = parse_datetime_with_timezone(data['end'])
    except ValueError:
        return APIResponse.validation_error({
            'datetime': 'Invalid datetime format. Use ISO 8601 format'
        })
    
    # Remove timezone info
    start_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)
    
    # Validate time logic
    if end_time <= start_time:
        return APIResponse.validation_error({
            'times': 'End time must be after start time'
        })
    
    # Handle all-day events
    event_type = data.get('event_type', 'timed')
    if event_type == 'all_day':
        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Validate meal_id if provided
    meal_id = data.get('meal_id')
    if meal_id:
        meal = Meal.query.get(meal_id)
        if not meal:
            return APIResponse.validation_error({
                'meal_id': 'Invalid meal_id - meal does not exist'
            })
    
    # Create event
    event = Event(
        id=str(uuid.uuid4()),
        title=data['title'],
        start_time=start_time,
        end_time=end_time,
        is_blocking=data.get('is_blocking', True),
        description=data.get('description', ''),
        location=data.get('location', ''),
        event_type=event_type,
        meal_id=meal_id,
        notifications_enabled=data.get('notifications_enabled', True),
        status=data.get('status', 'scheduled'),
        priority=data.get('priority', 'medium'),
        project_id=data.get('project_id'),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Handle recurring event fields
    if data.get('is_recurring', False):
        if not data.get('recurrence_rrule'):
            return APIResponse.validation_error({
                'recurrence_rrule': 'RRULE is required for recurring events'
            })
        
        event.is_recurring = True
        event.is_recurrence_master = True
        event.recurrence_pattern = data.get('recurrence_pattern', '')
        event.recurrence_rrule = data['recurrence_rrule']
        event.dtstart = start_time
        event.dtend = end_time
        
        if data.get('recurrence_end'):
            try:
                event.recurrence_end = datetime.fromisoformat(
                    data['recurrence_end'].replace('Z', '+00:00')
                ).replace(tzinfo=None)
            except ValueError:
                return APIResponse.validation_error({
                    'recurrence_end': 'Invalid recurrence end date format'
                })
    
    db.session.add(event)
    db.session.commit()
    
    trigger_pool_regeneration()
    
    # Return appropriate response based on event type
    location = url_for('events_enhanced.get_event_enhanced', event_id=event.id, _external=True)
    
    if event.meal_id:
        return APIResponse.created(data=event.to_dict_with_meal(), location=location)
    else:
        return APIResponse.created(data=event.to_dict(), location=location)


@events_enhanced_bp.route('/v2/events/<event_id>', methods=['PUT'])
@handle_api_errors
def update_event_enhanced(event_id):
    """Update an event with validation"""
    event = Event.query.get(event_id)
    if not event:
        return APIResponse.not_found("Event not found")
    
    if not request.is_json:
        return APIResponse.error("Request must be JSON", status_code=415)
    
    data = request.get_json()
    changes_made = False
    
    # Handle datetime updates
    if 'start' in data:
        try:
            start_time = parse_datetime_with_timezone(data['start'])
            event.start_time = start_time.replace(tzinfo=None)
            if event.is_recurring:
                event.dtstart = event.start_time
            changes_made = True
        except ValueError:
            return APIResponse.validation_error({'start': 'Invalid datetime format'})
    
    if 'end' in data:
        try:
            end_time = parse_datetime_with_timezone(data['end'])
            event.end_time = end_time.replace(tzinfo=None)
            if event.is_recurring:
                event.dtend = event.end_time
            changes_made = True
        except ValueError:
            return APIResponse.validation_error({'end': 'Invalid datetime format'})
    
    # Validate time logic if both were updated
    if 'start' in data and 'end' in data:
        if event.end_time <= event.start_time:
            return APIResponse.validation_error({
                'times': 'End time must be after start time'
            })
    
    # Update other fields
    update_fields = [
        'title', 'description', 'location', 'event_type',
        'is_blocking', 'notifications_enabled', 'status', 'priority'
    ]
    
    for field in update_fields:
        if field in data:
            setattr(event, field, data[field])
            changes_made = True
    
    # Handle meal_id updates
    if 'meal_id' in data:
        meal_id = data['meal_id']
        if meal_id:
            meal = Meal.query.get(meal_id)
            if not meal:
                return APIResponse.validation_error({
                    'meal_id': 'Invalid meal_id - meal does not exist'
                })
        event.meal_id = meal_id
        changes_made = True
    
    # Handle recurring event updates
    if 'is_recurring' in data:
        event.is_recurring = data['is_recurring']
        if data['is_recurring']:
            event.is_recurrence_master = True
            if 'recurrence_pattern' in data:
                event.recurrence_pattern = data['recurrence_pattern']
            if 'recurrence_rrule' in data:
                event.recurrence_rrule = data['recurrence_rrule']
            if 'recurrence_end' in data:
                if data['recurrence_end']:
                    try:
                        event.recurrence_end = datetime.fromisoformat(
                            data['recurrence_end']
                        ).replace(tzinfo=None)
                    except ValueError:
                        return APIResponse.validation_error({
                            'recurrence_end': 'Invalid date format'
                        })
                else:
                    event.recurrence_end = None
        else:
            # Clear recurring fields
            event.is_recurrence_master = False
            event.recurrence_pattern = None
            event.recurrence_rrule = None
            event.recurrence_end = None
        changes_made = True
    
    if changes_made:
        event.updated_at = datetime.utcnow()
        db.session.commit()
        trigger_pool_regeneration()
    
    if event.meal_id:
        return APIResponse.success(data=event.to_dict_with_meal())
    else:
        return APIResponse.success(data=event.to_dict())


@events_enhanced_bp.route('/v2/events/<event_id>', methods=['DELETE'])
@handle_api_errors
def delete_event_enhanced(event_id):
    """Delete an event"""
    event = Event.query.get(event_id)
    if not event:
        return APIResponse.not_found("Event not found")
    
    # Check if this is a recurring event series
    if event.is_recurring and event.is_recurrence_master:
        # Option to delete entire series
        if request.args.get('delete_series', '').lower() == 'true':
            # Delete all instances in the series
            # This would require more complex logic
            pass
    
    db.session.delete(event)
    db.session.commit()
    
    trigger_pool_regeneration()
    
    return APIResponse.no_content()


@events_enhanced_bp.route('/v2/events/batch', methods=['POST'])
@handle_api_errors
def create_events_batch():
    """Batch create multiple events"""
    if not request.is_json:
        return APIResponse.error("Request must be JSON", status_code=415)
    
    data = request.get_json()
    if not isinstance(data, dict) or 'events' not in data:
        return APIResponse.validation_error({
            'events': 'Request must contain an "events" array'
        })
    
    events_data = data['events']
    if not isinstance(events_data, list):
        return APIResponse.validation_error({
            'events': 'Events must be an array'
        })
    
    created_events = []
    errors = []
    
    for idx, event_data in enumerate(events_data):
        required = ['title', 'start', 'end']
        missing = [field for field in required if field not in event_data]
        
        if missing:
            errors.append({
                'index': idx,
                'error': f'Missing required fields: {", ".join(missing)}'
            })
            continue
        
        try:
            # Use same validation logic as single create
            start_time = parse_datetime_with_timezone(event_data['start'])
            end_time = parse_datetime_with_timezone(event_data['end'])
            start_time = start_time.replace(tzinfo=None)
            end_time = end_time.replace(tzinfo=None)
            
            if end_time <= start_time:
                errors.append({
                    'index': idx,
                    'error': 'End time must be after start time'
                })
                continue
            
            event = Event(
                id=str(uuid.uuid4()),
                title=event_data['title'],
                start_time=start_time,
                end_time=end_time,
                is_blocking=event_data.get('is_blocking', True),
                description=event_data.get('description', ''),
                location=event_data.get('location', ''),
                event_type=event_data.get('event_type', 'timed'),
                notifications_enabled=event_data.get('notifications_enabled', True),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(event)
            created_events.append(event)
            
        except Exception as e:
            errors.append({
                'index': idx,
                'error': str(e)
            })
    
    if created_events:
        db.session.commit()
        trigger_pool_regeneration()
    
    response_data = {
        'created': [event.to_dict() for event in created_events],
        'errors': errors
    }
    
    status_code = 201 if not errors else 207  # 207 Multi-Status
    
    return APIResponse.success(
        data=response_data,
        message=f"Created {len(created_events)} events",
        status_code=status_code
    )


# Helper functions
def _get_calendar_events():
    """Get expanded events for calendar display"""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    start_date, end_date = parse_date_range(start_str, end_str)
    
    # Get all events
    query = Event.query
    
    # Apply filters if any (but not pagination for expansion)
    filters = []
    
    # Event type filter
    if request.args.get('event_type'):
        types = request.args.get('event_type').split(',')
        filters.append(Event.event_type.in_(types))
    
    # Blocking filter
    if request.args.get('is_blocking') is not None:
        is_blocking = request.args.get('is_blocking').lower() == 'true'
        filters.append(Event.is_blocking == is_blocking)
    
    if filters:
        query = query.filter(and_(*filters))
    
    all_events = query.all()
    
    # Expand recurring events
    expanded_events = recurring_service.expand_events_for_period(
        all_events, start_date, end_date
    )
    
    # Apply pagination to expanded results
    try:
        limit = min(int(request.args.get('limit', 200)), 500)
        offset = int(request.args.get('offset', 0))
    except (ValueError, TypeError):
        limit = 200
        offset = 0
    
    total = len(expanded_events)
    paginated_events = expanded_events[offset:offset + limit]
    
    return APIResponse.paginated(
        items=paginated_events,
        total=total,
        limit=limit,
        offset=offset,
        serializer=lambda x: x  # Already serialized by recurring_service
    )


def _get_expansion_info(event_id):
    """Get information about recurring event expansion"""
    event = Event.query.get(event_id)
    if not event or not event.is_recurring:
        return None
    
    # Get next few occurrences
    today = date.today()
    end_date = today + timedelta(days=30)
    
    expanded = recurring_service.expand_events_for_period(
        [event], today, end_date
    )
    
    return {
        'next_occurrences': len(expanded),
        'next_occurrence_dates': [
            e['start'][:10] for e in expanded[:5]  # First 5 dates
        ]
    }