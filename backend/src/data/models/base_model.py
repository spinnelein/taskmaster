"""
Base model with common fields
NO EMOJIS
"""
from sqlalchemy import Column, DateTime, String
import uuid
from datetime import datetime
from ..database import Base

class BaseModel(Base):
    """Base model with id and timestamps"""
    __abstract__ = True
    
    id = Column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        nullable=False
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )