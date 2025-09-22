"""
Search API Routes for Advanced Search Features

Provides comprehensive search endpoints with full-text search, faceting,
suggestions, and advanced query capabilities.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json
from typing import Dict, List, Any

from services.search_service import get_search_service, SearchResponse
from routes.api.response_utils import APIResponse


# Import saved search models
from models import SavedSearch, SearchTemplate, db

# Create search blueprint
search_bp = Blueprint('search', __name__, url_prefix='/search')


@search_bp.route('/search', methods=['GET'])
def search_all():
    """
    Comprehensive search across all entity types
    
    Query Parameters:
    - q: Search query string (required)
    - types: Comma-separated entity types to search (optional)
    - limit: Maximum results to return (default: 20, max: 100)
    - offset: Pagination offset (default: 0)
    - include_facets: Include faceted search results (default: true)
    - format: Response format (json, minimal) (default: json)
    
    Returns:
    {
        "success": true,
        "data": {
            "results": [...],
            "total_count": 150,
            "facets": {...},
            "query_time_ms": 45.2,
            "suggestions": [...],
            "corrected_query": null
        },
        "meta": {
            "query": "...",
            "types_searched": [...],
            "limit": 20,
            "offset": 0
        }
    }
    """
    try:
        # Validate required parameters
        query = request.args.get('q', '').strip()
        if not query:
            return create_error_response(
                "Query parameter 'q' is required",
                400,
                {'code': 'MISSING_QUERY'}
            )
        
        # Parse optional parameters
        entity_types = None
        types_param = request.args.get('types', '').strip()
        if types_param:
            entity_types = [t.strip() for t in types_param.split(',')]
            # Validate entity types
            valid_types = {'tasks', 'events', 'initiatives', 'projects', 'meals', 'dishes'}
            invalid_types = set(entity_types) - valid_types
            if invalid_types:
                return create_error_response(
                    f"Invalid entity types: {', '.join(invalid_types)}",
                    400,
                    {'code': 'INVALID_ENTITY_TYPES', 'invalid_types': list(invalid_types)}
                )
        
        # Pagination parameters
        try:
            limit = min(int(request.args.get('limit', 20)), 100)
            offset = max(int(request.args.get('offset', 0)), 0)
        except (ValueError, TypeError):
            return create_error_response(
                "Invalid pagination parameters",
                400,
                {'code': 'INVALID_PAGINATION'}
            )
        
        # Other parameters
        include_facets = request.args.get('include_facets', 'true').lower() == 'true'
        response_format = request.args.get('format', 'json').lower()
        
        # Perform search
        search_response = search_service.search(
            query=query,
            entity_types=entity_types,
            limit=limit,
            offset=offset,
            include_facets=include_facets
        )
        
        # Format response based on requested format
        if response_format == 'minimal':
            response_data = {
                'results': [
                    {
                        'id': result.id,
                        'type': result.type,
                        'title': result.title,
                        'relevance_score': result.relevance_score
                    }
                    for result in search_response.results
                ],
                'total_count': search_response.total_count
            }
        else:
            # Full format
            response_data = {
                'results': [
                    {
                        'id': result.id,
                        'type': result.type,
                        'title': result.title,
                        'description': result.description,
                        'relevance_score': result.relevance_score,
                        'snippet': result.snippet,
                        'metadata': result.metadata
                    }
                    for result in search_response.results
                ],
                'total_count': search_response.total_count,
                'facets': {
                    facet_name: [
                        {
                            'value': facet.value,
                            'count': facet.count,
                            'filter_key': facet.filter_key
                        }
                        for facet in facets
                    ]
                    for facet_name, facets in search_response.facets.items()
                } if include_facets else {},
                'query_time_ms': search_response.query_time_ms,
                'suggestions': search_response.suggestions,
                'corrected_query': search_response.corrected_query
            }
        
        # Response metadata
        meta = {
            'query': query,
            'types_searched': entity_types or ['tasks', 'events', 'initiatives', 'projects', 'meals', 'dishes'],
            'limit': limit,
            'offset': offset,
            'format': response_format,
            'include_facets': include_facets
        }
        
        return create_response(response_data, meta=meta)
        
    except Exception as e:
        current_app.logger.error(f"Search failed: {e}")
        return create_error_response(
            "Search operation failed",
            500,
            {'code': 'SEARCH_ERROR', 'details': str(e)}
        )


@search_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """
    Get auto-complete suggestions for partial queries
    
    Query Parameters:
    - q: Partial query string (required, min 2 characters)
    - limit: Maximum suggestions to return (default: 10, max: 20)
    
    Returns:
    {
        "success": true,
        "data": {
            "suggestions": ["project management", "project planning", ...],
            "query": "proj"
        }
    }
    """
    try:
        # Validate query parameter
        partial_query = request.args.get('q', '').strip()
        if len(partial_query) < 2:
            return create_error_response(
                "Query must be at least 2 characters long",
                400,
                {'code': 'QUERY_TOO_SHORT'}
            )
        
        # Parse limit parameter
        try:
            limit = min(int(request.args.get('limit', 10)), 20)
        except (ValueError, TypeError):
            limit = 10
        
        # Get suggestions
        suggestions = search_service.get_search_suggestions(partial_query, limit)
        
        response_data = {
            'suggestions': suggestions,
            'query': partial_query
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Suggestions failed: {e}")
        return create_error_response(
            "Failed to get suggestions",
            500,
            {'code': 'SUGGESTIONS_ERROR', 'details': str(e)}
        )


@search_bp.route('/facets', methods=['GET'])
def get_facets():
    """
    Get available facets and their possible values
    
    Returns:
    {
        "success": true,
        "data": {
            "facets": {
                "type": {
                    "display_name": "Content Type",
                    "values": ["task", "event", "initiative", ...]
                },
                "status": {
                    "display_name": "Status", 
                    "values": ["active", "completed", "blocked", ...]
                }
            }
        }
    }
    """
    try:
        # This would typically be cached or computed from actual data
        facets_info = {
            'type': {
                'display_name': 'Content Type',
                'values': ['task', 'event', 'initiative', 'project', 'meal', 'dish']
            },
            'status': {
                'display_name': 'Status',
                'values': ['active', 'completed', 'blocked', 'cancelled', 'draft']
            },
            'priority': {
                'display_name': 'Priority',
                'values': ['low', 'medium', 'high', 'urgent']
            },
            'date_range': {
                'display_name': 'Date Created',
                'values': ['Today', 'This Week', 'This Month', 'This Year', 'Older']
            }
        }
        
        return create_response({'facets': facets_info})
        
    except Exception as e:
        current_app.logger.error(f"Get facets failed: {e}")
        return create_error_response(
            "Failed to get facets",
            500,
            {'code': 'FACETS_ERROR', 'details': str(e)}
        )


@search_bp.route('/query/analyze', methods=['POST'])
def analyze_query():
    """
    Analyze search query and return processed components
    
    Request Body:
    {
        "query": "project:work status:active urgent task"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "original_query": "project:work status:active urgent task",
            "cleaned_query": "project work status active urgent task",
            "terms": ["urgent", "task"],
            "phrases": [],
            "filters": {"project": "work", "status": "active"},
            "fts_query": "urgent OR task"
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return create_error_response(
                "Query is required in request body",
                400,
                {'code': 'MISSING_QUERY'}
            )
        
        query = data['query'].strip()
        if not query:
            return create_error_response(
                "Query cannot be empty",
                400,
                {'code': 'EMPTY_QUERY'}
            )
        
        # Process the query
        processed = search_service.query_processor.process_query(query)
        
        return create_response(processed)
        
    except Exception as e:
        current_app.logger.error(f"Query analysis failed: {e}")
        return create_error_response(
            "Failed to analyze query",
            500,
            {'code': 'QUERY_ANALYSIS_ERROR', 'details': str(e)}
        )


@search_bp.route('/index/rebuild', methods=['POST'])
def rebuild_search_index():
    """
    Rebuild search indexes (admin operation)
    
    Request Body (optional):
    {
        "tables": ["tasks", "events"]  // Specific tables to rebuild
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "message": "Search indexes rebuilt successfully",
            "tables_rebuilt": ["tasks_fts", "events_fts", ...]
        }
    }
    """
    try:
        data = request.get_json() or {}
        specific_tables = data.get('tables', [])
        
        if specific_tables:
            # Rebuild specific tables
            tables_rebuilt = []
            for table in specific_tables:
                if table in ['tasks', 'events', 'initiatives', 'projects', 'meals', 'dishes']:
                    search_service.index.rebuild_index(f"{table}_fts")
                    tables_rebuilt.append(f"{table}_fts")
        else:
            # Rebuild all indexes
            search_service.rebuild_all_indexes()
            tables_rebuilt = list(search_service.index.fts_tables.keys())
        
        response_data = {
            'message': 'Search indexes rebuilt successfully',
            'tables_rebuilt': tables_rebuilt
        }
        
        current_app.logger.info(f"Search indexes rebuilt: {tables_rebuilt}")
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Index rebuild failed: {e}")
        return create_error_response(
            "Failed to rebuild search indexes",
            500,
            {'code': 'INDEX_REBUILD_ERROR', 'details': str(e)}
        )


@search_bp.route('/health', methods=['GET'])
def search_health():
    """
    Check search service health and capabilities
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "fts_enabled": true,
            "indexed_tables": ["tasks_fts", "events_fts", ...],
            "capabilities": ["full_text_search", "faceted_search", "suggestions"]
        }
    }
    """
    try:
        # Check FTS table existence
        from models import db
        from sqlalchemy import text
        
        result = db.session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_fts'"
        ))
        indexed_tables = [row[0] for row in result.fetchall()]
        
        response_data = {
            'status': 'healthy',
            'fts_enabled': len(indexed_tables) > 0,
            'indexed_tables': indexed_tables,
            'capabilities': [
                'full_text_search',
                'faceted_search', 
                'suggestions',
                'query_analysis',
                'relevance_scoring'
            ]
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Search health check failed: {e}")
        return create_error_response(
            "Search health check failed",
            500,
            {'code': 'HEALTH_CHECK_ERROR', 'details': str(e)}
        )


# Register error handlers
@search_bp.errorhandler(404)
def not_found(error):
    return create_error_response(
        "Search endpoint not found",
        404,
        {'code': 'ENDPOINT_NOT_FOUND'}
    )


@search_bp.route('/saved', methods=['GET'])
def get_saved_searches():
    """
    Get saved searches for current user
    
    Query Parameters:
    - category: Filter by category
    - favorite: Show only favorites (true/false)
    - recent: Show recently used (true/false)
    - limit: Maximum results (default: 20)
    
    Returns saved searches list
    """
    try:
        # Parse query parameters
        category = request.args.get('category')
        show_favorites = request.args.get('favorite', '').lower() == 'true'
        show_recent = request.args.get('recent', '').lower() == 'true'
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Build query
        query = SavedSearch.query
        
        if category:
            query = query.filter(SavedSearch.category == category)
        
        if show_favorites:
            query = query.filter(SavedSearch.is_favorite == True)
        
        if show_recent:
            query = query.filter(SavedSearch.last_used_at.isnot(None))
            query = query.order_by(SavedSearch.last_used_at.desc())
        else:
            query = query.order_by(SavedSearch.name.asc())
        
        saved_searches = query.limit(limit).all()
        
        response_data = {
            'saved_searches': [search.to_dict() for search in saved_searches],
            'total_count': query.count()
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get saved searches failed: {e}")
        return create_error_response(
            "Failed to get saved searches",
            500,
            {'code': 'GET_SAVED_SEARCHES_ERROR', 'details': str(e)}
        )


@search_bp.route('/saved', methods=['POST'])
def create_saved_search():
    """
    Create new saved search
    
    Request Body:
    {
        "name": "My Search",
        "query": "task priority:high",
        "description": "High priority tasks",
        "entity_types": ["tasks"],
        "filters": {},
        "category": "work",
        "is_favorite": false,
        "color": "#ff0000"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return create_error_response(
                "Request body is required",
                400,
                {'code': 'MISSING_REQUEST_BODY'}
            )
        
        # Validate required fields
        if not data.get('name'):
            return create_error_response(
                "Name is required",
                400,
                {'code': 'MISSING_NAME'}
            )
        
        if not data.get('query'):
            return create_error_response(
                "Query is required",
                400,
                {'code': 'MISSING_QUERY'}
            )
        
        # Check for duplicate name
        existing = SavedSearch.query.filter_by(name=data['name']).first()
        if existing:
            return create_error_response(
                "Saved search with this name already exists",
                409,
                {'code': 'DUPLICATE_NAME'}
            )
        
        # Create saved search
        saved_search = SavedSearch(
            name=data['name'],
            query=data['query'],
            description=data.get('description'),
            entity_types=data.get('entity_types', []),
            filters=data.get('filters', {}),
            sort_order=data.get('sort_order'),
            category=data.get('category'),
            is_favorite=data.get('is_favorite', False),
            color=data.get('color'),
            tags=data.get('tags', [])
        )
        
        db.session.add(saved_search)
        db.session.commit()
        
        return create_response(
            saved_search.to_dict(),
            message="Saved search created successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Create saved search failed: {e}")
        return create_error_response(
            "Failed to create saved search",
            500,
            {'code': 'CREATE_SAVED_SEARCH_ERROR', 'details': str(e)}
        )


@search_bp.route('/saved/<saved_search_id>', methods=['GET'])
def get_saved_search(saved_search_id):
    """Get specific saved search by ID"""
    try:
        saved_search = SavedSearch.query.get(saved_search_id)
        if not saved_search:
            return create_error_response(
                "Saved search not found",
                404,
                {'code': 'SAVED_SEARCH_NOT_FOUND'}
            )
        
        return create_response(saved_search.to_dict())
        
    except Exception as e:
        current_app.logger.error(f"Get saved search failed: {e}")
        return create_error_response(
            "Failed to get saved search",
            500,
            {'code': 'GET_SAVED_SEARCH_ERROR', 'details': str(e)}
        )


@search_bp.route('/saved/<saved_search_id>/execute', methods=['GET'])
def execute_saved_search(saved_search_id):
    """Execute a saved search and track usage"""
    try:
        saved_search = SavedSearch.query.get(saved_search_id)
        if not saved_search:
            return create_error_response(
                "Saved search not found",
                404,
                {'code': 'SAVED_SEARCH_NOT_FOUND'}
            )
        
        # Track usage
        saved_search.increment_usage()
        db.session.commit()
        
        # Get search parameters from saved search
        search_params = saved_search.to_search_params()
        
        # Parse pagination from request
        try:
            limit = min(int(request.args.get('limit', 20)), 100)
            offset = max(int(request.args.get('offset', 0)), 0)
        except (ValueError, TypeError):
            limit = 20
            offset = 0
        
        # Execute search
        search_response = search_service.search(
            query=search_params['query'],
            entity_types=search_params.get('entity_types'),
            limit=limit,
            offset=offset
        )
        
        # Format response
        response_data = {
            'saved_search': saved_search.to_dict(),
            'search_results': {
                'results': [
                    {
                        'id': result.id,
                        'type': result.type,
                        'title': result.title,
                        'description': result.description,
                        'relevance_score': result.relevance_score,
                        'snippet': result.snippet,
                        'metadata': result.metadata
                    }
                    for result in search_response.results
                ],
                'total_count': search_response.total_count,
                'query_time_ms': search_response.query_time_ms
            }
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Execute saved search failed: {e}")
        return create_error_response(
            "Failed to execute saved search",
            500,
            {'code': 'EXECUTE_SAVED_SEARCH_ERROR', 'details': str(e)}
        )


@search_bp.route('/saved/<saved_search_id>', methods=['PUT'])
def update_saved_search(saved_search_id):
    """Update saved search"""
    try:
        saved_search = SavedSearch.query.get(saved_search_id)
        if not saved_search:
            return create_error_response(
                "Saved search not found",
                404,
                {'code': 'SAVED_SEARCH_NOT_FOUND'}
            )
        
        data = request.get_json()
        if not data:
            return create_error_response(
                "Request body is required",
                400,
                {'code': 'MISSING_REQUEST_BODY'}
            )
        
        # Update fields
        if 'name' in data:
            # Check for duplicate name (excluding current)
            existing = SavedSearch.query.filter(
                SavedSearch.name == data['name'],
                SavedSearch.id != saved_search_id
            ).first()
            if existing:
                return create_error_response(
                    "Saved search with this name already exists",
                    409,
                    {'code': 'DUPLICATE_NAME'}
                )
            saved_search.name = data['name']
        
        if 'query' in data:
            saved_search.query = data['query']
        if 'description' in data:
            saved_search.description = data['description']
        if 'entity_types' in data:
            saved_search.entity_types = data['entity_types']
        if 'filters' in data:
            saved_search.filters = data['filters']
        if 'sort_order' in data:
            saved_search.sort_order = data['sort_order']
        if 'category' in data:
            saved_search.category = data['category']
        if 'is_favorite' in data:
            saved_search.is_favorite = data['is_favorite']
        if 'color' in data:
            saved_search.color = data['color']
        if 'tags' in data:
            saved_search.tags = data['tags']
        
        saved_search.updated_at = datetime.utcnow()
        db.session.commit()
        
        return create_response(
            saved_search.to_dict(),
            message="Saved search updated successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Update saved search failed: {e}")
        return create_error_response(
            "Failed to update saved search",
            500,
            {'code': 'UPDATE_SAVED_SEARCH_ERROR', 'details': str(e)}
        )


@search_bp.route('/saved/<saved_search_id>', methods=['DELETE'])
def delete_saved_search(saved_search_id):
    """Delete saved search"""
    try:
        saved_search = SavedSearch.query.get(saved_search_id)
        if not saved_search:
            return create_error_response(
                "Saved search not found",
                404,
                {'code': 'SAVED_SEARCH_NOT_FOUND'}
            )
        
        db.session.delete(saved_search)
        db.session.commit()
        
        return create_response(
            {},
            message="Saved search deleted successfully"
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete saved search failed: {e}")
        return create_error_response(
            "Failed to delete saved search",
            500,
            {'code': 'DELETE_SAVED_SEARCH_ERROR', 'details': str(e)}
        )


@search_bp.route('/templates', methods=['GET'])
def get_search_templates():
    """Get available search templates"""
    try:
        category = request.args.get('category')
        include_system = request.args.get('include_system', 'true').lower() == 'true'
        
        query = SearchTemplate.query
        
        if category:
            query = query.filter(SearchTemplate.category == category)
        
        if not include_system:
            query = query.filter(SearchTemplate.is_system_template == False)
        
        templates = query.order_by(SearchTemplate.name.asc()).all()
        
        response_data = {
            'templates': [template.to_dict() for template in templates],
            'total_count': len(templates)
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get search templates failed: {e}")
        return create_error_response(
            "Failed to get search templates",
            500,
            {'code': 'GET_TEMPLATES_ERROR', 'details': str(e)}
        )


@search_bp.route('/templates/<template_id>/render', methods=['POST'])
def render_search_template(template_id):
    """
    Render search template with parameters
    
    Request Body:
    {
        "parameters": {
            "priority": "high",
            "project_name": "TaskMaster"
        }
    }
    """
    try:
        template = SearchTemplate.query.get(template_id)
        if not template:
            return create_error_response(
                "Search template not found",
                404,
                {'code': 'TEMPLATE_NOT_FOUND'}
            )
        
        data = request.get_json() or {}
        parameters = data.get('parameters', {})
        
        # Validate parameters
        validation_errors = template.validate_parameters(parameters)
        if validation_errors:
            return create_error_response(
                "Invalid parameters",
                400,
                {'code': 'INVALID_PARAMETERS', 'errors': validation_errors}
            )
        
        # Render template
        rendered_query = template.render_query(parameters)
        
        # Track usage
        template.usage_count += 1
        db.session.commit()
        
        response_data = {
            'template': template.to_dict(),
            'rendered_query': rendered_query,
            'parameters_used': parameters
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Render template failed: {e}")
        return create_error_response(
            "Failed to render template",
            500,
            {'code': 'RENDER_TEMPLATE_ERROR', 'details': str(e)}
        )


@search_bp.errorhandler(404)
def not_found(error):
    return create_error_response(
        "Search endpoint not found",
        404,
        {'code': 'ENDPOINT_NOT_FOUND'}
    )


@search_bp.errorhandler(405)
def method_not_allowed(error):
    return create_error_response(
        "Method not allowed for this search endpoint",
        405,
        {'code': 'METHOD_NOT_ALLOWED'}
    )