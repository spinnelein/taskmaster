"""
Query Utilities for Enhanced REST API

Provides pagination, filtering, sorting, and field selection capabilities
for all API endpoints. Follows CODING_STANDARDS.md compliance.
"""
from flask import request
from sqlalchemy import desc, asc, and_, or_, func
from datetime import datetime, date, timedelta
import json


class QueryEnhancer:
    """Enhances SQLAlchemy queries with REST API features"""
    
    def __init__(self, query, model_class):
        self.query = query
        self.model_class = model_class
        self.total_count = None
    
    def apply_pagination(self, default_limit=20, max_limit=100):
        """Apply limit/offset pagination to query"""
        # Get pagination parameters from request
        try:
            limit = min(int(request.args.get('limit', default_limit)), max_limit)
            offset = int(request.args.get('offset', 0))
        except (ValueError, TypeError):
            limit = default_limit
            offset = 0
        
        # Store total count before pagination
        self.total_count = self.query.count()
        
        # Apply pagination
        self.query = self.query.limit(limit).offset(offset)
        
        return self
    
    def apply_sorting(self, allowed_fields, default_sort='created_at:desc'):
        """Apply multi-field sorting with direction control"""
        # Get sort parameter (format: field1:asc,field2:desc)
        sort_param = request.args.get('sort', default_sort)
        
        if sort_param:
            sort_parts = sort_param.split(',')
            for sort_part in sort_parts:
                if ':' in sort_part:
                    field, direction = sort_part.split(':', 1)
                else:
                    field = sort_part
                    direction = 'asc'
                
                # Validate field is allowed
                if field in allowed_fields and hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    if direction.lower() == 'desc':
                        self.query = self.query.order_by(desc(column))
                    else:
                        self.query = self.query.order_by(asc(column))
        
        return self
    
    def apply_filters(self, filter_config):
        """Apply advanced filtering based on configuration"""
        filters = []
        
        for field, config in filter_config.items():
            param_value = request.args.get(field)
            if param_value is None:
                continue
            
            column = getattr(self.model_class, config['column'], None)
            if not column:
                continue
            
            filter_type = config.get('type', 'exact')
            
            if filter_type == 'exact':
                filters.append(column == param_value)
            
            elif filter_type == 'like':
                filters.append(column.like(f'%{param_value}%'))
            
            elif filter_type == 'in':
                values = param_value.split(',')
                filters.append(column.in_(values))
            
            elif filter_type == 'boolean':
                filters.append(column == (param_value.lower() in ['true', '1', 'yes']))
            
            elif filter_type == 'date_range':
                # Handle date range filters (e.g., due_date_from, due_date_to)
                if field.endswith('_from'):
                    try:
                        date_value = datetime.fromisoformat(param_value).date()
                        filters.append(column >= date_value)
                    except ValueError:
                        pass
                elif field.endswith('_to'):
                    try:
                        date_value = datetime.fromisoformat(param_value).date()
                        filters.append(column <= date_value)
                    except ValueError:
                        pass
            
            elif filter_type == 'numeric_range':
                # Handle numeric range filters
                if field.endswith('_min'):
                    try:
                        filters.append(column >= int(param_value))
                    except ValueError:
                        pass
                elif field.endswith('_max'):
                    try:
                        filters.append(column <= int(param_value))
                    except ValueError:
                        pass
        
        # Apply all filters with AND logic
        if filters:
            self.query = self.query.filter(and_(*filters))
        
        return self
    
    def apply_search(self, search_fields):
        """Apply full-text search across multiple fields"""
        search_term = request.args.get('q', '').strip()
        
        if search_term and search_fields:
            search_filters = []
            for field in search_fields:
                if hasattr(self.model_class, field):
                    column = getattr(self.model_class, field)
                    search_filters.append(column.like(f'%{search_term}%'))
            
            if search_filters:
                self.query = self.query.filter(or_(*search_filters))
        
        return self
    
    def apply_field_selection(self):
        """Apply sparse fieldsets for reduced payload size"""
        # This would require more complex query construction
        # For now, we'll handle this in the serialization phase
        fields_param = request.args.get('fields', '')
        self.selected_fields = fields_param.split(',') if fields_param else None
        return self
    
    def get_results(self):
        """Execute query and return results with metadata"""
        items = self.query.all()
        
        return {
            'items': items,
            'total': self.total_count,
            'limit': min(int(request.args.get('limit', 20)), 100),
            'offset': int(request.args.get('offset', 0))
        }
    
    def serialize_results(self, serializer_func=None):
        """Serialize results with optional field selection"""
        results = self.get_results()
        
        # Serialize items
        if serializer_func:
            serialized_items = [serializer_func(item) for item in results['items']]
        else:
            serialized_items = [item.to_dict() for item in results['items']]
        
        # Apply field selection if specified
        if hasattr(self, 'selected_fields') and self.selected_fields:
            filtered_items = []
            for item in serialized_items:
                filtered_item = {
                    field: item.get(field)
                    for field in self.selected_fields
                    if field in item
                }
                # Always include 'id' field
                if 'id' in item:
                    filtered_item['id'] = item['id']
                filtered_items.append(filtered_item)
            serialized_items = filtered_items
        
        return {
            'data': serialized_items,
            'meta': {
                'total': results['total'],
                'limit': results['limit'],
                'offset': results['offset'],
                'has_more': results['offset'] + len(serialized_items) < results['total']
            }
        }


def create_filter_config(model_class, field_configs):
    """Create filter configuration for a model"""
    config = {}
    
    for field, settings in field_configs.items():
        if isinstance(settings, str):
            # Simple field mapping
            config[field] = {'column': settings, 'type': 'exact'}
        else:
            # Complex configuration
            config[field] = settings
    
    return config


def apply_standard_enhancements(query, model_class, config):
    """Apply standard REST API enhancements to a query"""
    enhancer = QueryEnhancer(query, model_class)
    
    # Apply enhancements in order
    enhancer.apply_filters(config.get('filters', {}))
    enhancer.apply_search(config.get('search_fields', []))
    enhancer.apply_sorting(config.get('sortable_fields', []), config.get('default_sort', 'created_at:desc'))
    enhancer.apply_field_selection()
    enhancer.apply_pagination(
        default_limit=config.get('default_limit', 20),
        max_limit=config.get('max_limit', 100)
    )
    
    return enhancer