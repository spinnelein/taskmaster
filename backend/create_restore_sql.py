#!/usr/bin/env python3
"""
Create SQL script to restore events from backup
NO EMOJIS
"""
import json
from pathlib import Path

# Configuration
BACKUP_FILE = Path(r"C:\Users\Aaron\Documents\Python Scripts\Taskmaster\data_backup\backup_2025-09-13_01-16-58\events_backup.json")
SQL_OUTPUT = Path(__file__).parent / "restore_events.sql"

def escape_sql(value):
    """Escape SQL string values"""
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)

def create_restore_sql():
    """Create SQL script to restore events"""
    print(f"Reading backup from: {BACKUP_FILE}")
    
    with open(BACKUP_FILE, 'r') as f:
        backup_data = json.load(f)
    
    events = backup_data.get("data", [])
    total_events = len(events)
    print(f"Found {total_events} events to process")
    
    # Start SQL script
    sql_lines = [
        "-- Event restoration script",
        "-- Generated from backup",
        "BEGIN TRANSACTION;",
        ""
    ]
    
    # Process each event
    restored = 0
    for event in events:
        # Skip events with invalid data
        if not event.get('title') or not event.get('start_time') or not event.get('end_time'):
            continue
            
        # Build INSERT statement
        insert_sql = f"""INSERT INTO events (
    id, title, start_time, end_time, is_blocking,
    location, description, is_recurring, recurrence_pattern,
    recurrence_parent_id, created_at, updated_at
) VALUES (
    {escape_sql(event.get('id'))},
    {escape_sql(event.get('title'))},
    {escape_sql(event.get('start_time'))},
    {escape_sql(event.get('end_time'))},
    {int(event.get('is_blocking', 1))},
    {escape_sql(event.get('location'))},
    {escape_sql(event.get('description', ''))},
    {int(event.get('is_recurring', 0))},
    {escape_sql(event.get('recurrence_pattern'))},
    {escape_sql(event.get('recurrence_parent_id'))},
    {escape_sql(event.get('created_at'))},
    {escape_sql(event.get('updated_at'))}
);"""
        
        sql_lines.append(insert_sql)
        sql_lines.append("")
        restored += 1
        
        # Add progress comments
        if restored % 100 == 0:
            sql_lines.append(f"-- Processed {restored} events...")
            sql_lines.append("")
    
    # End transaction
    sql_lines.extend([
        "COMMIT;",
        f"-- Restored {restored} events from {total_events} total"
    ])
    
    # Write SQL file
    print(f"Writing SQL script to: {SQL_OUTPUT}")
    with open(SQL_OUTPUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"Created SQL script with {restored} event insertions")
    print(f"Run with: cd backend && sqlite3 taskmaster.db < restore_events.sql")

if __name__ == "__main__":
    create_restore_sql()