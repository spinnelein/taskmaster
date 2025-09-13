#!/usr/bin/env python3
"""
Database backup script for TaskMaster
NO EMOJIS
"""
import sys
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Add the backend src directory to Python path
script_dir = Path(__file__).parent
backend_src = script_dir.parent / 'backend' / 'src'
sys.path.insert(0, str(backend_src))

def backup_table_to_json(db_path: str, table_name: str, output_file: str):
    """Backup a table to JSON file"""
    print(f"Backing up {table_name}...")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    cursor = conn.cursor()
    
    try:
        # Get all data from table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        data = []
        for row in rows:
            data.append(dict(row))
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'table_name': table_name,
                'backup_date': datetime.now().isoformat(),
                'record_count': len(data),
                'data': data
            }, f, indent=2, default=str)
        
        print(f"Backed up {len(data)} records from {table_name} to {output_file}")
        return len(data)
        
    except Exception as e:
        print(f"Error backing up {table_name}: {e}")
        return 0
    finally:
        conn.close()

def get_table_schema(db_path: str, table_name: str) -> dict:
    """Get table schema information"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema_info = cursor.fetchall()
        
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table_name}'")
        create_sql = cursor.fetchone()
        
        return {
            'columns': [{'name': col[1], 'type': col[2], 'nullable': not col[3], 'default': col[4]} for col in schema_info],
            'create_sql': create_sql[0] if create_sql else None
        }
    finally:
        conn.close()

def main():
    """Main backup function"""
    print("TaskMaster Database Backup Starting...")
    
    # Paths
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / 'backend' / 'taskmaster.db'
    backup_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Create timestamped backup directory
    backup_dir = script_dir / f'backup_{backup_date}'
    backup_dir.mkdir(exist_ok=True)
    
    print(f"Database path: {db_path}")
    print(f"Backup directory: {backup_dir}")
    
    if not db_path.exists():
        print(f"ERROR: Database file not found at {db_path}")
        return
    
    total_records = 0
    
    # Backup critical tables
    tables_to_backup = [
        'events',
        'tasks', 
        'reminders',
        'weather_forecasts',
        'initiatives'  # Empty but need schema
    ]
    
    # Backup each table
    for table_name in tables_to_backup:
        output_file = backup_dir / f'{table_name}_backup.json'
        try:
            record_count = backup_table_to_json(str(db_path), table_name, str(output_file))
            total_records += record_count
            
            # Also save schema info
            schema_file = backup_dir / f'{table_name}_schema.json'
            schema = get_table_schema(str(db_path), table_name)
            with open(schema_file, 'w') as f:
                json.dump(schema, f, indent=2)
                
        except Exception as e:
            print(f"ERROR backing up {table_name}: {e}")
    
    # Copy original database file as backup
    import shutil
    db_backup_path = backup_dir / 'taskmaster_original.db'
    shutil.copy2(db_path, db_backup_path)
    print(f"Copied original database to {db_backup_path}")
    
    # Create backup summary
    summary = {
        'backup_date': datetime.now().isoformat(),
        'source_database': str(db_path),
        'backup_directory': str(backup_dir),
        'total_records_backed_up': total_records,
        'tables_backed_up': tables_to_backup,
        'backup_files': [
            f'{table}_backup.json' for table in tables_to_backup
        ] + [f'{table}_schema.json' for table in tables_to_backup] + ['taskmaster_original.db']
    }
    
    summary_file = backup_dir / 'backup_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nBackup completed successfully!")
    print(f"Total records backed up: {total_records}")
    print(f"Backup directory: {backup_dir}")
    print(f"Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()