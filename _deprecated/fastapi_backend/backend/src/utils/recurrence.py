"""
Recurrence pattern utility - Enhanced with RRULE support
NO EMOJIS
"""
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from dateutil.relativedelta import relativedelta
import calendar

# Try to import RRULE functionality, fall back to original if not available
try:
    from dateutil.rrule import rrule, rrulestr, DAILY, WEEKLY, MONTHLY, YEARLY
    from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU
    RRULE_AVAILABLE = True
except ImportError:
    RRULE_AVAILABLE = False

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

def calculate_next_occurrence(base_date: datetime.date, pattern: Dict[str, Any]) -> Optional[datetime.date]:
    """Calculate the next occurrence date for a recurring task"""
    
    if not pattern:
        return None
    
    frequency = pattern.get('frequency', 'daily')
    interval = pattern.get('interval', 1)
    
    try:
        if frequency == 'daily':
            return base_date + timedelta(days=interval)
        elif frequency == 'weekly':
            return base_date + timedelta(weeks=interval)
        elif frequency == 'monthly':
            # Use relativedelta for proper month arithmetic
            base_datetime = datetime.combine(base_date, datetime.min.time())
            next_datetime = base_datetime + relativedelta(months=interval)
            return next_datetime.date()
        elif frequency == 'yearly':
            base_datetime = datetime.combine(base_date, datetime.min.time())
            next_datetime = base_datetime + relativedelta(years=interval)
            return next_datetime.date()
        else:
            # Default to daily if unknown frequency
            return base_date + timedelta(days=interval)
            
    except Exception:
        # Fallback to daily increment if calculation fails
        return base_date + timedelta(days=1)


def json_to_rrule(json_pattern: Dict[str, Any], dtstart: datetime) -> str:
    """
    Convert TaskMaster JSON pattern to RFC 5545 RRULE string.
    Enhanced version with fallback for when python-dateutil is not available.
    """
    if not RRULE_AVAILABLE:
        return ""  # Fallback to empty RRULE
    
    if not json_pattern:
        return ""
    
    pattern = json_pattern.get('pattern', 'daily').lower()
    interval = json_pattern.get('interval', 1)
    weekdays = json_pattern.get('weekdays', [])
    end_type = json_pattern.get('end_type', 'never')
    end_after_count = json_pattern.get('end_after_count')
    end_date_str = json_pattern.get('end_date')
    
    # Build RRULE components
    rrule_parts = [f"FREQ={pattern.upper()}"]
    
    if interval > 1:
        rrule_parts.append(f"INTERVAL={interval}")
    
    # Handle weekdays for weekly patterns
    if pattern == 'weekly' and weekdays:
        weekday_map = {
            'Sun': 'SU', 'Mon': 'MO', 'Tue': 'TU', 'Wed': 'WE', 
            'Thu': 'TH', 'Fri': 'FR', 'Sat': 'SA'
        }
        byday_values = []
        for weekday in weekdays:
            if weekday in weekday_map:
                byday_values.append(weekday_map[weekday])
        if byday_values:
            rrule_parts.append(f"BYDAY={','.join(byday_values)}")
    
    # Handle end conditions
    if end_type == 'after' and end_after_count:
        rrule_parts.append(f"COUNT={end_after_count}")
    elif end_type == 'on' and end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            until_str = end_date.strftime('%Y%m%d')
            rrule_parts.append(f"UNTIL={until_str}")
        except ValueError:
            pass
    
    return ";".join(rrule_parts)


def generate_occurrences_from_rrule(
    dtstart: datetime,
    dtend: datetime,
    rrule_string: str,
    start_range: date,
    end_range: date,
    max_occurrences: int = 365
) -> List[Dict[str, Any]]:
    """
    Generate event occurrences from RRULE within a date range.
    Falls back to JSON-based generation if RRULE is not available.
    """
    if not RRULE_AVAILABLE or not rrule_string:
        # Fallback to single event
        if dtstart.date() >= start_range and dtstart.date() <= end_range:
            return [{
                'start': dtstart,
                'end': dtend,
                'occurrence_date': dtstart.date(),
                'is_exception': False
            }]
        return []
    
    try:
        # Parse RRULE
        rrule_obj = rrulestr(rrule_string, dtstart=dtstart)
        
        # Calculate event duration
        duration = dtend - dtstart
        
        occurrences = []
        count = 0
        
        for occurrence_start in rrule_obj:
            if count >= max_occurrences:
                break
                
            occurrence_date = occurrence_start.date()
            
            # Check if within requested range
            if occurrence_date > end_range:
                break
                
            if occurrence_date >= start_range:
                occurrence_end = occurrence_start + duration
                
                occurrences.append({
                    'start': occurrence_start,
                    'end': occurrence_end,
                    'occurrence_date': occurrence_date,
                    'is_exception': False
                })
            
            count += 1
            
        return occurrences
    
    except Exception as e:
        print(f"RRULE parsing error: {e}")
        # Fallback to single event
        if dtstart.date() >= start_range and dtstart.date() <= end_range:
            return [{
                'start': dtstart,
                'end': dtend,
                'occurrence_date': dtstart.date(),
                'is_exception': False
            }]
        return []