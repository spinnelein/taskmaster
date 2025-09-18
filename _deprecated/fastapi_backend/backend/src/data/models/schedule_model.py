"""
Schedule and Time Pool database models
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship
from .base_model import BaseModel

class ScheduleModel(BaseModel):
    """Schedule table model - represents a weekly schedule"""
    __tablename__ = "schedules"
    
    # Schedule identification
    week_start_date = Column(Date, nullable=False)  # Monday of the week
    week_end_date = Column(Date, nullable=False)    # Sunday of the week
    
    # Metadata
    is_current = Column(Boolean, default=False)  # Is this the current week's schedule?
    generated_at = Column(DateTime, nullable=True)  # When was this schedule auto-generated?
    
    # Configuration
    default_work_start = Column(String(8), default="09:00:00")  # HH:MM:SS format
    default_work_end = Column(String(8), default="17:00:00")    # HH:MM:SS format
    min_task_duration_minutes = Column(Integer, default=15)
    
    # Relationships
    time_pools = relationship("TimePoolModel", back_populates="schedule", cascade="all, delete-orphan")
    scheduled_tasks = relationship("TaskScheduleModel", back_populates="schedule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, week_start={self.week_start_date})>"

class TimePoolModel(BaseModel):
    """Time pool table model - represents available time blocks"""
    __tablename__ = "time_pools"
    
    # Pool identification
    schedule_id = Column(String(36), ForeignKey("schedules.id"), nullable=False)
    pool_date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Pool properties
    total_minutes = Column(Integer, nullable=False)  # Total duration in minutes
    allocated_minutes = Column(Integer, default=0)   # Minutes already allocated to tasks
    available_minutes = Column(Integer, nullable=False)  # Remaining available minutes
    
    # Context for this time pool
    weather_conditions = Column(JSON, nullable=True)  # {"temp": 72, "condition": "sunny", "precipitation": false}
    context_tags = Column(JSON, nullable=True)  # ["home", "kids_at_school", "weekend"]
    
    # Pool type
    is_work_time = Column(Boolean, default=True)  # Is this normal work hours?
    is_flexible = Column(Boolean, default=True)   # Can tasks be moved around in this pool?
    
    # Relationships
    schedule = relationship("ScheduleModel", back_populates="time_pools")
    scheduled_tasks = relationship("TaskScheduleModel", back_populates="time_pool")
    
    def __repr__(self):
        return f"<TimePool(id={self.id}, date={self.pool_date}, start={self.start_time.time()})>"

class TaskScheduleModel(BaseModel):
    """Task schedule table model - maps tasks to specific time slots"""
    __tablename__ = "task_schedules"
    
    # Foreign keys
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    schedule_id = Column(String(36), ForeignKey("schedules.id"), nullable=False)
    time_pool_id = Column(String(36), ForeignKey("time_pools.id"), nullable=False)
    
    # Scheduled time
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    scheduled_duration_minutes = Column(Integer, nullable=False)
    
    # Progress tracking
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    minutes_worked = Column(Integer, default=0)
    
    # Status
    is_started = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    is_partial = Column(Boolean, default=False)  # Is this a partial allocation of a larger task?
    
    # Relationships
    task = relationship("TaskModel", backref="scheduled_instances")
    schedule = relationship("ScheduleModel", back_populates="scheduled_tasks")
    time_pool = relationship("TimePoolModel", back_populates="scheduled_tasks")
    
    def __repr__(self):
        return f"<TaskSchedule(task_id={self.task_id}, start={self.scheduled_start})>"

class ContextConditionModel(BaseModel):
    """Context condition table model - defines contextual conditions"""
    __tablename__ = "context_conditions"
    
    name = Column(String(100), nullable=False, unique=True)  # "kids_at_school", "home", etc.
    description = Column(String(500), nullable=True)
    
    # Schedule for this condition (e.g., kids at school Mon-Fri 8:30-3:00)
    schedule_pattern = Column(JSON, nullable=True)  # {"monday": [{"start": "08:30", "end": "15:00"}], ...}
    
    # Override dates (e.g., school holidays)
    override_dates = Column(JSON, nullable=True)  # [{"date": "2025-12-25", "active": false}, ...]
    
    def __repr__(self):
        return f"<ContextCondition(id={self.id}, name='{self.name}')>"