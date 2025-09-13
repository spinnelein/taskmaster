"""
Initiative schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from .base_schemas import BaseResponse

class InitiativeCreate(BaseModel):
    """Schema for creating an initiative"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    frequency: str = Field("weekly")
    interval: int = Field(1, ge=1)
    preferred_start_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$")
    estimated_duration_minutes: Optional[int] = Field(None, gt=0)
    
    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v):
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly", "yearly", "custom"]
        if v not in valid_frequencies:
            raise ValueError(f"Frequency must be one of {valid_frequencies}")
        return v

class InitiativeUpdate(BaseModel):
    """Schema for updating an initiative"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    frequency: Optional[str] = None
    interval: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None
    preferred_start_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$")
    estimated_duration_minutes: Optional[int] = Field(None, gt=0)
    
    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v):
        if v is not None:
            valid_frequencies = ["daily", "weekly", "monthly", "quarterly", "yearly", "custom"]
            if v not in valid_frequencies:
                raise ValueError(f"Frequency must be one of {valid_frequencies}")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["active", "paused", "completed", "archived"]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
        return v

class InitiativeResponse(BaseResponse):
    """Schema for initiative response"""
    title: str
    description: Optional[str]
    frequency: str
    interval: int
    status: str
    is_template: bool
    preferred_start_time: Optional[str]
    estimated_duration_minutes: Optional[int]
    
    class Config:
        from_attributes = True

class InitiativeListResponse(BaseModel):
    """Schema for list of initiatives"""
    initiatives: List[InitiativeResponse]
    total: int

class InitiativeStats(BaseModel):
    """Schema for initiative statistics"""
    initiative_id: str
    completion_rate: float
    average_duration_minutes: Optional[int]
    last_completed_at: Optional[datetime]
    next_due_date: Optional[datetime]
    overdue_count: int