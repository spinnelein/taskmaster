#!/usr/bin/env python3
"""
Debug script for recurring task generation
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
from src.utils.recurring_tasks import (
    should_generate_recurring_task,
    calculate_next_due_date,
    create_recurring_task_data
)

# Mock task object for testing
class MockTask:
    def __init__(self):
        self.id = "test-task-123"
        self.initiative_id = "test-initiative-123"
        self.recurrence_pattern = {"frequency": "days", "interval": 2}
        self.parent_task_id = None
        self.title = "Vacuum the floor"
        self.description = "Regular floor vacuuming"
        self.duration = 30
        self.urgency = 6
        self.priority = "medium"
        self.due_time = None
        self.is_divisible = False
        self.min_chunk_size = None
        self.required_weather = "any"
        self.required_context = None
        self.equipment_needed = None
        self.project_id = None
        self.phase_id = None

def test_utility_functions():
    """Test the utility functions directly"""
    
    print("=== Testing Recurring Task Utility Functions ===")
    
    # Test 1: should_generate_recurring_task
    print("\n1. Testing should_generate_recurring_task...")
    task = MockTask()
    
    result = should_generate_recurring_task(task)
    print(f"   Task with initiative_id and recurrence_pattern: {result}")
    
    # Test without initiative_id
    task.initiative_id = None
    result = should_generate_recurring_task(task)
    print(f"   Task without initiative_id: {result}")
    
    # Test with parent_task_id (should not generate)
    task.initiative_id = "test-initiative-123"
    task.parent_task_id = "parent-123"
    result = should_generate_recurring_task(task)
    print(f"   Task with parent_task_id: {result}")
    
    # Reset for next tests
    task.parent_task_id = None
    
    # Test 2: calculate_next_due_date
    print("\n2. Testing calculate_next_due_date...")
    completion_date = datetime(2025, 9, 15, 14, 30, 0)
    
    # Test days
    pattern = {"frequency": "days", "interval": 2}
    next_due = calculate_next_due_date(completion_date, pattern)
    print(f"   Days pattern: {next_due}")
    print(f"   Expected: 2025-09-17 14:30:00")
    
    # Test weeks
    pattern = {"frequency": "weeks", "interval": 1}
    next_due = calculate_next_due_date(completion_date, pattern)
    print(f"   Weeks pattern: {next_due}")
    print(f"   Expected: 2025-09-22 14:30:00")
    
    # Test months
    pattern = {"frequency": "months", "interval": 1}
    next_due = calculate_next_due_date(completion_date, pattern)
    print(f"   Months pattern: {next_due}")
    print(f"   Expected: 2025-10-15 14:30:00")
    
    # Test invalid pattern
    pattern = {"frequency": "invalid", "interval": 1}
    next_due = calculate_next_due_date(completion_date, pattern)
    print(f"   Invalid pattern: {next_due}")
    print(f"   Expected: None")
    
    # Test 3: create_recurring_task_data
    print("\n3. Testing create_recurring_task_data...")
    next_due_date = datetime(2025, 9, 17, 14, 30, 0)
    completion_date = datetime(2025, 9, 15, 14, 30, 0)
    
    task_data = create_recurring_task_data(task, next_due_date, completion_date)
    
    print(f"   Title: {task_data['title']}")
    print(f"   Initiative ID: {task_data['initiative_id']}")
    print(f"   Parent Task ID: {task_data['parent_task_id']}")
    print(f"   Due Date: {task_data['due_date']}")
    print(f"   Status: {task_data['status']}")
    print(f"   Is Recurring: {task_data['is_recurring']}")
    print(f"   Recurrence Pattern: {task_data['recurrence_pattern']}")
    
    print("\n=== Utility functions test completed ===")

if __name__ == "__main__":
    test_utility_functions()