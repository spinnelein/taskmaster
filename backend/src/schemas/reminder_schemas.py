"""
Reminder schemas for API
NO EMOJIS
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base_schemas import BaseResponse

class ReminderCreate(BaseModel):
    """Schema for creating a reminder"""
    reminder_type: str = Field(..., description="Type of reminder")
    title: str = Field(..., min_length=1, max_length=255)
    message: Optional[str] = Field(None, max_length=1000)
    scheduled_time: datetime = Field(..., description="When to send the reminder")
    minutes_before: int = Field(default=0, ge=0, description="Minutes before the associated event/task")
    task_id: Optional[str] = Field(None, description="Associated task ID")
    event_id: Optional[str] = Field(None, description="Associated event ID")
    meal_id: Optional[str] = Field(None, description="Associated meal ID")
    telegram_chat_id: Optional[str] = Field(None, description="Override default chat ID")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="Additional custom data")

class ReminderUpdate(BaseModel):
    """Schema for updating a reminder"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, max_length=1000)
    scheduled_time: Optional[datetime] = None
    minutes_before: Optional[int] = Field(None, ge=0)
    telegram_chat_id: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None

class ReminderResponse(BaseResponse):
    """Schema for reminder response"""
    reminder_type: str
    title: str
    message: Optional[str]
    scheduled_time: datetime
    minutes_before: int
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    snooze_until: Optional[datetime]
    snooze_count: int
    task_id: Optional[str]
    event_id: Optional[str]
    meal_id: Optional[str]
    telegram_chat_id: Optional[str]
    telegram_message_id: Optional[str]
    custom_data: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class ReminderListResponse(BaseModel):
    """Schema for list of reminders"""
    reminders: List[ReminderResponse]
    total: int

class ReminderTemplateCreate(BaseModel):
    """Schema for creating a reminder template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    reminder_type: str = Field(..., description="Type of reminder")
    default_minutes_before: int = Field(default=15, ge=0)
    message_template: str = Field(..., min_length=1, max_length=1000, description="Template with placeholders")
    applies_to_tasks: bool = Field(default=False)
    applies_to_events: bool = Field(default=False)
    applies_to_meals: bool = Field(default=False)
    condition_tags: Optional[List[str]] = Field(None, description="Tags that must be present")

class ReminderTemplateUpdate(BaseModel):
    """Schema for updating a reminder template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    reminder_type: Optional[str] = None
    default_minutes_before: Optional[int] = Field(None, ge=0)
    message_template: Optional[str] = Field(None, min_length=1, max_length=1000)
    applies_to_tasks: Optional[bool] = None
    applies_to_events: Optional[bool] = None
    applies_to_meals: Optional[bool] = None
    condition_tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ReminderTemplateResponse(BaseResponse):
    """Schema for reminder template response"""
    name: str
    description: Optional[str]
    reminder_type: str
    default_minutes_before: int
    message_template: str
    applies_to_tasks: bool
    applies_to_events: bool
    applies_to_meals: bool
    condition_tags: Optional[List[str]]
    is_active: bool
    
    class Config:
        from_attributes = True

class ReminderTemplateListResponse(BaseModel):
    """Schema for list of reminder templates"""
    templates: List[ReminderTemplateResponse]
    total: int

class ChatIdRegister(BaseModel):
    """Schema for registering Telegram chat ID"""
    chat_id: str = Field(..., description="Telegram chat ID")
    user_name: Optional[str] = Field(None, description="Optional user identifier")

class TestReminderRequest(BaseModel):
    """Schema for test reminder request"""
    reminder_id: str = Field(..., description="ID of reminder to send")

class ReminderStats(BaseModel):
    """Schema for reminder statistics"""
    total_reminders: int
    pending_count: int
    sent_count: int
    failed_count: int
    snoozed_count: int
    cancelled_count: int
    success_rate: float

class BulkReminderOperation(BaseModel):
    """Schema for bulk reminder operations"""
    reminder_ids: List[str] = Field(..., min_items=1, description="List of reminder IDs")
    operation: str = Field(..., description="Operation to perform: cancel, retry, delete")

class BulkReminderResult(BaseModel):
    """Schema for bulk reminder operation results"""
    operation: str
    total_processed: int
    successful: int
    failed: int
    errors: List[str]