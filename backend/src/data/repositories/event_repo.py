"""
Event repository implementation
NO EMOJIS
"""
from typing import Optional, List
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import pytz

from .base import BaseRepository
from ..models.event_model import EventModel
from ...domain.event import Event

class EventRepository(BaseRepository[Event, EventModel]):
    """Repository for Event entities"""
    
    def __init__(self, session: Session):
        super().__init__(session, Event, EventModel)
    
    def _to_domain(self, db_model: EventModel) -> Event:
        """Convert EventModel to Event domain entity"""
        event = Event(
            title=db_model.title,
            start_time=db_model.start_time,
            end_time=db_model.end_time,
            is_blocking=db_model.is_blocking,
            location=db_model.location,
            description=db_model.description or "",
            is_recurring=db_model.is_recurring or False,
            recurrence_pattern=db_model.recurrence_pattern,
            recurrence_parent_id=db_model.recurrence_parent_id
        )
        # Set ID and timestamps from DB
        event.id = db_model.id
        event.created_at = db_model.created_at
        event.updated_at = db_model.updated_at
        return event
    
    def _to_db_model(self, domain_model: Event) -> EventModel:
        """Convert Event domain entity to EventModel"""
        return EventModel(
            id=domain_model.id,
            title=domain_model.title,
            start_time=domain_model.start_time,
            end_time=domain_model.end_time,
            is_blocking=domain_model.is_blocking,
            location=domain_model.location,
            description=domain_model.description,
            is_recurring=domain_model.is_recurring,
            recurrence_pattern=domain_model.recurrence_pattern,
            recurrence_parent_id=domain_model.recurrence_parent_id,
            created_at=domain_model.created_at,
            updated_at=domain_model.updated_at
        )
    
    def get_by_date(self, target_date: date) -> List[Event]:
        """Get events for a specific date - treating stored times as Pacific time"""
        # Create start and end of day
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        # Query events that occur on this date
        db_models = self.session.query(EventModel).filter(
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
        return [self._to_domain(model) for model in db_models]
    
    def get_blocking_events(self, start: datetime, end: datetime) -> List[Event]:
        """Get blocking events in time range"""
        db_models = self.session.query(EventModel).filter(
            and_(
                EventModel.is_blocking == True,
                EventModel.start_time < end,
                EventModel.end_time > start
            )
        ).all()
        return [self._to_domain(model) for model in db_models]
    
    def get_overlapping(self, start: datetime, end: datetime) -> List[Event]:
        """Get events that overlap with time range"""
        db_models = self.session.query(EventModel).filter(
            and_(
                EventModel.start_time < end,
                EventModel.end_time > start
            )
        ).all()
        return [self._to_domain(model) for model in db_models]