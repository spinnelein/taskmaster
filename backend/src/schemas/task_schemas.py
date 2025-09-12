"""
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
    status: str = Field("active")
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["active", "blocked", "completed"]
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
    
    class Config:
        orm_mode = True

class TaskListResponse(BaseModel):
    """Schema for list of tasks"""
    tasks: list[TaskResponse]
    total: int