# Test schedule expansion logic locally
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime
from dateutil.rrule import rrulestr
from src.data.database import SessionLocal
from src.data.repositories.event_repo import EventRepository
from src.data.repositories.event_exception_repo import EventExceptionRepository

def test_schedule_expansion():
    schedule_date = date(2025, 9, 15)
    
    db = SessionLocal()
    try:
        event_repo = EventRepository(db)
        exception_repo = EventExceptionRepository(db)
        
        all_events = event_repo.get_all()
        expanded_events = []
        
        print(f"Processing {len(all_events)} events for date {schedule_date}")
        
        for event in all_events:
            if event.is_recurring and event.recurrence_rrule:
                print(f"Expanding recurring event '{event.title}' with RRULE: {event.recurrence_rrule}")
                try:
                    dtstart = event.dtstart or event.start_time
                    dtend = event.dtend or event.end_time
                    
                    print(f"  dtstart: {dtstart}, dtend: {dtend}")
                    
                    if dtstart and dtend:
                        # Parse RRULE
                        rrule_obj = rrulestr(event.recurrence_rrule, dtstart=dtstart)
                        
                        # Calculate event duration
                        duration = dtend - dtstart
                        
                        print(f"  Checking occurrences for {schedule_date}...")
                        
                        # Check if this event occurs on the schedule date
                        count = 0
                        for occurrence_start in rrule_obj:
                            occurrence_date = occurrence_start.date()
                            count += 1
                            
                            print(f"    Occurrence {count}: {occurrence_date}")
                            
                            if count > 10:  # Safety limit for debugging
                                print("    Reached safety limit")
                                break
                            
                            if occurrence_date > schedule_date:
                                print(f"    {occurrence_date} > {schedule_date}, breaking")
                                break
                                
                            if occurrence_date == schedule_date:
                                print(f"    MATCH! Event occurs on {occurrence_date}")
                                
                                # Check for exceptions
                                exception = exception_repo.get_exception_by_date(
                                    event.id, 
                                    occurrence_date
                                )
                                
                                if exception and exception.is_cancelled:
                                    print(f"    Skipped - cancelled exception")
                                    break
                                
                                # Create event occurrence
                                occurrence_end = occurrence_start + duration
                                
                                # Apply modifications from exception
                                if exception:
                                    if exception.new_start:
                                        occurrence_start = exception.new_start
                                    if exception.new_end:
                                        occurrence_end = exception.new_end
                                
                                event_dict = {
                                    'id': f"{event.id}_{occurrence_date.isoformat()}",
                                    'title': exception.custom_title if exception and exception.custom_title else event.title,
                                    'start_time': occurrence_start,
                                    'end_time': occurrence_end,
                                    'is_blocking': event.is_blocking
                                }
                                
                                expanded_events.append(event_dict)
                                print(f"    Added occurrence: {event_dict['title']} at {occurrence_start}")
                                break
                                
                except Exception as e:
                    print(f"Error expanding recurring event {event.id}: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # Non-recurring event
                if event.start_time.date() == schedule_date:
                    print(f"Adding non-recurring event: {event.title}")
                    expanded_events.append({
                        'id': event.id,
                        'title': event.title,
                        'start_time': event.start_time,
                        'end_time': event.end_time,
                        'is_blocking': event.is_blocking
                    })
        
        print(f"\nFinal result: {len(expanded_events)} events for {schedule_date}")
        for event in expanded_events:
            print(f"  - {event['title']} at {event['start_time']}")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_schedule_expansion()