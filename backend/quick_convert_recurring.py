#!/usr/bin/env python3
"""
Quick conversion of recurring events using direct SQL
NO EMOJIS
"""
import sqlite3
import uuid
import json
from pathlib import Path

# Configuration
DB_PATH = Path(__file__).parent / "taskmaster.db"

def quick_convert():
    """Quickly convert recurring events using SQL"""
    print("Quick conversion of recurring events...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get recurring patterns
    recurring_events = [
        ("Wake Up", "daily", 1),
        ("Breakfast/Get Ready", "daily", 1), 
        ("Take Kids to School", "daily", 1)
    ]
    
    total_deleted = 0
    
    for title, pattern, interval in recurring_events:
        print(f"\nProcessing: {title}")
        
        # Count current instances
        cursor.execute("SELECT COUNT(*) FROM events WHERE title = ?", (title,))
        count = cursor.fetchone()[0]
        print(f"  Found {count} instances")
        
        if count <= 1:
            continue
        
        # Get details from first event
        cursor.execute("""
            SELECT start_time, end_time, is_blocking, location, description,
                   notifications_enabled, created_at, updated_at
            FROM events 
            WHERE title = ? 
            ORDER BY datetime(start_time) ASC 
            LIMIT 1
        """, (title,))
        
        row = cursor.fetchone()
        if not row:
            continue
            
        start_time, end_time, is_blocking, location, description, notifications_enabled, created_at, updated_at = row
        
        # Create master event
        master_id = str(uuid.uuid4())
        recurrence_pattern = json.dumps({
            "pattern": pattern,
            "interval": interval,
            "weekdays": [],
            "end_type": "never"
        })
        
        cursor.execute("""
            INSERT INTO events (
                id, title, start_time, end_time, is_blocking, location, description,
                is_recurring, recurrence_pattern, is_recurrence_master,
                notifications_enabled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 1, ?, ?, ?)
        """, (
            master_id, title, start_time, end_time, is_blocking or True,
            location, description or "", recurrence_pattern,
            notifications_enabled, created_at, updated_at
        ))
        
        print(f"  Created master: {master_id}")
        
        # Delete all instances
        cursor.execute("DELETE FROM events WHERE title = ? AND id != ?", (title, master_id))
        deleted = cursor.rowcount
        total_deleted += deleted
        print(f"  Deleted {deleted} instances")
    
    conn.commit()
    conn.close()
    
    print(f"\nTotal deleted: {total_deleted} instances")
    print("Conversion complete!")

if __name__ == "__main__":
    quick_convert()