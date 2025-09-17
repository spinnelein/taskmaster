# Simple test of event update
import requests
import json

BASE_URL = "http://localhost:8000"

# Get an event
response = requests.get(f"{BASE_URL}/api/events")
events = response.json()["events"]

if events:
    event = events[0]
    event_id = event["id"]
    print(f"Testing with event: {event['title']} (ID: {event_id})")
    
    # Try regular update
    update_data = {
        "description": "Test update"
    }
    
    response = requests.put(f"{BASE_URL}/api/events/{event_id}", json=update_data)
    print(f"Regular update: {response.status_code}")
    if response.status_code != 200:
        print(response.text)
    
    # Check recurring info endpoint
    response = requests.get(f"{BASE_URL}/api/events/{event_id}/recurring-info")
    print(f"Recurring info: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))