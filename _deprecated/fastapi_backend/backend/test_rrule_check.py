# Check if events have RRULE
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.database import SessionLocal
from src.data.repositories.event_repo import EventRepository

db = SessionLocal()
try:
    repo = EventRepository(db)
    events = repo.get_all()
    
    print(f"Found {len(events)} events")
    
    for event in events[:3]:
        print(f"\nEvent: {event.title}")
        print(f"  is_recurring: {event.is_recurring}")
        print(f"  recurrence_rrule: {getattr(event, 'recurrence_rrule', 'MISSING')}")
        print(f"  start_time: {event.start_time}")
        
finally:
    db.close()