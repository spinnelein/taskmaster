"""
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