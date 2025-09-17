#!/usr/bin/env python3
"""
Fix database schema by adding missing recurrence_days column
NO EMOJIS
"""
import sqlite3
import os

def fix_database():
    db_path = "./taskmaster.db"  # Relative to backend directory
    
    print("=== FIXING DATABASE SCHEMA ===")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if recurrence_days column exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"Current task columns: {columns}")
        
        if 'recurrence_days' not in columns:
            print("Adding recurrence_days column...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN recurrence_days INTEGER")
            print("Added recurrence_days column successfully")
        else:
            print("recurrence_days column already exists")
        
        conn.commit()
        print("Database schema fixed!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()