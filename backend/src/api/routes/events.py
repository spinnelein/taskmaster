"""
Event API routes
NO EMOJIS
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from ...schemas.event_schemas import EventCreate, EventUpdate, EventResponse, EventListResponse
from ...schemas.base_schemas import MessageResponse
from ...data.repositories.event_repo import EventRepository
from ...domain.event import Event
from ..dependencies import get_db

router = APIRouter(prefix="/api/events", tags=["events"])

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
    repo = EventRepository(db)
    
    try:
        event = Event(
            title=event_data.title,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            is_blocking=event_data.is_blocking,
            location=event_data.location,
            description=event_data.description
        )
        saved_event = repo.save(event)
        return EventResponse(**saved_event.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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