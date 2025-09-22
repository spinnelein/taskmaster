# base.py - Base model classes and shared functionality
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

# Create db instance that will be initialized by the app
db = SQLAlchemy()


class BaseModel(db.Model):
    """Base model class with common fields and functionality"""
    __abstract__ = True
    
    id = db.Column(db.String(36), primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
    
    def save(self):
        """Save the model to database"""
        self.updated_at = datetime.utcnow()
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the model from database"""
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert model to dictionary - to be overridden by subclasses"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class JSONFieldMixin:
    """Mixin for handling JSON fields"""
    
    def parse_json_field(self, field_value):
        """Parse a JSON field safely"""
        if not field_value:
            return []
        
        import json
        try:
            return json.loads(field_value) if isinstance(field_value, str) else field_value
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_json_field(self, field_value):
        """Set a JSON field safely"""
        import json
        return json.dumps(field_value) if field_value else None