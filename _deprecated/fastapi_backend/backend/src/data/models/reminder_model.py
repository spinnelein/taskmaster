"""
Reminder database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base_model import BaseModel
import enum

class ReminderType(enum.Enum):
    """Types of reminders"""
    TASK_START = "task_start"          # Reminder to start a task
    TASK_DUE = "task_due"              # Reminder that task is due soon
    EVENT_START = "event_start"        # Reminder for event starting
    EVENT_PREP = "event_prep"          # Reminder to prepare for event
    MEAL_PREP = "meal_prep"            # Reminder to start meal preparation
    CUSTOM = "custom"                  # Custom reminder

class ReminderStatus(enum.Enum):
    """Status of reminders"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SNOOZED = "snoozed"

class ReminderModel(BaseModel):
    """Reminder table model - Telegram-based notifications"""
    __tablename__ = "reminders"
    
    # Reminder details
    reminder_type = Column(SQLEnum(ReminderType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=True)
    
    # Timing
    scheduled_time = Column(DateTime, nullable=False)
    minutes_before = Column(Integer, default=0)  # Minutes before the associated event/task
    
    # Status tracking
    status = Column(SQLEnum(ReminderStatus), default=ReminderStatus.PENDING)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(String(500), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Snooze functionality
    snooze_until = Column(DateTime, nullable=True)
    snooze_count = Column(Integer, default=0)
    
    # Associated entities
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=True)
    meal_id = Column(String(36), ForeignKey("meals.id"), nullable=True)
    
    # Telegram configuration
    telegram_chat_id = Column(String(100), nullable=True)  # Override default chat ID if needed
    telegram_message_id = Column(String(100), nullable=True)  # For editing/deleting sent messages
    
    # Custom data
    custom_data = Column(JSON, nullable=True)  # Additional data for custom reminders
    
    # Relationships
    task = relationship("TaskModel", backref="reminders")
    event = relationship("EventModel", backref="reminders")
    meal = relationship("MealModel", backref="reminders")
    
    def __repr__(self):
        return f"<Reminder(id={self.id}, type={self.reminder_type.value}, scheduled={self.scheduled_time})>"

class ReminderTemplateModel(BaseModel):
    """Reminder template table model - predefined reminder configurations"""
    __tablename__ = "reminder_templates"
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    
    # Template configuration
    reminder_type = Column(SQLEnum(ReminderType), nullable=False)
    default_minutes_before = Column(Integer, default=15)
    message_template = Column(String(1000), nullable=False)  # Can include placeholders like {task_title}
    
    # Applicability
    applies_to_tasks = Column(Boolean, default=False)
    applies_to_events = Column(Boolean, default=False)
    applies_to_meals = Column(Boolean, default=False)
    
    # Conditions
    condition_tags = Column(JSON, nullable=True)  # Only apply to items with these tags
    
    # Active flag
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<ReminderTemplate(id={self.id}, name='{self.name}')>"