#!/usr/bin/env python3
"""
Restore events from backup JSON file
NO EMOJIS
"""
import json
import requests
from datetime import datetime
from pathlib import Path
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api"
BACKUP_FILE = Path(r"C:\Users\Aaron\Documents\Python Scripts\Taskmaster\data_backup\backup_2025-09-13_01-16-58\events_backup.json")

def parse_datetime(dt_str):
    """Parse datetime string to ISO format"""
    if not dt_str:
        return None
    # Handle the format from backup: "2025-09-12 07:00:00.000000"
    try:
        dt = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M:%S.%f")
        return dt.isoformat()
    except:
        # Try without microseconds
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
        # Ensure required fields exist
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

def convert_bool(value):
    """Convert integer to boolean"""
    if value is None:
        return None
    return bool(value)

def restore_events():
    """Restore events from backup file"""
    print(f"Loading backup from: {BACKUP_FILE}")
    
    # Load backup data
    with open(BACKUP_FILE, 'r') as f:
        backup_data = json.load(f)
    
    events = backup_data.get("data", [])
    total_events = len(events)
    print(f"Found {total_events} events to restore")
    
    # Track statistics
    restored = 0
    failed = 0
    skipped = 0
    
    # Process each event
    for i, event in enumerate(events):
        print(f"\nProcessing event {i+1}/{total_events}: {event.get('title', 'Untitled')}")
        
        # Parse datetime fields
        start_time = parse_datetime(event.get("start_time"))
        end_time = parse_datetime(event.get("end_time"))
        
        if not start_time or not end_time:
            print("  - Skipping: Invalid start/end time")
            skipped += 1
            continue
        
        # Prepare event data for API
        event_data = {
            "title": event.get("title", "Untitled Event"),
            "start_time": start_time,
            "end_time": end_time,
            "is_blocking": convert_bool(event.get("is_blocking", 1)),
            "location": event.get("location"),
            "description": event.get("description", ""),
            "is_recurring": convert_bool(event.get("is_recurring", 0)),
        }
        
        # Add recurrence pattern if event is recurring
        if event_data["is_recurring"] and event.get("recurrence_pattern"):
            pattern = parse_recurrence_pattern(event["recurrence_pattern"])
            if pattern:
                event_data["recurrence_pattern"] = pattern
        
        # Send to API
        try:
            response = requests.post(
                f"{API_BASE_URL}/events/",
                json=event_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                print("  + Restored successfully")
                restored += 1
            else:
                print(f"  - Failed: {response.status_code} - {response.text}")
                failed += 1
                
        except Exception as e:
            print(f"  - Error: {str(e)}")
            failed += 1
        
        # Rate limiting - don't overwhelm the API
        if i % 10 == 0 and i > 0:
            print(f"\nProgress: {i}/{total_events} processed...")
            time.sleep(0.5)  # Small delay every 10 events
    
    # Summary
    print("\n" + "="*50)
    print("RESTORATION COMPLETE")
    print("="*50)
    print(f"Total events in backup: {total_events}")
    print(f"Successfully restored: {restored}")
    print(f"Failed to restore: {failed}")
    print(f"Skipped (invalid data): {skipped}")
    
    # Verify restoration
    try:
        response = requests.get(f"{API_BASE_URL}/events/debug_list")
        if response.status_code == 200:
            data = response.json()
            print(f"\nEvents now in database: {data.get('count', 0)}")
    except:
        print("\nCould not verify final count")

if __name__ == "__main__":
    restore_events()