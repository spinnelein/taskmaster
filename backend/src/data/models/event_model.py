"""
Event database model - Enhanced
NO EMOJIS
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class EventType(enum.Enum):
    """Types of events"""
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    DEADLINE = "deadline"
    PERSONAL = "personal"
    WORK = "work"
    TRAVEL = "travel"
    MEAL = "meal"
    BREAK = "break"
    EXERCISE = "exercise"
    CUSTOM = "custom"

class EventStatus(enum.Enum):
    """Status of events"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"

class EventModel(BaseModel):
    """Enhanced Event table model"""
    __tablename__ = "events"
    
    # Basic event info
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    # Event classification
    event_type = Column(SQLEnum(EventType), default=EventType.CUSTOM)
    status = Column(SQLEnum(EventStatus), default=EventStatus.SCHEDULED)
    
    # Time pool behavior - CRITICAL for task scheduling
    is_blocking = Column(Boolean, default=True)  # Does this prevent tasks from being scheduled?
    allows_multitasking = Column(Boolean, default=False)  # Can tasks run during this event?
    buffer_before_minutes = Column(Integer, default=0)    # Buffer time before event
    buffer_after_minutes = Column(Integer, default=0)     # Buffer time after event
    
    # Priority and flexibility
    priority = Column(Integer, default=5)  # 1-10, affects scheduling conflicts
    is_moveable = Column(Boolean, default=False)  # Can this event be rescheduled automatically?
    min_notice_hours = Column(Integer, default=0)  # Minimum notice needed to move this event
    
    # Recurrence - Enhanced Master/Exception Pattern
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # Legacy JSON format
    recurrence_rrule = Column(Text, nullable=True)  # New RRULE format (RFC 5545)
    recurrence_end = Column(DateTime, nullable=True)  # Series termination date
    
    # Timezone support
    timezone = Column(String(50), default='America/Los_Angeles')  # Event timezone
    
    # RFC 5545 standard field names (for RRULE compatibility)
    dtstart = Column(DateTime, nullable=True)  # Synonym for start_time
    dtend = Column(DateTime, nullable=True)    # Synonym for end_time
    
    # Master/Instance relationship
    recurrence_master_id = Column(String(36), ForeignKey("events.id"), nullable=True)  # Points to master event
    is_recurrence_master = Column(Boolean, default=False)  # True for the master event
    is_recurrence_exception = Column(Boolean, default=False)  # True if this instance was individually modified
    recurrence_instance_date = Column(DateTime, nullable=True)  # Original date this instance represents
    
    # Legacy field for backward compatibility
    recurrence_parent_id = Column(String(36), nullable=True)  # Deprecated - use recurrence_master_id
    
    # Organization relationships
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    
    # Special relationships
    # Note: meal relationship is defined via MealModel.event_id foreign key
    
    # Attendees and resources
    attendees = Column(JSON, nullable=True)  # Array of attendee objects
    required_resources = Column(JSON, nullable=True)  # Array of required resources
    
    # Notifications
    reminder_minutes_before = Column(JSON, nullable=True)  # Array of reminder times
    notifications_enabled = Column(Boolean, default=True)  # Enable/disable all notifications for this event
    
    # Relationships - ONE WAY ONLY (remove back_populates to break circular dependencies)
    project = relationship("ProjectModel", lazy="noload")
    meal = relationship("MealModel", uselist=False, foreign_keys="MealModel.event_id", lazy="noload")
    
    # Recurring event relationships - ONE WAY ONLY (remove back_populates to break circular dependencies)
    recurrence_master = relationship("EventModel", remote_side="EventModel.id", lazy="noload")
    recurrence_instances = relationship("EventModel", foreign_keys="EventModel.recurrence_master_id", cascade="all, delete-orphan", lazy="noload")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', is_blocking={self.is_blocking})>"
    
    def duration_minutes(self):
        """Calculate event duration in minutes"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0
    
    def creates_time_pool_gap(self):
        """Determine if this event creates gaps where tasks can be scheduled"""
        return not self.is_blocking or self.allows_multitasking