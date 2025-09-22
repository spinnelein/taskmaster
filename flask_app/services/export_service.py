"""
Advanced Export Service for TaskMaster

Provides multi-format data export capabilities with streaming support
for large datasets. Supports JSON, CSV, Excel, iCal, and PDF formats.
Follows CODING_STANDARDS.md compliance with ASCII-only content.
"""
import io
import csv
import json
import tempfile
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Generator, Union
from dataclasses import dataclass
from enum import Enum
import uuid

from flask import current_app, Response, stream_template
from sqlalchemy.orm import Query
# import pandas as pd  # Temporarily commented out due to numpy version conflict

from models import db, Task, Event, Initiative, Project, Meal, Dish


class ExportFormat(Enum):
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    ICAL = "ical"
    PDF = "pdf"
    XML = "xml"


class ExportStatus(Enum):
    """Export job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportRequest:
    """Export request configuration"""
    format: ExportFormat
    entity_types: List[str]
    filters: Dict[str, Any]
    include_fields: Optional[List[str]]
    exclude_fields: Optional[List[str]]
    date_range: Optional[Dict[str, str]]
    sort_order: Optional[str]
    custom_template: Optional[str]
    compression: bool = False
    chunk_size: int = 1000


@dataclass
class ExportResult:
    """Export operation result"""
    export_id: str
    status: ExportStatus
    format: ExportFormat
    file_path: Optional[str]
    file_size: Optional[int]
    record_count: int
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    download_url: Optional[str]


class ExportFormatter:
    """Base formatter for different export formats"""
    
    def __init__(self, format_type: ExportFormat):
        self.format_type = format_type
        self.mime_type = self._get_mime_type()
        self.file_extension = self._get_file_extension()
    
    def _get_mime_type(self) -> str:
        """Get MIME type for format"""
        mime_types = {
            ExportFormat.JSON: "application/json",
            ExportFormat.CSV: "text/csv",
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.ICAL: "text/calendar",
            ExportFormat.PDF: "application/pdf",
            ExportFormat.XML: "application/xml"
        }
        return mime_types.get(self.format_type, "application/octet-stream")
    
    def _get_file_extension(self) -> str:
        """Get file extension for format"""
        extensions = {
            ExportFormat.JSON: ".json",
            ExportFormat.CSV: ".csv",
            ExportFormat.EXCEL: ".xlsx",
            ExportFormat.ICAL: ".ics",
            ExportFormat.PDF: ".pdf",
            ExportFormat.XML: ".xml"
        }
        return extensions.get(self.format_type, ".bin")
    
    def format_data(self, data: List[Dict], metadata: Dict = None) -> Union[str, bytes]:
        """Format data according to the specified format"""
        raise NotImplementedError("Subclasses must implement format_data method")


class JSONFormatter(ExportFormatter):
    """JSON export formatter"""
    
    def __init__(self):
        super().__init__(ExportFormat.JSON)
    
    def format_data(self, data: List[Dict], metadata: Dict = None) -> str:
        """Format data as JSON"""
        export_data = {
            "data": data,
            "metadata": metadata or {},
            "exported_at": datetime.utcnow().isoformat(),
            "record_count": len(data)
        }
        
        return json.dumps(export_data, indent=2, default=str)


class CSVFormatter(ExportFormatter):
    """CSV export formatter"""
    
    def __init__(self):
        super().__init__(ExportFormat.CSV)
    
    def format_data(self, data: List[Dict], metadata: Dict = None) -> str:
        """Format data as CSV"""
        if not data:
            return ""
        
        output = io.StringIO()
        fieldnames = set()
        
        # Collect all unique field names
        for row in data:
            fieldnames.update(self._flatten_dict(row).keys())
        
        fieldnames = sorted(list(fieldnames))
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            flattened_row = self._flatten_dict(row)
            writer.writerow(flattened_row)
        
        return output.getvalue()
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary for CSV export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert lists to comma-separated strings
                items.append((new_key, ', '.join(map(str, v)) if v else ''))
            else:
                items.append((new_key, v))
        
        return dict(items)


class ExcelFormatter(ExportFormatter):
    """Excel export formatter"""
    
    def __init__(self):
        super().__init__(ExportFormat.EXCEL)
    
    def format_data(self, data: List[Dict], metadata: Dict = None) -> bytes:
        """Format data as Excel file"""
        if not data:
            # Create empty workbook
            df = pd.DataFrame()
        else:
            # Flatten data for Excel
            flattened_data = []
            for row in data:
                flattened_data.append(self._flatten_dict(row))
            
            df = pd.DataFrame(flattened_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
            
            # Add metadata sheet if provided
            if metadata:
                metadata_df = pd.DataFrame(list(metadata.items()), columns=['Key', 'Value'])
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary for Excel export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, ', '.join(map(str, v)) if v else ''))
            else:
                items.append((new_key, v))
        
        return dict(items)


class iCalFormatter(ExportFormatter):
    """iCal export formatter for events"""
    
    def __init__(self):
        super().__init__(ExportFormat.ICAL)
    
    def format_data(self, data: List[Dict], metadata: Dict = None) -> str:
        """Format events as iCal"""
        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//TaskMaster//TaskMaster//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]
        
        for event_data in data:
            if event_data.get('type') == 'event' or 'start_time' in event_data:
                ical_lines.extend(self._format_event(event_data))
        
        ical_lines.append("END:VCALENDAR")
        return "\r\n".join(ical_lines)
    
    def _format_event(self, event_data: Dict) -> List[str]:
        """Format single event for iCal"""
        lines = ["BEGIN:VEVENT"]
        
        # Required fields
        lines.append(f"UID:{event_data.get('id', str(uuid.uuid4()))}")
        
        # Format datetime
        start_time = event_data.get('start_time')
        if start_time:
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                lines.append(f"DTSTART:{dt.strftime('%Y%m%dT%H%M%SZ')}")
            except:
                pass
        
        end_time = event_data.get('end_time')
        if end_time:
            try:
                dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                lines.append(f"DTEND:{dt.strftime('%Y%m%dT%H%M%SZ')}")
            except:
                pass
        
        # Optional fields
        if 'title' in event_data:
            lines.append(f"SUMMARY:{self._escape_ical_text(event_data['title'])}")
        
        if 'description' in event_data:
            lines.append(f"DESCRIPTION:{self._escape_ical_text(event_data['description'])}")
        
        if 'location' in event_data:
            lines.append(f"LOCATION:{self._escape_ical_text(event_data['location'])}")
        
        # Timestamps
        now = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        lines.append(f"DTSTAMP:{now}")
        
        if 'created_at' in event_data:
            try:
                dt = datetime.fromisoformat(event_data['created_at'].replace('Z', '+00:00'))
                lines.append(f"CREATED:{dt.strftime('%Y%m%dT%H%M%SZ')}")
            except:
                pass
        
        lines.append("END:VEVENT")
        return lines
    
    def _escape_ical_text(self, text: str) -> str:
        """Escape text for iCal format"""
        if not text:
            return ""
        
        # iCal text escaping
        text = text.replace('\\', '\\\\')
        text = text.replace(';', '\\;')
        text = text.replace(',', '\\,')
        text = text.replace('\n', '\\n')
        return text


class ExportService:
    """Main export service coordinating all export operations"""
    
    def __init__(self):
        self.formatters = {
            ExportFormat.JSON: JSONFormatter(),
            ExportFormat.CSV: CSVFormatter(),
            ExportFormat.EXCEL: ExcelFormatter(),
            ExportFormat.ICAL: iCalFormatter()
        }
        self.active_exports = {}
    
    def create_export(self, export_request: ExportRequest) -> ExportResult:
        """Create new export operation"""
        export_id = str(uuid.uuid4())
        
        try:
            # Validate request
            self._validate_export_request(export_request)
            
            # Create export result
            result = ExportResult(
                export_id=export_id,
                status=ExportStatus.PENDING,
                format=export_request.format,
                file_path=None,
                file_size=None,
                record_count=0,
                created_at=datetime.utcnow(),
                completed_at=None,
                error_message=None,
                download_url=None
            )
            
            self.active_exports[export_id] = result
            
            # Process export
            self._process_export(export_id, export_request)
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Export creation failed: {e}")
            return ExportResult(
                export_id=export_id,
                status=ExportStatus.FAILED,
                format=export_request.format,
                file_path=None,
                file_size=None,
                record_count=0,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error_message=str(e),
                download_url=None
            )
    
    def _validate_export_request(self, request: ExportRequest):
        """Validate export request parameters"""
        if not request.entity_types:
            raise ValueError("At least one entity type must be specified")
        
        valid_types = {'tasks', 'events', 'initiatives', 'projects', 'meals', 'dishes'}
        invalid_types = set(request.entity_types) - valid_types
        if invalid_types:
            raise ValueError(f"Invalid entity types: {', '.join(invalid_types)}")
        
        if request.format not in self.formatters:
            raise ValueError(f"Unsupported export format: {request.format}")
    
    def _process_export(self, export_id: str, request: ExportRequest):
        """Process export request"""
        result = self.active_exports[export_id]
        result.status = ExportStatus.PROCESSING
        
        try:
            # Fetch data based on request
            data = self._fetch_export_data(request)
            result.record_count = len(data)
            
            # Format data
            formatter = self.formatters[request.format]
            formatted_data = formatter.format_data(data, self._build_metadata(request))
            
            # Save to file
            file_path = self._save_export_file(export_id, formatted_data, formatter)
            result.file_path = file_path
            result.file_size = len(formatted_data) if isinstance(formatted_data, (str, bytes)) else 0
            
            # Complete export
            result.status = ExportStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            result.download_url = f"/api/export/{export_id}/download"
            
        except Exception as e:
            current_app.logger.error(f"Export processing failed: {e}")
            result.status = ExportStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
    
    def _fetch_export_data(self, request: ExportRequest) -> List[Dict]:
        """Fetch data for export based on request parameters"""
        all_data = []
        
        model_map = {
            'tasks': Task,
            'events': Event,
            'initiatives': Initiative,
            'projects': Project,
            'meals': Meal,
            'dishes': Dish
        }
        
        for entity_type in request.entity_types:
            model = model_map.get(entity_type)
            if not model:
                continue
            
            # Build query
            query = model.query
            
            # Apply filters
            if request.filters:
                query = self._apply_filters(query, model, request.filters)
            
            # Apply date range
            if request.date_range and hasattr(model, 'created_at'):
                if 'start_date' in request.date_range:
                    start_date = datetime.fromisoformat(request.date_range['start_date'])
                    query = query.filter(model.created_at >= start_date)
                
                if 'end_date' in request.date_range:
                    end_date = datetime.fromisoformat(request.date_range['end_date'])
                    query = query.filter(model.created_at <= end_date)
            
            # Apply sorting
            if request.sort_order and hasattr(model, 'created_at'):
                if request.sort_order == 'newest':
                    query = query.order_by(model.created_at.desc())
                elif request.sort_order == 'oldest':
                    query = query.order_by(model.created_at.asc())
            
            # Fetch entities
            entities = query.all()
            
            # Convert to dictionaries
            for entity in entities:
                entity_dict = entity.to_dict()
                entity_dict['type'] = entity_type.rstrip('s')  # Remove plural
                
                # Apply field filtering
                if request.include_fields:
                    entity_dict = {k: v for k, v in entity_dict.items() if k in request.include_fields}
                elif request.exclude_fields:
                    entity_dict = {k: v for k, v in entity_dict.items() if k not in request.exclude_fields}
                
                all_data.append(entity_dict)
        
        return all_data
    
    def _apply_filters(self, query: Query, model, filters: Dict) -> Query:
        """Apply filters to query"""
        for field, value in filters.items():
            if hasattr(model, field):
                column = getattr(model, field)
                
                if isinstance(value, list):
                    query = query.filter(column.in_(value))
                elif isinstance(value, dict) and 'operator' in value:
                    # Advanced filtering
                    operator = value['operator']
                    filter_value = value['value']
                    
                    if operator == 'like':
                        query = query.filter(column.like(f'%{filter_value}%'))
                    elif operator == 'gt':
                        query = query.filter(column > filter_value)
                    elif operator == 'lt':
                        query = query.filter(column < filter_value)
                    elif operator == 'gte':
                        query = query.filter(column >= filter_value)
                    elif operator == 'lte':
                        query = query.filter(column <= filter_value)
                else:
                    query = query.filter(column == value)
        
        return query
    
    def _build_metadata(self, request: ExportRequest) -> Dict:
        """Build export metadata"""
        return {
            'format': request.format.value,
            'entity_types': request.entity_types,
            'filters': request.filters,
            'date_range': request.date_range,
            'sort_order': request.sort_order,
            'exported_at': datetime.utcnow().isoformat(),
            'chunk_size': request.chunk_size,
            'compression': request.compression
        }
    
    def _save_export_file(self, export_id: str, data: Union[str, bytes], formatter: ExportFormatter) -> str:
        """Save export data to file"""
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        file_path = f"{temp_dir}/export_{export_id}{formatter.file_extension}"
        
        mode = 'wb' if isinstance(data, bytes) else 'w'
        encoding = None if isinstance(data, bytes) else 'utf-8'
        
        with open(file_path, mode, encoding=encoding) as f:
            f.write(data)
        
        return file_path
    
    def get_export_status(self, export_id: str) -> Optional[ExportResult]:
        """Get export status by ID"""
        return self.active_exports.get(export_id)
    
    def get_export_file(self, export_id: str) -> Optional[str]:
        """Get export file path"""
        result = self.active_exports.get(export_id)
        if result and result.status == ExportStatus.COMPLETED:
            return result.file_path
        return None
    
    def cancel_export(self, export_id: str) -> bool:
        """Cancel export operation"""
        result = self.active_exports.get(export_id)
        if result and result.status in [ExportStatus.PENDING, ExportStatus.PROCESSING]:
            result.status = ExportStatus.CANCELLED
            result.completed_at = datetime.utcnow()
            return True
        return False
    
    def cleanup_old_exports(self, max_age_hours: int = 24):
        """Clean up old export files and records"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        exports_to_remove = []
        for export_id, result in self.active_exports.items():
            if result.created_at < cutoff_time:
                # Remove file if it exists
                if result.file_path:
                    try:
                        import os
                        os.remove(result.file_path)
                    except:
                        pass
                
                exports_to_remove.append(export_id)
        
        # Remove from active exports
        for export_id in exports_to_remove:
            del self.active_exports[export_id]
        
        current_app.logger.info(f"Cleaned up {len(exports_to_remove)} old exports")


# Global export service instance
export_service = ExportService()