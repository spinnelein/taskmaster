"""
WebSocket Integration Layer for TaskMaster YOLO Phase 2.2

Provides integration between REST API operations and WebSocket 
real-time broadcasting for seamless task and event synchronization.

This module acts as a bridge between the existing API routes and 
the new WebSocket broadcasting system.
"""

from typing import Dict, Any, Optional
from .websocket_service import get_websocket_service
from .websocket_events import EventBroadcaster, EventType
import logging

logger = logging.getLogger(__name__)


class WebSocketIntegrator:
    """
    Integration service that connects REST API operations
    with WebSocket real-time broadcasting.
    """
    
    def __init__(self):
        self.websocket_service = None
        self.event_broadcaster = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize WebSocket services if available"""
        try:
            self.websocket_service = get_websocket_service()
            if self.websocket_service:
                self.event_broadcaster = EventBroadcaster(self.websocket_service)
                logger.info("WebSocket integration initialized successfully")
            else:
                logger.warning("WebSocket service not available")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket integration: {e}")
    
    def is_available(self) -> bool:
        """Check if WebSocket services are available"""
        return self.websocket_service is not None and self.event_broadcaster is not None
    
    # Task Event Integrations
    
    def on_task_created(self, task_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast task creation event"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_task_event(
                EventType.TASK_CREATED,
                task_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted task created: {task_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast task created event: {e}")
    
    def on_task_updated(self, task_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast task update event"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_task_event(
                EventType.TASK_UPDATED,
                task_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted task updated: {task_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast task updated event: {e}")
    
    def on_task_completed(self, task_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast task completion event"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_task_event(
                EventType.TASK_COMPLETED,
                task_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted task completed: {task_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast task completed event: {e}")
    
    def on_task_deleted(self, task_id: str, user_id: Optional[str] = None):
        """Broadcast task deletion event"""
        if not self.is_available():
            return
        
        try:
            task_data = {'id': task_id, 'deleted': True}
            self.event_broadcaster.broadcast_task_event(
                EventType.TASK_DELETED,
                task_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted task deleted: {task_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast task deleted event: {e}")
    
    def on_task_assigned(self, task_data: Dict[str, Any], time_pool_data: Dict[str, Any],
                        user_id: Optional[str] = None):
        """Broadcast task assignment to time pool"""
        if not self.is_available():
            return
        
        try:
            assignment_data = {
                'task': task_data,
                'time_pool': time_pool_data,
                'assigned_at': task_data.get('updated_at')
            }
            
            self.event_broadcaster.broadcast_task_event(
                EventType.TASK_ASSIGNED,
                assignment_data,
                source_user_id=user_id
            )
            
            # Also broadcast schedule update
            self.event_broadcaster.broadcast_schedule_event(
                EventType.TIME_POOL_ASSIGNED,
                assignment_data,
                source_user_id=user_id
            )
            
            logger.info(f"Broadcasted task assignment: {task_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast task assignment event: {e}")
    
    def on_task_priority_changed(self, task_data: Dict[str, Any], 
                               old_priority: int, new_priority: int,
                               user_id: Optional[str] = None):
        """Broadcast task priority change"""
        if not self.is_available():
            return
        
        try:
            priority_data = {
                **task_data,
                'old_priority': old_priority,
                'new_priority': new_priority
            }
            
            self.event_broadcaster.broadcast_task_event(
                EventType.TASK_PRIORITY_CHANGED,
                priority_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted priority change: {task_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast priority change event: {e}")
    
    # Event/Calendar Event Integrations
    
    def on_event_created(self, event_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast calendar event creation"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_event_event(
                EventType.EVENT_CREATED,
                event_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted event created: {event_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast event created: {e}")
    
    def on_event_updated(self, event_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast calendar event update"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_event_event(
                EventType.EVENT_UPDATED,
                event_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted event updated: {event_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast event updated: {e}")
    
    def on_event_deleted(self, event_id: str, user_id: Optional[str] = None):
        """Broadcast calendar event deletion"""
        if not self.is_available():
            return
        
        try:
            event_data = {'id': event_id, 'deleted': True}
            self.event_broadcaster.broadcast_event_event(
                EventType.EVENT_DELETED,
                event_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted event deleted: {event_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast event deleted: {e}")
    
    # Schedule Event Integrations
    
    def on_schedule_regenerated(self, schedule_data: Dict[str, Any], 
                              user_id: Optional[str] = None):
        """Broadcast schedule regeneration completion"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_schedule_event(
                EventType.SCHEDULE_REGENERATED,
                schedule_data,
                source_user_id=user_id
            )
            logger.info("Broadcasted schedule regeneration")
        except Exception as e:
            logger.error(f"Failed to broadcast schedule regeneration: {e}")
    
    def on_schedule_conflict_detected(self, conflict_data: Dict[str, Any],
                                    user_id: Optional[str] = None):
        """Broadcast schedule conflict detection"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_schedule_event(
                EventType.SCHEDULE_CONFLICT,
                conflict_data,
                source_user_id=user_id
            )
            logger.warning(f"Broadcasted schedule conflict: {conflict_data}")
        except Exception as e:
            logger.error(f"Failed to broadcast schedule conflict: {e}")
    
    # Project/Initiative Event Integrations
    
    def on_project_created(self, project_data: Dict[str, Any], user_id: Optional[str] = None):
        """Broadcast project creation"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_project_event(
                EventType.PROJECT_CREATED,
                project_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted project created: {project_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast project created: {e}")
    
    def on_initiative_created(self, initiative_data: Dict[str, Any], 
                            user_id: Optional[str] = None):
        """Broadcast initiative creation"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_project_event(
                EventType.INITIATIVE_CREATED,
                initiative_data,
                source_user_id=user_id
            )
            logger.info(f"Broadcasted initiative created: {initiative_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to broadcast initiative created: {e}")
    
    # System Event Integrations
    
    def on_ai_analysis_complete(self, analysis_data: Dict[str, Any],
                              target_user_id: Optional[str] = None):
        """Broadcast AI analysis completion"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_ai_insight(
                analysis_data,
                target_user_id=target_user_id
            )
            logger.info("Broadcasted AI analysis completion")
        except Exception as e:
            logger.error(f"Failed to broadcast AI analysis: {e}")
    
    def on_weather_update(self, weather_data: Dict[str, Any]):
        """Broadcast weather update"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_to_room(
                "global",
                EventType.WEATHER_UPDATE.value,
                weather_data
            )
            logger.info("Broadcasted weather update")
        except Exception as e:
            logger.error(f"Failed to broadcast weather update: {e}")
    
    # Notification Integrations
    
    def send_notification(self, message: str, notification_type: str = "info",
                         target_user_id: Optional[str] = None):
        """Send real-time notification"""
        if not self.is_available():
            return
        
        try:
            notification_data = {
                'message': message,
                'type': notification_type,
                'timestamp': None  # Will be set by WebSocketEvent
            }
            
            self.event_broadcaster.broadcast_notification(
                EventType.NOTIFICATION_CREATED,
                notification_data,
                target_user_id=target_user_id
            )
            logger.info(f"Sent notification: {message}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    # Connection Management
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        if not self.is_available():
            return {'status': 'unavailable'}
        
        try:
            return self.websocket_service.get_connection_stats()
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def broadcast_presence_update(self, user_id: str, status: str,
                                context: Optional[Dict[str, Any]] = None):
        """Broadcast user presence update"""
        if not self.is_available():
            return
        
        try:
            self.event_broadcaster.broadcast_presence_update(
                user_id, status, context
            )
        except Exception as e:
            logger.error(f"Failed to broadcast presence update: {e}")


# Global integrator instance
_websocket_integrator: Optional[WebSocketIntegrator] = None


def get_websocket_integrator() -> WebSocketIntegrator:
    """Get the global WebSocket integrator instance"""
    global _websocket_integrator
    if _websocket_integrator is None:
        _websocket_integrator = WebSocketIntegrator()
    return _websocket_integrator


# Convenience functions for easy integration with existing API routes

def broadcast_task_created(task_data: Dict[str, Any], user_id: Optional[str] = None):
    """Convenience function to broadcast task creation"""
    get_websocket_integrator().on_task_created(task_data, user_id)


def broadcast_task_completed(task_data: Dict[str, Any], user_id: Optional[str] = None):
    """Convenience function to broadcast task completion"""
    get_websocket_integrator().on_task_completed(task_data, user_id)


def broadcast_event_created(event_data: Dict[str, Any], user_id: Optional[str] = None):
    """Convenience function to broadcast event creation"""
    get_websocket_integrator().on_event_created(event_data, user_id)


def send_notification(message: str, notification_type: str = "info",
                     target_user_id: Optional[str] = None):
    """Convenience function to send notifications"""
    get_websocket_integrator().send_notification(message, notification_type, target_user_id)