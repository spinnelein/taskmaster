
IMPORTANT: Clean State Setup
Commands to run FIRST:

git checkout develop
git pull origin develop
git branch -D feature/api-routes (if it exists)
git checkout -b feature/api-routes

Objective
Create REST API endpoints with FastAPI
Files to Create in Order:
1. backend/src/schemas/init.py
Create empty file
2. backend/src/schemas/base_schemas.py
Content:
python"""
Base schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model"""
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
3. backend/src/schemas/task_schemas.py
Content:
python"""
Task schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date, time
from .base_schemas import BaseResponse

class TaskCreate(BaseModel):
    """Schema for creating a task"""
    title: str = Field(..., min_length=1, max_length=255)
    duration: int = Field(..., gt=0, description="Duration in minutes")
    urgency: int = Field(5, ge=1, le=10)
    description: str = Field("", max_length=1000)
    status: str = Field("pending")
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    duration: Optional[int] = Field(None, gt=0)
    urgency: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["pending", "in_progress", "completed", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class TaskResponse(BaseResponse):
    """Schema for task response"""
    title: str
    duration: int
    urgency: int
    description: str
    status: str
    due_date: Optional[date]
    due_time: Optional[time]
    is_completed: bool
    
    class Config:
        orm_mode = True

class TaskListResponse(BaseModel):
    """Schema for list of tasks"""
    tasks: list[TaskResponse]
    total: int
4. backend/src/schemas/event_schemas.py
Content:
python"""
Event schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from .base_schemas import BaseResponse

class EventCreate(BaseModel):
    """Schema for creating an event"""
    title: str = Field(..., min_length=1, max_length=255)
    start_time: datetime
    end_time: datetime
    is_blocking: bool = Field(True)
    location: Optional[str] = Field(None, max_length=255)
    description: str = Field("", max_length=1000)
    
    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class EventUpdate(BaseModel):
    """Schema for updating an event"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_blocking: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        if v and 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError('End time must be after start time')
        return v

class EventResponse(BaseResponse):
    """Schema for event response"""
    title: str
    start_time: datetime
    end_time: datetime
    is_blocking: bool
    location: Optional[str]
    description: str
    duration_minutes: int
    
    class Config:
        orm_mode = True

class EventListResponse(BaseModel):
    """Schema for list of events"""
    events: list[EventResponse]
    total: int
5. backend/src/schemas/schedule_schemas.py
Content:
python"""
Schedule schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from .task_schemas import TaskResponse
from .event_schemas import EventResponse

class TimeSlotResponse(BaseModel):
    """Schema for available time slot"""
    start: datetime
    end: datetime
    duration_minutes: int

class ScheduleResponse(BaseModel):
    """Schema for daily schedule"""
    date: date
    events: List[EventResponse]
    scheduled_tasks: List[dict]  # Contains task and start_time
    free_slots: List[TimeSlotResponse]

class ScheduleTaskRequest(BaseModel):
    """Request to schedule a task"""
    task_id: str = Field(..., description="Task ID to schedule")
    start_time: datetime = Field(..., description="When to start the task")
6. backend/src/api/dependencies.py
Update existing file with new content:
python"""
API dependencies
NO EMOJIS
"""
from typing import Generator
from sqlalchemy.orm import Session
from ..data.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
7. backend/src/api/routes/init.py
Create empty file
8. backend/src/api/routes/tasks.py
Content:
python"""
Task API routes
NO EMOJIS
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from ...schemas.task_schemas import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from ...schemas.base_schemas import MessageResponse
from ...data.repositories.task_repo import TaskRepository
from ...domain.task import Task
from ..dependencies import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("", response_model=TaskListResponse)
def get_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get all tasks with optional status filter"""
    repo = TaskRepository(db)
    
    if status:
        tasks = repo.get_by_status(status)
    else:
        tasks = repo.get_all()
    
    return TaskListResponse(
        tasks=[TaskResponse(**task.to_dict()) for task in tasks],
        total=len(tasks)
    )

@router.post("", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new task"""
    repo = TaskRepository(db)
    
    try:
        task = Task(
            title=task_data.title,
            duration=task_data.duration,
            urgency=task_data.urgency,
            description=task_data.description,
            status=task_data.status,
            due_date=task_data.due_date,
            due_time=task_data.due_time
        )
        saved_task = repo.save(task)
        return TaskResponse(**saved_task.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/overdue", response_model=TaskListResponse)
def get_overdue_tasks(db: Session = Depends(get_db)):
    """Get all overdue tasks"""
    repo = TaskRepository(db)
    tasks = repo.get_overdue()
    
    return TaskListResponse(
        tasks=[TaskResponse(**task.to_dict()) for task in tasks],
        total=len(tasks)
    )

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific task by ID"""
    repo = TaskRepository(db)
    task = repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(**task.to_dict())

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update a task"""
    repo = TaskRepository(db)
    task = repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields if provided
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    try:
        task.validate()
        saved_task = repo.save(task)
        return TaskResponse(**saved_task.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Delete a task"""
    repo = TaskRepository(db)
    
    if not repo.get_by_id(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    deleted = repo.delete(task_id)
    
    if deleted:
        return MessageResponse(message="Task deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Mark a task as completed"""
    repo = TaskRepository(db)
    task = repo.get_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        task.complete()
        saved_task = repo.save(task)
        return TaskResponse(**saved_task.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
9. backend/src/api/routes/events.py
Content:
python"""
Event API routes
NO EMOJIS
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from ...schemas.event_schemas import EventCreate, EventUpdate, EventResponse, EventListResponse
from ...schemas.base_schemas import MessageResponse
from ...data.repositories.event_repo import EventRepository
from ...domain.event import Event
from ..dependencies import get_db

router = APIRouter(prefix="/api/events", tags=["events"])

@router.get("", response_model=EventListResponse)
def get_events(
    date: Optional[date] = Query(None, description="Filter by date"),
    db: Session = Depends(get_db)
):
    """Get all events with optional date filter"""
    repo = EventRepository(db)
    
    if date:
        events = repo.get_by_date(date)
    else:
        events = repo.get_all()
    
    return EventListResponse(
        events=[EventResponse(**event.to_dict()) for event in events],
        total=len(events)
    )

@router.post("", response_model=EventResponse)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db)
):
    """Create a new event"""
    repo = EventRepository(db)
    
    try:
        event = Event(
            title=event_data.title,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            is_blocking=event_data.is_blocking,
            location=event_data.location,
            description=event_data.description
        )
        saved_event = repo.save(event)
        return EventResponse(**saved_event.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific event by ID"""
    repo = EventRepository(db)
    event = repo.get_by_id(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return EventResponse(**event.to_dict())

@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: str,
    event_data: EventUpdate,
    db: Session = Depends(get_db)
):
    """Update an event"""
    repo = EventRepository(db)
    event = repo.get_by_id(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Update fields if provided
    update_data = event_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    try:
        event.validate()
        saved_event = repo.save(event)
        return EventResponse(**saved_event.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{event_id}", response_model=MessageResponse)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    """Delete an event"""
    repo = EventRepository(db)
    
    if not repo.get_by_id(event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    
    deleted = repo.delete(event_id)
    
    if deleted:
        return MessageResponse(message="Event deleted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete event")
10. backend/src/api/routes/schedule.py
Content:
python"""
Schedule API routes
NO EMOJIS
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime

from ...schemas.schedule_schemas import ScheduleResponse, TimeSlotResponse
from ...data.repositories.task_repo import TaskRepository
from ...data.repositories.event_repo import EventRepository
from ...domain.schedule import Schedule
from ..dependencies import get_db

router = APIRouter(prefix="/api/schedule", tags=["schedule"])

@router.get("/{schedule_date}", response_model=ScheduleResponse)
def get_schedule(
    schedule_date: date,
    db: Session = Depends(get_db)
):
    """Get schedule for a specific date"""
    task_repo = TaskRepository(db)
    event_repo = EventRepository(db)
    
    # Create schedule
    schedule = Schedule(schedule_date)
    
    # Add events for the day
    events = event_repo.get_by_date(schedule_date)
    for event in events:
        schedule.add_event(event)
    
    # Get pending tasks
    pending_tasks = task_repo.get_pending()
    
    # Find free time slots (for 30 minute minimum)
    free_slots = schedule.find_free_time(30)
    
    return ScheduleResponse(
        date=schedule_date,
        events=[e.to_dict() for e in events],
        scheduled_tasks=[],  # Will be populated when scheduling is implemented
        free_slots=[
            TimeSlotResponse(
                start=slot.start,
                end=slot.end,
                duration_minutes=slot.duration_minutes
            ) for slot in free_slots
        ]
    )
11. Update backend/src/api/app.py
Update the existing app.py to include routers:
python"""
FastAPI application setup
NO EMOJIS
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import tasks, events, schedule

# Create FastAPI instance
app = FastAPI(
    title="TaskMaster API",
    description="Task and Schedule Management API",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router)
app.include_router(events.router)
app.include_router(schedule.router)

# Health check endpoint
@app.get("/health")
def health_check():
    """Check if API is running"""
    return {"status": "healthy", "service": "TaskMaster API"}

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "TaskMaster API", "version": "1.0.0", "docs": "/docs"}
12. backend/tests/integration/test_api_tasks.py
Content:
python"""
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
Windows Commands to Run:
Navigate to backend and activate venv:

cd backend
venv\Scripts\activate

Run API tests:

pytest tests\integration\test_api_tasks.py -v

Start the server to test manually:

uvicorn src.api.app:app --reload

Check the API documentation:

Open browser to http://localhost:8000/docs

Git Commands to Complete:
After all tests pass and API works:

git add .
git commit -m "feat: API routes - REST endpoints for tasks, events, and schedule"
git push origin feature/api-routes

Merge to develop:

git checkout develop
git merge feature/api-routes
git push origin develop
git branch -d feature/api-routes

Success Criteria:

All API tests pass
Server runs with all endpoints
Swagger docs available at /docs
Can create, read, update, delete tasks and events
Schedule endpoint returns free time slots