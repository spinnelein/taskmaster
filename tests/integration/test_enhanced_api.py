#!/usr/bin/env python3
"""
Test script for TaskMaster Enhanced REST API v2

Tests pagination, filtering, sorting, and batch operations.
"""
import requests
import json
from datetime import datetime, timedelta

# Base URL
BASE_URL = "http://localhost:5000/api"

def test_task_pagination():
    """Test task pagination"""
    print("\n=== Testing Task Pagination ===")
    
    # Get tasks with pagination
    response = requests.get(f"{BASE_URL}/v2/tasks?limit=5&offset=0")
    if response.status_code == 200:
        data = response.json()
        print(f"First page: {data['meta']['total']} total, showing {len(data['data'])} items")
        print(f"Has more: {data['meta']['has_more']}")
        
        # Get second page
        response2 = requests.get(f"{BASE_URL}/v2/tasks?limit=5&offset=5")
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Second page: showing {len(data2['data'])} items")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_task_filtering():
    """Test task filtering"""
    print("\n=== Testing Task Filtering ===")
    
    # Filter by priority
    response = requests.get(f"{BASE_URL}/v2/tasks?priority=high,urgent")
    if response.status_code == 200:
        data = response.json()
        print(f"High/Urgent priority tasks: {len(data['data'])}")
    
    # Filter by date range
    today = datetime.now().date()
    week_later = today + timedelta(days=7)
    response = requests.get(
        f"{BASE_URL}/v2/tasks?due_date_from={today}&due_date_to={week_later}"
    )
    if response.status_code == 200:
        data = response.json()
        print(f"Tasks due this week: {len(data['data'])}")
    
    # Filter by status
    response = requests.get(f"{BASE_URL}/v2/tasks?status=active&is_snoozed=false")
    if response.status_code == 200:
        data = response.json()
        print(f"Active, not snoozed tasks: {len(data['data'])}")

def test_task_sorting():
    """Test task sorting"""
    print("\n=== Testing Task Sorting ===")
    
    # Sort by urgency descending, then created_at ascending
    response = requests.get(f"{BASE_URL}/v2/tasks?sort=urgency:desc,created_at:asc&limit=10")
    if response.status_code == 200:
        data = response.json()
        print("Tasks sorted by urgency (desc):")
        for task in data['data'][:5]:
            print(f"  - {task['title']} (urgency: {task['urgency']})")

def test_task_search():
    """Test task search"""
    print("\n=== Testing Task Search ===")
    
    response = requests.get(f"{BASE_URL}/v2/tasks?q=meeting")
    if response.status_code == 200:
        data = response.json()
        print(f"Tasks matching 'meeting': {len(data['data'])}")
        for task in data['data'][:3]:
            print(f"  - {task['title']}")

def test_batch_create_tasks():
    """Test batch task creation"""
    print("\n=== Testing Batch Task Creation ===")
    
    tasks = {
        "tasks": [
            {"title": "Test Task 1", "duration": 30, "priority": "medium"},
            {"title": "Test Task 2", "duration": 60, "priority": "high"},
            {"title": "Test Task 3", "duration": 15, "urgency": 8},
            {"description": "Missing title"},  # This should fail
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/v2/tasks/batch",
        json=tasks,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code in [201, 207]:
        data = response.json()
        print(f"Created {len(data['data']['created'])} tasks")
        print(f"Errors: {len(data['data']['errors'])}")
        if data['data']['errors']:
            print("Error details:")
            for error in data['data']['errors']:
                print(f"  - Index {error['index']}: {error['error']}")

def test_event_calendar_mode():
    """Test event calendar mode with expansion"""
    print("\n=== Testing Event Calendar Mode ===")
    
    # Get events for current month
    today = datetime.now()
    month_start = today.replace(day=1).isoformat()
    month_end = (today.replace(day=1) + timedelta(days=32)).replace(day=1).isoformat()
    
    response = requests.get(
        f"{BASE_URL}/v2/events/calendar?start={month_start}&end={month_end}"
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Calendar events this month: {data['meta']['total']}")
        print(f"Showing: {len(data['data'])}")
        
        # Count recurring vs one-time
        recurring = sum(1 for e in data['data'] if e.get('is_recurring'))
        print(f"Recurring instances: {recurring}")

def test_event_filtering():
    """Test event filtering"""
    print("\n=== Testing Event Filtering ===")
    
    # Filter by event type
    response = requests.get(f"{BASE_URL}/v2/events?event_type=all_day,instant")
    if response.status_code == 200:
        data = response.json()
        print(f"All-day and instant events: {len(data['data'])}")
    
    # Filter by blocking status
    response = requests.get(f"{BASE_URL}/v2/events?is_blocking=false")
    if response.status_code == 200:
        data = response.json()
        print(f"Non-blocking events: {len(data['data'])}")

def test_field_selection():
    """Test field selection"""
    print("\n=== Testing Field Selection ===")
    
    response = requests.get(f"{BASE_URL}/v2/tasks?fields=id,title,status&limit=3")
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            print("Selected fields only:")
            print(json.dumps(data['data'][0], indent=2))

def test_include_related_data():
    """Test including related data"""
    print("\n=== Testing Include Related Data ===")
    
    # Get first task with dependencies
    response = requests.get(f"{BASE_URL}/v2/tasks?limit=1")
    if response.status_code == 200 and response.json()['data']:
        task_id = response.json()['data'][0]['id']
        
        # Get with dependencies and subtasks
        response2 = requests.get(f"{BASE_URL}/v2/tasks/{task_id}?include=dependencies,subtasks")
        if response2.status_code == 200:
            data = response2.json()
            print(f"Task: {data['data']['title']}")
            if 'dependencies' in data['data']:
                print(f"Dependencies: {len(data['data']['dependencies'])}")
            if 'subtasks' in data['data']:
                print(f"Subtasks: {len(data['data']['subtasks'])}")

def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    # Invalid date format
    response = requests.post(
        f"{BASE_URL}/v2/tasks",
        json={"title": "Test", "due_date": "not-a-date"},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 422:
        print(f"Validation error (expected): {response.json()['errors']}")
    
    # Missing required field
    response = requests.post(
        f"{BASE_URL}/v2/tasks",
        json={"description": "Missing title"},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 422:
        print(f"Missing field error (expected): {response.json()['errors']}")
    
    # Non-existent resource
    response = requests.get(f"{BASE_URL}/v2/tasks/non-existent-id")
    if response.status_code == 404:
        print(f"Not found (expected): {response.json()['message']}")

def main():
    """Run all tests"""
    print("Testing TaskMaster Enhanced REST API v2")
    print("=======================================")
    
    try:
        # Test connection
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("Error: Cannot connect to API. Is the Flask server running?")
            return
        
        # Run tests
        test_task_pagination()
        test_task_filtering()
        test_task_sorting()
        test_task_search()
        test_batch_create_tasks()
        test_event_calendar_mode()
        test_event_filtering()
        test_field_selection()
        test_include_related_data()
        test_error_handling()
        
        print("\n=== All tests completed ===")
        
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the Flask server at http://localhost:5000")
        print("Please ensure the Flask app is running: python flask_app/app.py")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()