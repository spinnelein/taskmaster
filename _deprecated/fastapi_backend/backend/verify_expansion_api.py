# Verify expansion API is working
import requests
import json

BASE_URL = "http://localhost:8000"

def test_expansion_api():
    """Test the expansion API endpoint"""
    
    print("Testing expansion API endpoint...")
    
    # Get a recurring event ID
    events_response = requests.get(f"{BASE_URL}/api/events")
    if events_response.status_code != 200:
        print(f"ERROR: Failed to get events: {events_response.status_code}")
        return
        
    events_data = events_response.json()
    recurring_events = [e for e in events_data["events"] if e["is_recurring"]]
    
    if not recurring_events:
        print("ERROR: No recurring events found")
        return
        
    event_id = recurring_events[0]["id"]
    event_title = recurring_events[0]["title"]
    print(f"Testing with event: {event_title} (ID: {event_id})")
    
    # Test expansion endpoint
    expansion_url = f"{BASE_URL}/api/events/expand/{event_id}"
    params = {
        "start_date": "2025-09-15",
        "end_date": "2025-09-17",
        "max_occurrences": 5
    }
    
    print(f"Calling: {expansion_url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(expansion_url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Found {data['total_occurrences']} occurrences")
            
            for i, occ in enumerate(data["occurrences"][:3], 1):
                print(f"  {i}. {occ['title']} on {occ['occurrence_date']} at {occ['start']}")
                
            print(f"RRULE available: {data['rrule_available']}")
            
        elif response.status_code == 404:
            print("ERROR: 404 - Expansion endpoint not found")
            print("This suggests the API changes haven't been loaded")
            
        else:
            print(f"ERROR: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"REQUEST ERROR: {e}")

if __name__ == "__main__":
    test_expansion_api()