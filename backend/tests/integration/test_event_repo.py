"""
Test EventRepository
NO EMOJIS
"""
import pytest
from datetime import datetime, date, timedelta
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.data.repositories.event_repo import EventRepository
from src.domain.event import Event

def test_save_and_get_event(db_session):
    """Test saving and retrieving an event"""
    repo = EventRepository(db_session)
    
    # Create event
    start = datetime.now()
    end = start + timedelta(hours=1)
    event = Event(
        title="Test Event",
        start_time=start,
        end_time=end,
        is_blocking=True
    )
    
    # Save event
    saved_event = repo.save(event)
    assert saved_event.id == event.id
    
    # Get event by ID
    retrieved_event = repo.get_by_id(event.id)
    assert retrieved_event is not None
    assert retrieved_event.title == "Test Event"

def test_get_events_by_date(db_session):
    """Test getting events by date"""
    repo = EventRepository(db_session)
    
    today = date.today()
    
    # Create event for today
    start = datetime.combine(today, datetime.min.time()) + timedelta(hours=10)
    end = start + timedelta(hours=1)
    today_event = Event(
        title="Today Event",
        start_time=start,
        end_time=end
    )
    
    # Create event for tomorrow
    tomorrow_start = start + timedelta(days=1)
    tomorrow_end = tomorrow_start + timedelta(hours=1)
    tomorrow_event = Event(
        title="Tomorrow Event",
        start_time=tomorrow_start,
        end_time=tomorrow_end
    )
    
    repo.save(today_event)
    repo.save(tomorrow_event)
    
    # Get today's events
    today_events = repo.get_by_date(today)
    assert any(e.id == today_event.id for e in today_events)
    assert not any(e.id == tomorrow_event.id for e in today_events)

def test_get_blocking_events(db_session):
    """Test getting blocking events"""
    repo = EventRepository(db_session)
    
    start = datetime.now()
    end = start + timedelta(hours=1)
    
    # Create blocking event
    blocking_event = Event(
        title="Blocking",
        start_time=start,
        end_time=end,
        is_blocking=True
    )
    
    # Create non-blocking event
    non_blocking_event = Event(
        title="Non-blocking",
        start_time=start,
        end_time=end,
        is_blocking=False
    )
    
    repo.save(blocking_event)
    repo.save(non_blocking_event)
    
    # Get blocking events
    blocking = repo.get_blocking_events(
        start - timedelta(minutes=30),
        end + timedelta(minutes=30)
    )
    
    assert any(e.id == blocking_event.id for e in blocking)
    assert not any(e.id == non_blocking_event.id for e in blocking)

def test_get_overlapping_events(db_session):
    """Test getting overlapping events"""
    repo = EventRepository(db_session)
    
    base_time = datetime.now()
    
    # Create overlapping event
    overlap_event = Event(
        title="Overlapping",
        start_time=base_time,
        end_time=base_time + timedelta(hours=2)
    )
    
    # Create non-overlapping event
    no_overlap_event = Event(
        title="No Overlap",
        start_time=base_time + timedelta(hours=3),
        end_time=base_time + timedelta(hours=4)
    )
    
    repo.save(overlap_event)
    repo.save(no_overlap_event)
    
    # Check for overlaps
    overlapping = repo.get_overlapping(
        base_time + timedelta(hours=1),
        base_time + timedelta(hours=2, minutes=30)
    )
    
    assert any(e.id == overlap_event.id for e in overlapping)
    assert not any(e.id == no_overlap_event.id for e in overlapping)