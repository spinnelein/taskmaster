#!/usr/bin/env python3
"""
Debug tasks API directly
NO EMOJIS
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database import SessionLocal
from src.data.repositories.task_repo import TaskRepository

def debug_tasks():
    print("=== DEBUG TASKS DIRECTLY ===")
    
    try:
        # Create database session
        db = SessionLocal()
        print("Database session created")
        
        # Create repository
        repo = TaskRepository(db)
        print("Repository created")
        
        # Try to get all tasks
        tasks = repo.get_all()
        print(f"Got {len(tasks)} tasks")
        
        for task in tasks[:3]:  # Just show first 3
            print(f"  - {task.title} ({task.status.value})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    debug_tasks()