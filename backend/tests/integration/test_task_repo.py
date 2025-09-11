"""
Test TaskRepository
NO EMOJIS
"""
import pytest
from datetime import date, time, datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data.repositories.task_repo import TaskRepository
from src.domain.task import Task

def test_save_and_get_task(db_session):
    """Test saving and retrieving a task"""
    repo = TaskRepository(db_session)
    
    # Create task
    task = Task(
        title="Test Task",
        duration=60,
        urgency=7,
        description="Test description"
    )
    
    # Save task
    saved_task = repo.save(task)
    assert saved_task.id == task.id
    
    # Get task by ID
    retrieved_task = repo.get_by_id(task.id)
    assert retrieved_task is not None
    assert retrieved_task.title == "Test Task"
    assert retrieved_task.duration == 60

def test_get_all_tasks(db_session):
    """Test getting all tasks"""
    repo = TaskRepository(db_session)
    
    # Create multiple tasks
    task1 = Task(title="Task 1", duration=30)
    task2 = Task(title="Task 2", duration=45)
    
    repo.save(task1)
    repo.save(task2)
    
    # Get all tasks
    all_tasks = repo.get_all()
    assert len(all_tasks) >= 2

def test_update_task(db_session):
    """Test updating a task"""
    repo = TaskRepository(db_session)
    
    # Create and save task
    task = Task(title="Original", duration=30)
    repo.save(task)
    
    # Update task
    task.title = "Updated"
    task.duration = 60
    updated_task = repo.save(task)
    
    # Verify update
    retrieved = repo.get_by_id(task.id)
    assert retrieved.title == "Updated"
    assert retrieved.duration == 60

def test_delete_task(db_session):
    """Test deleting a task"""
    repo = TaskRepository(db_session)
    
    # Create and save task
    task = Task(title="To Delete", duration=30)
    repo.save(task)
    
    # Delete task
    deleted = repo.delete(task.id)
    assert deleted == True
    
    # Verify deletion
    retrieved = repo.get_by_id(task.id)
    assert retrieved is None

def test_get_by_status(db_session):
    """Test getting tasks by status"""
    repo = TaskRepository(db_session)
    
    # Create tasks with different statuses
    pending_task = Task(title="Pending", duration=30, status="pending")
    completed_task = Task(title="Completed", duration=30, status="completed")
    
    repo.save(pending_task)
    repo.save(completed_task)
    
    # Get pending tasks
    pending_tasks = repo.get_by_status("pending")
    assert any(t.id == pending_task.id for t in pending_tasks)

def test_get_overdue_tasks(db_session):
    """Test getting overdue tasks"""
    repo = TaskRepository(db_session)
    
    # Create overdue task
    yesterday = date.today() - timedelta(days=1)
    overdue_task = Task(
        title="Overdue",
        duration=30,
        due_date=yesterday
    )
    
    # Create future task
    tomorrow = date.today() + timedelta(days=1)
    future_task = Task(
        title="Future",
        duration=30,
        due_date=tomorrow
    )
    
    repo.save(overdue_task)
    repo.save(future_task)
    
    # Get overdue tasks
    overdue = repo.get_overdue()
    assert any(t.id == overdue_task.id for t in overdue)
    assert not any(t.id == future_task.id for t in overdue)