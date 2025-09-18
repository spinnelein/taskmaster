# Test Exception Handling for Recurring Events
# NO EMOJIS

import requests
from datetime import datetime, date, timedelta
import json

BASE_URL = "http://localhost:8000"

def test_exception_handling():
    """Test that exceptions (cancellations and modifications) work correctly"""
    
    print("=== Testing Exception Handling for Recurring Events ===\n")
    
    # 1. Get a recurring event
    print("1. Getting recurring events...")
    response = requests.get(f"{BASE_URL}/api/events")
    events = response.json()["events"]
    recurring_events = [e for e in events if e["is_recurring"]]
    
    if not recurring_events:
        print("ERROR: No recurring events found!")
        return
    
    # Use the first recurring event
    test_event = recurring_events[0]
    event_id = test_event["id"]
    print(f"   Using event: {test_event['title']} (ID: {event_id})")
    
    # 2. Get occurrences for next 7 days
    today = date.today()
    next_week = today + timedelta(days=7)
    
    print(f"\n2. Getting occurrences from {today} to {next_week}...")
    response = requests.get(
        f"{BASE_URL}/api/events/expand/{event_id}",
        params={
            "start_date": today.isoformat(),
            "end_date": next_week.isoformat(),
            "max_occurrences": 10
        }
    )
    
    if response.status_code != 200:
        print(f"ERROR: Failed to get occurrences: {response.text}")
        return
    
    expansion_data = response.json()
    occurrences = expansion_data["occurrences"]
    print(f"   Found {len(occurrences)} occurrences")
    
    if len(occurrences) < 2:
        print("ERROR: Need at least 2 occurrences to test exceptions")
        return
    
    # 3. Create a cancellation exception for the first occurrence
    first_occurrence_date = occurrences[0]["occurrence_date"]
    print(f"\n3. Creating cancellation exception for {first_occurrence_date}...")
    
    # First, we need to add the exception to the database
    # Since we don't have an API endpoint for this yet, let's add it directly
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.data.repositories.event_exception_repo import EventExceptionRepository
    
    engine = create_engine("sqlite:///taskmaster.db")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        exception_repo = EventExceptionRepository(db)
        exception = exception_repo.create_cancellation_exception(
            master_event_id=event_id,
            occurrence_date=datetime.fromisoformat(first_occurrence_date).date()
        )
        print(f"   Created cancellation exception ID: {exception.id}")
    except Exception as e:
        print(f"   ERROR creating exception: {e}")
    finally:
        db.close()
    
    # 4. Create a modification exception for the second occurrence
    if len(occurrences) >= 2:
        second_occurrence = occurrences[1]
        second_occurrence_date = second_occurrence["occurrence_date"]
        original_start = datetime.fromisoformat(second_occurrence["start"])
        new_start = original_start + timedelta(hours=2)  # Move 2 hours later
        new_end = new_start + timedelta(hours=1)
        
        print(f"\n4. Creating modification exception for {second_occurrence_date}...")
        print(f"   Original time: {original_start.strftime('%H:%M')}")
        print(f"   New time: {new_start.strftime('%H:%M')}")
        
        db = SessionLocal()
        try:
            exception_repo = EventExceptionRepository(db)
            exception = exception_repo.create_modification_exception(
                master_event_id=event_id,
                occurrence_date=datetime.fromisoformat(second_occurrence_date).date(),
                new_start=new_start,
                new_end=new_end,
                custom_title=f"{test_event['title']} (Rescheduled)"
            )
            print(f"   Created modification exception ID: {exception.id}")
        except Exception as e:
            print(f"   ERROR creating exception: {e}")
        finally:
            db.close()
    
    # 5. Get occurrences again and verify exceptions are applied
    print(f"\n5. Getting occurrences again to verify exceptions...")
    response = requests.get(
        f"{BASE_URL}/api/events/expand/{event_id}",
        params={
            "start_date": today.isoformat(),
            "end_date": next_week.isoformat(),
            "max_occurrences": 10
        }
    )
    
    if response.status_code != 200:
        print(f"ERROR: Failed to get occurrences: {response.text}")
        return
    
    new_expansion_data = response.json()
    new_occurrences = new_expansion_data["occurrences"]
    
    print(f"   Found {len(new_occurrences)} occurrences (was {len(occurrences)})")
    
    # Check if first occurrence is cancelled (should be missing)
    first_dates = [occ["occurrence_date"] for occ in new_occurrences]
    if first_occurrence_date not in first_dates:
        print(f"   SUCCESS: Cancelled occurrence {first_occurrence_date} is not in results")
    else:
        print(f"   ERROR: Cancelled occurrence {first_occurrence_date} still appears")
    
    # Check if second occurrence is modified
    if len(occurrences) >= 2:
        modified_occ = next((occ for occ in new_occurrences 
                           if occ["occurrence_date"] == second_occurrence_date), None)
        if modified_occ:
            if "(Rescheduled)" in modified_occ["title"]:
                print(f"   SUCCESS: Modified occurrence has updated title: {modified_occ['title']}")
            else:
                print(f"   ERROR: Modified occurrence title not updated: {modified_occ['title']}")
            
            if modified_occ["is_exception"]:
                print(f"   SUCCESS: Modified occurrence is marked as exception")
            else:
                print(f"   ERROR: Modified occurrence not marked as exception")
    
    print("\n=== Exception Handling Test Complete ===")


if __name__ == "__main__":
    # Add parent directory to path so imports work
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    test_exception_handling()