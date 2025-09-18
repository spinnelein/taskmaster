"""
Test Task domain entity
NO EMOJIS
"""
import pytest
from datetime import date, time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.domain.task import Task

def test_task_creation():
    """Test creating a task"""
    task = Task(
        title="Test Task",
        duration=30,
        urgency=7,
        description="Test description"
    )
    
    assert task.title == "Test Task"
    assert task.duration == 30
    assert task.urgency == 7
    assert task.status == "pending"
    assert task.id is not None

def test_task_validation():
    """Test task validation"""
    # Test empty title
    with pytest.raises(ValueError):
        Task(title="", duration=30)
    
    # Test invalid duration
    with pytest.raises(ValueError):
        Task(title="Test", duration=0)
    
    # Test invalid urgency
    with pytest.raises(ValueError):
        Task(title="Test", duration=30, urgency=11)

def test_task_can_start():
    """Test can_start method"""
    task = Task(title="Test", duration=30)
    assert task.can_start() == True
    
    task.status = "in_progress"
    assert task.can_start() == False

def test_task_complete():
    """Test completing a task"""
    task = Task(title="Test", duration=30)
    task.complete()
    
    assert task.is_completed == True
    assert task.status == "completed"
    
    # Cannot complete again
    with pytest.raises(ValueError):
        task.complete()

def test_task_to_dict():
    """Test converting task to dictionary"""
    task = Task(
        title="Test",
        duration=30,
        urgency=5,
        due_date=date(2024, 1, 1)
    )
    
    data = task.to_dict()
    assert data['title'] == "Test"
    assert data['duration'] == 30
    assert data['urgency'] == 5
    assert 'id' in data