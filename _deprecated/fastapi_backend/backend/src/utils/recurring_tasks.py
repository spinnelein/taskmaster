"""
Recurring task utility functions
NO EMOJIS
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dateutil.relativedelta import relativedelta


def calculate_next_due_date(
    completion_date: datetime,
    recurrence_pattern: Dict[str, Any]
) -> Optional[datetime]:
    """
    Calculate the next due date for a recurring task based on completion date and frequency.
    
    Args:
        completion_date: When the task was completed
        recurrence_pattern: Dictionary with frequency and interval
                          Example: {"frequency": "days", "interval": 2}
    
    Returns:
        Next due date or None if pattern is invalid
    """
    if not recurrence_pattern:
        return None
    
    frequency = recurrence_pattern.get("frequency", "").lower()
    interval = recurrence_pattern.get("interval", 1)
    
    if not frequency or interval <= 0:
        return None
    
    try:
        if frequency == "days":
            return completion_date + timedelta(days=interval)
        elif frequency == "weeks":
            return completion_date + timedelta(weeks=interval)
        elif frequency == "months":
            return completion_date + relativedelta(months=interval)
        elif frequency == "years":
            return completion_date + relativedelta(years=interval)
        else:
            # Unsupported frequency
            return None
    except Exception:
        return None


def should_generate_recurring_task(task) -> bool:
    """
    Check if a task should generate a recurring instance when completed.
    
    Args:
        task: TaskModel instance
        
    Returns:
        True if task should generate recurring instance
    """
    # Must belong to an initiative
    if not task.initiative_id:
        return False
    
    # Must have recurrence pattern
    if not task.recurrence_pattern:
        return False
    
    # Don't create infinite chains - only master tasks can generate instances
    if task.parent_task_id:
        return False
    
    return True


def create_recurring_task_data(
    original_task,
    next_due_date: datetime,
    completion_date: datetime
) -> Dict[str, Any]:
    """
    Create data for a new recurring task instance.
    
    Args:
        original_task: The completed task
        next_due_date: When the new task should be due
        completion_date: When the original task was completed
        
    Returns:
        Dictionary of data for creating new task
    """
    return {
        # Copy core task properties
        "title": original_task.title,
        "description": original_task.description,
        "duration": original_task.duration,
        "urgency": original_task.urgency,
        "priority": original_task.priority,
        "status": "active",  # New task starts as active
        
        # Set new due date
        "due_date": next_due_date.date() if next_due_date else None,
        "due_time": original_task.due_time,  # Keep same time of day
        
        # Copy task characteristics
        "is_divisible": original_task.is_divisible,
        "min_chunk_size": original_task.min_chunk_size,
        "required_weather": original_task.required_weather,
        "required_context": original_task.required_context,
        "equipment_needed": original_task.equipment_needed,
        
        # Link to original initiative and task
        "initiative_id": original_task.initiative_id,
        "project_id": original_task.project_id,
        "phase_id": original_task.phase_id,
        
        # Mark as recurring instance
        "is_recurring": True,
        "recurrence_pattern": original_task.recurrence_pattern,
        "parent_task_id": original_task.id,
        
        # Reset completion fields
        "is_completed": False,
        "last_completed_at": None,
        "partial_completion_minutes": 0,
        "remaining_minutes": original_task.duration,
        
        # Reset snooze
        "is_snoozed": False,
        "snoozed_until": None
    }