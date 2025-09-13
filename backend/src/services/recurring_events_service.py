"""
Recurring Events Service - Master/Exception Pattern
Handles proper recurring event management with edit modes
NO EMOJIS
"""
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from enum import Enum

from ..data.repositories.event_repo import EventRepository
from ..data.models.event_model import EventModel
from ..utils.recurrence import generate_recurring_events


class RecurringEditMode(Enum):
    """Edit modes for recurring events"""
    THIS_ONLY = "this_only"          # Edit only this instance
    THIS_AND_FUTURE = "this_and_future"  # Edit this and all future instances
    ALL_IN_SERIES = "all_in_series"  # Edit all instances in the series


class RecurringEventsService:
    """Service for managing recurring events with master/exception pattern"""
    
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = EventRepository(db)
    
    def create_recurring_event(self, event_data: Dict[str, Any]) -> EventModel:
        """
        Create a new recurring event with master/instance pattern
        
        Args:
            event_data: Event data including recurrence_pattern
            
        Returns:
            The master event
        """
        if not event_data.get('is_recurring') or not event_data.get('recurrence_pattern'):
            raise ValueError("Event must be recurring with a valid recurrence pattern")
        
        # Create the master event
        master_data = event_data.copy()
        master_data['is_recurrence_master'] = True
        master_data['is_recurrence_exception'] = False
        master_data['recurrence_master_id'] = None
        master_data['recurrence_instance_date'] = None
        
        master_event = self.event_repo.create(master_data)
        
        # Generate recurring instances
        self._generate_instances_for_master(master_event)
        
        return master_event
    
    def edit_recurring_event(
        self, 
        event_id: str, 
        update_data: Dict[str, Any], 
        edit_mode: RecurringEditMode,
        original_date: Optional[datetime] = None
    ) -> List[EventModel]:
        """
        Edit a recurring event based on the specified mode
        
        Args:
            event_id: ID of the event being edited
            update_data: Data to update
            edit_mode: How to apply the edit (this only, this and future, all)
            original_date: Original date for this instance (for THIS_ONLY mode)
            
        Returns:
            List of affected events
        """
        event = self.event_repo.get(event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
        
        # Determine if this is a master or instance
        is_master = event.is_recurrence_master
        master_event = event if is_master else self._get_master_event(event)
        
        if not master_event:
            raise ValueError("Could not find master event for recurring series")
        
        if edit_mode == RecurringEditMode.THIS_ONLY:
            return self._edit_single_instance(event, update_data, original_date)
        
        elif edit_mode == RecurringEditMode.ALL_IN_SERIES:
            return self._edit_entire_series(master_event, update_data)
        
        elif edit_mode == RecurringEditMode.THIS_AND_FUTURE:
            return self._edit_this_and_future(event, update_data, original_date)
        
        else:
            raise ValueError(f"Invalid edit mode: {edit_mode}")
    
    def delete_recurring_event(
        self, 
        event_id: str, 
        edit_mode: RecurringEditMode,
        original_date: Optional[datetime] = None
    ) -> bool:
        """
        Delete a recurring event based on the specified mode
        
        Args:
            event_id: ID of the event being deleted
            edit_mode: How to apply the deletion
            original_date: Original date for this instance (for THIS_ONLY mode)
            
        Returns:
            True if successful
        """
        event = self.event_repo.get(event_id)
        if not event:
            return False
        
        master_event = event if event.is_recurrence_master else self._get_master_event(event)
        
        if edit_mode == RecurringEditMode.THIS_ONLY:
            # Mark as exception (deleted)
            if event.is_recurrence_master:
                # Can't delete master with THIS_ONLY, create exception instead
                return self._create_deletion_exception(master_event, original_date or event.start_time)
            else:
                return self.event_repo.delete(event_id)
        
        elif edit_mode == RecurringEditMode.ALL_IN_SERIES:
            # Delete entire series
            return self._delete_entire_series(master_event)
        
        elif edit_mode == RecurringEditMode.THIS_AND_FUTURE:
            # Delete this and future instances
            return self._delete_this_and_future(event, original_date)
        
        return False
    
    def get_recurring_instances(
        self, 
        master_id: str, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[EventModel]:
        """
        Get all instances of a recurring event within a date range
        
        Args:
            master_id: ID of the master event
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            
        Returns:
            List of event instances
        """
        query = self.db.query(EventModel).filter(
            EventModel.recurrence_master_id == master_id
        )
        
        if start_date:
            query = query.filter(EventModel.start_time >= start_date)
        
        if end_date:
            query = query.filter(EventModel.start_time <= end_date)
        
        return query.order_by(EventModel.start_time).all()
    
    def is_recurring_event(self, event_id: str) -> bool:
        """Check if an event is part of a recurring series"""
        event = self.event_repo.get(event_id)
        return event and (event.is_recurrence_master or event.recurrence_master_id is not None)
    
    def get_master_event(self, event_id: str) -> Optional[EventModel]:
        """Get the master event for any event in a recurring series"""
        event = self.event_repo.get(event_id)
        if not event:
            return None
        
        if event.is_recurrence_master:
            return event
        
        return self._get_master_event(event)
    
    # Private methods
    
    def _get_master_event(self, event: EventModel) -> Optional[EventModel]:
        """Get the master event from an instance"""
        if event.recurrence_master_id:
            return self.event_repo.get(event.recurrence_master_id)
        return None
    
    def _generate_instances_for_master(self, master_event: EventModel) -> List[EventModel]:
        """Generate recurring instances for a master event"""
        if not master_event.recurrence_pattern:
            return []
        
        # Use existing recurrence generation logic
        recurrence_dict = master_event.recurrence_pattern
        recurring_events = generate_recurring_events(
            title=master_event.title,
            start_time=master_event.start_time,
            end_time=master_event.end_time,
            recurrence_pattern=recurrence_dict,
            is_blocking=master_event.is_blocking,
            location=master_event.location,
            description=master_event.description
        )
        
        # Create instances (skip first as it's the master)
        instances = []
        for event_data in recurring_events[1:]:
            instance_data = event_data.copy()
            instance_data['recurrence_master_id'] = master_event.id
            instance_data['is_recurrence_master'] = False
            instance_data['is_recurrence_exception'] = False
            instance_data['recurrence_instance_date'] = instance_data['start_time']
            instance_data['is_recurring'] = False  # Instances are not recurring themselves
            instance_data['recurrence_pattern'] = None
            
            instance = self.event_repo.create(instance_data)
            instances.append(instance)
        
        return instances
    
    def _edit_single_instance(
        self, 
        event: EventModel, 
        update_data: Dict[str, Any],
        original_date: Optional[datetime]
    ) -> List[EventModel]:
        """Edit only a single instance, creating an exception if needed"""
        if event.is_recurrence_master:
            # Create an exception for this date
            return self._create_exception_instance(event, update_data, original_date)
        else:
            # Update the existing instance and mark as exception
            update_data['is_recurrence_exception'] = True
            updated_event = self.event_repo.update(event.id, update_data)
            return [updated_event] if updated_event else []
    
    def _edit_entire_series(self, master_event: EventModel, update_data: Dict[str, Any]) -> List[EventModel]:
        """Edit all events in the series"""
        affected_events = []
        
        # Update master event
        master_update = update_data.copy()
        # Don't change master-specific fields
        master_update.pop('is_recurrence_master', None)
        master_update.pop('recurrence_master_id', None)
        
        updated_master = self.event_repo.update(master_event.id, master_update)
        if updated_master:
            affected_events.append(updated_master)
        
        # Update all non-exception instances
        instances = self.get_recurring_instances(master_event.id)
        for instance in instances:
            if not instance.is_recurrence_exception:
                instance_update = update_data.copy()
                # Don't change instance-specific fields
                instance_update.pop('is_recurring', None)
                instance_update.pop('recurrence_pattern', None)
                instance_update.pop('is_recurrence_master', None)
                
                updated_instance = self.event_repo.update(instance.id, instance_update)
                if updated_instance:
                    affected_events.append(updated_instance)
        
        return affected_events
    
    def _edit_this_and_future(
        self, 
        event: EventModel, 
        update_data: Dict[str, Any],
        original_date: Optional[datetime]
    ) -> List[EventModel]:
        """Edit this instance and all future instances"""
        master_event = event if event.is_recurrence_master else self._get_master_event(event)
        if not master_event:
            return []
        
        # Determine the cutoff date
        cutoff_date = original_date or event.start_time
        
        affected_events = []
        
        # If editing the master and it's before cutoff, update master
        if master_event.start_time >= cutoff_date:
            master_update = update_data.copy()
            updated_master = self.event_repo.update(master_event.id, master_update)
            if updated_master:
                affected_events.append(updated_master)
        
        # Update all instances on or after cutoff date
        instances = self.get_recurring_instances(master_event.id)
        for instance in instances:
            if instance.start_time >= cutoff_date and not instance.is_recurrence_exception:
                instance_update = update_data.copy()
                instance_update.pop('is_recurring', None)
                instance_update.pop('recurrence_pattern', None)
                instance_update.pop('is_recurrence_master', None)
                
                updated_instance = self.event_repo.update(instance.id, instance_update)
                if updated_instance:
                    affected_events.append(updated_instance)
        
        return affected_events
    
    def _create_exception_instance(
        self, 
        master_event: EventModel, 
        update_data: Dict[str, Any],
        exception_date: Optional[datetime]
    ) -> List[EventModel]:
        """Create an exception instance for a specific date"""
        if not exception_date:
            exception_date = master_event.start_time
        
        # Create new exception instance
        exception_data = {
            'title': update_data.get('title', master_event.title),
            'start_time': update_data.get('start_time', exception_date),
            'end_time': update_data.get('end_time', exception_date + (master_event.end_time - master_event.start_time)),
            'is_blocking': update_data.get('is_blocking', master_event.is_blocking),
            'location': update_data.get('location', master_event.location),
            'description': update_data.get('description', master_event.description),
            'recurrence_master_id': master_event.id,
            'is_recurrence_master': False,
            'is_recurrence_exception': True,
            'recurrence_instance_date': exception_date,
            'is_recurring': False,
            'recurrence_pattern': None
        }
        
        exception_instance = self.event_repo.create(exception_data)
        return [exception_instance] if exception_instance else []
    
    def _delete_entire_series(self, master_event: EventModel) -> bool:
        """Delete the entire recurring series"""
        try:
            # Delete all instances first
            instances = self.get_recurring_instances(master_event.id)
            for instance in instances:
                self.event_repo.delete(instance.id)
            
            # Delete master event
            return self.event_repo.delete(master_event.id)
        except Exception:
            return False
    
    def _delete_this_and_future(self, event: EventModel, original_date: Optional[datetime]) -> bool:
        """Delete this instance and all future instances"""
        master_event = event if event.is_recurrence_master else self._get_master_event(event)
        if not master_event:
            return False
        
        cutoff_date = original_date or event.start_time
        
        try:
            # Delete future instances
            instances = self.get_recurring_instances(master_event.id)
            for instance in instances:
                if instance.start_time >= cutoff_date:
                    self.event_repo.delete(instance.id)
            
            # If master is on or after cutoff, delete it too
            if master_event.start_time >= cutoff_date:
                return self.event_repo.delete(master_event.id)
            
            return True
        except Exception:
            return False
    
    def _create_deletion_exception(self, master_event: EventModel, deletion_date: datetime) -> bool:
        """Create an exception to mark a specific date as deleted"""
        # Create a hidden exception instance to mark this date as deleted
        exception_data = {
            'title': f"[DELETED] {master_event.title}",
            'start_time': deletion_date,
            'end_time': deletion_date + (master_event.end_time - master_event.start_time),
            'is_blocking': False,
            'location': master_event.location,
            'description': "This instance was deleted",
            'recurrence_master_id': master_event.id,
            'is_recurrence_master': False,
            'is_recurrence_exception': True,
            'recurrence_instance_date': deletion_date,
            'is_recurring': False,
            'recurrence_pattern': None
        }
        
        exception_instance = self.event_repo.create(exception_data)
        return exception_instance is not None