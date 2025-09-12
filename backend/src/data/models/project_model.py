"""
Project database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class ProjectStatus(enum.Enum):
    """Status options for projects"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProjectPriority(enum.Enum):
    """Priority levels for projects"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProjectModel(BaseModel):
    """Project table model"""
    __tablename__ = "projects"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status and priority
    status = Column(SQLEnum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)
    priority = Column(SQLEnum(ProjectPriority), nullable=False, default=ProjectPriority.MEDIUM)
    
    # Timeline
    estimated_start_date = Column(DateTime, nullable=True)
    estimated_end_date = Column(DateTime, nullable=True)
    actual_start_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    # Organization
    initiative_id = Column(String(36), ForeignKey("initiatives.id"), nullable=True)
    template_id = Column(String(36), ForeignKey("project_templates.id"), nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tags
    custom_fields = Column(JSON, nullable=True)  # Flexible custom data
    
    # Relationships
    initiative = relationship("InitiativeModel", back_populates="project")
    template = relationship("ProjectTemplateModel", back_populates="projects")
    phases = relationship("ProjectPhaseModel", back_populates="project", cascade="all, delete-orphan", order_by="ProjectPhaseModel.order")
    tasks = relationship("TaskModel", back_populates="project")
    events = relationship("EventModel", back_populates="project")
    
    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}', status={self.status.value})>"

class ProjectPhaseModel(BaseModel):
    """Project phase table model"""
    __tablename__ = "project_phases"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)  # Order within project
    
    # Status
    status = Column(SQLEnum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)
    
    # Timeline
    estimated_start_date = Column(DateTime, nullable=True)
    estimated_end_date = Column(DateTime, nullable=True)
    actual_start_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    # Dependencies
    depends_on_phase_ids = Column(JSON, nullable=True)  # Array of phase IDs this depends on
    
    # Foreign keys
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="phases")
    tasks = relationship("TaskModel", back_populates="phase")
    
    def __repr__(self):
        return f"<ProjectPhase(id={self.id}, title='{self.title}', order={self.order})>"