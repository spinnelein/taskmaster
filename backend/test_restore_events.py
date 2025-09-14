#!/usr/bin/env python3
"""
Test restore of first 5 events from backup
NO EMOJIS
"""
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000/api"
BACKUP_FILE = Path(r"C:\Users\Aaron\Documents\Python Scripts\Taskmaster\data_backup\backup_2025-09-13_01-16-58\events_backup.json")

def parse_datetime(dt_str):
    """Parse datetime string to ISO format"""
    if not dt_str:
        return None
    try:
        dt = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M:%S.%f")
        return dt.isoformat()
    except:
        try:
            dt = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M:%S")
            return dt.isoformat()
        except:
            print(f"Warning: Could not parse datetime: {dt_str}")
            return None

def parse_recurrence_pattern(pattern_str):
    """Parse recurrence pattern JSON string"""
    if not pattern_str:
        return None
    try:
        pattern = json.loads(pattern_str)
        return {
            "pattern": pattern.get("pattern", "daily"),
            "interval": pattern.get("interval", 1),
            "weekdays": pattern.get("weekdays", []),
            "end_type": pattern.get("end_type", "never"),
            "end_after_count": pattern.get("end_after_count"),
            "end_date": pattern.get("end_date")
        }
    except:
        print(f"Warning: Could not parse recurrence pattern: {pattern_str}")
        return None

def test_restore():
    """Test restoring first 5 events"""
    print("Testing event restoration...")
    
    # Load backup data
    with open(BACKUP_FILE, 'r') as f:
        backup_data = json.load(f)
    
    events = backup_data.get("data", [])[:5]  # Only first 5 events
    print(f"Testing with {len(events)} events")
    
    for i, event in enumerate(events):
        print(f"\nEvent {i+1}:")
        print(f"  Title: {event.get('title')}")
        print(f"  Start: {event.get('start_time')}")
        print(f"  End: {event.get('end_time')}")
        print(f"  Is Recurring: {event.get('is_recurring')}")
        print(f"  Is Blocking: {event.get('is_blocking')}")
        
        # Parse datetime fields
        start_time = parse_datetime(event.get("start_time"))
        end_time = parse_datetime(event.get("end_time"))
        
        if not start_time or not end_time:
            print("  - Skipping: Invalid times")
            continue
        
        # Prepare event data
        event_data = {
            "title": event.get("title", "Untitled Event"),
            "start_time": start_time,
            "end_time": end_time,
            "is_blocking": bool(event.get("is_blocking", 1)),
            "location": event.get("location"),
            "description": event.get("description") or "",
            "is_recurring": bool(event.get("is_recurring", 0)),
        }
        
        # Add recurrence pattern if applicable
        if event_data["is_recurring"] and event.get("recurrence_pattern"):
            pattern = parse_recurrence_pattern(event["recurrence_pattern"])
            if pattern:
                event_data["recurrence_pattern"] = pattern
        
        print(f"  Sending data: {json.dumps(event_data, indent=2)}")
        
        # Send to API
        try:
            response = requests.post(
                f"{API_BASE_URL}/events/",
                json=event_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                print(f"  SUCCESS: Event created with ID {response.json().get('id')}")
            else:
                print(f"  FAILED: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ERROR: {str(e)}")
    
    # Check result
    print("\nChecking events in database...")
    response = requests.get(f"{API_BASE_URL}/events/debug_list")
    if response.status_code == 200:
        data = response.json()
        print(f"Total events now: {data.get('count', 0)}")
        for event in data.get('events', []):
            print(f"  - {event['title']} at {event['start_time']}")

if __name__ == "__main__":
    test_restore()