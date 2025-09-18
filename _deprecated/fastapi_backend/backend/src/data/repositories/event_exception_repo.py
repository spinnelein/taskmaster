# Event Exception Repository
# NO EMOJIS

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from src.data.models.event_exception_model import EventExceptionModel, EventSeriesSplitModel
from src.data.repositories.base import BaseRepository


class EventExceptionRepository(BaseRepository[EventExceptionModel]):
    """Repository for event exceptions"""
    
    def __init__(self, db: Session):
        super().__init__(EventExceptionModel, db)
    
    def get_exceptions_for_event(
        self, 
        master_event_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[EventExceptionModel]:
        """Get all exceptions for a master event within date range"""
        query = self.db.query(EventExceptionModel).filter(
            EventExceptionModel.master_event_id == master_event_id
        )
        
        if start_date:
            query = query.filter(EventExceptionModel.occurrence_date >= start_date)
        
        if end_date:
            query = query.filter(EventExceptionModel.occurrence_date <= end_date)
        
        return query.all()
    
    def get_exception_by_date(
        self, 
        master_event_id: str,
        occurrence_date: date
    ) -> Optional[EventExceptionModel]:
        """Get a specific exception by master event and date"""
        return self.db.query(EventExceptionModel).filter(
            EventExceptionModel.master_event_id == master_event_id,
            EventExceptionModel.occurrence_date == occurrence_date
        ).first()
    
    def create_cancellation_exception(
        self,
        master_event_id: str,
        occurrence_date: date
    ) -> EventExceptionModel:
        """Create an exception that cancels an occurrence"""
        exception = EventExceptionModel(
            master_event_id=master_event_id,
            occurrence_date=occurrence_date,
            is_cancelled=True
        )
        self.db.add(exception)
        self.db.commit()
        self.db.refresh(exception)
        return exception
    
    def create_modification_exception(
        self,
        master_event_id: str,
        occurrence_date: date,
        new_start=None,
        new_end=None,
        custom_title=None,
        custom_description=None,
        custom_location=None
    ) -> EventExceptionModel:
        """Create an exception that modifies an occurrence"""
        exception = EventExceptionModel(
            master_event_id=master_event_id,
            occurrence_date=occurrence_date,
            is_rescheduled=bool(new_start or new_end),
            new_start=new_start,
            new_end=new_end,
            custom_title=custom_title,
            custom_description=custom_description,
            custom_location=custom_location
        )
        self.db.add(exception)
        self.db.commit()
        self.db.refresh(exception)
        return exception


class EventSeriesSplitRepository(BaseRepository[EventSeriesSplitModel]):
    """Repository for event series splits"""
    
    def __init__(self, db: Session):
        super().__init__(EventSeriesSplitModel, db)
    
    def get_split_for_event(
        self,
        original_master_id: str
    ) -> Optional[EventSeriesSplitModel]:
        """Get the split record for an original master event"""
        return self.db.query(EventSeriesSplitModel).filter(
            EventSeriesSplitModel.original_master_id == original_master_id
        ).first()
    
    def create_split(
        self,
        original_master_id: str,
        new_master_id: str,
        split_date: date
    ) -> EventSeriesSplitModel:
        """Create a series split record"""
        split = EventSeriesSplitModel(
            original_master_id=original_master_id,
            new_master_id=new_master_id,
            split_date=split_date
        )
        self.db.add(split)
        self.db.commit()
        self.db.refresh(split)
        return split