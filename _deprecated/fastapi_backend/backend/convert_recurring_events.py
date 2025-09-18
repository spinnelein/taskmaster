#!/usr/bin/env python3
"""
Convert individual recurring event instances to master/instance architecture
NO EMOJIS
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Configuration
DB_PATH = Path(__file__).parent / "taskmaster.db"

def analyze_recurring_patterns():
    """Analyze events to identify recurring patterns"""
    print("Analyzing recurring event patterns...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find events that occur multiple times with same title
    cursor.execute("""
        SELECT 
            title,
            COUNT(*) as count,
            MIN(start_time) as first_occurrence,
            MAX(start_time) as last_occurrence,
            MIN(datetime(start_time)) as first_dt,
            MAX(datetime(start_time)) as last_dt
        FROM events 
        WHERE title IN (
            SELECT title FROM events GROUP BY title HAVING COUNT(*) > 3
        )
        GROUP BY title 
        ORDER BY count DESC
    """)
    
    patterns = []
    for row in cursor.fetchall():
        title, count, first_time, last_time, first_dt, last_dt = row
        
        # Calculate if it looks like a daily pattern
        try:
            first = datetime.fromisoformat(first_dt.replace(' ', 'T'))
            last = datetime.fromisoformat(last_dt.replace(' ', 'T'))
            total_days = (last - first).days + 1
            
            # If count is close to total days, it's likely daily
            if count >= total_days * 0.8:  # Allow for some missing days
                patterns.append({
                    'title': title,
                    'count': count,
                    'first_time': first_time,
                    'pattern': 'daily',
                    'interval': 1
                })
                print(f"  - {title}: {count} events (daily pattern)")
        except:
            print(f"  - {title}: {count} events (unknown pattern)")
    
    conn.close()
    return patterns

def get_event_details(title):
    """Get details of the first event with this title"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, start_time, end_time, is_blocking, location, description,
               event_type, status, allows_multitasking, buffer_before_minutes,
               buffer_after_minutes, priority, is_moveable, min_notice_hours,
               project_id, attendees, required_resources, reminder_minutes_before,
               notifications_enabled, created_at, updated_at
        FROM events 
        WHERE title = ? 
        ORDER BY datetime(start_time) ASC 
        LIMIT 1
    """, (title,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        columns = ['id', 'title', 'start_time', 'end_time', 'is_blocking', 'location', 
                  'description', 'event_type', 'status', 'allows_multitasking', 
                  'buffer_before_minutes', 'buffer_after_minutes', 'priority', 
                  'is_moveable', 'min_notice_hours', 'project_id', 'attendees', 
                  'required_resources', 'reminder_minutes_before', 'notifications_enabled',
                  'created_at', 'updated_at']
        return dict(zip(columns, row))
    return None

def create_master_event(event_details, pattern_info):
    """Create a master event for the recurring series"""
    master_id = str(uuid.uuid4())
    
    # Create recurrence pattern JSON
    recurrence_pattern = {
        "pattern": pattern_info['pattern'],
        "interval": pattern_info['interval'],
        "weekdays": [],
        "end_type": "never",
        "end_after_count": None,
        "end_date": None
    }
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert master event
    cursor.execute("""
        INSERT INTO events (
            id, title, start_time, end_time, is_blocking, location, description,
            event_type, status, allows_multitasking, buffer_before_minutes,
            buffer_after_minutes, priority, is_moveable, min_notice_hours,
            is_recurring, recurrence_pattern, is_recurrence_master,
            project_id, attendees, required_resources, reminder_minutes_before,
            notifications_enabled, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        master_id, event_details['title'], event_details['start_time'], 
        event_details['end_time'], event_details['is_blocking'],
        event_details['location'], event_details['description'],
        event_details['event_type'], event_details['status'],
        event_details['allows_multitasking'], event_details['buffer_before_minutes'],
        event_details['buffer_after_minutes'], event_details['priority'],
        event_details['is_moveable'], event_details['min_notice_hours'],
        True, json.dumps(recurrence_pattern), True,  # is_recurring, pattern, is_master
        event_details['project_id'], event_details['attendees'],
        event_details['required_resources'], event_details['reminder_minutes_before'],
        event_details['notifications_enabled'], event_details['created_at'],
        event_details['updated_at']
    ))
    
    conn.commit()
    conn.close()
    
    print(f"  Created master event: {master_id} for '{event_details['title']}'")
    return master_id

def delete_individual_instances(title):
    """Delete all individual instances of a recurring event"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Count before deletion
    cursor.execute("SELECT COUNT(*) FROM events WHERE title = ?", (title,))
    count_before = cursor.fetchone()[0]
    
    # Delete all instances
    cursor.execute("DELETE FROM events WHERE title = ? AND (is_recurrence_master IS NULL OR is_recurrence_master = 0)", (title,))
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"  Deleted {deleted} individual instances of '{title}'")
    return deleted

def convert_recurring_events():
    """Convert recurring events to master/instance architecture"""
    print("Converting recurring events to master/instance pattern...")
    print("="*60)
    
    # Analyze patterns
    patterns = analyze_recurring_patterns()
    
    total_deleted = 0
    total_masters = 0
    
    print(f"\nFound {len(patterns)} recurring patterns to convert:")
    print("="*60)
    
    # Process each pattern
    for pattern_info in patterns:
        title = pattern_info['title']
        count = pattern_info['count']
        
        print(f"\nProcessing: {title} ({count} instances)")
        
        # Get event details from first occurrence
        event_details = get_event_details(title)
        if not event_details:
            print(f"  ERROR: Could not find event details for {title}")
            continue
        
        # Create master event
        master_id = create_master_event(event_details, pattern_info)
        total_masters += 1
        
        # Delete individual instances
        deleted = delete_individual_instances(title)
        total_deleted += deleted
    
    print("\n" + "="*60)
    print("CONVERSION COMPLETE")
    print("="*60)
    print(f"Created {total_masters} master events")
    print(f"Deleted {total_deleted} individual instances")
    
    # Verify final count
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM events")
    final_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events WHERE is_recurrence_master = 1")
    master_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"Final event count: {final_count} (including {master_count} masters)")

if __name__ == "__main__":
    convert_recurring_events()