#!/usr/bin/env python3
"""
Debug the new task queue system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flask_app'))

from app import create_app
from assignment_service import get_assignment_service

def test_task_queue():
    """Test the new _get_all_tasks_for_assignment method"""
    app = create_app()
    
    with app.app_context():
        print("=== Testing New Task Queue System ===\n")
        
        assignment_service = get_assignment_service()
        
        # Test the new method
        task_queue = assignment_service._get_all_tasks_for_assignment()
        
        print(f"[QUEUE] Found {len(task_queue)} tasks in queue")
        
        if task_queue:
            print("\n[QUEUE] Task details:")
            for i, task in enumerate(task_queue[:10], 1):  # Show first 10
                print(f"   {i}. {task.get('title', 'Unknown')} (Priority Score: {task.get('priority_score', 0)})")
                print(f"      Status: {task.get('status', 'Unknown')}, Duration: {task.get('duration', 'Unknown')}min")
                print(f"      Snoozed: {task.get('is_snoozed', False)}, Snoozed Until: {task.get('snoozed_until', 'None')}")
                print(f"      Due Date: {task.get('due_date', 'None')}")
                print("")
        else:
            print("[ERROR] No tasks found in queue!")
            
            # Debug: Check if there are any tasks at all
            from models import Task
            all_tasks = Task.query.all()
            incomplete_tasks = Task.query.filter(Task.is_completed == False).all()
            
            print(f"[DEBUG] Total tasks in database: {len(all_tasks)}")
            print(f"[DEBUG] Incomplete tasks: {len(incomplete_tasks)}")
            
            if incomplete_tasks:
                print("[DEBUG] Sample incomplete tasks:")
                for task in incomplete_tasks[:5]:
                    print(f"   - {task.title} (Status: {task.status}, Completed: {task.is_completed})")

if __name__ == "__main__":
    test_task_queue()