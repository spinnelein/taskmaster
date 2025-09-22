"""
Response Utilities for Enhanced REST API

Provides consistent response formatting, error handling, and metadata
for all API endpoints. Follows CODING_STANDARDS.md compliance.
"""
from flask import jsonify, request, make_response
from datetime import datetime
import hashlib
import json


class APIResponse:
    """Standardized API response builder"""
    
    @staticmethod
    def success(data=None, message=None, meta=None, status_code=200):
        """Create a successful response"""
        response = {'status': 'success'}
        
        if data is not None:
            response['data'] = data
        
        if message:
            response['message'] = message
        
        if meta:
            response['meta'] = meta
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message, errors=None, status_code=400):
        """Create an error response"""
        response = {
            'status': 'error',
            'message': message
        }
        
        if errors:
            response['errors'] = errors
        
        return jsonify(response), status_code
    
    @staticmethod
    def paginated(items, total, limit, offset, serializer=None):
        """Create a paginated response"""
        # Serialize items if serializer provided
        if serializer:
            serialized_items = [serializer(item) for item in items]
        else:
            serialized_items = [item.to_dict() for item in items]
        
        meta = {
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + len(items) < total,
            'page': (offset // limit) + 1 if limit > 0 else 1,
            'total_pages': (total + limit - 1) // limit if limit > 0 else 1
        }
        
        return APIResponse.success(data=serialized_items, meta=meta)
    
    @staticmethod
    def created(data, location=None):
        """Create a 201 Created response"""
        response, status = APIResponse.success(data=data, status_code=201)
        
        if location:
            response = make_response(response)
            response.headers['Location'] = location
        
        return response, status
    
    @staticmethod
    def no_content():
        """Create a 204 No Content response"""
        return '', 204
    
    @staticmethod
    def not_found(message="Resource not found"):
        """Create a 404 Not Found response"""
        return APIResponse.error(message, status_code=404)
    
    @staticmethod
    def conflict(message="Resource conflict"):
        """Create a 409 Conflict response"""
        return APIResponse.error(message, status_code=409)
    
    @staticmethod
    def validation_error(errors):
        """Create a 422 Unprocessable Entity response"""
        return APIResponse.error(
            message="Validation failed",
            errors=errors,
            status_code=422
        )


class CacheHeaders:
    """Manages cache headers for responses"""
    
    @staticmethod
    def add_etag(response, data):
        """Add ETag header to response"""
        # Generate ETag from data
        if isinstance(data, (dict, list)):
            content = json.dumps(data, sort_keys=True)
        else:
            content = str(data)
        
        etag = hashlib.md5(content.encode()).hexdigest()
        response.headers['ETag'] = f'"{etag}"'
        
        return response
    
    @staticmethod
    def add_cache_control(response, max_age=300, private=False, must_revalidate=True):
        """Add Cache-Control header to response"""
        directives = []
        
        if private:
            directives.append('private')
        else:
            directives.append('public')
        
        directives.append(f'max-age={max_age}')
        
        if must_revalidate:
            directives.append('must-revalidate')
        
        response.headers['Cache-Control'] = ', '.join(directives)
        
        return response
    
    @staticmethod
    def add_last_modified(response, timestamp):
        """Add Last-Modified header to response"""
        if isinstance(timestamp, datetime):
            response.headers['Last-Modified'] = timestamp.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        return response
    
    @staticmethod
    def check_not_modified(request, etag=None, last_modified=None):
        """Check if resource has not been modified"""
        # Check If-None-Match header
        if etag and request.headers.get('If-None-Match'):
            if request.headers.get('If-None-Match').strip('"') == etag:
                return True
        
        # Check If-Modified-Since header
        if last_modified and request.headers.get('If-Modified-Since'):
            try:
                if_modified = datetime.strptime(
                    request.headers.get('If-Modified-Since'),
                    '%a, %d %b %Y %H:%M:%S GMT'
                )
                if last_modified <= if_modified:
                    return True
            except ValueError:
                pass
        
        return False


def handle_api_errors(func):
    """Decorator for consistent error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return APIResponse.validation_error({'value_error': str(e)})
        except KeyError as e:
            return APIResponse.validation_error({'missing_field': str(e)})
        except Exception as e:
            # Log the error here if logging is set up
            return APIResponse.error(
                message="An unexpected error occurred",
                errors={'exception': str(e)},
                status_code=500
            )
    
    wrapper.__name__ = func.__name__
    return wrapper


def validate_request_data(required_fields=None, optional_fields=None):
    """Decorator to validate request JSON data"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return APIResponse.error(
                    message="Request must be JSON",
                    status_code=415
                )
            
            data = request.get_json()
            
            # Check required fields
            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return APIResponse.validation_error({
                        'missing_fields': missing
                    })
            
            # Add to kwargs for the function
            kwargs['validated_data'] = data
            
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    
    return decorator