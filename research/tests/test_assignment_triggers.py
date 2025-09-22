#!/usr/bin/env python3
"""
Test that assignment regeneration is triggered when tasks change
"""

import requests
import json
import time
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "http://localhost:5000"

def check_server():
    """Check if Flask server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_assignments_count():
    """Get current count of assignments"""
    try:
        response = requests.get(f"{BASE_URL}/api/assignments_api")
        if response.status_code == 200:
            assignments = response.json()
            active_assignments = [a for a in assignments if a.get('status') in ['assigned', 'started']]
            return len(active_assignments)
        return 0
    except:
        return 0

def create_test_task():
    """Create a test task and return its ID"""
    task_data = {
        'title': f'Test Assignment Trigger Task {int(time.time())}',
        'description': 'Created to test assignment regeneration triggers',
        'duration': 30,
        'urgency': 5,
        'priority': 'medium'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
        if response.status_code == 200:
            task = response.json()
            return task['id']
        else:
            print(f"Failed to create task: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error creating task: {e}")
        return None

def update_test_task(task_id):
    """Update the test task"""
    update_data = {
        'description': 'Updated to test assignment regeneration triggers',
        'urgency': 7
    }
    
    try:
        response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error updating task: {e}")
        return False

def complete_test_task(task_id):
    """Complete the test task"""
    try:
        response = requests.post(f"{BASE_URL}/api/tasks/{task_id}/complete")
        return response.status_code == 200
    except Exception as e:
        print(f"Error completing task: {e}")
        return False

def delete_test_task(task_id):
    """Delete the test task"""
    try:
        response = requests.delete(f"{BASE_URL}/api/tasks/{task_id}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error deleting task: {e}")
        return False

def wait_for_assignment_change(initial_count, max_wait=20):
    """Wait for assignment count to change"""
    print(f"Waiting for assignment count to change from {initial_count}...")
    
    for i in range(max_wait):
        current_count = get_assignments_count()
        if current_count != initial_count:
            print(f"Assignment count changed to {current_count} after {i+1} seconds")
            return True
        time.sleep(1)
    
    print(f"Assignment count did not change after {max_wait} seconds")
    return False

def main():
    """Main test execution"""
    print("=== Assignment Trigger Test ===\n")
    
    # Check server
    if not check_server():
        print("[ERROR] Flask server is not running")
        return 1
    print("[OK] Flask server is running")
    
    # Get initial assignment count
    initial_count = get_assignments_count()
    print(f"[INFO] Initial assignment count: {initial_count}")
    
    # Test 1: Create task trigger
    print("\n--- Test 1: Create Task Trigger ---")
    task_id = create_test_task()
    if not task_id:
        print("[ERROR] Failed to create test task")
        return 1
    print(f"[OK] Created test task: {task_id}")
    
    # Wait for assignment regeneration
    create_changed = wait_for_assignment_change(initial_count)
    new_count_after_create = get_assignments_count()
    
    # Test 2: Update task trigger
    print("\n--- Test 2: Update Task Trigger ---")
    update_success = update_test_task(task_id)
    if not update_success:
        print("[ERROR] Failed to update test task")
        return 1
    print("[OK] Updated test task")
    
    # Wait for assignment regeneration
    update_changed = wait_for_assignment_change(new_count_after_create)
    new_count_after_update = get_assignments_count()
    
    # Test 3: Complete task trigger (this should reduce assignments)
    print("\n--- Test 3: Complete Task Trigger ---")
    complete_success = complete_test_task(task_id)
    if not complete_success:
        print("[ERROR] Failed to complete test task")
        return 1
    print("[OK] Completed test task")
    
    # Wait for assignment regeneration
    complete_changed = wait_for_assignment_change(new_count_after_update)
    new_count_after_complete = get_assignments_count()
    
    # Summary
    print("\n=== Test Results ===")
    print(f"Create task trigger: {'PASS' if create_changed else 'FAIL'}")
    print(f"Update task trigger: {'PASS' if update_changed else 'FAIL'}")
    print(f"Complete task trigger: {'PASS' if complete_changed else 'FAIL'}")
    
    print(f"\nAssignment count progression:")
    print(f"  Initial: {initial_count}")
    print(f"  After create: {new_count_after_create}")
    print(f"  After update: {new_count_after_update}")
    print(f"  After complete: {new_count_after_complete}")
    
    # Overall result
    all_passed = create_changed and update_changed and complete_changed
    print(f"\nOverall result: {'PASS' if all_passed else 'FAIL'}")
    
    if all_passed:
        print("[SUCCESS] Assignment regeneration triggers are working correctly!")
    else:
        print("[ERROR] Some assignment regeneration triggers are not working")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())