# Test if we can import the exception repository
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.data.repositories.event_exception_repo import EventExceptionRepository
    print("SUCCESS: EventExceptionRepository imported successfully")
    
    # Test instantiation
    from src.data.database import SessionLocal
    db = SessionLocal()
    
    try:
        repo = EventExceptionRepository(db)
        print("SUCCESS: EventExceptionRepository instantiated")
        
        # Test getting exceptions
        exceptions = repo.get_exceptions_for_event("d77aaa83-2dcf-4097-a6d3-d04f2571d54e")
        print(f"Found {len(exceptions)} exceptions")
        
        for ex in exceptions:
            print(f"  - {ex.occurrence_date}: cancelled={ex.is_cancelled}")
            
    finally:
        db.close()
        
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()