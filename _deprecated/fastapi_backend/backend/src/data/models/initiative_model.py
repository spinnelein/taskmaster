"""
Initiative database model - Simplified recurring task generator
NO EMOJIS
"""
from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base_model import BaseModel

class InitiativeModel(BaseModel):
    """Initiative table model - Simple recurring task generator"""
    __tablename__ = "initiatives"
    
    # Basic info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Task templates stored as JSON
    task_templates = Column(JSON, default=list)
    # Example: [{"title": "Vacuum floor", "duration": 45, "recurrence_days": 2}]
    
    # Foreign keys for relationships  
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    
    # Relationships - ONE WAY ONLY (remove back_populates to break circular dependencies)
    tasks = relationship("TaskModel", cascade="all, delete-orphan", lazy="noload", overlaps="initiative")
    project = relationship("ProjectModel", uselist=False, lazy="noload", foreign_keys=[project_id], overlaps="initiative")
    
    def __repr__(self):
        return f"<Initiative(id={self.id}, title='{self.title}')>"