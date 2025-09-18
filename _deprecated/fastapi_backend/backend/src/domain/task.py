"""
Task domain entity
NO EMOJIS
"""
from typing import Optional, Dict, Any
from datetime import date, time, datetime
from .base import DomainEntity

class Task(DomainEntity):
    """Task domain model with business logic"""
    
    def __init__(
        self,
        title: str,
        duration: int,
        urgency: int = 5,
        description: str = "",
        status: str = "active",
        due_date: Optional[date] = None,
        due_time: Optional[time] = None
    ):
        super().__init__()
        self.title = title
        self.duration = duration  # minutes
        self.urgency = urgency
        self.description = description
        self.status = status
        self.due_date = due_date
        self.due_time = due_time
        self.is_completed = False
        self.validate()
    
    def validate(self):
        """Validate task properties"""
        if not self.title:
            raise ValueError("Task title cannot be empty")
        if self.duration <= 0:
            raise ValueError("Duration must be positive")
        if not 1 <= self.urgency <= 10:
            raise ValueError("Urgency must be between 1 and 10")
        if self.status not in ["active", "blocked", "completed"]:
            raise ValueError("Invalid status")
    
    def can_start(self) -> bool:
        """Check if task can be started"""
        return self.status == "active" and not self.is_completed
    
    def block(self):
        """Block the task due to dependencies or external factors"""
        if self.is_completed:
            raise ValueError("Cannot block completed task")
        self.status = "blocked"
        self.updated_at = datetime.utcnow()
    
    def unblock(self):
        """Unblock the task, setting it back to active"""
        if self.status != "blocked":
            raise ValueError("Task is not blocked")
        self.status = "active"
        self.updated_at = datetime.utcnow()
    
    def complete(self):
        """Mark task as completed"""
        if self.is_completed:
            raise ValueError("Task already completed")
        self.status = "completed"
        self.is_completed = True
        self.updated_at = datetime.utcnow()
    
    def update_status(self, status: str):
        """Update task status"""
        old_status = self.status
        self.status = status
        self.validate()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'title': self.title,
            'duration': self.duration,
            'urgency': self.urgency,
            'description': self.description,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'due_time': self.due_time.isoformat() if self.due_time else None,
            'is_completed': self.is_completed
        })
        return data