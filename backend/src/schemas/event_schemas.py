"""
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