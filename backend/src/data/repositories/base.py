"""
Base repository with common CRUD operations
NO EMOJIS
"""
from typing import TypeVar, Generic, Optional, List, Type, Dict, Any
from sqlalchemy.orm import Session
import uuid

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository with common database operations"""
    
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db
    
    def get(self, entity_id: str) -> Optional[T]:
        """Get entity by ID"""
        return self.db.query(self.model).filter(
            self.model.id == entity_id
        ).first()
    
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID (alias for get method for backwards compatibility)"""
        return self.get(entity_id)
    
    def get_all(self) -> List[T]:
        """Get all entities"""
        return self.db.query(self.model).all()
    
    def create(self, data: Dict[str, Any]) -> T:
        """Create new entity"""
        # Generate ID if not provided
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        entity = self.model(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update entity by ID"""
        entity = self.get(entity_id)
        if not entity:
            return None
        
        for key, value in data.items():
            if hasattr(entity, key):
                # Allow setting boolean False values
                if value is not None or isinstance(value, bool):
                    setattr(entity, key, value)
        
        self.db.commit()
        self.db.refresh(entity)
        
        return entity
    
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID"""
        entity = self.get(entity_id)
        if not entity:
            return False
        
        self.db.delete(entity)
        self.db.commit()
        return True