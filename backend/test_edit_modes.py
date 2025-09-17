# Test Edit Modes for Recurring Events
# NO EMOJIS

import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000"

def test_edit_modes():
    """Test different edit modes for recurring events"""
    
    print("=== Testing Edit Modes for Recurring Events ===\n")
    
    # 1. Get a different recurring event (not the one with exceptions)
    print("1. Getting recurring events...")
    response = requests.get(f"{BASE_URL}/api/events")
    events = response.json()["events"]
    
    # Find Breakfast event
    breakfast_event = next((e for e in events if e["title"] == "Breakfast/Get Ready"), None)
    
    if not breakfast_event:
        print("ERROR: Breakfast event not found!")
        return
    
    event_id = breakfast_event["id"]
    print(f"   Using event: {breakfast_event['title']} (ID: {event_id})")
    
    # 2. Test THIS_ONLY edit mode
    print("\n2. Testing THIS_ONLY edit mode...")
    print("   Updating title for occurrence on 2025-09-20 only")
    
    update_data = {
        "edit_mode": "this_only",
        "original_date": "2025-09-20T00:00:00",
        "event_data": {
            "title": "Late Breakfast (Special Day)",
            "start_time": "2025-09-20T09:00:00",
            "end_time": "2025-09-20T09:40:00"
        }
    }
    
    response = requests.put(
        f"{BASE_URL}/api/events/{event_id}/recurring",
        json=update_data
    )
    
    if response.status_code == 200:
        print("   SUCCESS: THIS_ONLY update completed")
        # Check the expansion to verify
        exp_response = requests.get(
            f"{BASE_URL}/api/events/expand/{event_id}",
            params={
                "start_date": "2025-09-19",
                "end_date": "2025-09-21",
                "max_occurrences": 5
            }
        )
        if exp_response.status_code == 200:
            occurrences = exp_response.json()["occurrences"]
            for occ in occurrences:
                if occ["occurrence_date"] == "2025-09-20":
                    print(f"   Verified: {occ['occurrence_date']} shows '{occ['title']}'")
    else:
        print(f"   ERROR: {response.status_code} - {response.text}")
    
    # 3. Test ALL_IN_SERIES edit mode
    print("\n3. Testing ALL_IN_SERIES edit mode...")
    print("   Updating description for all occurrences")
    
    update_data = {
        "edit_mode": "all_in_series",
        "event_data": {
            "description": "Updated breakfast routine - now includes meditation"
        }
    }
    
    response = requests.put(
        f"{BASE_URL}/api/events/{event_id}/recurring",
        json=update_data
    )
    
    if response.status_code == 200:
        print("   SUCCESS: ALL_IN_SERIES update completed")
        # Verify the master event was updated
        event_response = requests.get(f"{BASE_URL}/api/events/{event_id}")
        if event_response.status_code == 200:
            updated_event = event_response.json()
            print(f"   Verified: Description is now '{updated_event['description']}'")
    else:
        print(f"   ERROR: {response.status_code} - {response.text}")
    
    # 4. Test THIS_AND_FUTURE edit mode
    print("\n4. Testing THIS_AND_FUTURE edit mode...")
    print("   Creating new series starting from 2025-09-25")
    
    # Find a different event for this test
    chore_event = next((e for e in events if e["title"] == "Chore Time"), None)
    
    if chore_event:
        update_data = {
            "edit_mode": "this_and_future",
            "original_date": "2025-09-25T00:00:00",
            "event_data": {
                "title": "Extended Chore Time",
                "end_time": "2025-09-25T19:00:00"  # Extended by 15 minutes
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/events/{chore_event['id']}/recurring",
            json=update_data
        )
        
        if response.status_code == 200:
            print("   SUCCESS: THIS_AND_FUTURE update completed")
            result = response.json()
            if len(result) > 1:
                print(f"   Created {len(result)} events (original series + new series)")
        else:
            print(f"   ERROR: {response.status_code} - {response.text}")
    
    # 5. Test delete modes
    print("\n5. Testing delete modes...")
    
    # Create a test event first
    test_event_data = {
        "title": "Test Event for Deletion",
        "start_time": "2025-09-16T10:00:00",
        "end_time": "2025-09-16T11:00:00",
        "is_recurring": True,
        "recurrence_pattern": {
            "pattern": "daily",
            "interval": 1,
            "end_type": "count",
            "end_after_count": 5
        }
    }
    
    create_response = requests.post(f"{BASE_URL}/api/events", json=test_event_data)
    
    if create_response.status_code == 200:
        test_event = create_response.json()
        test_id = test_event["id"]
        print(f"   Created test event: {test_id}")
        
        # Test THIS_ONLY deletion
        delete_data = {
            "edit_mode": "this_only",
            "original_date": "2025-09-17T00:00:00"
        }
        
        delete_response = requests.delete(
            f"{BASE_URL}/api/events/{test_id}/recurring",
            json=delete_data
        )
        
        if delete_response.status_code == 200:
            print("   SUCCESS: THIS_ONLY deletion completed")
        else:
            print(f"   ERROR deleting: {delete_response.status_code}")
    
    print("\n=== Edit Modes Test Complete ===")


if __name__ == "__main__":
    test_edit_modes()