#!/usr/bin/env python3
"""
Directly restore events from backup using repository pattern
NO EMOJIS
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the backend src to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.database import SessionLocal
from src.data.repositories.event_repo import EventRepository

# Configuration
BACKUP_FILE = Path(r"C:\Users\Aaron\Documents\Python Scripts\Taskmaster\data_backup\backup_2025-09-13_01-16-58\events_backup.json")

def parse_datetime(dt_str):
    """Parse datetime string to datetime object"""
    if not dt_str:
        return None
    try:
        # Handle the format from backup: "2025-09-12 07:00:00.000000"
        return datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M:%S.%f")
    except:
        try:
            return datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M:%S")
        except:
            print(f"Warning: Could not parse datetime: {dt_str}")
            return None

def parse_recurrence_pattern(pattern_str):
    """Parse recurrence pattern JSON string"""
    if not pattern_str:
        return None
    try:
        return json.loads(pattern_str)
    except:
        print(f"Warning: Could not parse recurrence pattern: {pattern_str}")
        return None

def restore_events_directly():
    """Restore events directly to database"""
    print(f"Loading backup from: {BACKUP_FILE}")
    
    # Load backup data
    with open(BACKUP_FILE, 'r') as f:
        backup_data = json.load(f)
    
    events = backup_data.get("data", [])
    total_events = len(events)
    print(f"Found {total_events} events to restore")
    
    # Create database session
    db = SessionLocal()
    repo = EventRepository(db)
    
    try:
        # Track statistics
        restored = 0
        failed = 0
        skipped = 0
        
        # Process each event
        for i, event in enumerate(events):
            if i % 50 == 0:
                print(f"\nProcessing events {i}-{min(i+50, total_events)} of {total_events}...")
            
            # Parse datetime fields
            start_time = parse_datetime(event.get("start_time"))
            end_time = parse_datetime(event.get("end_time"))
            
            if not start_time or not end_time:
                skipped += 1
                continue
            
            # Prepare event data for repository
            event_data = {
                "id": event.get("id"),  # Preserve original ID if possible
                "title": event.get("title", "Untitled Event"),
                "start_time": start_time,
                "end_time": end_time,
                "is_blocking": bool(event.get("is_blocking", 1)),
                "location": event.get("location"),
                "description": event.get("description", ""),
                "is_recurring": bool(event.get("is_recurring", 0)),
                "recurrence_pattern": parse_recurrence_pattern(event.get("recurrence_pattern")),
                "recurrence_parent_id": event.get("recurrence_parent_id"),
                # Add timestamps if available
                "created_at": parse_datetime(event.get("created_at")) if event.get("created_at") else datetime.now(),
                "updated_at": parse_datetime(event.get("updated_at")) if event.get("updated_at") else datetime.now(),
            }
            
            # Remove None values
            event_data = {k: v for k, v in event_data.items() if v is not None}
            
            try:
                # Create event
                saved_event = repo.create(event_data)
                restored += 1
                
                # Commit every 50 events to avoid memory issues
                if restored % 50 == 0:
                    db.commit()
                    print(f"  Committed {restored} events so far...")
                    
            except Exception as e:
                db.rollback()
                print(f"\n  Error restoring event '{event.get('title')}': {str(e)}")
                failed += 1
        
        # Final commit
        db.commit()
        
        # Summary
        print("\n" + "="*50)
        print("RESTORATION COMPLETE")
        print("="*50)
        print(f"Total events in backup: {total_events}")
        print(f"Successfully restored: {restored}")
        print(f"Failed to restore: {failed}")
        print(f"Skipped (invalid data): {skipped}")
        
        # Verify restoration
        all_events = repo.get_all()
        print(f"\nEvents now in database: {len(all_events)}")
        
    finally:
        db.close()

if __name__ == "__main__":
    restore_events_directly()