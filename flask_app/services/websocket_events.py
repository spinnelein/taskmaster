"""
WebSocket Event Broadcasting System for TaskMaster YOLO Phase 2.2

Defines event types, room organization strategies, and broadcasting
patterns for real-time task and event synchronization.

Event Categories:
- Task Events: completion, assignment, priority changes
- Schedule Events: time pool updates, conflict detection
- Collaboration Events: user presence, live editing
- System Events: notifications, AI insights
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json


class EventType(Enum):
    """Enumeration of all WebSocket event types"""
    
    # Task Management Events
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_DELETED = "task_deleted"
    TASK_ASSIGNED = "task_assigned"
    TASK_UNASSIGNED = "task_unassigned"
    TASK_PRIORITY_CHANGED = "task_priority_changed"
    TASK_STATUS_CHANGED = "task_status_changed"
    
    # Event/Calendar Events
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_DELETED = "event_deleted"
    EVENT_STARTED = "event_started"
    EVENT_ENDED = "event_ended"
    
    # Schedule Events
    SCHEDULE_UPDATED = "schedule_updated"
    TIME_POOL_ASSIGNED = "time_pool_assigned"
    TIME_POOL_RELEASED = "time_pool_released"
    SCHEDULE_CONFLICT = "schedule_conflict"
    SCHEDULE_REGENERATED = "schedule_regenerated"
    
    # Project/Initiative Events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_PHASE_CHANGED = "project_phase_changed"
    INITIATIVE_CREATED = "initiative_created"
    INITIATIVE_UPDATED = "initiative_updated"
    
    # Collaboration Events
    USER_PRESENCE = "user_presence"
    USER_TYPING = "user_typing"
    USER_VIEWING = "user_viewing"
    USER_EDITING = "user_editing"
    EDIT_LOCK_ACQUIRED = "edit_lock_acquired"
    EDIT_LOCK_RELEASED = "edit_lock_released"
    
    # Notification Events
    NOTIFICATION_CREATED = "notification_created"
    NOTIFICATION_READ = "notification_read"
    REMINDER_TRIGGERED = "reminder_triggered"
    DEADLINE_WARNING = "deadline_warning"
    
    # System Events
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"
    WEATHER_UPDATE = "weather_update"
    SYSTEM_MAINTENANCE = "system_maintenance"
    DATA_SYNC_COMPLETE = "data_sync_complete"


class RoomType(Enum):
    """Types of rooms for organizing WebSocket clients"""
    
    USER = "user"           # Personal user room (user_123)
    GLOBAL = "global"       # All connected users
    PROJECT = "project"     # Project-specific room (project_abc)
    INITIATIVE = "initiative"  # Initiative-specific room (initiative_xyz)
    CALENDAR = "calendar"   # Calendar view synchronization
    DASHBOARD = "dashboard" # Dashboard real-time updates
    ADMIN = "admin"         # Administrative users only


@dataclass
class WebSocketEvent:
    """Structured WebSocket event with metadata"""
    
    event_type: EventType
    data: Dict[str, Any]
    source_user_id: Optional[str] = None
    target_rooms: Optional[List[str]] = None
    target_users: Optional[List[str]] = None
    timestamp: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: str = "normal"  # low, normal, high, critical
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        return result
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict())


class RoomManager:
    """
    Manages WebSocket room assignments and routing logic.
    
    Provides intelligent room assignment based on data relationships
    and user permissions for efficient event distribution.
    """
    
    @staticmethod
    def get_task_rooms(task_data: Dict[str, Any]) -> List[str]:
        """Get relevant rooms for a task event"""
        rooms = ["global", "dashboard"]
        
        # Add project room if task belongs to project
        if task_data.get('project_id'):
            rooms.append(f"project_{task_data['project_id']}")
        
        # Add initiative room if task belongs to initiative
        if task_data.get('initiative_id'):
            rooms.append(f"initiative_{task_data['initiative_id']}")
        
        # Add assigned user room if task is assigned
        if task_data.get('assigned_user_id'):
            rooms.append(f"user_{task_data['assigned_user_id']}")
        
        return rooms
    
    @staticmethod
    def get_event_rooms(event_data: Dict[str, Any]) -> List[str]:
        """Get relevant rooms for a calendar event"""
        rooms = ["global", "calendar", "dashboard"]
        
        # Add user room for event creator/attendees
        if event_data.get('created_by'):
            rooms.append(f"user_{event_data['created_by']}")
        
        # Add attendee rooms
        for attendee in event_data.get('attendees', []):
            rooms.append(f"user_{attendee}")
        
        return rooms
    
    @staticmethod
    def get_project_rooms(project_data: Dict[str, Any]) -> List[str]:
        """Get relevant rooms for a project event"""
        rooms = ["global", "dashboard"]
        rooms.append(f"project_{project_data['id']}")
        
        # Add team member rooms
        for member_id in project_data.get('team_members', []):
            rooms.append(f"user_{member_id}")
        
        return rooms
    
    @staticmethod
    def get_schedule_rooms(schedule_data: Dict[str, Any]) -> List[str]:
        """Get relevant rooms for schedule events"""
        rooms = ["global", "calendar", "dashboard"]
        
        # Add user room if schedule is user-specific
        if schedule_data.get('user_id'):
            rooms.append(f"user_{schedule_data['user_id']}")
        
        return rooms
    
    @staticmethod
    def get_notification_rooms(notification_data: Dict[str, Any]) -> List[str]:
        """Get relevant rooms for notification events"""
        rooms = []
        
        # Add target user room
        if notification_data.get('user_id'):
            rooms.append(f"user_{notification_data['user_id']}")
        
        # Add global room for system-wide notifications
        if notification_data.get('is_global', False):
            rooms.append("global")
        
        return rooms


class EventBroadcaster:
    """
    High-level event broadcasting service that combines
    WebSocket service with intelligent room routing.
    """
    
    def __init__(self, websocket_service):
        self.websocket_service = websocket_service
        self.room_manager = RoomManager()
    
    def broadcast_task_event(self, event_type: EventType, task_data: Dict[str, Any], 
                           source_user_id: Optional[str] = None):
        """Broadcast task-related events to appropriate rooms"""
        rooms = self.room_manager.get_task_rooms(task_data)
        
        event = WebSocketEvent(
            event_type=event_type,
            data=task_data,
            source_user_id=source_user_id,
            target_rooms=rooms
        )
        
        self._broadcast_to_rooms(event, rooms)
    
    def broadcast_event_event(self, event_type: EventType, event_data: Dict[str, Any],
                            source_user_id: Optional[str] = None):
        """Broadcast calendar event-related events"""
        rooms = self.room_manager.get_event_rooms(event_data)
        
        event = WebSocketEvent(
            event_type=event_type,
            data=event_data,
            source_user_id=source_user_id,
            target_rooms=rooms
        )
        
        self._broadcast_to_rooms(event, rooms)
    
    def broadcast_schedule_event(self, event_type: EventType, schedule_data: Dict[str, Any],
                               source_user_id: Optional[str] = None):
        """Broadcast schedule-related events"""
        rooms = self.room_manager.get_schedule_rooms(schedule_data)
        
        event = WebSocketEvent(
            event_type=event_type,
            data=schedule_data,
            source_user_id=source_user_id,
            target_rooms=rooms
        )
        
        self._broadcast_to_rooms(event, rooms)
    
    def broadcast_project_event(self, event_type: EventType, project_data: Dict[str, Any],
                              source_user_id: Optional[str] = None):
        """Broadcast project-related events"""
        rooms = self.room_manager.get_project_rooms(project_data)
        
        event = WebSocketEvent(
            event_type=event_type,
            data=project_data,
            source_user_id=source_user_id,
            target_rooms=rooms
        )
        
        self._broadcast_to_rooms(event, rooms)
    
    def broadcast_notification(self, event_type: EventType, notification_data: Dict[str, Any],
                             target_user_id: Optional[str] = None):
        """Broadcast notification events"""
        if target_user_id:
            notification_data['user_id'] = target_user_id
        
        rooms = self.room_manager.get_notification_rooms(notification_data)
        
        event = WebSocketEvent(
            event_type=event_type,
            data=notification_data,
            target_rooms=rooms
        )
        
        self._broadcast_to_rooms(event, rooms)
    
    def broadcast_ai_insight(self, insight_data: Dict[str, Any], 
                           target_user_id: Optional[str] = None):
        """Broadcast AI analysis results"""
        event = WebSocketEvent(
            event_type=EventType.AI_ANALYSIS_COMPLETE,
            data=insight_data,
            priority="high"
        )
        
        if target_user_id:
            self.websocket_service.broadcast_to_user(
                target_user_id, 
                event.event_type.value, 
                event.data
            )
        else:
            self._broadcast_to_rooms(event, ["global"])
    
    def broadcast_presence_update(self, user_id: str, status: str, 
                                context: Optional[Dict[str, Any]] = None):
        """Broadcast user presence updates"""
        presence_data = {
            'user_id': user_id,
            'status': status,
            'context': context or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        event = WebSocketEvent(
            event_type=EventType.USER_PRESENCE,
            data=presence_data,
            source_user_id=user_id
        )
        
        # Broadcast to global room for presence awareness
        self._broadcast_to_rooms(event, ["global"])
    
    def _broadcast_to_rooms(self, event: WebSocketEvent, rooms: List[str]):
        """Internal method to broadcast event to multiple rooms"""
        for room in rooms:
            try:
                self.websocket_service.broadcast_to_room(
                    room, 
                    event.event_type.value, 
                    event.data
                )
            except Exception as e:
                # Log error but continue broadcasting to other rooms
                print(f"Error broadcasting to room {room}: {e}")


def create_task_event(event_type: EventType, task_dict: Dict[str, Any], 
                     user_id: Optional[str] = None) -> WebSocketEvent:
    """Helper function to create task-related WebSocket events"""
    return WebSocketEvent(
        event_type=event_type,
        data=task_dict,
        source_user_id=user_id
    )


def create_calendar_event(event_type: EventType, event_dict: Dict[str, Any],
                         user_id: Optional[str] = None) -> WebSocketEvent:
    """Helper function to create calendar-related WebSocket events"""
    return WebSocketEvent(
        event_type=event_type,
        data=event_dict,
        source_user_id=user_id
    )


def create_notification_event(message: str, notification_type: str = "info",
                            target_user_id: Optional[str] = None) -> WebSocketEvent:
    """Helper function to create notification events"""
    notification_data = {
        'message': message,
        'type': notification_type,
        'user_id': target_user_id,
        'is_global': target_user_id is None
    }
    
    return WebSocketEvent(
        event_type=EventType.NOTIFICATION_CREATED,
        data=notification_data,
        target_users=[target_user_id] if target_user_id else None
    )