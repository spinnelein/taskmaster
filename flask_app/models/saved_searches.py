"""
Saved Searches Model for Advanced Search Features

Allows users to save frequently used search queries with metadata
and preferences for quick access and reuse.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from datetime import datetime
import uuid
import json

from .base import db, BaseModel


class SavedSearch(BaseModel):
    """Model for user-saved search queries"""
    
    __tablename__ = 'saved_searches'
    
    # Core fields
    name = db.Column(db.String(200), nullable=False)
    query = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Search parameters
    entity_types = db.Column(db.JSON, nullable=True)  # List of entity types
    filters = db.Column(db.JSON, nullable=True)  # Additional filters
    sort_order = db.Column(db.String(100), nullable=True)
    
    # User preferences
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
    color = db.Column(db.String(7), nullable=True)  # Hex color code
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    # Categories and tags
    category = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.JSON, nullable=True)  # List of tags
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.entity_types:
            self.entity_types = []
        if not self.filters:
            self.filters = {}
        if not self.tags:
            self.tags = []
    
    def to_dict(self):
        """Convert saved search to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'name': self.name,
            'query': self.query,
            'description': self.description,
            'entity_types': self.entity_types or [],
            'filters': self.filters or {},
            'sort_order': self.sort_order,
            'is_public': self.is_public,
            'is_favorite': self.is_favorite,
            'color': self.color,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'category': self.category,
            'tags': self.tags or []
        })
        return base_dict
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def to_search_params(self):
        """Convert saved search to search parameters"""
        return {
            'query': self.query,
            'entity_types': self.entity_types,
            'filters': self.filters,
            'sort_order': self.sort_order
        }
    
    @classmethod
    def create_from_search_params(cls, name, query, entity_types=None, 
                                 filters=None, sort_order=None, **kwargs):
        """Create saved search from search parameters"""
        return cls(
            name=name,
            query=query,
            entity_types=entity_types or [],
            filters=filters or {},
            sort_order=sort_order,
            **kwargs
        )
    
    @classmethod
    def get_popular_searches(cls, limit=10):
        """Get most popular saved searches"""
        return cls.query.filter(
            cls.is_public == True
        ).order_by(
            cls.usage_count.desc(),
            cls.last_used_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_recent_searches(cls, limit=10):
        """Get recently used saved searches"""
        return cls.query.filter(
            cls.last_used_at.isnot(None)
        ).order_by(
            cls.last_used_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_by_category(cls, category, limit=20):
        """Get saved searches by category"""
        return cls.query.filter(
            cls.category == category
        ).order_by(
            cls.name.asc()
        ).limit(limit).all()
    
    @classmethod
    def search_by_name(cls, search_term, limit=10):
        """Search saved searches by name"""
        return cls.query.filter(
            cls.name.like(f'%{search_term}%')
        ).order_by(
            cls.usage_count.desc()
        ).limit(limit).all()


class SearchTemplate(BaseModel):
    """Model for search query templates"""
    
    __tablename__ = 'search_templates'
    
    # Core fields
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    query_template = db.Column(db.Text, nullable=False)  # Template with placeholders
    
    # Template configuration
    parameters = db.Column(db.JSON, nullable=False)  # Parameter definitions
    default_values = db.Column(db.JSON, nullable=True)  # Default parameter values
    
    # Metadata
    category = db.Column(db.String(100), nullable=True)
    is_system_template = db.Column(db.Boolean, default=False, nullable=False)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.parameters:
            self.parameters = {}
        if not self.default_values:
            self.default_values = {}
    
    def to_dict(self):
        """Convert search template to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'name': self.name,
            'description': self.description,
            'query_template': self.query_template,
            'parameters': self.parameters or {},
            'default_values': self.default_values or {},
            'category': self.category,
            'is_system_template': self.is_system_template,
            'usage_count': self.usage_count
        })
        return base_dict
    
    def render_query(self, parameter_values=None):
        """Render template with parameter values"""
        values = self.default_values.copy()
        if parameter_values:
            values.update(parameter_values)
        
        try:
            # Simple template rendering (replace {param} with values)
            rendered_query = self.query_template
            for param, value in values.items():
                placeholder = f"{{{param}}}"
                rendered_query = rendered_query.replace(placeholder, str(value))
            
            return rendered_query
        except Exception:
            return self.query_template
    
    def validate_parameters(self, parameter_values):
        """Validate provided parameter values"""
        errors = []
        
        for param_name, param_config in self.parameters.items():
            required = param_config.get('required', False)
            param_type = param_config.get('type', 'string')
            
            if required and param_name not in parameter_values:
                errors.append(f"Required parameter '{param_name}' is missing")
                continue
            
            if param_name in parameter_values:
                value = parameter_values[param_name]
                
                # Type validation
                if param_type == 'integer':
                    try:
                        int(value)
                    except ValueError:
                        errors.append(f"Parameter '{param_name}' must be an integer")
                
                elif param_type == 'date':
                    try:
                        datetime.fromisoformat(str(value))
                    except ValueError:
                        errors.append(f"Parameter '{param_name}' must be a valid date")
        
        return errors
    
    @classmethod
    def get_system_templates(cls):
        """Get all system templates"""
        return cls.query.filter(cls.is_system_template == True).all()
    
    @classmethod
    def get_by_category(cls, category):
        """Get templates by category"""
        return cls.query.filter(cls.category == category).all()


# Initialize default search templates
def create_default_search_templates():
    """Create default system search templates"""
    default_templates = [
        {
            'name': 'Tasks by Priority',
            'description': 'Find tasks by priority level',
            'query_template': 'type:task priority:{priority}',
            'parameters': {
                'priority': {
                    'type': 'string',
                    'required': True,
                    'options': ['low', 'medium', 'high', 'urgent']
                }
            },
            'default_values': {'priority': 'high'},
            'category': 'tasks',
            'is_system_template': True
        },
        {
            'name': 'Events in Date Range',
            'description': 'Find events within a specific date range',
            'query_template': 'type:event date_from:{start_date} date_to:{end_date}',
            'parameters': {
                'start_date': {
                    'type': 'date',
                    'required': True
                },
                'end_date': {
                    'type': 'date',
                    'required': True
                }
            },
            'category': 'events',
            'is_system_template': True
        },
        {
            'name': 'Project Content Search',
            'description': 'Search within specific project',
            'query_template': 'project:{project_name} {search_term}',
            'parameters': {
                'project_name': {
                    'type': 'string',
                    'required': True
                },
                'search_term': {
                    'type': 'string',
                    'required': False
                }
            },
            'category': 'projects',
            'is_system_template': True
        }
    ]
    
    try:
        for template_data in default_templates:
            existing = SearchTemplate.query.filter_by(
                name=template_data['name'],
                is_system_template=True
            ).first()
            
            if not existing:
                template = SearchTemplate(**template_data)
                db.session.add(template)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to create default search templates: {e}")