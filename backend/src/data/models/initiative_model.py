"""
Initiative database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class InitiativeStatus(enum.Enum):
    """Status options for initiatives"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class InitiativeModel(BaseModel):
    """Initiative table model - A container for related tasks and events"""
    __tablename__ = "initiatives"
    
    # Basic info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status and control
    status = Column(SQLEnum(InitiativeStatus), nullable=False, default=InitiativeStatus.ACTIVE)
    is_template = Column(Boolean, default=False)  # If true, this is a template for creating new initiatives
    
    # Goal/target (optional)
    target_completion_count = Column(Integer, nullable=True)  # e.g., "Complete 30 workouts"
    current_completion_count = Column(Integer, default=0)
    
    # Relationships - The key part: initiatives contain tasks and can have projects
    tasks = relationship("TaskModel", back_populates="initiative", cascade="all, delete-orphan")
    project = relationship("ProjectModel", back_populates="initiative", uselist=False)
    
    def __repr__(self):
        return f"<Initiative(id={self.id}, title='{self.title}', status={self.status.value}, tasks={len(self.tasks)})>"