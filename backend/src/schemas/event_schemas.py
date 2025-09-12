"""
Event schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base_schemas import BaseResponse

class RecurrencePattern(BaseModel):
    """Schema for recurrence pattern"""
    pattern: str = Field(..., pattern="^(daily|weekly|monthly|yearly)$")
    interval: int = Field(1, ge=1, le=99)
    weekdays: List[str] = Field(default_factory=list)
    end_type: str = Field("never", pattern="^(never|after|on)$")
    end_after_count: Optional[int] = Field(None, ge=1, le=999)
    end_date: Optional[str] = None

class EventCreate(BaseModel):
    """Schema for creating an event"""
    title: str = Field(..., min_length=1, max_length=255)
    start_time: datetime
    end_time: datetime
    is_blocking: bool = Field(True)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field("", max_length=1000)
    is_recurring: bool = Field(False)
    recurrence_pattern: Optional[RecurrencePattern] = None
    
    @field_validator('description', mode='before')
    @classmethod
    def validate_description(cls, v):
        return v if v is not None else ""
    
    @field_validator('end_time')
    @classmethod
    def validate_end_after_start(cls, v, info):
        if info.data.get('start_time') and v <= info.data['start_time']:
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
    
    @field_validator('end_time')
    @classmethod
    def validate_end_after_start(cls, v, info):
        if v and info.data.get('start_time') and v <= info.data['start_time']:
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