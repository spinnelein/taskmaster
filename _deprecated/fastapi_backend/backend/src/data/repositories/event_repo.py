"""
Event repository implementation
NO EMOJIS
"""
from typing import Optional, List
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import pytz
import uuid

from .base import BaseRepository
from ..models.event_model import EventModel

class EventRepository(BaseRepository[EventModel]):
    """Repository for Event entities"""
    
    def __init__(self, db: Session):
        super().__init__(EventModel, db)
        
    def get_by_id(self, event_id: str) -> Optional[EventModel]:
        """Get event by ID"""
        return self.get(event_id)
    
    def save(self, event) -> EventModel:
        """Save event (create or update)"""
        if hasattr(event, 'id') and event.id:
            # Update existing
            self.db.merge(event)
        else:
            # Create new
            event.id = str(uuid.uuid4())
            self.db.add(event)
        
        self.db.commit()
        self.db.refresh(event)
        return event
    
    
    def get_by_date(self, target_date: date) -> List[EventModel]:
        """Get events for a specific date - treating stored times as Pacific time"""
        # Create start and end of day
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # Query events that occur on this date
        return self.db.query(EventModel).filter(
            or_(
                # Events that start during the day
                and_(
                    EventModel.start_time >= start_of_day,
                    EventModel.start_time <= end_of_day
                ),
                # Events that span across the day
                and_(
                    EventModel.start_time < start_of_day,
                    EventModel.end_time > start_of_day
                )
            )
        ).all()
    
    def get_blocking_events(self, start: datetime, end: datetime) -> List[EventModel]:
        """Get blocking events in time range"""
        return self.db.query(EventModel).filter(
            and_(
                EventModel.is_blocking == True,
                EventModel.start_time < end,
                EventModel.end_time > start
            )
        ).all()
    
    def get_overlapping(self, start: datetime, end: datetime) -> List[EventModel]:
        """Get events that overlap with time range"""
        return self.db.query(EventModel).filter(
            and_(
                EventModel.start_time < end,
                EventModel.end_time > start
            )
        ).all()