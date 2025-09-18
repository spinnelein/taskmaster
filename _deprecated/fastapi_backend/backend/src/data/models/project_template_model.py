"""
Project Template database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class TemplateCategory(enum.Enum):
    """Categories for project templates"""
    PERSONAL = "personal"
    WORK = "work"
    HOME = "home"
    CREATIVE = "creative"
    LEARNING = "learning"
    HEALTH = "health"
    CUSTOM = "custom"

class ProjectTemplateModel(BaseModel):
    """Project template table model"""
    __tablename__ = "project_templates"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(TemplateCategory), nullable=False, default=TemplateCategory.PERSONAL)
    
    # Template metadata
    version = Column(String(20), default="1.0")
    is_public = Column(Boolean, default=False)  # Can be shared with other users
    usage_count = Column(Integer, default=0)  # How many times this template has been used
    
    # Template structure
    phases_template = Column(JSON, nullable=True)  # Template for phases
    tasks_template = Column(JSON, nullable=True)   # Template for tasks
    events_template = Column(JSON, nullable=True)  # Template for events
    
    # Execution settings
    execution_script = Column(Text, nullable=True)  # Command script to create project
    default_settings = Column(JSON, nullable=True)  # Default values for variables
    
    # Relationships
    projects = relationship("ProjectModel", back_populates="template")
    
    def __repr__(self):
        return f"<ProjectTemplate(id={self.id}, title='{self.title}', category={self.category.value})>"

class TemplateExecutionModel(BaseModel):
    """Template execution log table model"""
    __tablename__ = "template_executions"
    
    template_id = Column(String(36), ForeignKey("project_templates.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    # Execution details
    execution_parameters = Column(JSON, nullable=True)  # Parameters used during execution
    execution_log = Column(Text, nullable=True)  # Log of what was created
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    template = relationship("ProjectTemplateModel")
    project = relationship("ProjectModel")
    
    def __repr__(self):
        return f"<TemplateExecution(template_id={self.template_id}, project_id={self.project_id}, success={self.success})>"