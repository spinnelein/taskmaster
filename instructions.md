Milestone 3: Repository Layer
IMPORTANT: Clean State Setup
Commands to run FIRST:

git checkout develop
git pull origin develop
git branch -D feature/repositories (if it exists)
git checkout -b feature/repositories

Objective
Implement repository pattern to bridge domain models and database models
Files to Create in Order:
1. backend/src/data/repositories/init.py
Create empty file
2. backend/src/data/repositories/base.py
Content:
python"""
Base repository with common CRUD operations
NO EMOJIS
"""
from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod
import uuid

DomainModel = TypeVar('DomainModel')
DBModel = TypeVar('DBModel')

class BaseRepository(Generic[DomainModel, DBModel], ABC):
    """Base repository with common database operations"""
    
    def __init__(self, session: Session, domain_class: Type[DomainModel], db_class: Type[DBModel]):
        self.session = session
        self.domain_class = domain_class
        self.db_class = db_class
    
    @abstractmethod
    def _to_domain(self, db_model: DBModel) -> DomainModel:
        """Convert database model to domain model"""
        pass
    
    @abstractmethod
    def _to_db_model(self, domain_model: DomainModel) -> DBModel:
        """Convert domain model to database model"""
        pass
    
    def get_by_id(self, entity_id: str) -> Optional[DomainModel]:
        """Get entity by ID"""
        db_model = self.session.query(self.db_class).filter(
            self.db_class.id == entity_id
        ).first()
        
        if db_model:
            return self._to_domain(db_model)
        return None
    
    def get_all(self) -> List[DomainModel]:
        """Get all entities"""
        db_models = self.session.query(self.db_class).all()
        return [self._to_domain(model) for model in db_models]
    
    def save(self, entity: DomainModel) -> DomainModel:
        """Save or update entity"""
        db_model = self._to_db_model(entity)
        
        # Check if exists
        existing = self.session.query(self.db_class).filter(
            self.db_class.id == db_model.id
        ).first()
        
        if existing:
            # Update existing
            for key, value in db_model.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
            db_model = existing
        else:
            # Add new
            self.session.add(db_model)
        
        self.session.commit()
        self.session.refresh(db_model)
        return self._to_domain(db_model)
    
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID"""
        db_model = self.session.query(self.db_class).filter(
            self.db_class.id == entity_id
        ).first()
        
        if db_model:
            self.session.delete(db_model)
            self.session.commit()
            return True
        return False
3. backend/src/data/repositories/task_repo.py
Content:
python"""
Task repository implementation
NO EMOJIS
"""
from typing import Optional, List
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import BaseRepository
from ..models.task_model import TaskModel
from ...domain.task import Task

class TaskRepository(BaseRepository[Task, TaskModel]):
    """Repository for Task entities"""
    
    def __init__(self, session: Session):
        super().__init__(session, Task, TaskModel)
    
    def _to_domain(self, db_model: TaskModel) -> Task:
        """Convert TaskModel to Task domain entity"""
        task = Task(
            title=db_model.title,
            duration=db_model.duration,
            urgency=db_model.urgency,
            description=db_model.description or "",
            status=db_model.status,
            due_date=db_model.due_date,
            due_time=db_model.due_time
        )
        # Set ID and timestamps from DB
        task.id = db_model.id
        task.created_at = db_model.created_at
        task.updated_at = db_model.updated_at
        task.is_completed = db_model.is_completed
        return task
    
    def _to_db_model(self, domain_model: Task) -> TaskModel:
        """Convert Task domain entity to TaskModel"""
        return TaskModel(
            id=domain_model.id,
            title=domain_model.title,
            duration=domain_model.duration,
            urgency=domain_model.urgency,
            description=domain_model.description,
            status=domain_model.status,
            due_date=domain_model.due_date,
            due_time=domain_model.due_time,
            is_completed=domain_model.is_completed,
            created_at=domain_model.created_at,
            updated_at=domain_model.updated_at
        )
    
    def get_by_status(self, status: str) -> List[Task]:
        """Get tasks by status"""
        db_models = self.session.query(TaskModel).filter(
            TaskModel.status == status
        ).all()
        return [self._to_domain(model) for model in db_models]
    
    def get_pending(self) -> List[Task]:
        """Get all pending tasks"""
        return self.get_by_status("pending")
    
    def get_overdue(self) -> List[Task]:
        """Get overdue tasks"""
        now = datetime.now()
        today = now.date()
        current_time = now.time()
        
        db_models = self.session.query(TaskModel).filter(
            and_(
                TaskModel.status != "completed",
                TaskModel.due_date != None,
                TaskModel.due_date <= today
            )
        ).all()
        
        overdue_tasks = []
        for model in db_models:
            # Check if task is overdue
            if model.due_date < today:
                overdue_tasks.append(self._to_domain(model))
            elif model.due_date == today and model.due_time and model.due_time < current_time:
                overdue_tasks.append(self._to_domain(model))
        
        return overdue_tasks
    
    def get_by_date_range(self, start_date: date, end_date: date) -> List[Task]:
        """Get tasks within date range"""
        db_models = self.session.query(TaskModel).filter(
            and_(
                TaskModel.due_date != None,
                TaskModel.due_date >= start_date,
                TaskModel.due_date <= end_date
            )
        ).all()
        return [self._to_domain(model) for model in db_models]
4. backend/src/data/repositories/event_repo.py
Content:
python"""
Event repository implementation
NO EMOJIS
"""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .base import BaseRepository
from ..models.event_model import EventModel
from ...domain.event import Event

class EventRepository(BaseRepository[Event, EventModel]):
    """Repository for Event entities"""
    
    def __init__(self, session: Session):
        super().__init__(session, Event, EventModel)
    
    def _to_domain(self, db_model: EventModel) -> Event:
        """Convert EventModel to Event domain entity"""
        event = Event(
            title=db_model.title,
            start_time=db_model.start_time,
            end_time=db_model.end_time,
            is_blocking=db_model.is_blocking,
            location=db_model.location,
            description=db_model.description or ""
        )
        # Set ID and timestamps from DB
        event.id = db_model.id
        event.created_at = db_model.created_at
        event.updated_at = db_model.updated_at
        return event
    
    def _to_db_model(self, domain_model: Event) -> EventModel:
        """Convert Event domain entity to EventModel"""
        return EventModel(
            id=domain_model.id,
            title=domain_model.title,
            start_time=domain_model.start_time,
            end_time=domain_model.end_time,
            is_blocking=domain_model.is_blocking,
            location=domain_model.location,
            description=domain_model.description,
            created_at=domain_model.created_at,
            updated_at=domain_model.updated_at
        )
    
    def get_by_date(self, target_date: date) -> List[Event]:
        """Get events for a specific date"""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        db_models = self.session.query(EventModel).filter(
            and_(
                EventModel.start_time >= start_of_day,
                EventModel.start_time <= end_of_day
            )
        ).all()
        return [self._to_domain(model) for model in db_models]
    
    def get_blocking_events(self, start: datetime, end: datetime) -> List[Event]:
        """Get blocking events in time range"""
        db_models = self.session.query(EventModel).filter(
            and_(
                EventModel.is_blocking == True,
                EventModel.start_time < end,
                EventModel.end_time > start
            )
        ).all()
        return [self._to_domain(model) for model in db_models]
    
    def get_overlapping(self, start: datetime, end: datetime) -> List[Event]:
        """Get events that overlap with time range"""
        db_models = self.session.query(EventModel).filter(
            and_(
                EventModel.start_time < end,
                EventModel.end_time > start
            )
        ).all()
        return [self._to_domain(model) for model in db_models]
5. backend/tests/integration/init.py
Create empty file
6. backend/tests/integration/test_task_repo.py
Content:
python"""
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
7. backend/tests/integration/test_event_repo.py
Content:
python"""
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
Windows Commands to Run:
Navigate to backend and activate venv:

cd backend
venv\Scripts\activate

Run integration tests:

pytest tests\integration\test_task_repo.py -v
pytest tests\integration\test_event_repo.py -v

Run all repository tests:

pytest tests\integration\ -v

Git Commands to Complete:
After all tests pass:

git add .
git commit -m "feat: repository layer - implemented repository pattern for data access"
git push origin feature/repositories

Merge to develop:

git checkout develop
git merge feature/repositories
git push origin develop
git branch -d feature/repositories

Success Criteria:

All repository tests pass
CRUD operations work
Custom queries work
Domain/DB model conversion works