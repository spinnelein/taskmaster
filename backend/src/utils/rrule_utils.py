"""
RRULE utilities for RFC 5545 compliant recurring events
Handles conversion between JSON patterns and RRULE format
NO EMOJIS
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from dateutil.rrule import rrule, rrulestr, DAILY, WEEKLY, MONTHLY, YEARLY
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU
import json


# Weekday mapping for RRULE
WEEKDAY_MAP = {
    'MO': MO, 'TU': TU, 'WE': WE, 'TH': TH, 'FR': FR, 'SA': SA, 'SU': SU,
    'Mon': MO, 'Tue': TU, 'Wed': WE, 'Thu': TH, 'Fri': FR, 'Sat': SA, 'Sun': SU,
    'monday': MO, 'tuesday': TU, 'wednesday': WE, 'thursday': TH, 
    'friday': FR, 'saturday': SA, 'sunday': SU
}

FREQUENCY_MAP = {
    'daily': DAILY,
    'weekly': WEEKLY, 
    'monthly': MONTHLY,
    'yearly': YEARLY
}


def json_to_rrule(json_pattern: Dict[str, Any], dtstart: datetime) -> str:
    """
    Convert TaskMaster JSON pattern to RFC 5545 RRULE string.
    
    Args:
        json_pattern: TaskMaster JSON recurrence pattern
        dtstart: Start datetime for the recurrence
        
    Returns:
        RRULE string in RFC 5545 format
        
    Example:
        {"pattern": "weekly", "interval": 2, "weekdays": ["Mon", "Wed"]}
        -> "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE"
    """
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
        byday_values = []
        for weekday in weekdays:
            if weekday in WEEKDAY_MAP:
                byday_values.append(str(WEEKDAY_MAP[weekday]))
        if byday_values:
            rrule_parts.append(f"BYDAY={','.join(byday_values)}")
    
    # Handle end conditions
    if end_type == 'after' and end_after_count:
        rrule_parts.append(f"COUNT={end_after_count}")
    elif end_type == 'on' and end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Format as YYYYMMDD
            until_str = end_date.strftime('%Y%m%d')
            rrule_parts.append(f"UNTIL={until_str}")
        except ValueError:
            pass  # Invalid date format, skip
    
    return ";".join(rrule_parts)


def rrule_to_json(rrule_string: str) -> Dict[str, Any]:
    """
    Convert RRULE string back to TaskMaster JSON pattern.
    
    Args:
        rrule_string: RFC 5545 RRULE string
        
    Returns:
        TaskMaster JSON pattern dictionary
    """
    if not rrule_string:
        return {}
    
    # Parse RRULE components
    components = {}
    for part in rrule_string.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            components[key] = value
    
    # Convert to JSON format
    json_pattern = {}
    
    # Frequency
    freq = components.get('FREQ', 'DAILY').lower()
    json_pattern['pattern'] = freq
    
    # Interval
    interval = int(components.get('INTERVAL', 1))
    json_pattern['interval'] = interval
    
    # Weekdays (for weekly patterns)
    if 'BYDAY' in components:
        byday = components['BYDAY']
        weekdays = []
        for day_code in byday.split(','):
            # Map RRULE weekday codes back to our format
            reverse_map = {v: k for k, v in WEEKDAY_MAP.items() if len(k) == 3}
            for rrule_obj, day_str in reverse_map.items():
                if str(rrule_obj) == day_code:
                    weekdays.append(day_str)
                    break
        json_pattern['weekdays'] = weekdays
    else:
        json_pattern['weekdays'] = []
    
    # End conditions
    if 'COUNT' in components:
        json_pattern['end_type'] = 'after'
        json_pattern['end_after_count'] = int(components['COUNT'])
    elif 'UNTIL' in components:
        json_pattern['end_type'] = 'on'
        until_str = components['UNTIL']
        # Parse YYYYMMDD format
        try:
            until_date = datetime.strptime(until_str, '%Y%m%d')
            json_pattern['end_date'] = until_date.strftime('%Y-%m-%d')
        except ValueError:
            json_pattern['end_type'] = 'never'
    else:
        json_pattern['end_type'] = 'never'
    
    return json_pattern


def generate_occurrences(
    dtstart: datetime,
    dtend: datetime,
    rrule_string: str,
    start_range: date,
    end_range: date,
    max_occurrences: int = 365
) -> List[Dict[str, Any]]:
    """
    Generate event occurrences from RRULE within a date range.
    
    Args:
        dtstart: Start datetime of the master event
        dtend: End datetime of the master event
        rrule_string: RRULE string for recurrence pattern
        start_range: Start of date range to generate
        end_range: End of date range to generate
        max_occurrences: Safety limit for number of occurrences
        
    Returns:
        List of occurrence dictionaries with start/end times
    """
    if not rrule_string:
        # Single event
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
    
    except Exception as e:
        # If RRULE parsing fails, fall back to single event
        print(f"RRULE parsing error: {e}")
        if dtstart.date() >= start_range and dtstart.date() <= end_range:
            return [{
                'start': dtstart,
                'end': dtend,
                'occurrence_date': dtstart.date(),
                'is_exception': False
            }]
        return []
    
    return occurrences


def validate_rrule(rrule_string: str) -> bool:
    """
    Validate that an RRULE string is properly formatted.
    
    Args:
        rrule_string: RRULE string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not rrule_string:
        return False
    
    try:
        # Try to parse with a dummy start date
        rrulestr(rrule_string, dtstart=datetime.now())
        return True
    except Exception:
        return False


def migrate_json_to_rrule(json_pattern: Dict[str, Any], dtstart: datetime) -> str:
    """
    Migration helper to convert existing JSON patterns to RRULE.
    
    Args:
        json_pattern: Existing JSON pattern
        dtstart: Start datetime for the event
        
    Returns:
        RRULE string
    """
    try:
        return json_to_rrule(json_pattern, dtstart)
    except Exception as e:
        print(f"Migration error for pattern {json_pattern}: {e}")
        # Fallback to daily pattern
        return "FREQ=DAILY;COUNT=1"