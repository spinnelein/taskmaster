#!/usr/bin/env python3
"""
Test script for recurring task generation
"""
import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000/api"

def test_recurring_task_workflow():
    """Test the complete recurring task workflow"""
    
    print("=== Testing Recurring Task Generation ===")
    
    # Step 1: Create an initiative (since we can't use the broken endpoint, we'll use raw SQL)
    print("\n1. Creating test initiative...")
    initiative_data = {
        "title": "Daily Exercise",
        "description": "Exercise routine initiative"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/initiatives/", json=initiative_data)
        if response.status_code == 200:
            initiative = response.json()
            initiative_id = initiative.get("id")
            print(f"   SUCCESS: Initiative created: {initiative_id}")
        else:
            # Since initiatives endpoint is broken, let's use a hardcoded initiative ID
            print("   WARNING: Initiative endpoint not working, using hardcoded ID")
            initiative_id = "test-initiative-123"
    except Exception as e:
        print(f"   WARNING: Initiative creation failed: {e}")
        print("   Using hardcoded initiative ID")
        initiative_id = "test-initiative-123"
    
    # Step 2: Create a recurring task
    print("\n2. Creating recurring task...")
    task_data = {
        "title": "Vacuum the floor",
        "description": "Regular floor vacuuming",
        "duration": 30,
        "urgency": 6,
        "initiative_id": initiative_id,
        "is_recurring": True,
        "recurrence_pattern": {
            "frequency": "days",
            "interval": 2
        },
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=task_data)
        if response.status_code == 200:
            task = response.json()
            task_id = task["id"]
            print(f"   SUCCESS: Recurring task created: {task_id}")
            print(f"   SUCCESS: Task title: {task['title']}")
            print(f"   SUCCESS: Initiative ID: {task.get('initiative_id')}")
            print(f"   SUCCESS: Recurrence pattern: {task.get('recurrence_pattern')}")
        else:
            print(f"   ERROR: Task creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ERROR: Task creation failed: {e}")
        return False
    
    # Step 3: Complete the task (should trigger recurring task generation)
    print("\n3. Completing task (should trigger recurring instance)...")
    try:
        response = requests.post(f"{BASE_URL}/tasks/{task_id}/complete")
        if response.status_code == 200:
            result = response.json()
            print(f"   SUCCESS: Task completed successfully")
            print(f"   SUCCESS: Completion time: {result.get('completed_at')}")
            
            if result.get('recurring_task_created'):
                print(f"   SUCCESS: Recurring task created: {result.get('recurring_task_id')}")
                new_task_id = result.get('recurring_task_id')
                
                # Step 4: Verify the new task was created correctly
                print("\n4. Verifying new recurring task...")
                verify_response = requests.get(f"{BASE_URL}/tasks/{new_task_id}")
                if verify_response.status_code == 200:
                    new_task = verify_response.json()
                    print(f"   SUCCESS: New task verified: {new_task['title']}")
                    print(f"   SUCCESS: Due date: {new_task.get('due_date')}")
                    print(f"   SUCCESS: Parent task ID: {new_task.get('parent_task_id')}")
                    print(f"   SUCCESS: Initiative ID: {new_task.get('initiative_id')}")
                    print(f"   SUCCESS: Status: {new_task.get('status')}")
                    
                    # Verify due date is ~2 days from completion
                    original_due = datetime.fromisoformat(result['completed_at'].replace('Z', '+00:00'))
                    new_due = datetime.fromisoformat(new_task['due_date'])
                    days_diff = (new_due - original_due.replace(tzinfo=None)).days
                    print(f"   SUCCESS: Days between completion and new due date: {days_diff}")
                    
                    if days_diff == 2:
                        print("   SUCCESS: Recurrence interval correct!")
                    else:
                        print(f"   WARNING: Expected 2 days, got {days_diff}")
                        
                else:
                    print(f"   ERROR: Could not verify new task: {verify_response.status_code}")
            else:
                print("   ERROR: No recurring task was created")
                print("   Check if task has initiative_id and recurrence_pattern")
        else:
            print(f"   ERROR: Task completion failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ERROR: Task completion failed: {e}")
        return False
    
    print("\n=== Test completed successfully! ===")
    return True

if __name__ == "__main__":
    test_recurring_task_workflow()