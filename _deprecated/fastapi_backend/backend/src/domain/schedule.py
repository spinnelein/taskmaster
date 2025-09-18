"""
Schedule domain entity
NO EMOJIS
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, time, timedelta
from .task import Task
from .event import Event

class TimeSlot:
    """Represents an available time slot"""
    
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end
        self.duration_minutes = int((end - start).total_seconds() / 60)

class Schedule:
    """Daily schedule with tasks and events"""
    
    def __init__(self, schedule_date: date):
        self.date = schedule_date
        self.events: List[Event] = []
        self.scheduled_tasks: List[Tuple[Task, datetime]] = []
    
    def add_event(self, event: Event):
        """Add an event to the schedule"""
        # Check if event is on this day
        if event.start_time.date() != self.date:
            raise ValueError("Event is not on this schedule date")
        self.events.append(event)
    
    def add_task(self, task: Task, start_time: datetime):
        """Schedule a task at a specific time"""
        if start_time.date() != self.date:
            raise ValueError("Task start time is not on this schedule date")
        
        end_time = start_time + timedelta(minutes=task.duration)
        
        # Check for conflicts
        if self.has_conflict(start_time, end_time):
            raise ValueError("Time slot has conflict")
        
        self.scheduled_tasks.append((task, start_time))
    
    def has_conflict(self, start: datetime, end: datetime) -> bool:
        """Check if time period has conflicts"""
        # Check against blocking events
        for event in self.events:
            if event.blocks_time_period(start, end):
                return True
        
        # Check against scheduled tasks
        for task, task_start in self.scheduled_tasks:
            task_end = task_start + timedelta(minutes=task.duration)
            if not (end <= task_start or start >= task_end):
                return True
        
        return False
    
    def find_free_time(self, duration_minutes: int) -> List[TimeSlot]:
        """Find available time slots of given duration"""
        free_slots = []
        
        # Define work hours (8 AM to 8 PM)
        day_start = datetime.combine(self.date, time(8, 0))
        day_end = datetime.combine(self.date, time(20, 0))
        
        # Get all busy periods
        busy_periods = []
        
        # Add blocking events
        for event in self.events:
            if event.is_blocking:
                busy_periods.append((event.start_time, event.end_time))
        
        # Add scheduled tasks
        for task, start_time in self.scheduled_tasks:
            end_time = start_time + timedelta(minutes=task.duration)
            busy_periods.append((start_time, end_time))
        
        # Sort busy periods
        busy_periods.sort(key=lambda x: x[0])
        
        # Find gaps
        current_time = day_start
        for busy_start, busy_end in busy_periods:
            if busy_start > current_time:
                gap_minutes = int((busy_start - current_time).total_seconds() / 60)
                if gap_minutes >= duration_minutes:
                    free_slots.append(TimeSlot(current_time, busy_start))
            current_time = max(current_time, busy_end)
        
        # Check final gap
        if current_time < day_end:
            gap_minutes = int((day_end - current_time).total_seconds() / 60)
            if gap_minutes >= duration_minutes:
                free_slots.append(TimeSlot(current_time, day_end))
        
        return free_slots