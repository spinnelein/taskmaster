#!/usr/bin/env python3
"""Test script to verify the frontend start date functionality"""

import requests
import time
from datetime import datetime, timedelta

def create_test_task():
    """Create a test task with start date to verify frontend display"""
    start_date = (datetime.now() + timedelta(days=2)).date().isoformat()
    due_date = (datetime.now() + timedelta(days=7)).date().isoformat()
    
    task_data = {
        "title": "Frontend Test Task with Start Date",
        "description": "This task tests the frontend start date display",
        "duration": 45,
        "urgency": 6,
        "priority": "medium",
        "start_date": start_date,
        "due_date": due_date
    }
    
    response = requests.post("http://localhost:5000/api/tasks", json=task_data)
    if response.status_code == 200:
        task = response.json()
        print(f"Created task for frontend testing:")
        print(f"  ID: {task['id']}")
        print(f"  Title: {task['title']}")
        print(f"  Start Date: {task.get('snoozed_until')}")
        print(f"  Due Date: {task.get('due_date')}")
        print(f"  Status: {task.get('status')}")
        print(f"  Is Snoozed: {task.get('is_snoozed')}")
        return task['id']
    else:
        print(f"Failed to create task: {response.text}")
        return None

def check_tasks_api():
    """Check that the tasks API returns the start date information"""
    response = requests.get("http://localhost:5000/api/tasks")
    if response.status_code == 200:
        tasks = response.json()
        print(f"\nFound {len(tasks)} tasks in API response")
        
        # Find our test task
        for task in tasks:
            if "Frontend Test Task" in task.get('title', ''):
                print(f"Found test task in API response:")
                print(f"  Title: {task['title']}")
                print(f"  Start Date: {task.get('snoozed_until')}")
                print(f"  Due Date: {task.get('due_date')}")
                print(f"  Is Snoozed: {task.get('is_snoozed')}")
                return True
        
        print("Test task not found in tasks list")
        return False
    else:
        print(f"Failed to get tasks: {response.text}")
        return False

if __name__ == "__main__":
    print("=== Testing Frontend Start Date Integration ===")
    
    # Create a test task
    task_id = create_test_task()
    
    if task_id:
        # Check API response includes start date info
        check_tasks_api()
        
        print(f"\n✅ Test task created successfully!")
        print(f"You can now:")
        print(f"1. Open http://localhost:5000/tasks in your browser")
        print(f"2. Click 'Edit' on the 'Frontend Test Task with Start Date'")
        print(f"3. Verify the Start Date field is populated")
        print(f"4. Test creating a new task with a start date")
        print(f"5. Verify start date validation works")
    else:
        print("❌ Failed to create test task")
    
    print("\n=== Frontend Test Setup Complete ===")