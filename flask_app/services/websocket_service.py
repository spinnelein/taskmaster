"""
Real-time WebSocket Service for TaskMaster YOLO Phase 2.2

Provides real-time communication capabilities for task management, 
event synchronization, and multi-user collaboration features.

Key Features:
- Task and event real-time updates
- Multi-user collaboration with presence indicators
- Schedule synchronization and conflict detection
- Smart notifications and AI insights broadcasting
- Room-based event distribution for efficient scaling
"""

import logging
from typing import Dict, List, Optional, Set
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from datetime import datetime
import json
import uuid
from .websocket_security import get_security_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketService:
    """
    Core WebSocket service managing real-time connections and event broadcasting.
    
    Handles connection lifecycle, room management, and event distribution
    following Flask-SocketIO best practices for scalability.
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_connections: Dict[str, Dict] = {}
        self.user_rooms: Dict[str, Set[str]] = {}
        self.room_members: Dict[str, Set[str]] = {}
        self.security_manager = get_security_manager()
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("WebSocket service initialized with security manager")
    
    def _register_handlers(self):
        """Register all WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle client connection with security checks"""
            session_id = request.sid
            ip_address = request.environ.get('REMOTE_ADDR', 'unknown')
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            # Security check
            allowed, reason = self.security_manager.check_connection_allowed(ip_address, user_agent)
            if not allowed:
                logger.warning(f"Connection denied for {ip_address}: {reason}")
                self.security_manager.record_connection(ip_address, session_id, False)
                emit('error', {'message': f'Connection denied: {reason}'})
                disconnect()
                return
            
            # Record successful connection
            self.security_manager.record_connection(ip_address, session_id, True)
            
            client_info = {
                'session_id': session_id,
                'connected_at': datetime.utcnow().isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent,
                'rooms': set(),
                'authenticated': False,
                'user_id': None
            }
            
            # Store connection info
            self.active_connections[session_id] = client_info
            
            logger.info(f"Client connected: {session_id} from {ip_address}")
            
            # Send connection confirmation
            emit('connection_confirmed', {
                'session_id': session_id,
                'server_time': datetime.utcnow().isoformat(),
                'status': 'connected'
            })
            
            # Emit presence update to other clients
            self.broadcast_presence_update('user_connected', session_id)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection and cleanup"""
            session_id = request.sid
            
            if session_id in self.active_connections:
                client_info = self.active_connections[session_id]
                
                # Leave all rooms
                for room in client_info.get('rooms', set()).copy():
                    self.leave_room(session_id, room)
                
                # Clean up user rooms if authenticated
                user_id = client_info.get('user_id')
                if user_id and user_id in self.user_rooms:
                    self.user_rooms[user_id].discard(session_id)
                    if not self.user_rooms[user_id]:
                        del self.user_rooms[user_id]
                
                # Clean up security manager state
                self.security_manager.invalidate_session(session_id)
                
                # Remove connection
                del self.active_connections[session_id]
                
                logger.info(f"Client disconnected: {session_id}")
                
                # Emit presence update
                self.broadcast_presence_update('user_disconnected', session_id)
        
        @self.socketio.on('authenticate')
        def handle_authenticate(data):
            """Handle user authentication with security validation"""
            session_id = request.sid
            
            if session_id not in self.active_connections:
                emit('error', {'message': 'Invalid session'})
                return
            
            # Check message format
            allowed, reason = self.security_manager.check_message_allowed(session_id, data)
            if not allowed:
                emit('error', {'message': f'Message validation failed: {reason}'})
                return
            
            user_id = data.get('user_id')
            if not user_id:
                emit('error', {'message': 'User ID required'})
                return
            
            # Authenticate with security manager
            client_info = self.active_connections[session_id]
            ip_address = client_info.get('ip_address', 'unknown')
            
            auth_success, auth_message = self.security_manager.authenticate_session(
                session_id, user_id, ip_address
            )
            
            if not auth_success:
                emit('error', {'message': f'Authentication failed: {auth_message}'})
                return
            
            # Update connection info
            self.active_connections[session_id]['authenticated'] = True
            self.active_connections[session_id]['user_id'] = user_id
            
            # Track user sessions
            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            self.user_rooms[user_id].add(session_id)
            
            # Join user's personal room
            self.join_room(session_id, f"user_{user_id}")
            
            emit('authenticated', {
                'user_id': user_id,
                'session_id': session_id,
                'status': 'authenticated'
            })
            
            logger.info(f"User authenticated: {user_id} (session: {session_id})")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room join requests with security checks"""
            session_id = request.sid
            
            # Check message format
            allowed, reason = self.security_manager.check_message_allowed(session_id, data)
            if not allowed:
                emit('error', {'message': f'Message validation failed: {reason}'})
                return
            
            room_name = data.get('room')
            if not room_name:
                emit('error', {'message': 'Room name required'})
                return
            
            # Check room access permissions
            access_allowed, access_reason = self.security_manager.check_room_access(session_id, room_name)
            if not access_allowed:
                emit('error', {'message': f'Room access denied: {access_reason}'})
                return
            
            success = self.join_room(session_id, room_name)
            if success:
                emit('room_joined', {'room': room_name, 'session_id': session_id})
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leave requests with security checks"""
            session_id = request.sid
            
            # Check message format
            allowed, reason = self.security_manager.check_message_allowed(session_id, data)
            if not allowed:
                emit('error', {'message': f'Message validation failed: {reason}'})
                return
            
            room_name = data.get('room')
            if not room_name:
                emit('error', {'message': 'Room name required'})
                return
            
            success = self.leave_room(session_id, room_name)
            if success:
                emit('room_left', {'room': room_name, 'session_id': session_id})
        
        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping for connection health checks"""
            emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    def join_room(self, session_id: str, room_name: str):
        """Add client to a room with proper tracking"""
        if session_id not in self.active_connections:
            return False
        
        # Join the room
        join_room(room_name, sid=session_id)
        
        # Update tracking
        self.active_connections[session_id]['rooms'].add(room_name)
        
        if room_name not in self.room_members:
            self.room_members[room_name] = set()
        self.room_members[room_name].add(session_id)
        
        logger.info(f"Session {session_id} joined room {room_name}")
        
        # Notify room members
        self.socketio.emit('user_joined_room', {
            'session_id': session_id,
            'room': room_name,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_name)
        
        return True
    
    def leave_room(self, session_id: str, room_name: str):
        """Remove client from a room with proper cleanup"""
        if session_id not in self.active_connections:
            return False
        
        # Leave the room
        leave_room(room_name, sid=session_id)
        
        # Update tracking
        self.active_connections[session_id]['rooms'].discard(room_name)
        
        if room_name in self.room_members:
            self.room_members[room_name].discard(session_id)
            if not self.room_members[room_name]:
                del self.room_members[room_name]
        
        logger.info(f"Session {session_id} left room {room_name}")
        
        # Notify room members
        self.socketio.emit('user_left_room', {
            'session_id': session_id,
            'room': room_name,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_name)
        
        return True
    
    def broadcast_to_room(self, room_name: str, event_type: str, data: Dict):
        """Broadcast event to all clients in a room"""
        event_data = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'room': room_name
        }
        
        self.socketio.emit('broadcast_event', event_data, room=room_name)
        logger.info(f"Broadcasted {event_type} to room {room_name}")
    
    def broadcast_to_user(self, user_id: str, event_type: str, data: Dict):
        """Broadcast event to all sessions of a specific user"""
        if user_id not in self.user_rooms:
            logger.warning(f"User {user_id} not found for broadcast")
            return False
        
        event_data = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id
        }
        
        for session_id in self.user_rooms[user_id]:
            self.socketio.emit('user_event', event_data, room=session_id)
        
        logger.info(f"Broadcasted {event_type} to user {user_id}")
        return True
    
    def broadcast_presence_update(self, event_type: str, session_id: str):
        """Broadcast presence updates to relevant rooms"""
        if session_id not in self.active_connections:
            return
        
        client_info = self.active_connections[session_id]
        user_id = client_info.get('user_id')
        
        presence_data = {
            'session_id': session_id,
            'user_id': user_id,
            'event': event_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Broadcast to all rooms the user was in
        for room in client_info.get('rooms', set()):
            self.socketio.emit('presence_update', presence_data, room=room)
    
    def get_connection_stats(self) -> Dict:
        """Get current connection statistics including security info"""
        security_stats = self.security_manager.get_security_stats()
        
        return {
            'total_connections': len(self.active_connections),
            'authenticated_connections': len([
                c for c in self.active_connections.values() 
                if c.get('authenticated', False)
            ]),
            'total_rooms': len(self.room_members),
            'active_users': len(self.user_rooms),
            'rooms': {
                room: len(members) 
                for room, members in self.room_members.items()
            },
            'security': security_stats
        }
    
    def disconnect_user(self, user_id: str, reason: str = "Server disconnect"):
        """Force disconnect all sessions for a user"""
        if user_id not in self.user_rooms:
            return False
        
        for session_id in self.user_rooms[user_id].copy():
            self.socketio.emit('force_disconnect', {
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id)
            disconnect(sid=session_id)
        
        logger.info(f"Disconnected user {user_id}: {reason}")
        return True


# Global service instance
_websocket_service: Optional[WebSocketService] = None


def initialize_websocket_service(socketio: SocketIO) -> WebSocketService:
    """Initialize the global WebSocket service instance"""
    global _websocket_service
    _websocket_service = WebSocketService(socketio)
    return _websocket_service


def get_websocket_service() -> Optional[WebSocketService]:
    """Get the global WebSocket service instance"""
    return _websocket_service