#!/usr/bin/env python3
"""
Simple test to check events and restore one
NO EMOJIS
"""
import json
from datetime import datetime
from pathlib import Path

# Direct database access
import sqlite3

# Configuration
DB_PATH = Path(__file__).parent / "taskmaster.db"
BACKUP_FILE = Path(r"C:\Users\Aaron\Documents\Python Scripts\Taskmaster\data_backup\backup_2025-09-13_01-16-58\events_backup.json")

def check_events():
    """Check current events in database"""
    print(f"Checking database: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if events table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    if not cursor.fetchone():
        print("ERROR: Events table does not exist!")
        return
    
    # Count events
    cursor.execute("SELECT COUNT(*) FROM events")
    count = cursor.fetchone()[0]
    print(f"Current events in database: {count}")
    
    # Show first few events if any
    if count > 0:
        cursor.execute("SELECT id, title, start_time FROM events LIMIT 5")
        print("\nFirst few events:")
        for row in cursor.fetchall():
            print(f"  - {row[1]} at {row[2]}")
    
    conn.close()
    return count

def restore_one_event():
    """Restore just one event as a test"""
    print("\nRestoring one event from backup...")
    
    # Load backup
    with open(BACKUP_FILE, 'r') as f:
        backup_data = json.load(f)
    
    events = backup_data.get("data", [])
    if not events:
        print("No events in backup!")
        return
    
    # Take first event
    event = events[0]
    print(f"\nRestoring event: {event.get('title')}")
    print(f"  Start: {event.get('start_time')}")
    print(f"  End: {event.get('end_time')}")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Insert event - use basic fields only
        cursor.execute("""
            INSERT INTO events (
                id, title, start_time, end_time, is_blocking, 
                location, description, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get('id'),
            event.get('title', 'Untitled'),
            event.get('start_time'),
            event.get('end_time'),
            event.get('is_blocking', 1),
            event.get('location'),
            event.get('description', ''),
            event.get('created_at', datetime.now().isoformat()),
            event.get('updated_at', datetime.now().isoformat())
        ))
        
        conn.commit()
        print("Event restored successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    count = check_events()
    if count == 0:
        restore_one_event()
        print("\nRechecking events...")
        check_events()
    else:
        print("\nEvents already exist, skipping restore")