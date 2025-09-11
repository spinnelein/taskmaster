"""
Base repository with common CRUD operations
NO EMOJIS
"""
from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod
import uuid

DomainModel = TypeVar('DomainModel')
DBModel = TypeVar('DBModel')

class BaseRepository(Generic[DomainModel, DBModel], ABC):
    """Base repository with common database operations"""
    
    def __init__(self, session: Session, domain_class: Type[DomainModel], db_class: Type[DBModel]):
        self.session = session
        self.domain_class = domain_class
        self.db_class = db_class
    
    @abstractmethod
    def _to_domain(self, db_model: DBModel) -> DomainModel:
        """Convert database model to domain model"""
        pass
    
    @abstractmethod
    def _to_db_model(self, domain_model: DomainModel) -> DBModel:
        """Convert domain model to database model"""
        pass
    
    def get_by_id(self, entity_id: str) -> Optional[DomainModel]:
        """Get entity by ID"""
        db_model = self.session.query(self.db_class).filter(
            self.db_class.id == entity_id
        ).first()
        
        if db_model:
            return self._to_domain(db_model)
        return None
    
    def get_all(self) -> List[DomainModel]:
        """Get all entities"""
        db_models = self.session.query(self.db_class).all()
        return [self._to_domain(model) for model in db_models]
    
    def save(self, entity: DomainModel) -> DomainModel:
        """Save or update entity"""
        db_model = self._to_db_model(entity)
        
        # Check if exists
        existing = self.session.query(self.db_class).filter(
            self.db_class.id == db_model.id
        ).first()
        
        if existing:
            # Update existing
            for key, value in db_model.__dict__.items():
                if not key.startswith('_'):
                    setattr(existing, key, value)
            db_model = existing
        else:
            # Add new
            self.session.add(db_model)
        
        self.session.commit()
        self.session.refresh(db_model)
        return self._to_domain(db_model)
    
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID"""
        db_model = self.session.query(self.db_class).filter(
            self.db_class.id == entity_id
        ).first()
        
        if db_model:
            self.session.delete(db_model)
            self.session.commit()
            return True
        return False