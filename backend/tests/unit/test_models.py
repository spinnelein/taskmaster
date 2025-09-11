"""
Test database models
NO EMOJIS
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from datetime import datetime, date, time
from src.data.models.task_model import TaskModel
from src.data.models.event_model import EventModel

def test_task_model_creation(db_session):
    """Test creating a task model"""
    task = TaskModel(
        title="Test Task",
        description="Test Description",
        duration=30,
        urgency=7,
        status="pending"
    )
    
    db_session.add(task)
    db_session.commit()
    
    assert task.id is not None
    assert task.title == "Test Task"
    assert task.duration == 30
    assert task.urgency == 7
    assert task.created_at is not None

def test_event_model_creation(db_session):
    """Test creating an event model"""
    event = EventModel(
        title="Test Event",
        start_time=datetime.now(),
        end_time=datetime.now(),
        is_blocking=True
    )
    
    db_session.add(event)
    db_session.commit()
    
    assert event.id is not None
    assert event.title == "Test Event"
    assert event.is_blocking == True
    assert event.created_at is not None

def test_api_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"