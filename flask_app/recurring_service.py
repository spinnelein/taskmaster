# recurring_service.py - Recurring event expansion service
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import json

try:
    from dateutil.rrule import rrulestr, rrule, DAILY, WEEKLY
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    print("Warning: python-dateutil not available. Install with: pip install python-dateutil")

from models import Event

class RecurringEventService:
    """Service for handling recurring event expansion and management"""
    
    MAX_OCCURRENCES = 365  # Safety limit
    MAX_YEARS_AHEAD = 2    # Don't look more than 2 years ahead
    
    def __init__(self):
        pass
    
    def expand_events_for_period(self, events: List[Event], start_date: date, end_date: date) -> List[Dict]:
        """
        Expand recurring events for a specific date range.
        
        Args:
            events: List of Event objects (should be master events only)
            start_date: Start of period to expand
            end_date: End of period to expand
            
        Returns:
            List of expanded event dictionaries
        """
        expanded_events = []
        
        for event in events:
            if event.is_recurring and event.is_recurrence_master:
                # Expand recurring event
                occurrences = self._generate_occurrences(event, start_date, end_date)
                expanded_events.extend(occurrences)
            elif not event.is_recurring:
                # Single event - check if it falls in the range
                event_date = event.start_time.date() if event.start_time else None
                if event_date and start_date <= event_date <= end_date:
                    expanded_events.append(event.to_dict())
        
        return expanded_events
    
    def _generate_occurrences(self, event: Event, start_date: date, end_date: date) -> List[Dict]:
        """Generate occurrences for a recurring event"""
        if not DATEUTIL_AVAILABLE:
            # Fallback: just return the original event
            return [event.to_dict()]
        
        if not event.recurrence_rrule and not event.recurrence_pattern:
            # No recurrence rule, treat as single event
            return [event.to_dict()]
        
        occurrences = []
        
        try:
            # Use RRULE if available, fallback to recurrence_pattern
            rrule_str = event.recurrence_rrule or event.recurrence_pattern
            if not rrule_str:
                return [event.to_dict()]
            
            # Parse the RRULE
            if not rrule_str.startswith('RRULE:'):
                rrule_str = f'RRULE:{rrule_str}'
            
            # Use dtstart if available, otherwise use start_time
            dtstart = event.dtstart or event.start_time
            if not dtstart:
                return [event.to_dict()]
            
            # Generate the rule
            rule = rrulestr(rrule_str, dtstart=dtstart)
            
            # Calculate duration for consistent end times
            if event.dtend:
                duration = event.dtend - event.dtstart
            elif event.end_time and event.start_time:
                duration = event.end_time - event.start_time
            else:
                duration = timedelta(hours=1)  # Default 1 hour
            
            count = 0
            for occurrence_start in rule:
                # Safety limits
                if count >= self.MAX_OCCURRENCES:
                    break
                
                occurrence_date = occurrence_start.date()
                
                # Check if beyond our date range
                if occurrence_date > end_date:
                    break
                
                # Only include if within our range
                if occurrence_date >= start_date:
                    occurrence_end = occurrence_start + duration
                    
                    # Create occurrence dictionary
                    occurrence = {
                        'id': f"{event.id}_{occurrence_date.isoformat()}",  # Unique ID for this instance
                        'master_event_id': event.id,
                        'title': event.title,
                        'start': occurrence_start.isoformat(),
                        'end': occurrence_end.isoformat(),
                        'color': '#007bff',  # Blue for recurring events
                        'description': event.description or '',
                        'location': event.location or '',
                        'is_blocking': bool(event.is_blocking),
                        'is_recurring': True,
                        'is_recurrence_master': False,  # This is an instance
                        'is_recurrence_exception': False,
                        'recurrence_instance_date': occurrence_date.isoformat(),
                        'event_type': event.event_type,
                        'status': event.status,
                        'notifications_enabled': bool(event.notifications_enabled) if event.notifications_enabled is not None else True
                    }
                    
                    occurrences.append(occurrence)
                
                count += 1
            
        except Exception as e:
            print(f"Error expanding recurring event {event.id}: {e}")
            # Fallback: return original event
            return [event.to_dict()]
        
        return occurrences
    
    def get_master_events_only(self, events: List[Event]) -> List[Event]:
        """Filter to return only master events (for event lists)"""
        return [
            event for event in events 
            if event.is_master_event()
        ]
    
    def simple_daily_expansion(self, event: Event, start_date: date, end_date: date) -> List[Dict]:
        """
        Simple daily expansion fallback when dateutil is not available.
        Only handles basic daily recurrence.
        """
        if not event.is_recurring:
            return [event.to_dict()]
        
        occurrences = []
        current_date = max(start_date, event.start_time.date())
        duration = event.end_time - event.start_time if event.end_time and event.start_time else timedelta(hours=1)
        
        count = 0
        while current_date <= end_date and count < self.MAX_OCCURRENCES:
            # Create occurrence for this date
            occurrence_start = datetime.combine(current_date, event.start_time.time())
            occurrence_end = occurrence_start + duration
            
            occurrence = {
                'id': f"{event.id}_{current_date.isoformat()}",
                'master_event_id': event.id,
                'title': event.title,
                'start': occurrence_start.isoformat(),
                'end': occurrence_end.isoformat(),
                'color': '#007bff',
                'description': event.description or '',
                'location': event.location or '',
                'is_blocking': bool(event.is_blocking),
                'is_recurring': True,
                'is_recurrence_master': False,
                'is_recurrence_exception': False,
                'recurrence_instance_date': current_date.isoformat(),
                'event_type': event.event_type,
                'status': event.status,
                'notifications_enabled': True
            }
            
            occurrences.append(occurrence)
            
            # Move to next day
            current_date += timedelta(days=1)
            count += 1
        
        return occurrences

# Global service instance
recurring_service = RecurringEventService()