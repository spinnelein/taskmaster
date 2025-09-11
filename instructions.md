Milestone 2: Domain Layer
Git Setup - RUN THESE FIRST
IMPORTANT: Clean State Setup
Commands to run FIRST:

git checkout develop
git pull origin develop
git branch -D feature/domain-layer (if it exists from a previous attempt)
git checkout -b feature/domain-layer

Objective
Create domain models with business logic (separate from database models)
Files to Create in Order:
1. backend/src/domain/init.py
Create empty file
2. backend/src/domain/base.py
Content:
python"""
Base domain entity
NO EMOJIS
"""
from typing import Dict, Any
from datetime import datetime
import uuid

class DomainEntity:
    """Base class for all domain entities"""
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create entity from dictionary"""
        raise NotImplementedError
3. backend/src/domain/task.py
Content:
python"""
Task domain entity
NO EMOJIS
"""
from typing import Optional, Dict, Any
from datetime import date, time, datetime
from .base import DomainEntity

class Task(DomainEntity):
    """Task domain model with business logic"""
    
    def __init__(
        self,
        title: str,
        duration: int,
        urgency: int = 5,
        description: str = "",
        status: str = "pending",
        due_date: Optional[date] = None,
        due_time: Optional[time] = None
    ):
        super().__init__()
        self.title = title
        self.duration = duration  # minutes
        self.urgency = urgency
        self.description = description
        self.status = status
        self.due_date = due_date
        self.due_time = due_time
        self.is_completed = False
        self.validate()
    
    def validate(self):
        """Validate task properties"""
        if not self.title:
            raise ValueError("Task title cannot be empty")
        if self.duration <= 0:
            raise ValueError("Duration must be positive")
        if not 1 <= self.urgency <= 10:
            raise ValueError("Urgency must be between 1 and 10")
        if self.status not in ["pending", "in_progress", "completed", "cancelled"]:
            raise ValueError("Invalid status")
    
    def can_start(self) -> bool:
        """Check if task can be started"""
        return self.status == "pending" and not self.is_completed
    
    def start(self):
        """Start the task"""
        if not self.can_start():
            raise ValueError("Task cannot be started")
        self.status = "in_progress"
        self.updated_at = datetime.utcnow()
    
    def complete(self):
        """Mark task as completed"""
        if self.is_completed:
            raise ValueError("Task already completed")
        self.status = "completed"
        self.is_completed = True
        self.updated_at = datetime.utcnow()
    
    def update_status(self, status: str):
        """Update task status"""
        old_status = self.status
        self.status = status
        self.validate()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'title': self.title,
            'duration': self.duration,
            'urgency': self.urgency,
            'description': self.description,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'due_time': self.due_time.isoformat() if self.due_time else None,
            'is_completed': self.is_completed
        })
        return data
4. backend/src/domain/event.py
Content:
python"""
Event domain entity
NO EMOJIS
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .base import DomainEntity

class Event(DomainEntity):
    """Event domain model with business logic"""
    
    def __init__(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        is_blocking: bool = True,
        location: Optional[str] = None,
        description: str = ""
    ):
        super().__init__()
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.is_blocking = is_blocking
        self.location = location
        self.description = description
        self.validate()
    
    def validate(self):
        """Validate event properties"""
        if not self.title:
            raise ValueError("Event title cannot be empty")
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
    
    def duration_minutes(self) -> int:
        """Calculate duration in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    def blocks_time_period(self, start: datetime, end: datetime) -> bool:
        """Check if event blocks a time period"""
        if not self.is_blocking:
            return False
        # Check for overlap
        return not (end <= self.start_time or start >= self.end_time)
    
    def overlaps_with(self, other: 'Event') -> bool:
        """Check if this event overlaps with another"""
        return not (
            other.end_time <= self.start_time or 
            other.start_time >= self.end_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'is_blocking': self.is_blocking,
            'location': self.location,
            'description': self.description,
            'duration_minutes': self.duration_minutes()
        })
        return data
5. backend/src/domain/schedule.py
Content:
python"""
Schedule domain entity
NO EMOJIS
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, time, timedelta
from .task import Task
from .event import Event

class TimeSlot:
    """Represents an available time slot"""
    
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end
        self.duration_minutes = int((end - start).total_seconds() / 60)

class Schedule:
    """Daily schedule with tasks and events"""
    
    def __init__(self, schedule_date: date):
        self.date = schedule_date
        self.events: List[Event] = []
        self.scheduled_tasks: List[Tuple[Task, datetime]] = []
    
    def add_event(self, event: Event):
        """Add an event to the schedule"""
        # Check if event is on this day
        if event.start_time.date() != self.date:
            raise ValueError("Event is not on this schedule date")
        self.events.append(event)
    
    def add_task(self, task: Task, start_time: datetime):
        """Schedule a task at a specific time"""
        if start_time.date() != self.date:
            raise ValueError("Task start time is not on this schedule date")
        
        end_time = start_time + timedelta(minutes=task.duration)
        
        # Check for conflicts
        if self.has_conflict(start_time, end_time):
            raise ValueError("Time slot has conflict")
        
        self.scheduled_tasks.append((task, start_time))
    
    def has_conflict(self, start: datetime, end: datetime) -> bool:
        """Check if time period has conflicts"""
        # Check against blocking events
        for event in self.events:
            if event.blocks_time_period(start, end):
                return True
        
        # Check against scheduled tasks
        for task, task_start in self.scheduled_tasks:
            task_end = task_start + timedelta(minutes=task.duration)
            if not (end <= task_start or start >= task_end):
                return True
        
        return False
    
    def find_free_time(self, duration_minutes: int) -> List[TimeSlot]:
        """Find available time slots of given duration"""
        free_slots = []
        
        # Define work hours (8 AM to 8 PM)
        day_start = datetime.combine(self.date, time(8, 0))
        day_end = datetime.combine(self.date, time(20, 0))
        
        # Get all busy periods
        busy_periods = []
        
        # Add blocking events
        for event in self.events:
            if event.is_blocking:
                busy_periods.append((event.start_time, event.end_time))
        
        # Add scheduled tasks
        for task, start_time in self.scheduled_tasks:
            end_time = start_time + timedelta(minutes=task.duration)
            busy_periods.append((start_time, end_time))
        
        # Sort busy periods
        busy_periods.sort(key=lambda x: x[0])
        
        # Find gaps
        current_time = day_start
        for busy_start, busy_end in busy_periods:
            if busy_start > current_time:
                gap_minutes = int((busy_start - current_time).total_seconds() / 60)
                if gap_minutes >= duration_minutes:
                    free_slots.append(TimeSlot(current_time, busy_start))
            current_time = max(current_time, busy_end)
        
        # Check final gap
        if current_time < day_end:
            gap_minutes = int((day_end - current_time).total_seconds() / 60)
            if gap_minutes >= duration_minutes:
                free_slots.append(TimeSlot(current_time, day_end))
        
        return free_slots
6. backend/tests/unit/test_domain_task.py
Content:
python"""
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
7. backend/tests/unit/test_domain_event.py
Content:
python"""
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
8. backend/tests/unit/test_domain_schedule.py
Content:
python"""
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
Windows Commands to Run:
Navigate to backend and activate venv:

cd backend
venv\Scripts\activate

Run tests for each domain entity:

pytest tests\unit\test_domain_task.py -v
pytest tests\unit\test_domain_event.py -v
pytest tests\unit\test_domain_schedule.py -v

Run all domain tests:

pytest tests\unit\test_domain_* -v

Check coverage:

pytest tests\unit\test_domain_* --cov=src.domain --cov-report=term-missing

Git Commands to Complete:
After all tests pass:

git add .
git commit -m "feat: domain layer - Task, Event, and Schedule domain models with business logic"
git push origin feature/domain-layer

Merge to develop:

git checkout develop
git merge feature/domain-layer
git push origin develop
git branch -d feature/domain-layer

Success Criteria:

All domain tests pass
Coverage above 80%
Business logic works correctly
No validation errors