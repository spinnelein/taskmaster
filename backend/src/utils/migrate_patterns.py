"""
Migration script to convert existing JSON recurrence patterns to RRULE format
NO EMOJIS
"""
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data.database import get_db
from data.models.event_model import EventModel
from utils.rrule_utils import migrate_json_to_rrule
from sqlalchemy.orm import Session


def migrate_json_patterns_to_rrule():
    """
    Migrate all existing JSON recurrence patterns to RRULE format.
    """
    print("Starting migration of JSON patterns to RRULE format...")
    
    db = next(get_db())
    
    try:
        # Get all recurring events with JSON patterns
        events = db.query(EventModel).filter(
            EventModel.is_recurring == True,
            EventModel.recurrence_pattern != None,
            EventModel.recurrence_rrule == None  # Not already migrated
        ).all()
        
        print(f"Found {len(events)} events to migrate")
        
        migrated_count = 0
        error_count = 0
        
        for event in events:
            try:
                if event.recurrence_pattern and event.start_time:
                    # Convert JSON to RRULE
                    rrule_string = migrate_json_to_rrule(
                        event.recurrence_pattern, 
                        event.start_time
                    )
                    
                    # Update the event
                    event.recurrence_rrule = rrule_string
                    event.dtstart = event.start_time
                    event.dtend = event.end_time
                    
                    # Set default timezone if not set
                    if not event.timezone:
                        event.timezone = 'America/Los_Angeles'
                    
                    migrated_count += 1
                    print(f"Migrated event {event.id}: {event.title}")
                    print(f"  JSON: {event.recurrence_pattern}")
                    print(f"  RRULE: {rrule_string}")
                    
            except Exception as e:
                error_count += 1
                print(f"Error migrating event {event.id}: {e}")
        
        # Commit changes
        db.commit()
        
        print(f"\nMigration complete!")
        print(f"Successfully migrated: {migrated_count} events")
        print(f"Errors encountered: {error_count} events")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()


def preview_migration():
    """
    Preview what the migration will do without making changes.
    """
    print("Previewing migration of JSON patterns to RRULE format...")
    
    db = next(get_db())
    
    try:
        events = db.query(EventModel).filter(
            EventModel.is_recurring == True,
            EventModel.recurrence_pattern != None
        ).all()
        
        print(f"Found {len(events)} recurring events")
        
        for event in events:
            if event.recurrence_pattern and event.start_time:
                rrule_string = migrate_json_to_rrule(
                    event.recurrence_pattern, 
                    event.start_time
                )
                
                print(f"\nEvent: {event.title} ({event.id})")
                print(f"  Current JSON: {event.recurrence_pattern}")
                print(f"  Would become RRULE: {rrule_string}")
                print(f"  Has existing RRULE: {event.recurrence_rrule is not None}")
    
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate JSON patterns to RRULE")
    parser.add_argument("--preview", action="store_true", 
                       help="Preview migration without making changes")
    
    args = parser.parse_args()
    
    if args.preview:
        preview_migration()
    else:
        migrate_json_patterns_to_rrule()