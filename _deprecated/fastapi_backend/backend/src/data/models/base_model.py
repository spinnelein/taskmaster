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
    
    def to_dict(self, visited=None):
        """Convert model to dictionary for JSON serialization"""
        if visited is None:
            visited = set()
        
        # Prevent infinite recursion by tracking visited objects
        obj_key = (self.__class__.__name__, self.id)
        if obj_key in visited:
            # Return minimal representation for already visited objects
            return {
                'id': self.id,
                'type': self.__class__.__name__
            }
        
        visited.add(obj_key)
        
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Handle different data types
            if value is None:
                result[column.name] = None
            elif isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif hasattr(value, 'value'):  # Handle enum values
                result[column.name] = value.value
            else:
                result[column.name] = value
        
        # Handle relationships (for loaded related objects)
        from sqlalchemy.inspection import inspect
        relationships = inspect(self.__class__).relationships
        for relationship in relationships:
            if hasattr(self, relationship.key):
                related_obj = getattr(self, relationship.key)
                if related_obj is not None:
                    if hasattr(related_obj, '__iter__') and not isinstance(related_obj, str):
                        # Handle one-to-many relationships (lists)
                        result[relationship.key] = [
                            obj.to_dict(visited) if hasattr(obj, 'to_dict') else str(obj) 
                            for obj in related_obj
                        ]
                    else:
                        # Handle one-to-one relationships
                        if hasattr(related_obj, 'to_dict'):
                            result[relationship.key] = related_obj.to_dict(visited)
                        else:
                            result[relationship.key] = str(related_obj)
        
        return result