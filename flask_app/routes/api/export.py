"""
Export API Routes for Advanced Export Features

Provides multi-format data export capabilities with streaming support
for large datasets and scheduled exports.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
from flask import Blueprint, request, jsonify, current_app, send_file, Response
from datetime import datetime
import json
import os
from typing import Dict, List, Any

from services.export_service import export_service, ExportRequest, ExportFormat, ExportStatus
from routes.api.response_utils import APIResponse


# Create export blueprint
export_bp = Blueprint('export', __name__, url_prefix='/export')


@export_bp.route('/create', methods=['POST'])
def create_export():
    """
    Create new export operation
    
    Request Body:
    {
        "format": "json|csv|excel|ical|pdf",
        "entity_types": ["tasks", "events", "initiatives"],
        "filters": {
            "status": "active",
            "priority": "high"
        },
        "include_fields": ["id", "title", "description"],
        "exclude_fields": ["internal_notes"],
        "date_range": {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-12-31T23:59:59Z"
        },
        "sort_order": "newest|oldest",
        "compression": false,
        "chunk_size": 1000
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "export_id": "uuid",
            "status": "pending",
            "estimated_completion": "2024-01-01T12:00:00Z"
        }
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
        if 'format' not in data:
            return create_error_response(
                "Export format is required",
                400,
                {'code': 'MISSING_FORMAT'}
            )
        
        if 'entity_types' not in data or not data['entity_types']:
            return create_error_response(
                "At least one entity type is required",
                400,
                {'code': 'MISSING_ENTITY_TYPES'}
            )
        
        # Validate format
        try:
            export_format = ExportFormat(data['format'].lower())
        except ValueError:
            return create_error_response(
                f"Invalid export format: {data['format']}",
                400,
                {'code': 'INVALID_FORMAT', 'valid_formats': [f.value for f in ExportFormat]}
            )
        
        # Create export request
        export_request = ExportRequest(
            format=export_format,
            entity_types=data['entity_types'],
            filters=data.get('filters', {}),
            include_fields=data.get('include_fields'),
            exclude_fields=data.get('exclude_fields'),
            date_range=data.get('date_range'),
            sort_order=data.get('sort_order'),
            custom_template=data.get('custom_template'),
            compression=data.get('compression', False),
            chunk_size=data.get('chunk_size', 1000)
        )
        
        # Create export
        result = export_service.create_export(export_request)
        
        response_data = {
            'export_id': result.export_id,
            'status': result.status.value,
            'format': result.format.value,
            'created_at': result.created_at.isoformat(),
            'estimated_completion': None  # TODO: Calculate based on data size
        }
        
        if result.status == ExportStatus.FAILED:
            response_data['error_message'] = result.error_message
        
        return create_response(response_data, message="Export created successfully")
        
    except Exception as e:
        current_app.logger.error(f"Create export failed: {e}")
        return create_error_response(
            "Failed to create export",
            500,
            {'code': 'CREATE_EXPORT_ERROR', 'details': str(e)}
        )


@export_bp.route('/<export_id>/status', methods=['GET'])
def get_export_status(export_id):
    """
    Get export operation status
    
    Returns:
    {
        "success": true,
        "data": {
            "export_id": "uuid",
            "status": "completed",
            "format": "json",
            "record_count": 150,
            "file_size": 2048,
            "created_at": "2024-01-01T10:00:00Z",
            "completed_at": "2024-01-01T10:01:00Z",
            "download_url": "/api/export/uuid/download"
        }
    }
    """
    try:
        result = export_service.get_export_status(export_id)
        if not result:
            return create_error_response(
                "Export not found",
                404,
                {'code': 'EXPORT_NOT_FOUND'}
            )
        
        response_data = {
            'export_id': result.export_id,
            'status': result.status.value,
            'format': result.format.value,
            'record_count': result.record_count,
            'file_size': result.file_size,
            'created_at': result.created_at.isoformat(),
            'completed_at': result.completed_at.isoformat() if result.completed_at else None,
            'download_url': result.download_url,
            'error_message': result.error_message
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get export status failed: {e}")
        return create_error_response(
            "Failed to get export status",
            500,
            {'code': 'GET_STATUS_ERROR', 'details': str(e)}
        )


@export_bp.route('/<export_id>/download', methods=['GET'])
def download_export(export_id):
    """
    Download export file
    
    Returns binary file content with appropriate headers
    """
    try:
        result = export_service.get_export_status(export_id)
        if not result:
            return create_error_response(
                "Export not found",
                404,
                {'code': 'EXPORT_NOT_FOUND'}
            )
        
        if result.status != ExportStatus.COMPLETED:
            return create_error_response(
                f"Export is not ready for download. Status: {result.status.value}",
                400,
                {'code': 'EXPORT_NOT_READY', 'current_status': result.status.value}
            )
        
        file_path = export_service.get_export_file(export_id)
        if not file_path or not os.path.exists(file_path):
            return create_error_response(
                "Export file not found",
                404,
                {'code': 'FILE_NOT_FOUND'}
            )
        
        # Get formatter for MIME type
        formatter = export_service.formatters.get(result.format)
        if not formatter:
            return create_error_response(
                "Invalid export format",
                500,
                {'code': 'INVALID_FORMAT'}
            )
        
        # Generate filename
        timestamp = result.created_at.strftime('%Y%m%d_%H%M%S')
        filename = f"taskmaster_export_{timestamp}{formatter.file_extension}"
        
        return send_file(
            file_path,
            mimetype=formatter.mime_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Download export failed: {e}")
        return create_error_response(
            "Failed to download export",
            500,
            {'code': 'DOWNLOAD_ERROR', 'details': str(e)}
        )


@export_bp.route('/<export_id>/cancel', methods=['POST'])
def cancel_export(export_id):
    """
    Cancel export operation
    
    Returns:
    {
        "success": true,
        "data": {
            "export_id": "uuid",
            "status": "cancelled"
        }
    }
    """
    try:
        success = export_service.cancel_export(export_id)
        if not success:
            return create_error_response(
                "Export cannot be cancelled or not found",
                400,
                {'code': 'CANNOT_CANCEL'}
            )
        
        response_data = {
            'export_id': export_id,
            'status': 'cancelled'
        }
        
        return create_response(response_data, message="Export cancelled successfully")
        
    except Exception as e:
        current_app.logger.error(f"Cancel export failed: {e}")
        return create_error_response(
            "Failed to cancel export",
            500,
            {'code': 'CANCEL_ERROR', 'details': str(e)}
        )


@export_bp.route('/active', methods=['GET'])
def get_active_exports():
    """
    Get list of active exports
    
    Query Parameters:
    - status: Filter by status (pending|processing|completed|failed|cancelled)
    - format: Filter by format
    - limit: Maximum results (default: 20)
    
    Returns:
    {
        "success": true,
        "data": {
            "exports": [...],
            "total_count": 5
        }
    }
    """
    try:
        # Parse query parameters
        status_filter = request.args.get('status')
        format_filter = request.args.get('format')
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Get all active exports
        all_exports = list(export_service.active_exports.values())
        
        # Apply filters
        filtered_exports = all_exports
        
        if status_filter:
            try:
                status_enum = ExportStatus(status_filter.lower())
                filtered_exports = [e for e in filtered_exports if e.status == status_enum]
            except ValueError:
                return create_error_response(
                    f"Invalid status filter: {status_filter}",
                    400,
                    {'code': 'INVALID_STATUS', 'valid_statuses': [s.value for s in ExportStatus]}
                )
        
        if format_filter:
            try:
                format_enum = ExportFormat(format_filter.lower())
                filtered_exports = [e for e in filtered_exports if e.format == format_enum]
            except ValueError:
                return create_error_response(
                    f"Invalid format filter: {format_filter}",
                    400,
                    {'code': 'INVALID_FORMAT', 'valid_formats': [f.value for f in ExportFormat]}
                )
        
        # Sort by creation date (newest first)
        filtered_exports.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        limited_exports = filtered_exports[:limit]
        
        # Format response
        exports_data = []
        for export in limited_exports:
            exports_data.append({
                'export_id': export.export_id,
                'status': export.status.value,
                'format': export.format.value,
                'record_count': export.record_count,
                'file_size': export.file_size,
                'created_at': export.created_at.isoformat(),
                'completed_at': export.completed_at.isoformat() if export.completed_at else None,
                'download_url': export.download_url,
                'error_message': export.error_message
            })
        
        response_data = {
            'exports': exports_data,
            'total_count': len(filtered_exports)
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get active exports failed: {e}")
        return create_error_response(
            "Failed to get active exports",
            500,
            {'code': 'GET_ACTIVE_EXPORTS_ERROR', 'details': str(e)}
        )


@export_bp.route('/formats', methods=['GET'])
def get_supported_formats():
    """
    Get list of supported export formats
    
    Returns:
    {
        "success": true,
        "data": {
            "formats": [
                {
                    "format": "json",
                    "mime_type": "application/json",
                    "file_extension": ".json",
                    "description": "JavaScript Object Notation"
                }
            ]
        }
    }
    """
    try:
        formats_data = []
        
        format_descriptions = {
            ExportFormat.JSON: "JavaScript Object Notation - structured data format",
            ExportFormat.CSV: "Comma Separated Values - tabular data format",
            ExportFormat.EXCEL: "Microsoft Excel spreadsheet format",
            ExportFormat.ICAL: "iCalendar format for events and calendar data",
            ExportFormat.PDF: "Portable Document Format (not yet implemented)",
            ExportFormat.XML: "Extensible Markup Language (not yet implemented)"
        }
        
        for format_enum in ExportFormat:
            formatter = export_service.formatters.get(format_enum)
            if formatter:  # Only include implemented formats
                formats_data.append({
                    'format': format_enum.value,
                    'mime_type': formatter.mime_type,
                    'file_extension': formatter.file_extension,
                    'description': format_descriptions.get(format_enum, ""),
                    'implemented': True
                })
            else:
                formats_data.append({
                    'format': format_enum.value,
                    'mime_type': None,
                    'file_extension': None,
                    'description': format_descriptions.get(format_enum, ""),
                    'implemented': False
                })
        
        response_data = {'formats': formats_data}
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Get supported formats failed: {e}")
        return create_error_response(
            "Failed to get supported formats",
            500,
            {'code': 'GET_FORMATS_ERROR', 'details': str(e)}
        )


@export_bp.route('/cleanup', methods=['POST'])
def cleanup_old_exports():
    """
    Clean up old export files and records (admin operation)
    
    Request Body (optional):
    {
        "max_age_hours": 24
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "message": "Cleanup completed successfully",
            "exports_cleaned": 5
        }
    }
    """
    try:
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours', 24)
        
        # Validate max_age_hours
        if not isinstance(max_age_hours, (int, float)) or max_age_hours <= 0:
            return create_error_response(
                "max_age_hours must be a positive number",
                400,
                {'code': 'INVALID_MAX_AGE'}
            )
        
        # Count exports before cleanup
        exports_before = len(export_service.active_exports)
        
        # Perform cleanup
        export_service.cleanup_old_exports(max_age_hours)
        
        # Count exports after cleanup
        exports_after = len(export_service.active_exports)
        exports_cleaned = exports_before - exports_after
        
        response_data = {
            'message': 'Cleanup completed successfully',
            'exports_cleaned': exports_cleaned,
            'max_age_hours': max_age_hours
        }
        
        current_app.logger.info(f"Export cleanup completed: {exports_cleaned} exports cleaned")
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Cleanup exports failed: {e}")
        return create_error_response(
            "Failed to cleanup exports",
            500,
            {'code': 'CLEANUP_ERROR', 'details': str(e)}
        )


@export_bp.route('/health', methods=['GET'])
def export_health():
    """
    Check export service health and capabilities
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "active_exports": 3,
            "supported_formats": ["json", "csv", "excel", "ical"],
            "capabilities": ["multi_format", "streaming", "filtering"]
        }
    }
    """
    try:
        response_data = {
            'status': 'healthy',
            'active_exports': len(export_service.active_exports),
            'supported_formats': [f.value for f in ExportFormat if f in export_service.formatters],
            'capabilities': [
                'multi_format_export',
                'filtered_export',
                'field_selection',
                'date_range_filtering',
                'real_time_status',
                'automatic_cleanup'
            ]
        }
        
        return create_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Export health check failed: {e}")
        return create_error_response(
            "Export health check failed",
            500,
            {'code': 'HEALTH_CHECK_ERROR', 'details': str(e)}
        )


# Register error handlers
@export_bp.errorhandler(404)
def not_found(error):
    return create_error_response(
        "Export endpoint not found",
        404,
        {'code': 'ENDPOINT_NOT_FOUND'}
    )


@export_bp.errorhandler(405)
def method_not_allowed(error):
    return create_error_response(
        "Method not allowed for this export endpoint",
        405,
        {'code': 'METHOD_NOT_ALLOWED'}
    )