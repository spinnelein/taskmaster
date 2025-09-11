"""
Test Schedule domain entity
NO EMOJIS
"""
import pytest
from datetime import datetime, date, time, timedelta
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.domain.schedule import Schedule
from src.domain.task import Task
from src.domain.event import Event

def test_schedule_creation():
    """Test creating a schedule"""
    today = date.today()
    schedule = Schedule(today)
    
    assert schedule.date == today
    assert len(schedule.events) == 0
    assert len(schedule.scheduled_tasks) == 0

def test_add_event_to_schedule():
    """Test adding an event"""
    today = date.today()
    schedule = Schedule(today)
    
    event = Event(
        title="Meeting",
        start_time=datetime.combine(today, time(10, 0)),
        end_time=datetime.combine(today, time(11, 0))
    )
    
    schedule.add_event(event)
    assert len(schedule.events) == 1

def test_schedule_task():
    """Test scheduling a task"""
    today = date.today()
    schedule = Schedule(today)
    
    task = Task(title="Work", duration=60)
    start_time = datetime.combine(today, time(14, 0))
    
    schedule.add_task(task, start_time)
    assert len(schedule.scheduled_tasks) == 1

def test_schedule_conflict_detection():
    """Test conflict detection"""
    today = date.today()
    schedule = Schedule(today)
    
    # Add blocking event
    event = Event(
        title="Meeting",
        start_time=datetime.combine(today, time(10, 0)),
        end_time=datetime.combine(today, time(11, 0)),
        is_blocking=True
    )
    schedule.add_event(event)
    
    # Try to schedule task during event
    task = Task(title="Work", duration=30)
    with pytest.raises(ValueError):
        schedule.add_task(task, datetime.combine(today, time(10, 30)))

def test_find_free_time():
    """Test finding free time slots"""
    today = date.today()
    schedule = Schedule(today)
    
    # Add a blocking event
    event = Event(
        title="Meeting",
        start_time=datetime.combine(today, time(10, 0)),
        end_time=datetime.combine(today, time(11, 0)),
        is_blocking=True
    )
    schedule.add_event(event)
    
    # Find free time for 30 minute task
    free_slots = schedule.find_free_time(30)
    
    # Should have slots before and after the meeting
    assert len(free_slots) >= 2