"""
Task database model - Enhanced
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Date, Time, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum, Float, DateTime
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class TaskPriority(enum.Enum):
    """Priority levels for tasks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(enum.Enum):
    """Status options for tasks"""
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"

class WeatherCondition(enum.Enum):
    """Weather conditions that affect task execution"""
    ANY = "any"
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOWY = "snowy"
    CLEAR = "clear"
    WINDY = "windy"

class TaskModel(BaseModel):
    """Enhanced Task table model"""
    __tablename__ = "tasks"
    
    # Basic task info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=False)  # in minutes
    urgency = Column(Integer, default=5)  # 1-10 scale
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.ACTIVE)
    
    # Legacy fields (for backward compatibility)
    due_date = Column(Date, nullable=True)
    due_time = Column(Time, nullable=True)
    is_completed = Column(Boolean, default=False)
    
    # Enhanced properties
    is_divisible = Column(Boolean, default=False)  # Can task be split into smaller chunks?
    min_chunk_size = Column(Integer, nullable=True)  # Minimum chunk size if divisible
    
    # Context and conditions
    required_weather = Column(SQLEnum(WeatherCondition), default=WeatherCondition.ANY)
    required_context = Column(JSON, nullable=True)  # Array of contexts like ["home", "computer", "phone"]
    equipment_needed = Column(JSON, nullable=True)  # Array of required equipment
    
    # Dependencies
    depends_on_task_ids = Column(JSON, nullable=True)  # Array of task IDs this depends on
    blocks_task_ids = Column(JSON, nullable=True)     # Array of task IDs this blocks
    
    # Organization relationships
    initiative_id = Column(String(36), ForeignKey("initiatives.id"), nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    phase_id = Column(String(36), ForeignKey("project_phases.id"), nullable=True)
    meal_id = Column(String(36), ForeignKey("meals.id"), nullable=True)  # If this is a meal prep task
    
    # Queue management
    queue_position = Column(Integer, nullable=True)
    auto_scheduled = Column(Boolean, default=False)  # Was this auto-scheduled into a time pool?
    
    # Cost tracking
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    # Recurring task fields
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # {"frequency": "daily", "interval": 1}
    parent_task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    last_completed_at = Column(DateTime, nullable=True)
    
    # Progress tracking for divisible tasks
    partial_completion_minutes = Column(Integer, default=0)
    remaining_minutes = Column(Integer, nullable=True)  # Calculated as duration - partial_completion
    
    # Snooze functionality
    is_snoozed = Column(Boolean, default=False)
    snoozed_until = Column(DateTime, nullable=True)
    
    # Relationships
    initiative = relationship("InitiativeModel", back_populates="tasks")
    project = relationship("ProjectModel", back_populates="tasks")
    phase = relationship("ProjectPhaseModel", back_populates="tasks")
    meal = relationship("MealModel", back_populates="generated_tasks")
    parent_task = relationship("TaskModel", remote_side=[id], backref="recurring_instances")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status={self.status.value})>"

class TaskDependencyModel(BaseModel):
    """Task dependency relationships table"""
    __tablename__ = "task_dependencies"
    
    predecessor_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    successor_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    
    # Dependency type
    dependency_type = Column(String(50), default="finish_to_start")  # finish_to_start, start_to_start, etc.
    lag_minutes = Column(Integer, default=0)  # How many minutes after predecessor
    
    # Relationships
    predecessor = relationship("TaskModel", foreign_keys=[predecessor_id])
    successor = relationship("TaskModel", foreign_keys=[successor_id])
    
    def __repr__(self):
        return f"<TaskDependency(predecessor={self.predecessor_id}, successor={self.successor_id})>"