"""
Enhanced Schedule schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime
from .base_schemas import BaseResponse

class TimePoolCreate(BaseModel):
    """Schema for creating a time pool"""
    pool_date: date
    start_time: datetime
    end_time: datetime
    is_work_time: bool = Field(True)
    is_flexible: bool = Field(True)
    weather_conditions: Optional[Dict[str, Any]] = None
    context_tags: Optional[List[str]] = None

class TimePoolResponse(BaseResponse):
    """Schema for time pool response"""
    schedule_id: str
    pool_date: date
    start_time: datetime
    end_time: datetime
    total_minutes: int
    allocated_minutes: int
    available_minutes: int
    weather_conditions: Optional[Dict[str, Any]]
    context_tags: Optional[List[str]]
    is_work_time: bool
    is_flexible: bool
    
    class Config:
        orm_mode = True

class TaskScheduleCreate(BaseModel):
    """Schema for scheduling a task"""
    task_id: str
    time_pool_id: str
    scheduled_start: datetime
    scheduled_duration_minutes: int = Field(..., ge=15)
    is_partial: bool = Field(False)

class TaskScheduleResponse(BaseResponse):
    """Schema for task schedule response"""
    task_id: str
    task_title: str
    schedule_id: str
    time_pool_id: str
    scheduled_start: datetime
    scheduled_end: datetime
    scheduled_duration_minutes: int
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    minutes_worked: int
    is_started: bool
    is_completed: bool
    is_partial: bool
    
    class Config:
        orm_mode = True

class ScheduleCreate(BaseModel):
    """Schema for creating a schedule"""
    week_start_date: date
    default_work_start: str = Field("09:00:00", regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$")
    default_work_end: str = Field("17:00:00", regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$")
    min_task_duration_minutes: int = Field(15, ge=15)

class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule"""
    is_current: Optional[bool] = None
    default_work_start: Optional[str] = Field(None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$")
    default_work_end: Optional[str] = Field(None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$")
    min_task_duration_minutes: Optional[int] = Field(None, ge=15)

class ScheduleResponse(BaseResponse):
    """Schema for schedule response"""
    week_start_date: date
    week_end_date: date
    is_current: bool
    generated_at: Optional[datetime]
    default_work_start: str
    default_work_end: str
    min_task_duration_minutes: int
    time_pools: List[TimePoolResponse]
    scheduled_tasks: List[TaskScheduleResponse]
    
    class Config:
        orm_mode = True

class ScheduleGenerateRequest(BaseModel):
    """Schema for requesting schedule generation"""
    week_start_date: Optional[date] = None  # None means current week
    regenerate_pools: bool = Field(True)  # Regenerate time pools from events
    auto_schedule_tasks: bool = Field(True)  # Auto-schedule unscheduled tasks

class TaskQueueRequest(BaseModel):
    """Schema for requesting task queue"""
    include_blocked: bool = Field(False)
    include_snoozed: bool = Field(False)
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    limit: int = Field(100, ge=1, le=500)

class TaskQueueItem(BaseModel):
    """Schema for a task in the queue"""
    task: "TaskResponse"
    priority_score: float
    is_overdue: bool
    days_overdue: int
    can_be_scheduled: bool
    blocking_reasons: List[str]

class TaskQueueResponse(BaseModel):
    """Schema for task queue response"""
    unscheduled_tasks: List[TaskQueueItem]
    total_unscheduled: int
    blocked_count: int
    snoozed_count: int

class SnoozeTaskRequest(BaseModel):
    """Schema for snoozing a task"""
    snooze_until: datetime
    reason: Optional[str] = Field(None, max_length=255)

class PartialCompleteRequest(BaseModel):
    """Schema for marking partial completion"""
    minutes_worked: int = Field(..., ge=1)
    notes: Optional[str] = Field(None, max_length=500)

class ContextConditionCreate(BaseModel):
    """Schema for creating a context condition"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    schedule_pattern: Optional[Dict[str, List[Dict[str, str]]]] = None
    override_dates: Optional[List[Dict[str, Any]]] = None

class ContextConditionResponse(BaseResponse):
    """Schema for context condition response"""
    name: str
    description: Optional[str]
    schedule_pattern: Optional[Dict[str, List[Dict[str, str]]]]
    override_dates: Optional[List[Dict[str, Any]]]
    
    class Config:
        orm_mode = True

# Import TaskResponse to avoid circular import
from .task_schemas import TaskResponse
TaskQueueItem.update_forward_refs()