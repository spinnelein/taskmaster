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
    status: str = Field("active")
    is_template: bool = Field(False)
    target_completion_count: Optional[int] = Field(None, gt=0)
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["active", "paused", "completed", "archived"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v.lower()

class InitiativeUpdate(BaseModel):
    """Schema for updating an initiative"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    is_template: Optional[bool] = None
    target_completion_count: Optional[int] = Field(None, gt=0)
    current_completion_count: Optional[int] = Field(None, ge=0)
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["active", "paused", "completed", "archived"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
            return v.lower()
        return v

class InitiativeResponse(BaseResponse):
    """Schema for initiative response"""
    title: str
    description: Optional[str]
    status: str
    is_template: bool
    target_completion_count: Optional[int]
    current_completion_count: int
    task_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class InitiativeListResponse(BaseModel):
    """Schema for list of initiatives"""
    initiatives: List[InitiativeResponse]
    total: int

class InitiativeWithStats(BaseModel):
    """Schema for initiative with statistics"""
    initiative: InitiativeResponse
    stats: dict
    
    class Config:
        from_attributes = True

class InitiativeStats(BaseModel):
    """Schema for initiative statistics"""
    initiative_id: str
    total_tasks: int
    active_tasks: int
    completed_tasks: int
    blocked_tasks: int
    completion_rate: float
    last_completed_at: Optional[datetime]
    average_task_duration_minutes: Optional[int]