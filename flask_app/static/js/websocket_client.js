/**
 * TaskMaster WebSocket Client Library
 * 
 * Provides easy-to-use JavaScript client for connecting to TaskMaster
 * WebSocket service with real-time task and event synchronization.
 * 
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Event subscription and filtering
 * - Room management for organized event delivery
 * - Authentication handling
 * - Connection health monitoring
 */

class TaskMasterWebSocketClient {
    constructor(options = {}) {
        this.options = {
            url: options.url || `ws://${window.location.host}`,
            autoReconnect: options.autoReconnect !== false,
            maxReconnectAttempts: options.maxReconnectAttempts || 10,
            reconnectDelay: options.reconnectDelay || 1000,
            debug: options.debug || false,
            userId: options.userId || null,
            ...options
        };
        
        this.socket = null;
        this.isConnected = false;
        this.isAuthenticated = false;
        this.reconnectAttempts = 0;
        this.eventHandlers = new Map();
        this.subscriptions = new Set();
        this.joinedRooms = new Set();
        this.connectionStats = {};
        
        this.log('Initializing TaskMaster WebSocket client', this.options);
    }
    
    /**
     * Connect to the WebSocket server
     */
    async connect() {
        if (this.socket && this.isConnected) {
            this.log('Already connected');
            return Promise.resolve();
        }
        
        return new Promise((resolve, reject) => {
            try {
                // Load Socket.IO client library if not already loaded
                if (typeof io === 'undefined') {
                    this.loadSocketIO().then(() => {
                        this._establishConnection(resolve, reject);
                    }).catch(reject);
                } else {
                    this._establishConnection(resolve, reject);
                }
            } catch (error) {
                this.log('Connection error:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Load Socket.IO client library dynamically
     */
    loadSocketIO() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    /**
     * Establish WebSocket connection
     */
    _establishConnection(resolve, reject) {
        this.socket = io(this.options.url, {
            transports: ['websocket', 'polling'],
            autoConnect: true
        });
        
        // Connection events
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.log('Connected to WebSocket server');
            this._setupEventHandlers();
            resolve();
        });
        
        this.socket.on('disconnect', (reason) => {
            this.isConnected = false;
            this.isAuthenticated = false;
            this.log('Disconnected from WebSocket server:', reason);
            this._triggerEvent('disconnect', { reason });
            
            if (this.options.autoReconnect && reason !== 'io client disconnect') {
                this._attemptReconnect();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            this.log('Connection error:', error);
            this._triggerEvent('connection_error', { error });
            reject(error);
        });
        
        // Custom TaskMaster events
        this.socket.on('connection_confirmed', (data) => {
            this.log('Connection confirmed:', data);
            this.connectionStats = data;
            this._triggerEvent('connection_confirmed', data);
            
            // Auto-authenticate if user ID provided
            if (this.options.userId) {
                this.authenticate(this.options.userId);
            }
        });
        
        this.socket.on('authenticated', (data) => {
            this.isAuthenticated = true;
            this.log('Authenticated:', data);
            this._triggerEvent('authenticated', data);
        });
        
        this.socket.on('error', (error) => {
            this.log('Server error:', error);
            this._triggerEvent('error', error);
        });
    }
    
    /**
     * Set up event handlers for TaskMaster events
     */
    _setupEventHandlers() {
        // Broadcast events
        this.socket.on('broadcast_event', (event) => {
            this.log('Received broadcast event:', event);
            this._triggerEvent('broadcast', event);
            this._triggerEvent(event.type, event.data, event);
        });
        
        // User-specific events
        this.socket.on('user_event', (event) => {
            this.log('Received user event:', event);
            this._triggerEvent('user_event', event);
            this._triggerEvent(event.type, event.data, event);
        });
        
        // Presence updates
        this.socket.on('presence_update', (data) => {
            this.log('Presence update:', data);
            this._triggerEvent('presence_update', data);
        });
        
        // Room events
        this.socket.on('user_joined_room', (data) => {
            this.log('User joined room:', data);
            this._triggerEvent('user_joined_room', data);
        });
        
        this.socket.on('user_left_room', (data) => {
            this.log('User left room:', data);
            this._triggerEvent('user_left_room', data);
        });
        
        // Room management confirmations
        this.socket.on('room_joined', (data) => {
            this.joinedRooms.add(data.room);
            this.log('Joined room:', data);
            this._triggerEvent('room_joined', data);
        });
        
        this.socket.on('room_left', (data) => {
            this.joinedRooms.delete(data.room);
            this.log('Left room:', data);
            this._triggerEvent('room_left', data);
        });
        
        // Health check
        this.socket.on('pong', (data) => {
            this.log('Received pong:', data);
            this._triggerEvent('pong', data);
        });
    }
    
    /**
     * Authenticate with the server
     */
    authenticate(userId) {
        if (!this.isConnected) {
            throw new Error('Not connected to server');
        }
        
        this.log('Authenticating user:', userId);
        this.socket.emit('authenticate', { user_id: userId });
    }
    
    /**
     * Join a room for receiving targeted events
     */
    joinRoom(roomName) {
        if (!this.isConnected) {
            throw new Error('Not connected to server');
        }
        
        this.log('Joining room:', roomName);
        this.socket.emit('join_room', { room: roomName });
    }
    
    /**
     * Leave a room
     */
    leaveRoom(roomName) {
        if (!this.isConnected) {
            throw new Error('Not connected to server');
        }
        
        this.log('Leaving room:', roomName);
        this.socket.emit('leave_room', { room: roomName });
    }
    
    /**
     * Subscribe to specific event types
     */
    subscribe(eventType, handler) {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, new Set());
        }
        this.eventHandlers.get(eventType).add(handler);
        this.subscriptions.add(eventType);
        this.log('Subscribed to event:', eventType);
    }
    
    /**
     * Unsubscribe from event types
     */
    unsubscribe(eventType, handler = null) {
        if (handler) {
            this.eventHandlers.get(eventType)?.delete(handler);
        } else {
            this.eventHandlers.delete(eventType);
            this.subscriptions.delete(eventType);
        }
        this.log('Unsubscribed from event:', eventType);
    }
    
    /**
     * Send ping to check connection health
     */
    ping() {
        if (!this.isConnected) {
            throw new Error('Not connected to server');
        }
        
        this.socket.emit('ping');
    }
    
    /**
     * Disconnect from the server
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.isConnected = false;
        this.isAuthenticated = false;
        this.joinedRooms.clear();
        this.log('Disconnected from server');
    }
    
    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            authenticated: this.isAuthenticated,
            userId: this.options.userId,
            joinedRooms: Array.from(this.joinedRooms),
            subscriptions: Array.from(this.subscriptions),
            reconnectAttempts: this.reconnectAttempts,
            connectionStats: this.connectionStats
        };
    }
    
    /**
     * Attempt reconnection with exponential backoff
     */
    _attemptReconnect() {
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            this.log('Max reconnection attempts reached');
            this._triggerEvent('max_reconnect_attempts_reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.options.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        this.log(`Attempting reconnection ${this.reconnectAttempts}/${this.options.maxReconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect().catch((error) => {
                    this.log('Reconnection failed:', error);
                    this._attemptReconnect();
                });
            }
        }, delay);
    }
    
    /**
     * Trigger event handlers
     */
    _triggerEvent(eventType, data = {}, context = {}) {
        const handlers = this.eventHandlers.get(eventType);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data, context);
                } catch (error) {
                    this.log('Error in event handler:', error);
                }
            });
        }
    }
    
    /**
     * Debug logging
     */
    log(...args) {
        if (this.options.debug) {
            console.log('[TaskMaster WebSocket]', ...args);
        }
    }
}

/**
 * Convenience wrapper for TaskMaster-specific event handling
 */
class TaskMasterRealtimeClient extends TaskMasterWebSocketClient {
    constructor(options = {}) {
        super(options);
        this.taskHandlers = new Map();
        this.eventHandlers_specific = new Map();
        this.setupTaskMasterEvents();
    }
    
    setupTaskMasterEvents() {
        // Task events
        this.subscribe('task_created', (data) => this._handleTaskEvent('created', data));
        this.subscribe('task_updated', (data) => this._handleTaskEvent('updated', data));
        this.subscribe('task_completed', (data) => this._handleTaskEvent('completed', data));
        this.subscribe('task_deleted', (data) => this._handleTaskEvent('deleted', data));
        this.subscribe('task_assigned', (data) => this._handleTaskEvent('assigned', data));
        this.subscribe('task_priority_changed', (data) => this._handleTaskEvent('priority_changed', data));
        
        // Event/Calendar events
        this.subscribe('event_created', (data) => this._handleEventEvent('created', data));
        this.subscribe('event_updated', (data) => this._handleEventEvent('updated', data));
        this.subscribe('event_deleted', (data) => this._handleEventEvent('deleted', data));
        
        // Schedule events
        this.subscribe('schedule_updated', (data) => this._handleScheduleEvent('updated', data));
        this.subscribe('schedule_regenerated', (data) => this._handleScheduleEvent('regenerated', data));
        this.subscribe('schedule_conflict', (data) => this._handleScheduleEvent('conflict', data));
        
        // Notification events
        this.subscribe('notification_created', (data) => this._handleNotification(data));
    }
    
    // Task event handling
    onTaskEvent(eventType, handler) {
        if (!this.taskHandlers.has(eventType)) {
            this.taskHandlers.set(eventType, new Set());
        }
        this.taskHandlers.get(eventType).add(handler);
    }
    
    _handleTaskEvent(eventType, data) {
        const handlers = this.taskHandlers.get(eventType);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
        
        // Also trigger generic task handler
        const genericHandlers = this.taskHandlers.get('any');
        if (genericHandlers) {
            genericHandlers.forEach(handler => handler(eventType, data));
        }
    }
    
    // Calendar event handling
    onCalendarEvent(eventType, handler) {
        if (!this.eventHandlers_specific.has(eventType)) {
            this.eventHandlers_specific.set(eventType, new Set());
        }
        this.eventHandlers_specific.get(eventType).add(handler);
    }
    
    _handleEventEvent(eventType, data) {
        const handlers = this.eventHandlers_specific.get(eventType);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
    }
    
    // Schedule event handling
    onScheduleEvent(eventType, handler) {
        this.subscribe(`schedule_${eventType}`, handler);
    }
    
    _handleScheduleEvent(eventType, data) {
        this._triggerEvent(`schedule_${eventType}`, data);
    }
    
    // Notification handling
    onNotification(handler) {
        this.subscribe('notification_created', handler);
    }
    
    _handleNotification(data) {
        // Default notification display
        if (window.showTaskMasterNotification) {
            window.showTaskMasterNotification(data.message, data.type);
        } else {
            console.log('TaskMaster Notification:', data.message);
        }
    }
    
    // Room management shortcuts
    joinProjectRoom(projectId) {
        this.joinRoom(`project_${projectId}`);
    }
    
    joinInitiativeRoom(initiativeId) {
        this.joinRoom(`initiative_${initiativeId}`);
    }
    
    joinCalendarRoom() {
        this.joinRoom('calendar');
    }
    
    joinDashboardRoom() {
        this.joinRoom('dashboard');
    }
}

// Global instance for easy access
window.TaskMasterWebSocket = TaskMasterRealtimeClient;

// Auto-initialization if config is available
if (window.TaskMasterConfig && window.TaskMasterConfig.websocket) {
    window.taskMasterWS = new TaskMasterRealtimeClient(window.TaskMasterConfig.websocket);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TaskMasterWebSocketClient, TaskMasterRealtimeClient };
}