"""
Event Exception Model - For recurring event modifications
Industry standard approach for handling exceptions to recurring events
NO EMOJIS
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Date
from .base_model import BaseModel


class EventExceptionModel(BaseModel):
    """
    Event exceptions table for tracking modifications to recurring event instances.
    Follows industry standard master/exception pattern.
    """
    __tablename__ = "event_exceptions"
    
    # References the master event
    master_event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    # Which occurrence this exception affects (original date)
    occurrence_date = Column(Date, nullable=False)
    
    # Exception type
    is_cancelled = Column(Boolean, default=False, nullable=False)
    is_rescheduled = Column(Boolean, default=False, nullable=False)
    
    # Override fields (NULL means use master event's value)
    new_start = Column(DateTime, nullable=True)
    new_end = Column(DateTime, nullable=True)
    custom_title = Column(String(255), nullable=True)
    custom_description = Column(Text, nullable=True)
    custom_location = Column(String(255), nullable=True)
    
    def __repr__(self):
        return f"<EventException(master_id={self.master_event_id}, date={self.occurrence_date}, cancelled={self.is_cancelled})>"


class EventSeriesSplitModel(BaseModel):
    """
    Event series splits table for tracking "this and future" modifications.
    Records when a recurring series is split into two separate series.
    """
    __tablename__ = "event_series_splits"
    
    # Original event that was split
    original_event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    # New event created for future occurrences
    new_event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    
    # Date when the split occurred
    split_date = Column(Date, nullable=False)
    
    def __repr__(self):
        return f"<EventSeriesSplit(original={self.original_event_id}, new={self.new_event_id}, split_date={self.split_date})>"