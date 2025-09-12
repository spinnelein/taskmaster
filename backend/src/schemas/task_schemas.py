"""
Task schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, time, datetime
from .base_schemas import BaseResponse

class TaskCreate(BaseModel):
    """Schema for creating a task"""
    title: str = Field(..., min_length=1, max_length=255)
    duration: int = Field(..., gt=0, description="Duration in minutes")
    urgency: int = Field(5, ge=1, le=10)
    description: str = Field("", max_length=1000)
    status: str = Field("active")
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    
    # Enhanced fields
    is_divisible: bool = Field(False)
    min_chunk_size: Optional[int] = Field(None, gt=0)
    required_weather: str = Field("any")
    required_context: Optional[List[str]] = None
    equipment_needed: Optional[List[str]] = None
    depends_on_task_ids: Optional[List[str]] = None
    
    # Organization
    initiative_id: Optional[str] = None
    project_id: Optional[str] = None
    phase_id: Optional[str] = None
    
    # Recurring task
    is_recurring: bool = Field(False)
    recurrence_pattern: Optional[Dict[str, Any]] = None
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["active", "blocked", "completed"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    
    @validator('required_weather')
    def validate_weather(cls, v):
        valid_weather = ["any", "sunny", "cloudy", "rainy", "snowy", "clear", "windy"]
        if v not in valid_weather:
            raise ValueError(f"Weather must be one of {valid_weather}")
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
            valid_statuses = ["active", "blocked", "completed"]
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
    
    # Enhanced fields
    is_divisible: bool
    min_chunk_size: Optional[int]
    required_weather: str
    required_context: Optional[List[str]]
    equipment_needed: Optional[List[str]]
    depends_on_task_ids: Optional[List[str]]
    blocks_task_ids: Optional[List[str]]
    
    # Organization
    initiative_id: Optional[str]
    project_id: Optional[str]
    phase_id: Optional[str]
    meal_id: Optional[str]
    
    # Queue management
    queue_position: Optional[int]
    auto_scheduled: bool
    
    # Recurring task
    is_recurring: bool
    recurrence_pattern: Optional[Dict[str, Any]]
    parent_task_id: Optional[str]
    last_completed_at: Optional[datetime]
    
    # Progress tracking
    partial_completion_minutes: int
    remaining_minutes: Optional[int]
    
    # Snooze
    is_snoozed: bool
    snoozed_until: Optional[datetime]
    
    class Config:
        orm_mode = True

class TaskListResponse(BaseModel):
    """Schema for list of tasks"""
    tasks: list[TaskResponse]
    total: int