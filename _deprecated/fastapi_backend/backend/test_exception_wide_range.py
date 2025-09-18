# Test with a wider date range
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.database import SessionLocal
from src.data.repositories.event_exception_repo import EventExceptionRepository
from datetime import date

db = SessionLocal()
try:
    repo = EventExceptionRepository(db)
    
    # Get ALL exceptions for the event
    all_exceptions = repo.get_exceptions_for_event("d77aaa83-2dcf-4097-a6d3-d04f2571d54e")
    print(f"All exceptions: {len(all_exceptions)}")
    for ex in all_exceptions:
        print(f"  - {ex.occurrence_date}")
    
    # Get exceptions with date range
    start = date(2025, 9, 15)
    end = date(2025, 9, 18)
    
    range_exceptions = repo.get_exceptions_for_event(
        "d77aaa83-2dcf-4097-a6d3-d04f2571d54e",
        start_date=start,
        end_date=end
    )
    print(f"\nExceptions in range {start} to {end}: {len(range_exceptions)}")
    for ex in range_exceptions:
        print(f"  - {ex.occurrence_date}")
        
finally:
    db.close()