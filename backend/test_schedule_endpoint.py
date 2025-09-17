# Test schedule endpoint
import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

# Test today's schedule
today = date.today()
print(f"Testing schedule for {today}...")

response = requests.get(f"{BASE_URL}/api/schedule/{today}")

if response.status_code == 200:
    data = response.json()
    print(f"Events found: {len(data['events'])}")
    print(f"Free slots: {len(data['free_slots'])}")
    
    if data['events']:
        print("\nEvents:")
        for event in data['events']:
            print(f"  - {event['title']} at {event['start_time']}")
    else:
        print("\nNo events found")
        
    # Let's also check what events exist
        print("\nChecking master events...")
        events_response = requests.get(f"{BASE_URL}/api/events")
        if events_response.status_code == 200:
            events_data = events_response.json()
            print(f"Total master events: {events_data['total']}")
            for event in events_data['events'][:3]:
                print(f"  - {event['title']}: recurring={event['is_recurring']}, start={event['start_time']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)