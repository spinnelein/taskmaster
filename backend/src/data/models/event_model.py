"""
Event database model
NO EMOJIS
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from .base_model import BaseModel

class EventModel(BaseModel):
    """Event table model"""
    __tablename__ = "events"
    
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_blocking = Column(Boolean, default=True)
    location = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)
    recurrence_parent_id = Column(String(36), nullable=True)  # For recurring event instances