#!/usr/bin/env python3
"""Test script for start date functionality in task creation and editing API"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def test_task_creation_with_start_date():
    """Test creating a task with a start date"""
    print("Testing task creation with start date...")
    
    # Create a task with start date 3 days from now
    start_date = (datetime.now() + timedelta(days=3)).date().isoformat()
    due_date = (datetime.now() + timedelta(days=10)).date().isoformat()
    
    task_data = {
        "title": "Test Task with Start Date",
        "description": "This task should not be schedulable until the start date",
        "duration": 60,
        "urgency": 7,
        "priority": "high",
        "start_date": start_date,
        "due_date": due_date
    }
    
    response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
    print(f"Create task response status: {response.status_code}")
    
    if response.status_code == 200:
        task = response.json()
        print(f"Created task: {task['title']}")
        print(f"Start date (snoozed_until): {task.get('snoozed_until')}")
        print(f"Is snoozed: {task.get('is_snoozed')}")
        print(f"Status: {task.get('status')}")
        return task['id']
    else:
        print(f"Error: {response.text}")
        return None

def test_task_edit_start_date(task_id):
    """Test editing a task's start date"""
    print(f"\nTesting task edit with start date for task {task_id}...")
    
    # Update the start date to tomorrow
    new_start_date = (datetime.now() + timedelta(days=1)).date().isoformat()
    
    update_data = {
        "start_date": new_start_date,
        "title": "Updated Task with New Start Date"
    }
    
    response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data)
    print(f"Update task response status: {response.status_code}")
    
    if response.status_code == 200:
        task = response.json()
        print(f"Updated task: {task['title']}")
        print(f"New start date (snoozed_until): {task.get('snoozed_until')}")
        print(f"Is snoozed: {task.get('is_snoozed')}")
        print(f"Status: {task.get('status')}")
    else:
        print(f"Error: {response.text}")

def test_validation():
    """Test validation (start date after due date)"""
    print("\nTesting validation (start date after due date)...")
    
    # Try to create task with start date after due date
    start_date = (datetime.now() + timedelta(days=10)).date().isoformat()
    due_date = (datetime.now() + timedelta(days=5)).date().isoformat()
    
    task_data = {
        "title": "Invalid Task",
        "start_date": start_date,
        "due_date": due_date
    }
    
    response = requests.post(f"{BASE_URL}/api/tasks", json=task_data)
    print(f"Validation test response status: {response.status_code}")
    
    if response.status_code == 400:
        print(f"Validation working correctly: {response.json()}")
    else:
        print(f"Unexpected response: {response.text}")

def test_clear_start_date(task_id):
    """Test clearing a start date"""
    print(f"\nTesting clearing start date for task {task_id}...")
    
    update_data = {
        "start_date": None
    }
    
    response = requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=update_data)
    print(f"Clear start date response status: {response.status_code}")
    
    if response.status_code == 200:
        task = response.json()
        print(f"Task after clearing start date: {task['title']}")
        print(f"Start date (snoozed_until): {task.get('snoozed_until')}")
        print(f"Is snoozed: {task.get('is_snoozed')}")
        print(f"Status: {task.get('status')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("=== Testing Start Date API Functionality ===")
    
    # Test creating task with start date
    task_id = test_task_creation_with_start_date()
    
    if task_id:
        # Test editing start date
        test_task_edit_start_date(task_id)
        
        # Test clearing start date
        test_clear_start_date(task_id)
    
    # Test validation
    test_validation()
    
    print("\n=== Test Complete ===")