"""
Base domain entity
NO EMOJIS
"""
from typing import Dict, Any
from datetime import datetime
import uuid

class DomainEntity:
    """Base class for all domain entities"""
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create entity from dictionary"""
        raise NotImplementedError