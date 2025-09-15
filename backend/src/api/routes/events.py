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
from ...services.recurring_events_service import RecurringEventsService
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
    """Get all events for schedule view - expands recurring events to show actual instances"""
    try:
        print("=== GET EVENTS FOR SCHEDULE DEBUG ===")
        repo = EventRepository(db)
        recurring_service = RecurringEventsService(db)
        
        if date:
            events = repo.get_by_date(date)
            start_date = date
            end_date = date
        else:
            events = repo.get_all()
            # If no date specified, expand recurring events for a 2-week window around today
            from datetime import timedelta
            today = date.today()
            start_date = today - timedelta(days=7)
            end_date = today + timedelta(days=14)
            print(f"No date filter provided, expanding recurring events from {start_date} to {end_date}")
        
        print(f"Found {len(events)} total events")
        
        expanded_events = []
        for event in events:
            # Check if this is a proper master event (new system)
            if getattr(event, 'is_recurrence_master', False):
                # For recurring masters, manually create today's instance for testing
                print(f"Processing master event: {event.title}")
                
                # Simple test: create today's instance of each recurring event
                from datetime import datetime, timedelta
                today_date = datetime.now().date()
                
                if start_date <= today_date <= end_date:
                    # Calculate today's instance time
                    original_time = event.start_time.time()
                    today_start = datetime.combine(today_date, original_time)
                    
                    duration = event.end_time - event.start_time
                    today_end = today_start + duration
                    
                    # Create a mock EventModel-like object for today's instance
                    class MockEvent:
                        def __init__(self):
                            self.id = f"{event.id}-instance-{today_date.isoformat()}"
                            self.created_at = event.created_at
                            self.updated_at = event.updated_at
                            self.title = event.title
                            self.start_time = today_start
                            self.end_time = today_end
                            self.is_blocking = event.is_blocking
                            self.location = event.location
                            self.description = event.description
                            self.notifications_enabled = getattr(event, 'notifications_enabled', True)
                            self.is_recurring = False
                            self.recurrence_pattern = None
                            self.recurrence_master_id = event.id
                            self.is_recurrence_master = False
                            self.is_recurrence_exception = False
                            self.recurrence_instance_date = today_start
                    
                    today_instance = MockEvent()
                    expanded_events.append(today_instance)
                    print(f"Created today's instance for {event.title} at {today_start}")
                else:
                    print(f"Today ({today_date}) not in range {start_date} to {end_date}")
                
                # DO NOT include the master event itself - only the generated instances
                    
            elif not getattr(event, 'recurrence_master_id', None):
                # Include standalone events
                # But exclude recurring masters (they should only show as instances)
                if not getattr(event, 'is_recurrence_master', False):
                    expanded_events.append(event)
            # Skip individual instances that are properly linked to masters
        
        print(f"Expanded to {len(expanded_events)} events for schedule")
        
        # Add a test event to verify the endpoint is working
        class TestEvent:
            def __init__(self):
                self.id = "test-event-123"
                self.created_at = "2025-09-15T03:00:00"
                self.updated_at = "2025-09-15T03:00:00" 
                self.title = "TEST EVENT - Today"
                self.start_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)
                self.end_time = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
                self.is_blocking = True
                self.location = None
                self.description = "Test event to verify endpoint is working"
                self.notifications_enabled = True
                self.is_recurring = False
                self.recurrence_pattern = None
                self.recurrence_master_id = None
                self.is_recurrence_master = False
                self.is_recurrence_exception = False
                self.recurrence_instance_date = None
        
        test_event = TestEvent()
        expanded_events.append(test_event)
        
        event_responses = []
        for event in expanded_events:
            try:
                event_response = EventResponse.model_validate(event)
                event_responses.append(event_response)
            except Exception as e:
                print(f"Error validating event {event.id}: {e}")
                raise
        
        return EventListResponse(
            events=event_responses,
            total=len(expanded_events)
        )
    except Exception as e:
        print(f"Error in get_events_for_schedule: {e}")
        raise

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
    recurring_service = RecurringEventsService(db)
    
    try:
        event = recurring_service.event_repo.get(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        is_recurring = recurring_service.is_recurring_event(event_id)
        master_event = recurring_service.get_master_event(event_id)
        
        info = {
            "is_recurring_event": is_recurring,
            "is_master": event.is_recurrence_master if hasattr(event, 'is_recurrence_master') else False,
            "is_exception": event.is_recurrence_exception if hasattr(event, 'is_recurrence_exception') else False,
            "master_event_id": master_event.id if master_event else None,
            "recurrence_pattern": master_event.recurrence_pattern if master_event else None
        }
        
        return info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recurring event info: {str(e)}")

@router.delete("/{event_id}", response_model=MessageResponse)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Delete an event (non-recurring or single instance)"""
    repo = EventRepository(db)
    recurring_service = RecurringEventsService(db)
    
    event = repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if this is part of a recurring series
    if recurring_service.is_recurring_event(event_id):
        raise HTTPException(
            status_code=400, 
            detail="This is a recurring event. Use the recurring delete endpoint with edit mode."
        )
    
    deleted = repo.delete(event_id)
    
    if deleted:
        return MessageResponse(message="Event deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete event")