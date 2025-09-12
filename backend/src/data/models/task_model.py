"""
Task database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Date, Time, Boolean
from .base_model import BaseModel

class TaskModel(BaseModel):
    """Task table model"""
    __tablename__ = "tasks"
    
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    duration = Column(Integer, nullable=False)  # in minutes
    urgency = Column(Integer, default=5)  # 1-10
    status = Column(String(50), default="active")
    due_date = Column(Date, nullable=True)
    due_time = Column(Time, nullable=True)
    is_completed = Column(Boolean, default=False)