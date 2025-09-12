"""
Recurrence pattern utility
NO EMOJIS
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dateutil.relativedelta import relativedelta
import calendar

def generate_recurring_events(
    title: str,
    start_time: datetime,
    end_time: datetime,
    recurrence_pattern: Dict[str, Any],
    is_blocking: bool = True,
    location: str = None,
    description: str = "",
    max_events: int = 365  # Prevent infinite generation
) -> List[Dict[str, Any]]:
    """Generate a list of recurring event instances"""
    
    if not recurrence_pattern:
        # No recurrence, return single event
        return [{
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'is_blocking': is_blocking,
            'location': location,
            'description': description,
            'is_recurring': False,
            'recurrence_pattern': None,
            'recurrence_parent_id': None
        }]
    
    events = []
    pattern = recurrence_pattern.get('pattern', 'daily')
    interval = recurrence_pattern.get('interval', 1)
    weekdays = recurrence_pattern.get('weekdays', [])
    end_type = recurrence_pattern.get('end_type', 'never')
    end_after_count = recurrence_pattern.get('end_after_count', 10)
    end_date_str = recurrence_pattern.get('end_date')
    
    # Parse end date if provided
    end_date = None
    if end_date_str and end_type == 'on':
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)  # End of day
        except ValueError:
            end_date = None
    
    # Calculate event duration
    duration = end_time - start_time
    
    # Generate parent event (the original)
    parent_event = {
        'title': title,
        'start_time': start_time,
        'end_time': end_time,
        'is_blocking': is_blocking,
        'location': location,
        'description': description,
        'is_recurring': True,
        'recurrence_pattern': recurrence_pattern,
        'recurrence_parent_id': None
    }
    events.append(parent_event)
    
    current_start = start_time
    count = 1
    
    # Weekday mapping for weekly recurrence
    weekday_map = {
        'Sun': 6, 'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5
    }
    
    while count < max_events:
        # Calculate next occurrence
        if pattern == 'daily':
            current_start += timedelta(days=interval)
        elif pattern == 'weekly':
            if weekdays:
                # Find next occurrence on specified weekdays
                next_start = None
                for _ in range(7 * interval):  # Look within the interval period
                    current_start += timedelta(days=1)
                    current_weekday = current_start.weekday()
                    
                    # Check if this day matches any selected weekdays
                    for weekday in weekdays:
                        if weekday in weekday_map and weekday_map[weekday] == current_weekday:
                            next_start = current_start
                            break
                    
                    if next_start:
                        break
                
                if not next_start:
                    break  # No more valid occurrences
                current_start = next_start
            else:
                current_start += timedelta(weeks=interval)
        elif pattern == 'monthly':
            current_start += relativedelta(months=interval)
        elif pattern == 'yearly':
            current_start += relativedelta(years=interval)
        
        # Check end conditions
        if end_type == 'after' and count >= end_after_count:
            break
        elif end_type == 'on' and end_date and current_start > end_date:
            break
        
        # Create recurring event instance
        current_end = current_start + duration
        
        recurring_event = {
            'title': title,
            'start_time': current_start,
            'end_time': current_end,
            'is_blocking': is_blocking,
            'location': location,
            'description': description,
            'is_recurring': False,  # Instances are not recurring themselves
            'recurrence_pattern': None,
            'recurrence_parent_id': 'parent'  # Will be updated with actual parent ID
        }
        events.append(recurring_event)
        count += 1
    
    return events