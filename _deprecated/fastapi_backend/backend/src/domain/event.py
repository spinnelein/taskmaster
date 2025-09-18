"""
Event domain entity
NO EMOJIS
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from .base import DomainEntity

class Event(DomainEntity):
    """Event domain model with business logic"""
    
    def __init__(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        is_blocking: bool = True,
        location: Optional[str] = None,
        description: str = "",
        is_recurring: bool = False,
        recurrence_pattern: Optional[Dict[str, Any]] = None,
        recurrence_parent_id: Optional[str] = None
    ):
        super().__init__()
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.is_blocking = is_blocking
        self.location = location
        self.description = description
        self.is_recurring = is_recurring
        self.recurrence_pattern = recurrence_pattern
        self.recurrence_parent_id = recurrence_parent_id
        self.validate()
    
    def validate(self):
        """Validate event properties"""
        if not self.title:
            raise ValueError("Event title cannot be empty")
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
    
    def duration_minutes(self) -> int:
        """Calculate duration in minutes"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    def blocks_time_period(self, start: datetime, end: datetime) -> bool:
        """Check if event blocks a time period"""
        if not self.is_blocking:
            return False
        # Check for overlap
        return not (end <= self.start_time or start >= self.end_time)
    
    def overlaps_with(self, other: 'Event') -> bool:
        """Check if this event overlaps with another"""
        return not (
            other.end_time <= self.start_time or 
            other.start_time >= self.end_time
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'title': self.title,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'is_blocking': self.is_blocking,
            'location': self.location,
            'description': self.description,
            'is_recurring': self.is_recurring,
            'recurrence_pattern': self.recurrence_pattern,
            'recurrence_parent_id': self.recurrence_parent_id,
            'duration_minutes': self.duration_minutes()
        })
        return data