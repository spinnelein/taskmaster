Quick Fixes Needed:
The UUID issue in SQLite - I see you're using SQLite which doesn't have native UUID support. Let's fix the base_model.py:
python# backend/src/data/models/base_model.py
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
    
    # Use String for UUID compatibility with SQLite
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
Add Alembic setup (optional for now, but good to have):
bashcd backend
alembic init alembicThen edit alembic/env.py to import your models.