"""
Test Task API endpoints
NO EMOJIS
"""
import pytest
from datetime import date, time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_create_task(client):
    """Test creating a task via API"""
    response = client.post(
        "/api/tasks",
        json={
            "title": "Test Task",
            "duration": 60,
            "urgency": 7,
            "description": "Test description"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["duration"] == 60
    assert "id" in data

def test_get_all_tasks(client):
    """Test getting all tasks"""
    # Create a task first
    client.post(
        "/api/tasks",
        json={"title": "Task 1", "duration": 30}
    )
    
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data

def test_get_task_by_id(client):
    """Test getting a specific task"""
    # Create a task
    create_response = client.post(
        "/api/tasks",
        json={"title": "Test Task", "duration": 30}
    )
    task_id = create_response.json()["id"]
    
    # Get the task
    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id

def test_update_task(client):
    """Test updating a task"""
    # Create a task
    create_response = client.post(
        "/api/tasks",
        json={"title": "Original", "duration": 30}
    )
    task_id = create_response.json()["id"]
    
    # Update the task
    response = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "Updated", "duration": 60}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["duration"] == 60

def test_delete_task(client):
    """Test deleting a task"""
    # Create a task
    create_response = client.post(
        "/api/tasks",
        json={"title": "To Delete", "duration": 30}
    )
    task_id = create_response.json()["id"]
    
    # Delete the task
    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    
    # Verify it's gone
    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404

def test_complete_task(client):
    """Test completing a task"""
    # Create a task
    create_response = client.post(
        "/api/tasks",
        json={"title": "To Complete", "duration": 30}
    )
    task_id = create_response.json()["id"]
    
    # Complete the task
    response = client.post(f"/api/tasks/{task_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] == True
    assert data["status"] == "completed"