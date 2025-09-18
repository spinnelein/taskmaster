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
from ...data.repositories.event_exception_repo import EventExceptionRepository
from ...domain.schedule import Schedule
from ..dependencies import get_db
from dateutil.rrule import rrulestr

router = APIRouter(tags=["schedule"])

@router.get("/{schedule_date}", response_model=ScheduleResponse)
def get_schedule(
    schedule_date: date,
    db: Session = Depends(get_db)
):
    """Get schedule for a specific date with runtime expansion of recurring events"""
    task_repo = TaskRepository(db)
    event_repo = EventRepository(db)
    exception_repo = EventExceptionRepository(db)
    
    # Create schedule
    schedule = Schedule(schedule_date)
    
    # Get all master events (including recurring)
    all_events = event_repo.get_all()
    expanded_events = []
    
    print(f"DEBUG: Processing {len(all_events)} events for date {schedule_date}")
    
    for event in all_events:
        if event.is_recurring and event.recurrence_rrule:
            # Expand recurring event for this specific date
            print(f"DEBUG: Expanding recurring event '{event.title}' with RRULE: {event.recurrence_rrule}")
            try:
                dtstart = event.dtstart or event.start_time
                dtend = event.dtend or event.end_time
                
                if dtstart and dtend:
                    # Parse RRULE
                    rrule_obj = rrulestr(event.recurrence_rrule, dtstart=dtstart)
                    
                    # Calculate event duration
                    duration = dtend - dtstart
                    
                    # Check if this event occurs on the schedule date
                    for occurrence_start in rrule_obj:
                        occurrence_date = occurrence_start.date()
                        
                        if occurrence_date > schedule_date:
                            break
                            
                        if occurrence_date == schedule_date:
                            # Check for exceptions
                            exception = exception_repo.get_exception_by_date(
                                event.id, 
                                occurrence_date
                            )
                            
                            if exception and exception.is_cancelled:
                                # Skip cancelled occurrences
                                break
                            
                            # Create event occurrence
                            occurrence_end = occurrence_start + duration
                            
                            # Apply modifications from exception
                            if exception:
                                if exception.new_start:
                                    occurrence_start = exception.new_start
                                if exception.new_end:
                                    occurrence_end = exception.new_end
                            
                            # Create a dictionary representation for the schedule
                            event_dict = event.to_dict()
                            event_dict['start_time'] = occurrence_start
                            event_dict['end_time'] = occurrence_end
                            event_dict['id'] = f"{event.id}_{occurrence_date.isoformat()}"
                            
                            if exception and exception.custom_title:
                                event_dict['title'] = exception.custom_title
                            
                            # Create a temporary event-like object for the schedule
                            class TempEvent:
                                def __init__(self, data):
                                    for k, v in data.items():
                                        setattr(self, k, v)
                                
                                def to_dict(self):
                                    return {k: v for k, v in self.__dict__.items() 
                                           if not k.startswith('_')}
                            
                            expanded_events.append(TempEvent(event_dict))
                            print(f"DEBUG: Added occurrence for {event.title} on {occurrence_date}")
                            break
                            
            except Exception as e:
                print(f"Error expanding recurring event {event.id}: {e}")
                # Fallback: check if the master event itself is on this date
                if event.start_time.date() == schedule_date:
                    expanded_events.append(event)
        else:
            # Non-recurring event - check if it's on this date
            if event.start_time.date() == schedule_date:
                expanded_events.append(event)
    
    # Add all expanded events to schedule
    for event in expanded_events:
        schedule.add_event(event)
    
    # Get pending tasks
    pending_tasks = task_repo.get_pending()
    
    # Find free time slots (for 30 minute minimum)
    free_slots = schedule.find_free_time(30)
    
    return ScheduleResponse(
        date=schedule_date,
        events=[e.to_dict() for e in expanded_events],
        scheduled_tasks=[],  # Will be populated when scheduling is implemented
        free_slots=[
            TimeSlotResponse(
                start=slot.start,
                end=slot.end,
                duration_minutes=slot.duration_minutes
            ) for slot in free_slots
        ]
    )