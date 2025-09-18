"""
Event API routes
NO EMOJIS
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
import pytz

from ...schemas.event_schemas import (
    EventCreate, EventUpdate, EventResponse, EventListResponse, 
    RecurringEventEditRequest, RecurringEventDeleteRequest, RecurringEditMode
)
from ...schemas.base_schemas import MessageResponse
from ...data.repositories.event_repo import EventRepository
from ...data.repositories.event_exception_repo import EventExceptionRepository
# from ...services.recurring_events_service import RecurringEventsService  # Commented out to avoid import issues
# Temporarily inline the expansion logic to avoid import issues
from ..dependencies import get_db

router = APIRouter(tags=["events"])

@router.get("/debug_list", response_model=dict)
def debug_events(db: Session = Depends(get_db)):
    """Debug endpoint to list all events in database"""
    try:
        print("=== DEBUG EVENTS ===")
        repo = EventRepository(db)
        print("Repository created")
        events = repo.get_all()
        print(f"Got {len(events)} events")
        
        return {
            "count": len(events),
            "events": [
                {
                    "id": event.id,
                    "title": event.title,
                    "start_time": str(event.start_time),
                    "end_time": str(event.end_time),
                    "is_blocking": event.is_blocking,
                    "created_at": str(event.created_at) if hasattr(event, 'created_at') else None,
                    "notifications_enabled": getattr(event, 'notifications_enabled', None)
                }
                for event in events
            ]
        }
    except Exception as e:
        print(f"Debug error: {e}")
        return {"error": str(e)}

@router.get("/schedule", response_model=EventListResponse)
def get_events_for_schedule(
    date: Optional[date] = Query(None, description="Filter by date"),
    db: Session = Depends(get_db)
):
    """Get all events for schedule view - simplified version without complex recurring expansion"""
    try:
        print("=== GET EVENTS FOR SCHEDULE DEBUG ===")
        repo = EventRepository(db)
        
        if date:
            events = repo.get_by_date(date)
        else:
            events = repo.get_all()
        
        print(f"Found {len(events)} total events")
        
        # For now, just return all events as-is without complex recurring expansion
        # This simplifies the logic while keeping the endpoint functional
        filtered_events = []
        for event in events:
            # Include all events for schedule view
            # Master events and standalone events
            is_master = getattr(event, 'is_recurrence_master', False) or False
            has_master_id = getattr(event, 'recurrence_master_id', None) is not None
            
            # Include master events and standalone events
            # Exclude instance events (has_master_id = True) 
            if is_master or not has_master_id:
                filtered_events.append(event)
        
        print(f"Filtered to {len(filtered_events)} events for schedule")
        
        event_responses = []
        for event in filtered_events:
            try:
                event_response = EventResponse.model_validate(event)
                event_responses.append(event_response)
            except Exception as e:
                print(f"Error validating event {event.id}: {e}")
                raise
        
        return EventListResponse(
            events=event_responses,
            total=len(filtered_events)
        )
    except Exception as e:
        print(f"Error in get_events_for_schedule: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Schedule endpoint error: {str(e)}")

@router.get("", response_model=EventListResponse)
def get_events(
    date: Optional[date] = Query(None, description="Filter by date"),
    db: Session = Depends(get_db)
):
    """Get all events with optional date filter - shows only master events for recurring series"""
    try:
        print("=== GET EVENTS DEBUG ===")
        repo = EventRepository(db)
        
        if date:
            events = repo.get_by_date(date)
        else:
            events = repo.get_all()
        
        print(f"Found {len(events)} total events")
        
        # Filter to show only:
        # 1. Standalone events (no master_id - these are truly non-recurring)
        # 2. Master events of recurring series (is_recurrence_master = True)
        # Exclude: Instance events (has recurrence_master_id)
        filtered_events = []
        for event in events:
            is_master = getattr(event, 'is_recurrence_master', False) or False
            has_master_id = getattr(event, 'recurrence_master_id', None) is not None
            
            # Include if:
            # - Is a recurring master event, OR
            # - Is standalone (not part of any recurring series)
            # Exclude: recurring instances (has_master_id = True)
            if is_master or not has_master_id:
                filtered_events.append(event)
        
        print(f"Filtered to {len(filtered_events)} events (masters + non-recurring)")
        
        event_responses = []
        for event in filtered_events:
            try:
                event_response = EventResponse.model_validate(event)
                event_responses.append(event_response)
            except Exception as e:
                print(f"Error validating event {event.id}: {e}")
                raise
        
        return EventListResponse(
            events=event_responses,
            total=len(filtered_events)
        )
    except Exception as e:
        print(f"Error in get_events: {e}")
        raise

@router.post("", response_model=EventResponse)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db)
):
    """Create a new event"""
    print("=== BACKEND EVENT CREATION DEBUG ===")
    print(f"Received data: {event_data.model_dump()}")
    
    repo = EventRepository(db)
    recurring_service = RecurringEventsService(db)
    
    try:
        # Incoming times are already in Pacific time from frontend
        # Store them as-is without timezone conversion
        start_pacific = event_data.start_time.replace(tzinfo=None) if event_data.start_time.tzinfo else event_data.start_time
        end_pacific = event_data.end_time.replace(tzinfo=None) if event_data.end_time.tzinfo else event_data.end_time
        
        print(f"Storing times as Pacific: {start_pacific} - {end_pacific}")
        
        # Prepare event data
        event_dict = {
            'title': event_data.title,
            'start_time': start_pacific,
            'end_time': end_pacific,
            'is_blocking': event_data.is_blocking,
            'location': event_data.location,
            'description': event_data.description,
            'notifications_enabled': getattr(event_data, 'notifications_enabled', True),
            'is_recurring': event_data.is_recurring,
            'recurrence_pattern': event_data.recurrence_pattern.model_dump() if event_data.recurrence_pattern else None
        }
        
        if event_data.is_recurring and event_data.recurrence_pattern:
            print(f"Creating recurring event with pattern: {event_data.recurrence_pattern}")
            
            # Use new recurring events service
            master_event = recurring_service.create_recurring_event(event_dict)
            print(f"Created recurring event master with ID: {master_event.id}")
            
            return EventResponse.model_validate(master_event)
        else:
            # Single event
            print(f"Creating single event with data: {event_dict}")
            
            saved_event = repo.create(event_dict)
            print(f"Saved event with ID: {saved_event.id}")
            
            return EventResponse.model_validate(saved_event)
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    event_data: EventUpdate,
    db: Session = Depends(get_db)
):
    """Update an event"""
    repo = EventRepository(db)
    event = repo.get(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Convert update data to dict, excluding unset fields
    update_data = event_data.model_dump(exclude_unset=True)
    
    
    
    # Handle timezone conversion for start/end times if provided
    if 'start_time' in update_data:
        start_time = update_data['start_time']
        update_data['start_time'] = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
    
    if 'end_time' in update_data:
        end_time = update_data['end_time']
        update_data['end_time'] = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
    
    try:
        # Check if event is being updated to be recurring
        is_becoming_recurring = (
            'is_recurring' in update_data and 
            update_data.get('is_recurring') == True and 
            not getattr(event, 'is_recurring', False)
        )
        
        if is_becoming_recurring and 'recurrence_pattern' in update_data:
            print(f"Event {event_id} is becoming recurring, using RecurringEventsService...")
            
            # Delete the existing standalone event
            repo.delete(event_id)
            
            # Prepare data for new recurring event
            event_data = {
                'title': update_data.get('title', event.title),
                'start_time': update_data.get('start_time', event.start_time),
                'end_time': update_data.get('end_time', event.end_time),
                'is_blocking': update_data.get('is_blocking', event.is_blocking),
                'location': update_data.get('location', event.location),
                'description': update_data.get('description', event.description),
                'is_recurring': True,
                'recurrence_pattern': update_data['recurrence_pattern']
            }
            
            # Use RecurringEventsService to create proper master/instance structure
            recurring_service = RecurringEventsService(db)
            master_event = recurring_service.create_recurring_event(event_data)
            
            print(f"Created recurring event with master ID: {master_event.id}")
            updated_event = master_event
            
        else:
            # Regular update without recurring logic
            updated_event = repo.update(event_id, update_data)
        
        if not updated_event:
            raise HTTPException(status_code=500, detail="Failed to update event")
        
        return EventResponse.model_validate(updated_event)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")

@router.get("/test-exceptions/{event_id}")
def test_exceptions(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Test endpoint to verify exception loading"""
    exception_repo = EventExceptionRepository(db)
    exceptions = exception_repo.get_exceptions_for_event(event_id)
    
    return {
        "event_id": event_id,
        "exception_count": len(exceptions),
        "exceptions": [
            {
                "date": str(ex.occurrence_date),
                "cancelled": ex.is_cancelled,
                "rescheduled": ex.is_rescheduled
            }
            for ex in exceptions
        ]
    }

@router.get("/expand/{event_id}")
def get_event_occurrences(
    event_id: str,
    start_date: date = Query(..., description="Start date for occurrence range"),
    end_date: date = Query(..., description="End date for occurrence range"),
    max_occurrences: int = Query(365, description="Maximum number of occurrences to return"),
    db: Session = Depends(get_db)
):
    """
    Get expanded occurrences for a recurring event within a date range.
    Uses RRULE-based runtime expansion for performance.
    """
    print(f"DEBUG: get_event_occurrences called with event_id={event_id}")
    print(f"DEBUG: Date range: {start_date} to {end_date}")
    
    try:
        repo = EventRepository(db)
        event = repo.get(event_id)
        
        print(f"DEBUG: Found event: {event.title if event else 'None'}")
        
        if not event:
            raise HTTPException(status_code=404, detail=f"Event not found: {event_id}")
        
        # Get exceptions for this event
        exception_repo = EventExceptionRepository(db)
        exceptions = exception_repo.get_exceptions_for_event(event_id, start_date, end_date)
        
        print(f"DEBUG: Found {len(exceptions)} exceptions for event {event_id}")
        for ex in exceptions:
            print(f"  - Exception on {ex.occurrence_date}: cancelled={ex.is_cancelled}, rescheduled={ex.is_rescheduled}")
        
        # Create a dict for quick exception lookups by date
        exceptions_by_date = {ex.occurrence_date: ex for ex in exceptions}
        print(f"DEBUG: Exception dates in dict: {list(exceptions_by_date.keys())}")
        
        # Inline RRULE expansion logic
        try:
            from dateutil.rrule import rrulestr
            RRULE_AVAILABLE = True
        except ImportError:
            RRULE_AVAILABLE = False
        
        occurrences = []
        
        if event.is_recurring and event.recurrence_rrule and RRULE_AVAILABLE:
            # Use RRULE expansion
            try:
                dtstart = event.dtstart or event.start_time
                dtend = event.dtend or event.end_time
                
                if dtstart and dtend:
                    # Parse RRULE
                    rrule_obj = rrulestr(event.recurrence_rrule, dtstart=dtstart)
                    
                    # Calculate event duration
                    duration = dtend - dtstart
                    
                    count = 0
                    for occurrence_start in rrule_obj:
                        if count >= max_occurrences:
                            break
                            
                        occurrence_date = occurrence_start.date()
                        
                        print(f"DEBUG: Processing occurrence on {occurrence_date} (type: {type(occurrence_date)})")
                        
                        # Check if within requested range
                        if occurrence_date > end_date:
                            break
                            
                        if occurrence_date >= start_date:
                            # Check for exceptions
                            exception = exceptions_by_date.get(occurrence_date)
                            
                            print(f"DEBUG: Checking exception for {occurrence_date}: {exception}")
                            
                            if exception and exception.is_cancelled:
                                # Skip cancelled occurrences
                                print(f"DEBUG: Skipping cancelled occurrence on {occurrence_date}")
                                continue
                            
                            occurrence_end = occurrence_start + duration
                            title = event.title
                            location = event.location
                            description = event.description
                            is_exception = False
                            
                            # Apply modifications from exception
                            if exception:
                                is_exception = True
                                if exception.new_start:
                                    occurrence_start = exception.new_start
                                if exception.new_end:
                                    occurrence_end = exception.new_end
                                if exception.custom_title:
                                    title = exception.custom_title
                                if exception.custom_location:
                                    location = exception.custom_location
                                if exception.custom_description:
                                    description = exception.custom_description
                            
                            occurrences.append({
                                'id': f"{event.id}_{occurrence_date.isoformat()}",
                                'title': title,
                                'start': occurrence_start.isoformat(),
                                'end': occurrence_end.isoformat(),
                                'location': location,
                                'description': description,
                                'occurrence_date': occurrence_date.isoformat(),
                                'is_exception': is_exception,
                                'master_event_id': event.id
                            })
                        
                        count += 1
            except Exception as rrule_error:
                print(f"RRULE error: {rrule_error}")
                # Fallback to single occurrence
                if event.start_time.date() >= start_date and event.start_time.date() <= end_date:
                    occurrences = [{
                        'id': event.id,
                        'title': event.title,
                        'start': event.start_time.isoformat(),
                        'end': event.end_time.isoformat(),
                        'location': event.location,
                        'description': event.description,
                        'occurrence_date': event.start_time.date().isoformat(),
                        'is_exception': False,
                        'master_event_id': None
                    }]
        else:
            # Single event or no RRULE
            if event.start_time.date() >= start_date and event.start_time.date() <= end_date:
                occurrences = [{
                    'id': event.id,
                    'title': event.title,
                    'start': event.start_time.isoformat(),
                    'end': event.end_time.isoformat(),
                    'location': event.location,
                    'description': event.description,
                    'occurrence_date': event.start_time.date().isoformat(),
                    'is_exception': False,
                    'master_event_id': None
                }]
        
        return {
            "master_event_id": event_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_occurrences": len(occurrences),
            "occurrences": occurrences,
            "rrule_available": RRULE_AVAILABLE,
            "event_rrule": getattr(event, 'recurrence_rrule', None)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error expanding occurrences: {str(e)}")


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific event by ID"""
    repo = EventRepository(db)
    event = repo.get_by_id(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return EventResponse.model_validate(event)


@router.put("/{event_id}/recurring", response_model=List[EventResponse])
def update_recurring_event(
    event_id: str,
    request: RecurringEventEditRequest,
    db: Session = Depends(get_db)
):
    """Update a recurring event with specified edit mode"""
    recurring_service = RecurringEventsService(db)
    
    try:
        # Convert update data to dict, excluding unset fields
        update_data = request.event_data.model_dump(exclude_unset=True)
        
        # Handle timezone conversion for start/end times if provided
        if 'start_time' in update_data:
            start_time = update_data['start_time']
            update_data['start_time'] = start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
        
        if 'end_time' in update_data:
            end_time = update_data['end_time']
            update_data['end_time'] = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time
        
        affected_events = recurring_service.edit_recurring_event(
            event_id=event_id,
            update_data=update_data,
            edit_mode=request.edit_mode,
            original_date=request.original_date
        )
        
        return [EventResponse.model_validate(event) for event in affected_events]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating recurring event: {str(e)}")

@router.delete("/{event_id}/recurring", response_model=MessageResponse)
def delete_recurring_event(
    event_id: str,
    request: RecurringEventDeleteRequest,
    db: Session = Depends(get_db)
):
    """Delete a recurring event with specified edit mode"""
    # Simplified approach: just delete the event directly using EventRepository
    try:
        from ...data.repositories.event_repo import EventRepository
        repo = EventRepository(db)
        
        # Check if event exists
        event = repo.get(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # For now, just delete the event directly regardless of edit mode
        success = repo.delete(event_id)
        
        if success:
            return MessageResponse(message="Recurring event deleted successfully")
        else:
            raise HTTPException(status_code=500, detail="Failed to delete event")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting recurring event: {str(e)}")

@router.get("/{event_id}/recurring-info", response_model=dict)
def get_recurring_event_info(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get information about a recurring event series"""
    repo = EventRepository(db)
    
    try:
        event = repo.get(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if event is recurring using the event's own properties
        is_recurring = getattr(event, 'is_recurring', False)
        is_master = getattr(event, 'is_recurrence_master', False)
        is_exception = getattr(event, 'is_recurrence_exception', False)
        master_event_id = getattr(event, 'recurrence_master_id', None)
        
        # If this is an instance, get the master event
        master_event = None
        if master_event_id:
            master_event = repo.get(master_event_id)
        elif is_master:
            master_event = event
        
        info = {
            "is_recurring_event": is_recurring or is_master or master_event_id is not None,
            "is_master": is_master,
            "is_exception": is_exception,
            "master_event_id": master_event_id or (event.id if is_master else None),
            "recurrence_pattern": getattr(master_event, 'recurrence_pattern', None) if master_event else None
        }
        
        return info
        
    except Exception as e:
        print(f"Error in get_recurring_event_info: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting recurring event info: {str(e)}")

@router.delete("/{event_id}", response_model=MessageResponse)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Delete an event (non-recurring or single instance)"""
    repo = EventRepository(db)
    
    event = repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if this is part of a recurring series using event properties
    is_recurring = getattr(event, 'is_recurring', False)
    is_master = getattr(event, 'is_recurrence_master', False)
    master_event_id = getattr(event, 'recurrence_master_id', None)
    
    if is_recurring or is_master or master_event_id:
        raise HTTPException(
            status_code=400, 
            detail="This is a recurring event. Use the recurring delete endpoint with edit mode."
        )
    
    deleted = repo.delete(event_id)
    
    if deleted:
        return MessageResponse(message="Event deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete event")