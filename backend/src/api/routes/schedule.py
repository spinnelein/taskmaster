"""
Schedule API routes
NO EMOJIS
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime

from ...schemas.schedule_schemas import ScheduleResponse, TimeSlotResponse
from ...data.repositories.task_repo import TaskRepository
from ...data.repositories.event_repo import EventRepository
from ...domain.schedule import Schedule
from ..dependencies import get_db

router = APIRouter(tags=["schedule"])

@router.get("/{schedule_date}", response_model=ScheduleResponse)
def get_schedule(
    schedule_date: date,
    db: Session = Depends(get_db)
):
    """Get schedule for a specific date"""
    task_repo = TaskRepository(db)
    event_repo = EventRepository(db)
    
    # Create schedule
    schedule = Schedule(schedule_date)
    
    # Add events for the day
    events = event_repo.get_by_date(schedule_date)
    for event in events:
        schedule.add_event(event)
    
    # Get pending tasks
    pending_tasks = task_repo.get_pending()
    
    # Find free time slots (for 30 minute minimum)
    free_slots = schedule.find_free_time(30)
    
    return ScheduleResponse(
        date=schedule_date,
        events=[e.to_dict() for e in events],
        scheduled_tasks=[],  # Will be populated when scheduling is implemented
        free_slots=[
            TimeSlotResponse(
                start=slot.start,
                end=slot.end,
                duration_minutes=slot.duration_minutes
            ) for slot in free_slots
        ]
    )