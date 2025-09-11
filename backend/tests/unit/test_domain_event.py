"""
Test Event domain entity
NO EMOJIS
"""
import pytest
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.domain.event import Event

def test_event_creation():
    """Test creating an event"""
    start = datetime.now()
    end = start + timedelta(hours=1)
    
    event = Event(
        title="Test Event",
        start_time=start,
        end_time=end,
        is_blocking=True
    )
    
    assert event.title == "Test Event"
    assert event.start_time == start
    assert event.end_time == end
    assert event.is_blocking == True

def test_event_validation():
    """Test event validation"""
    start = datetime.now()
    
    # End time before start time
    with pytest.raises(ValueError):
        Event(
            title="Test",
            start_time=start,
            end_time=start - timedelta(hours=1)
        )

def test_event_duration():
    """Test duration calculation"""
    start = datetime.now()
    end = start + timedelta(minutes=90)
    
    event = Event(title="Test", start_time=start, end_time=end)
    assert event.duration_minutes() == 90

def test_event_blocks_time_period():
    """Test blocking time period"""
    start = datetime(2024, 1, 1, 10, 0)
    end = datetime(2024, 1, 1, 11, 0)
    
    event = Event(title="Test", start_time=start, end_time=end)
    
    # Test overlapping period
    assert event.blocks_time_period(
        datetime(2024, 1, 1, 10, 30),
        datetime(2024, 1, 1, 11, 30)
    ) == True
    
    # Test non-overlapping period
    assert event.blocks_time_period(
        datetime(2024, 1, 1, 11, 30),
        datetime(2024, 1, 1, 12, 30)
    ) == False
    
    # Non-blocking event
    event.is_blocking = False
    assert event.blocks_time_period(
        datetime(2024, 1, 1, 10, 30),
        datetime(2024, 1, 1, 11, 30)
    ) == False