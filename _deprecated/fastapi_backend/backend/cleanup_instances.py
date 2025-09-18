#!/usr/bin/env python3
"""
Cleanup script to remove pre-generated recurring event instances
and migrate JSON patterns to RRULE format.

This script implements the transition from pre-generation to runtime expansion.
NO EMOJIS
"""
import sys
import os
import sqlite3
from datetime import datetime

def cleanup_recurring_instances():
    """
    Remove pre-generated recurring event instances, keeping only master events.
    """
    print("Starting cleanup of pre-generated recurring event instances...")
    
    try:
        # Connect to database
        conn = sqlite3.connect('taskmaster.db')
        cursor = conn.cursor()
        
        # Get count of instance events (have recurrence_master_id but are not masters themselves)
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE recurrence_master_id IS NOT NULL 
            AND is_recurrence_master = 0
        """)
        instance_count = cursor.fetchone()[0]
        
        print(f"Found {instance_count} pre-generated instance events to remove")
        
        if instance_count > 0:
            # Delete instance events
            cursor.execute("""
                DELETE FROM events 
                WHERE recurrence_master_id IS NOT NULL 
                AND is_recurrence_master = 0
            """)
            
            print(f"Deleted {cursor.rowcount} instance events")
        
        # Migrate JSON patterns to RRULE format
        print("\nMigrating JSON patterns to RRULE format...")
        
        # Get all master events with JSON patterns but no RRULE
        cursor.execute("""
            SELECT id, title, start_time, recurrence_pattern 
            FROM events 
            WHERE is_recurring = 1 
            AND recurrence_pattern IS NOT NULL
            AND (recurrence_rrule IS NULL OR recurrence_rrule = '')
        """)
        
        events_to_migrate = cursor.fetchall()
        print(f"Found {len(events_to_migrate)} events to migrate")
        
        migrated_count = 0
        for event_id, title, start_time, pattern_json in events_to_migrate:
            try:
                # Simple JSON to RRULE conversion
                import json
                pattern = json.loads(pattern_json) if pattern_json else {}
                
                # Convert to basic RRULE
                freq = pattern.get('pattern', 'daily').upper()
                interval = pattern.get('interval', 1)
                
                rrule_parts = [f"FREQ={freq}"]
                if interval > 1:
                    rrule_parts.append(f"INTERVAL={interval}")
                
                # Handle end conditions
                end_type = pattern.get('end_type', 'never')
                if end_type == 'after' and pattern.get('end_after_count'):
                    rrule_parts.append(f"COUNT={pattern['end_after_count']}")
                elif end_type == 'on' and pattern.get('end_date'):
                    end_date = pattern['end_date'].replace('-', '')
                    rrule_parts.append(f"UNTIL={end_date}")
                
                rrule_string = ";".join(rrule_parts)
                
                # Update the event
                cursor.execute("""
                    UPDATE events 
                    SET recurrence_rrule = ?, 
                        dtstart = start_time,
                        dtend = end_time,
                        timezone = 'America/Los_Angeles'
                    WHERE id = ?
                """, (rrule_string, event_id))
                
                migrated_count += 1
                print(f"Migrated: {title} -> {rrule_string}")
                
            except Exception as e:
                print(f"Error migrating event {event_id}: {e}")
        
        # Commit changes
        conn.commit()
        
        print(f"\nCleanup complete!")
        print(f"- Removed {instance_count} pre-generated instances")
        print(f"- Migrated {migrated_count} events to RRULE format")
        print(f"- System now uses runtime expansion")
        
    except Exception as e:
        print(f"Cleanup failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


def preview_cleanup():
    """
    Preview what the cleanup will do without making changes.
    """
    print("Previewing cleanup operations...")
    
    try:
        conn = sqlite3.connect('taskmaster.db')
        cursor = conn.cursor()
        
        # Count instances
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE recurrence_master_id IS NOT NULL 
            AND is_recurrence_master = 0
        """)
        instance_count = cursor.fetchone()[0]
        
        # Count patterns to migrate
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE is_recurring = 1 
            AND recurrence_pattern IS NOT NULL
            AND (recurrence_rrule IS NULL OR recurrence_rrule = '')
        """)
        migration_count = cursor.fetchone()[0]
        
        print(f"Would remove: {instance_count} pre-generated instances")
        print(f"Would migrate: {migration_count} JSON patterns to RRULE")
        
        # Show sample events
        cursor.execute("""
            SELECT title, recurrence_pattern 
            FROM events 
            WHERE is_recurring = 1 
            AND recurrence_pattern IS NOT NULL
            LIMIT 3
        """)
        
        print("\nSample patterns to migrate:")
        for title, pattern in cursor.fetchall():
            print(f"  {title}: {pattern}")
    
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup recurring event instances")
    parser.add_argument("--preview", action="store_true", 
                       help="Preview cleanup without making changes")
    
    args = parser.parse_args()
    
    if args.preview:
        preview_cleanup()
    else:
        cleanup_recurring_instances()