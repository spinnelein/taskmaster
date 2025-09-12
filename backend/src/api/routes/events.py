"""
Event API routes
NO EMOJIS
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
import pytz

from ...schemas.event_schemas import EventCreate, EventUpdate, EventResponse, EventListResponse
from ...schemas.base_schemas import MessageResponse
from ...data.repositories.event_repo import EventRepository
from ...domain.event import Event
from ...utils.recurrence import generate_recurring_events
from ..dependencies import get_db

router = APIRouter(tags=["events"])

@router.get("", response_model=EventListResponse)
def get_events(
    date: Optional[date] = Query(None, description="Filter by date"),
    db: Session = Depends(get_db)
):
    """Get all events with optional date filter"""
    repo = EventRepository(db)
    
    if date:
        events = repo.get_by_date(date)
    else:
        events = repo.get_all()
    
    return EventListResponse(
        events=[EventResponse(**event.to_dict()) for event in events],
        total=len(events)
    )

@router.post("", response_model=EventResponse)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db)
):
    """Create a new event"""
    print("=== BACKEND EVENT CREATION DEBUG ===")
    print(f"Received data: {event_data.dict()}")
    
    repo = EventRepository(db)
    
    try:
        # Incoming times are already in Pacific time from frontend
        # Store them as-is without timezone conversion
        start_pacific = event_data.start_time.replace(tzinfo=None) if event_data.start_time.tzinfo else event_data.start_time
        end_pacific = event_data.end_time.replace(tzinfo=None) if event_data.end_time.tzinfo else event_data.end_time
        
        print(f"Storing times as Pacific: {start_pacific} - {end_pacific}")
        
        if event_data.is_recurring and event_data.recurrence_pattern:
            print(f"Creating recurring event with pattern: {event_data.recurrence_pattern}")
            
            # Generate recurring events
            recurrence_dict = event_data.recurrence_pattern.dict() if hasattr(event_data.recurrence_pattern, 'dict') else event_data.recurrence_pattern
            recurring_events = generate_recurring_events(
                title=event_data.title,
                start_time=start_pacific,
                end_time=end_pacific,
                recurrence_pattern=recurrence_dict,
                is_blocking=event_data.is_blocking,
                location=event_data.location,
                description=event_data.description
            )
            
            print(f"Generated {len(recurring_events)} recurring events")
            
            # Save parent event first
            parent_event_data = recurring_events[0]
            parent_event = Event(
                title=parent_event_data['title'],
                start_time=parent_event_data['start_time'],
                end_time=parent_event_data['end_time'],
                is_blocking=parent_event_data['is_blocking'],
                location=parent_event_data['location'],
                description=parent_event_data['description']
            )
            saved_parent = repo.save(parent_event)
            
            # Save recurring instances
            for event_instance in recurring_events[1:]:  # Skip parent (first item)
                instance_event = Event(
                    title=event_instance['title'],
                    start_time=event_instance['start_time'],
                    end_time=event_instance['end_time'],
                    is_blocking=event_instance['is_blocking'],
                    location=event_instance['location'],
                    description=event_instance['description']
                )
                repo.save(instance_event)
            
            return EventResponse(**saved_parent.to_dict())
        else:
            # Single event
            event = Event(
                title=event_data.title,
                start_time=start_pacific,
                end_time=end_pacific,
                is_blocking=event_data.is_blocking,
                location=event_data.location,
                description=event_data.description
            )
            print(f"Created event object: {event.__dict__}")
            
            saved_event = repo.save(event)
            print(f"Saved event with ID: {saved_event.id}")
            print(f"Event data: {saved_event.to_dict()}")
            
            return EventResponse(**saved_event.to_dict())
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    
    return EventResponse(**event.to_dict())

@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    event_data: EventUpdate,
    db: Session = Depends(get_db)
):
    """Update an event"""
    repo = EventRepository(db)
    event = repo.get_by_id(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update fields if provided
    update_data = event_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    try:
        event.validate()
        saved_event = repo.save(event)
        return EventResponse(**saved_event.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}", response_model=MessageResponse)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Delete an event"""
    repo = EventRepository(db)
    
    if not repo.get_by_id(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    
    deleted = repo.delete(event_id)
    
    if deleted:
        return MessageResponse(message="Event deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete event")

@router.get("/debug", response_model=dict)
def debug_events(db: Session = Depends(get_db)):
    """Debug endpoint to list all events in database"""
    repo = EventRepository(db)
    events = repo.get_all()
    
    return {
        "count": len(events),
        "events": [
            {
                "id": event.id,
                "title": event.title,
                "start_time": str(event.start_time),
                "end_time": str(event.end_time),
                "is_blocking": event.is_blocking,
                "created_at": str(event.created_at) if hasattr(event, 'created_at') else None
            }
            for event in events
        ]
    }