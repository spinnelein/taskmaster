"""
WebSocket Security Module for TaskMaster YOLO Phase 2.2

Provides authentication, authorization, rate limiting, and security
measures for WebSocket connections to prevent abuse and ensure
secure real-time communication.

Security Features:
- Connection rate limiting
- Event broadcasting rate limiting
- User authentication and session validation
- Room access control
- Message filtering and validation
- Connection monitoring and abuse detection
"""

import time
import hashlib
import json
from typing import Dict, Set, Optional, List, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for controlling WebSocket operation frequency.
    """
    
    def __init__(self, max_tokens: int, refill_rate: float):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = max_tokens
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens, returns True if allowed"""
        now = time.time()
        
        # Refill tokens based on elapsed time
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait before tokens are available"""
        if self.tokens >= tokens:
            return 0.0
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate


class ConnectionTracker:
    """
    Tracks connection patterns and detects potential abuse.
    """
    
    def __init__(self, window_size: int = 300):  # 5 minutes
        self.window_size = window_size
        self.connections: Dict[str, deque] = defaultdict(deque)
        self.failed_attempts: Dict[str, deque] = defaultdict(deque)
        self.suspicious_ips: Set[str] = set()
    
    def record_connection(self, ip_address: str, success: bool = True):
        """Record a connection attempt"""
        now = time.time()
        
        if success:
            self.connections[ip_address].append(now)
            self._cleanup_old_entries(self.connections[ip_address], now)
        else:
            self.failed_attempts[ip_address].append(now)
            self._cleanup_old_entries(self.failed_attempts[ip_address], now)
    
    def _cleanup_old_entries(self, entries: deque, current_time: float):
        """Remove entries older than window size"""
        while entries and current_time - entries[0] > self.window_size:
            entries.popleft()
    
    def is_rate_limited(self, ip_address: str, max_connections: int = 10) -> bool:
        """Check if IP is rate limited"""
        now = time.time()
        self._cleanup_old_entries(self.connections[ip_address], now)
        return len(self.connections[ip_address]) >= max_connections
    
    def is_suspicious(self, ip_address: str, max_failed: int = 5) -> bool:
        """Check if IP has too many failed attempts"""
        now = time.time()
        self._cleanup_old_entries(self.failed_attempts[ip_address], now)
        
        failed_count = len(self.failed_attempts[ip_address])
        if failed_count >= max_failed:
            self.suspicious_ips.add(ip_address)
            return True
        
        return ip_address in self.suspicious_ips
    
    def get_connection_stats(self, ip_address: str) -> Dict[str, int]:
        """Get connection statistics for an IP"""
        now = time.time()
        self._cleanup_old_entries(self.connections[ip_address], now)
        self._cleanup_old_entries(self.failed_attempts[ip_address], now)
        
        return {
            'connections': len(self.connections[ip_address]),
            'failed_attempts': len(self.failed_attempts[ip_address]),
            'is_suspicious': ip_address in self.suspicious_ips
        }


class MessageValidator:
    """
    Validates WebSocket messages for security and format compliance.
    """
    
    ALLOWED_EVENTS = {
        'authenticate', 'join_room', 'leave_room', 'ping',
        'task_created', 'task_updated', 'task_completed',
        'event_created', 'event_updated', 'event_deleted'
    }
    
    MAX_MESSAGE_SIZE = 10240  # 10KB
    MAX_ROOM_NAME_LENGTH = 100
    MAX_USER_ID_LENGTH = 50
    
    @classmethod
    def validate_message(cls, message: Any) -> tuple[bool, str]:
        """Validate a WebSocket message"""
        try:
            # Check message size
            message_str = json.dumps(message) if not isinstance(message, str) else message
            if len(message_str) > cls.MAX_MESSAGE_SIZE:
                return False, "Message too large"
            
            # Parse if string
            if isinstance(message, str):
                try:
                    message = json.loads(message)
                except json.JSONDecodeError:
                    return False, "Invalid JSON format"
            
            # Check for required structure
            if not isinstance(message, dict):
                return False, "Message must be an object"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @classmethod
    def validate_room_name(cls, room_name: str) -> tuple[bool, str]:
        """Validate room name format and content"""
        if not room_name or not isinstance(room_name, str):
            return False, "Room name must be a non-empty string"
        
        if len(room_name) > cls.MAX_ROOM_NAME_LENGTH:
            return False, "Room name too long"
        
        # Check for allowed characters (alphanumeric, underscore, dash)
        if not room_name.replace('_', '').replace('-', '').isalnum():
            return False, "Room name contains invalid characters"
        
        return True, "Valid"
    
    @classmethod
    def validate_user_id(cls, user_id: str) -> tuple[bool, str]:
        """Validate user ID format"""
        if not user_id or not isinstance(user_id, str):
            return False, "User ID must be a non-empty string"
        
        if len(user_id) > cls.MAX_USER_ID_LENGTH:
            return False, "User ID too long"
        
        # Basic format validation
        if not user_id.replace('_', '').replace('-', '').isalnum():
            return False, "User ID contains invalid characters"
        
        return True, "Valid"


class WebSocketSecurityManager:
    """
    Central security manager for WebSocket operations.
    """
    
    def __init__(self):
        # Rate limiters for different operations
        self.connection_limiter = defaultdict(lambda: RateLimiter(10, 0.1))  # 10 connections per 100 seconds
        self.message_limiter = defaultdict(lambda: RateLimiter(100, 1.0))    # 100 messages per 100 seconds
        self.room_limiter = defaultdict(lambda: RateLimiter(20, 0.2))        # 20 room ops per 100 seconds
        
        # Connection tracking
        self.connection_tracker = ConnectionTracker()
        
        # Authentication sessions
        self.authenticated_sessions: Dict[str, Dict] = {}
        self.session_timeouts: Dict[str, datetime] = {}
        
        # Blocked IPs and sessions
        self.blocked_ips: Set[str] = set()
        self.blocked_sessions: Set[str] = set()
        
        # Activity monitoring
        self.activity_log: deque = deque(maxlen=1000)
        
        logger.info("WebSocket security manager initialized")
    
    def check_connection_allowed(self, ip_address: str, user_agent: str = None) -> tuple[bool, str]:
        """Check if a connection is allowed"""
        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            return False, "IP address blocked"
        
        # Check rate limits
        if not self.connection_limiter[ip_address].consume():
            return False, "Connection rate limit exceeded"
        
        # Check for suspicious activity
        if self.connection_tracker.is_suspicious(ip_address):
            return False, "Suspicious activity detected"
        
        # Check connection rate limits
        if self.connection_tracker.is_rate_limited(ip_address):
            return False, "Too many connections from IP"
        
        return True, "Connection allowed"
    
    def record_connection(self, ip_address: str, session_id: str, success: bool = True):
        """Record a connection attempt"""
        self.connection_tracker.record_connection(ip_address, success)
        
        if success:
            self.activity_log.append({
                'type': 'connection',
                'ip': ip_address,
                'session_id': session_id,
                'timestamp': datetime.utcnow(),
                'success': True
            })
        else:
            self.activity_log.append({
                'type': 'connection_failed',
                'ip': ip_address,
                'timestamp': datetime.utcnow(),
                'success': False
            })
    
    def authenticate_session(self, session_id: str, user_id: str, ip_address: str) -> tuple[bool, str]:
        """Authenticate a WebSocket session"""
        # Validate user ID format
        valid, message = MessageValidator.validate_user_id(user_id)
        if not valid:
            return False, message
        
        # Check if session is blocked
        if session_id in self.blocked_sessions:
            return False, "Session blocked"
        
        # In production, validate against actual user system
        # For now, accept any valid format user ID
        
        # Store authentication info
        self.authenticated_sessions[session_id] = {
            'user_id': user_id,
            'ip_address': ip_address,
            'authenticated_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        
        # Set session timeout (24 hours)
        self.session_timeouts[session_id] = datetime.utcnow() + timedelta(hours=24)
        
        self.activity_log.append({
            'type': 'authentication',
            'session_id': session_id,
            'user_id': user_id,
            'ip': ip_address,
            'timestamp': datetime.utcnow()
        })
        
        logger.info(f"Session authenticated: {session_id} for user {user_id}")
        return True, "Authentication successful"
    
    def is_authenticated(self, session_id: str) -> bool:
        """Check if a session is authenticated and valid"""
        if session_id not in self.authenticated_sessions:
            return False
        
        # Check session timeout
        if session_id in self.session_timeouts:
            if datetime.utcnow() > self.session_timeouts[session_id]:
                self.invalidate_session(session_id)
                return False
        
        # Update last activity
        self.authenticated_sessions[session_id]['last_activity'] = datetime.utcnow()
        return True
    
    def get_session_user(self, session_id: str) -> Optional[str]:
        """Get user ID for an authenticated session"""
        if self.is_authenticated(session_id):
            return self.authenticated_sessions[session_id]['user_id']
        return None
    
    def check_room_access(self, session_id: str, room_name: str) -> tuple[bool, str]:
        """Check if a session can access a room"""
        # Validate room name
        valid, message = MessageValidator.validate_room_name(room_name)
        if not valid:
            return False, message
        
        # Check authentication for non-global rooms
        if room_name != 'global' and not self.is_authenticated(session_id):
            return False, "Authentication required for room access"
        
        # Get user ID
        user_id = self.get_session_user(session_id)
        
        # Check user-specific room access
        if room_name.startswith('user_'):
            target_user = room_name[5:]  # Remove 'user_' prefix
            if user_id != target_user:
                return False, "Access denied to user room"
        
        # Check rate limits for room operations
        ip = self.authenticated_sessions.get(session_id, {}).get('ip_address', 'unknown')
        if not self.room_limiter[ip].consume():
            return False, "Room operation rate limit exceeded"
        
        return True, "Room access allowed"
    
    def check_message_allowed(self, session_id: str, message: Any) -> tuple[bool, str]:
        """Check if a message is allowed"""
        # Get IP address for rate limiting
        session_info = self.authenticated_sessions.get(session_id, {})
        ip_address = session_info.get('ip_address', 'unknown')
        
        # Check message rate limits
        if not self.message_limiter[ip_address].consume():
            return False, "Message rate limit exceeded"
        
        # Validate message format
        valid, validation_message = MessageValidator.validate_message(message)
        if not valid:
            return False, validation_message
        
        return True, "Message allowed"
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        if session_id in self.authenticated_sessions:
            user_id = self.authenticated_sessions[session_id]['user_id']
            del self.authenticated_sessions[session_id]
            
            if session_id in self.session_timeouts:
                del self.session_timeouts[session_id]
            
            self.activity_log.append({
                'type': 'session_invalidated',
                'session_id': session_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow()
            })
            
            logger.info(f"Session invalidated: {session_id}")
    
    def block_ip(self, ip_address: str, reason: str = "Security violation"):
        """Block an IP address"""
        self.blocked_ips.add(ip_address)
        self.activity_log.append({
            'type': 'ip_blocked',
            'ip': ip_address,
            'reason': reason,
            'timestamp': datetime.utcnow()
        })
        logger.warning(f"IP blocked: {ip_address} - {reason}")
    
    def block_session(self, session_id: str, reason: str = "Security violation"):
        """Block a session"""
        self.blocked_sessions.add(session_id)
        self.invalidate_session(session_id)
        self.activity_log.append({
            'type': 'session_blocked',
            'session_id': session_id,
            'reason': reason,
            'timestamp': datetime.utcnow()
        })
        logger.warning(f"Session blocked: {session_id} - {reason}")
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        now = datetime.utcnow()
        
        # Count recent activities
        recent_activities = [
            log for log in self.activity_log 
            if (now - log['timestamp']).total_seconds() < 3600  # Last hour
        ]
        
        return {
            'active_sessions': len(self.authenticated_sessions),
            'blocked_ips': len(self.blocked_ips),
            'blocked_sessions': len(self.blocked_sessions),
            'suspicious_ips': len(self.connection_tracker.suspicious_ips),
            'recent_activities': len(recent_activities),
            'activity_breakdown': {
                activity_type: len([a for a in recent_activities if a['type'] == activity_type])
                for activity_type in set(a['type'] for a in recent_activities)
            },
            'total_activity_log_entries': len(self.activity_log)
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, timeout in self.session_timeouts.items()
            if now > timeout
        ]
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


# Global security manager instance
_security_manager: Optional[WebSocketSecurityManager] = None


def get_security_manager() -> WebSocketSecurityManager:
    """Get the global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = WebSocketSecurityManager()
    return _security_manager


def check_connection_security(ip_address: str, user_agent: str = None) -> tuple[bool, str]:
    """Convenience function to check connection security"""
    return get_security_manager().check_connection_allowed(ip_address, user_agent)


def authenticate_websocket_session(session_id: str, user_id: str, ip_address: str) -> tuple[bool, str]:
    """Convenience function to authenticate WebSocket session"""
    return get_security_manager().authenticate_session(session_id, user_id, ip_address)