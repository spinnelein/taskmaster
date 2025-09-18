# Test expansion with exceptions applied
# NO EMOJIS

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date, timedelta
from dateutil.rrule import rrulestr
from src.data.database import SessionLocal
from src.data.repositories.event_repo import EventRepository
from src.data.repositories.event_exception_repo import EventExceptionRepository

def test_expansion_with_exceptions():
    """Test the expansion logic with exceptions applied"""
    
    db = SessionLocal()
    try:
        # Get the event
        event_repo = EventRepository(db)
        event = event_repo.get("d77aaa83-2dcf-4097-a6d3-d04f2571d54e")
        
        if not event:
            print("ERROR: Event not found")
            return
            
        print(f"Event: {event.title}")
        print(f"RRULE: {event.recurrence_rrule}")
        
        # Get exceptions
        exception_repo = EventExceptionRepository(db)
        start_date = date(2025, 9, 15)
        end_date = date(2025, 9, 18)
        
        exceptions = exception_repo.get_exceptions_for_event(event.id, start_date, end_date)
        print(f"\nFound {len(exceptions)} exceptions:")
        for ex in exceptions:
            print(f"  - {ex.occurrence_date}: cancelled={ex.is_cancelled}, rescheduled={ex.is_rescheduled}")
        
        # Create exception lookup
        exceptions_by_date = {ex.occurrence_date: ex for ex in exceptions}
        
        # Expand with RRULE
        if event.recurrence_rrule:
            dtstart = event.dtstart or event.start_time
            dtend = event.dtend or event.end_time
            
            if dtstart and dtend:
                # Parse RRULE
                rrule_obj = rrulestr(event.recurrence_rrule, dtstart=dtstart)
                
                # Calculate duration
                duration = dtend - dtstart
                
                print(f"\nExpanding from {start_date} to {end_date}:")
                occurrences = []
                
                for occurrence_start in rrule_obj:
                    occurrence_date = occurrence_start.date()
                    
                    if occurrence_date > end_date:
                        break
                        
                    if occurrence_date >= start_date:
                        # Check for exceptions
                        exception = exceptions_by_date.get(occurrence_date)
                        
                        if exception and exception.is_cancelled:
                            print(f"  - {occurrence_date}: SKIPPED (cancelled)")
                            continue
                        
                        occurrence_end = occurrence_start + duration
                        title = event.title
                        is_exception = False
                        
                        # Apply modifications
                        if exception:
                            is_exception = True
                            if exception.new_start:
                                occurrence_start = exception.new_start
                            if exception.new_end:
                                occurrence_end = exception.new_end
                            if exception.custom_title:
                                title = exception.custom_title
                        
                        occurrences.append({
                            'date': occurrence_date,
                            'title': title,
                            'start': occurrence_start,
                            'end': occurrence_end,
                            'is_exception': is_exception
                        })
                        
                        status = "(modified)" if is_exception else ""
                        print(f"  - {occurrence_date}: {title} at {occurrence_start.strftime('%H:%M')} {status}")
                
                print(f"\nTotal occurrences: {len(occurrences)} (after applying exceptions)")
                
                # Verify the results
                expected_count = 3  # Should be 3 after skipping the cancelled one
                if len(occurrences) == expected_count:
                    print("SUCCESS: Correct number of occurrences after cancellation")
                else:
                    print(f"ERROR: Expected {expected_count} occurrences, got {len(occurrences)}")
                    
                # Check if modification was applied
                modified = [occ for occ in occurrences if occ['is_exception']]
                if modified:
                    print(f"SUCCESS: Found {len(modified)} modified occurrences")
                    for mod in modified:
                        print(f"  - {mod['date']}: {mod['title']}")
                
    finally:
        db.close()


if __name__ == "__main__":
    test_expansion_with_exceptions()