#!/usr/bin/env python3
"""
Quick test for task completion debugging
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

# Create a new task with initiative and recurrence pattern
task_data = {
    "title": "Test Recurring Task",
    "description": "Testing recurring task generation",
    "duration": 15,
    "urgency": 5,
    "initiative_id": "test-initiative-456",
    "is_recurring": True,
    "recurrence_pattern": {
        "frequency": "days",
        "interval": 3
    }
}

print("Creating test task...")
response = requests.post(f"{BASE_URL}/tasks", json=task_data)
if response.status_code == 200:
    task = response.json()
    task_id = task["id"]
    print(f"Task created: {task_id}")
    
    print("Completing task...")
    complete_response = requests.post(f"{BASE_URL}/tasks/{task_id}/complete")
    print(f"Response: {complete_response.json()}")
else:
    print(f"Task creation failed: {response.text}")