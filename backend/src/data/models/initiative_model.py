"""
Initiative database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class InitiativeFrequency(enum.Enum):
    """Frequency options for initiatives"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class InitiativeStatus(enum.Enum):
    """Status options for initiatives"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class InitiativeModel(BaseModel):
    """Initiative table model"""
    __tablename__ = "initiatives"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Recurrence settings
    frequency = Column(SQLEnum(InitiativeFrequency), nullable=False, default=InitiativeFrequency.WEEKLY)
    interval = Column(Integer, default=1)  # Every X frequency periods
    
    # Status and control
    status = Column(SQLEnum(InitiativeStatus), nullable=False, default=InitiativeStatus.ACTIVE)
    is_template = Column(Boolean, default=False)  # If true, this is a template for creating new initiatives
    
    # Schedule settings
    preferred_start_time = Column(String(8), nullable=True)  # HH:MM:SS format
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Relationships
    tasks = relationship("TaskModel", back_populates="initiative", cascade="all, delete-orphan")
    project = relationship("ProjectModel", back_populates="initiative", uselist=False)
    
    def __repr__(self):
        return f"<Initiative(id={self.id}, title='{self.title}', frequency={self.frequency.value})>"