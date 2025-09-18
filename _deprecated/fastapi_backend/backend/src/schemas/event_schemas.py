"""
Event schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .base_schemas import BaseResponse

class RecurringEditMode(str, Enum):
    """Edit modes for recurring events"""
    THIS_ONLY = "this_only"
    THIS_AND_FUTURE = "this_and_future"
    ALL_IN_SERIES = "all_in_series"

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
    notifications_enabled: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[RecurrencePattern] = None
    
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
    is_blocking: bool = True
    location: Optional[str] = None
    description: Optional[str] = None
    notifications_enabled: Optional[bool] = True
    is_recurring: Optional[bool] = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    
    # Master/Exception pattern fields
    recurrence_master_id: Optional[str] = None
    is_recurrence_master: Optional[bool] = False
    is_recurrence_exception: Optional[bool] = False
    recurrence_instance_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EventListResponse(BaseModel):
    """Schema for list of events"""
    events: list[EventResponse]
    total: int

class RecurringEventEditRequest(BaseModel):
    """Schema for editing recurring events with mode"""
    event_data: EventUpdate
    edit_mode: RecurringEditMode
    original_date: Optional[datetime] = None

class RecurringEventDeleteRequest(BaseModel):
    """Schema for deleting recurring events with mode"""
    edit_mode: RecurringEditMode
    original_date: Optional[datetime] = None