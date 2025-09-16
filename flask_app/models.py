# models.py - Separate models file to avoid circular imports
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# Create db instance that will be initialized by the app
db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    event_type = db.Column(db.String(20))
    status = db.Column(db.String(20))
    is_blocking = db.Column(db.Boolean, default=True)
    allows_multitasking = db.Column(db.Boolean)
    buffer_before_minutes = db.Column(db.Integer)
    buffer_after_minutes = db.Column(db.Integer)
    priority = db.Column(db.String(20))
    is_moveable = db.Column(db.Boolean)
    min_notice_hours = db.Column(db.Integer)
    is_recurring = db.Column(db.Boolean)
    recurrence_pattern = db.Column(db.Text)
    recurrence_master_id = db.Column(db.String(36))
    is_recurrence_master = db.Column(db.Boolean)
    is_recurrence_exception = db.Column(db.Boolean)
    recurrence_instance_date = db.Column(db.Date)
    recurrence_parent_id = db.Column(db.String(36))
    project_id = db.Column(db.String(36))
    attendees = db.Column(db.Text)
    required_resources = db.Column(db.Text)
    reminder_minutes_before = db.Column(db.Integer)
    notifications_enabled = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    # Additional recurring event columns from backend schema
    recurrence_rrule = db.Column(db.Text)
    recurrence_end = db.Column(db.DateTime)
    timezone = db.Column(db.String(50))
    dtstart = db.Column(db.DateTime)
    dtend = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'start': self.start_time.isoformat() if self.start_time else '',
            'end': self.end_time.isoformat() if self.end_time else '',
            'color': '#007bff' if self.is_recurring else ('#FF6B6B' if self.is_blocking else '#4ECDC4'),
            'description': self.description or '',
            'location': self.location or '',
            'is_blocking': bool(self.is_blocking),
            'is_recurring': bool(self.is_recurring),
            'is_recurrence_master': bool(self.is_recurrence_master),
            'is_recurrence_exception': bool(self.is_recurrence_exception),
            'recurrence_instance_date': self.recurrence_instance_date.isoformat() if self.recurrence_instance_date else None,
            'recurrence_rrule': self.recurrence_rrule,
            'event_type': self.event_type,
            'status': self.status,
            'notifications_enabled': bool(self.notifications_enabled) if self.notifications_enabled is not None else True
        }
    
    def is_master_event(self):
        """Check if this is a master recurring event (should be shown in event lists)"""
        return not self.is_recurrence_exception and not self.recurrence_instance_date

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)  # minutes
    urgency = db.Column(db.Integer)  # 1-10
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20))
    due_date = db.Column(db.Date)
    due_time = db.Column(db.Time)
    is_completed = db.Column(db.Boolean)  # Note: actual column name
    is_divisible = db.Column(db.Boolean)
    min_chunk_size = db.Column(db.Integer)
    required_weather = db.Column(db.Text)
    required_context = db.Column(db.Text)
    equipment_needed = db.Column(db.Text)
    depends_on_task_ids = db.Column(db.Text)
    blocks_task_ids = db.Column(db.Text)
    initiative_id = db.Column(db.String(36))
    project_id = db.Column(db.String(36))
    phase_id = db.Column(db.String(36))
    meal_id = db.Column(db.String(36))
    queue_position = db.Column(db.Integer)
    auto_scheduled = db.Column(db.Boolean)
    estimated_cost = db.Column(db.Numeric)
    actual_cost = db.Column(db.Numeric)
    is_recurring = db.Column(db.Boolean)
    recurrence_pattern = db.Column(db.Text)
    parent_task_id = db.Column(db.String(36))
    last_completed_at = db.Column(db.DateTime)
    partial_completion_minutes = db.Column(db.Integer)
    remaining_minutes = db.Column(db.Integer)
    is_snoozed = db.Column(db.Boolean)
    snoozed_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    recurrence_days = db.Column(db.Integer)  # Days between recurring instances
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'duration': self.duration or 0,
            'urgency': self.urgency or 5,
            'priority': self.priority or 'medium',
            'status': self.status or 'active',
            'completed': self.is_completed or False,  # Map to correct column
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'initiative_id': self.initiative_id,
            'parent_task_id': self.parent_task_id,
            'recurrence_days': self.recurrence_days,
            'is_recurring': bool(self.recurrence_days and self.recurrence_days > 0)
        }

class Initiative(db.Model):
    __tablename__ = 'initiatives'
    
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20))  # ACTIVE, COMPLETED, PAUSED
    is_template = db.Column(db.Boolean, default=False)
    target_completion_count = db.Column(db.Integer)
    current_completion_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    
    # Following plan.md - initiatives should have task_templates JSON field
    # For now, we'll work with existing schema and add task_templates functionality in API layer
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status or 'ACTIVE',
            'is_template': bool(self.is_template),
            'target_completion_count': self.target_completion_count or 0,
            'current_completion_count': self.current_completion_count or 0,
            'progress_percentage': self.calculate_progress(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'task_count': self.get_task_count()
        }
    
    def calculate_progress(self):
        """Calculate completion percentage"""
        if not self.target_completion_count or self.target_completion_count == 0:
            return 0
        percentage = (self.current_completion_count / self.target_completion_count) * 100
        return min(100, max(0, round(percentage, 1)))
    
    def get_task_count(self):
        """Get count of tasks associated with this initiative"""
        # In Flask, we'll query tasks separately to avoid relationship issues
        from sqlalchemy import text
        result = db.session.execute(
            text("SELECT COUNT(*) FROM tasks WHERE initiative_id = :init_id AND is_completed = 0"),
            {"init_id": self.id}
        ).scalar()
        return result or 0