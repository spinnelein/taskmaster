#!/usr/bin/env python3
"""
Quick test to check events in database
"""
import sqlite3
import json
from pathlib import Path

def test_events():
    """Test events in the database"""
    db_path = Path("backend/taskmaster.db")
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if events table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
        if not cursor.fetchone():
            print("Events table does not exist")
            return
        
        # Count total events
        cursor.execute("SELECT COUNT(*) FROM events")
        total_count = cursor.fetchone()[0]
        print(f"Total events in database: {total_count}")
        
        # Get column info
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        print(f"Events table has {len(columns)} columns")
        
        # Show first few events
        cursor.execute("SELECT id, title, start_time, is_recurrence_master, recurrence_master_id FROM events LIMIT 10")
        events = cursor.fetchall()
        
        print(f"\nFirst {len(events)} events:")
        for event in events:
            print(f"  ID: {event[0][:8]}... | Title: {event[1]} | Start: {event[2]} | Master: {event[3]} | Master ID: {event[4] or 'None'}")
        
        # Check for recurring events structure
        cursor.execute("SELECT COUNT(*) FROM events WHERE is_recurrence_master = 1")
        master_count = cursor.fetchone()[0]
        print(f"\nRecurring event masters: {master_count}")
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE recurrence_master_id IS NOT NULL")
        instance_count = cursor.fetchone()[0]
        print(f"Recurring event instances: {instance_count}")
        
        cursor.execute("SELECT COUNT(*) FROM events WHERE is_recurrence_master = 0 AND recurrence_master_id IS NULL")
        standalone_count = cursor.fetchone()[0]
        print(f"Standalone events: {standalone_count}")
        
        # Show events that should appear in the events page
        # (masters + standalone, excluding instances)
        cursor.execute("""
            SELECT id, title, start_time, is_recurrence_master 
            FROM events 
            WHERE is_recurrence_master = 1 OR recurrence_master_id IS NULL
            ORDER BY start_time DESC
            LIMIT 5
        """)
        display_events = cursor.fetchall()
        
        print(f"\nEvents that should appear on events page ({len(display_events)}):")
        for event in display_events:
            event_type = "Master" if event[3] else "Standalone"
            print(f"  {event_type}: {event[1]} | {event[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_events()