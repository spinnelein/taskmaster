# TaskMaster WebSocket Integration Guide

## Table of Contents

1. [Overview](#overview)
2. [WebSocket Connection](#websocket-connection)
3. [Authentication](#authentication)
4. [Event Types](#event-types)
5. [Channel Subscription](#channel-subscription)
6. [Message Format](#message-format)
7. [Client Implementation](#client-implementation)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)
10. [Code Examples](#code-examples)
11. [Troubleshooting](#troubleshooting)

## Overview

TaskMaster's WebSocket integration provides real-time updates for collaborative task management. Clients can receive instant notifications about task changes, event updates, schedule modifications, and AI insights without polling the REST API.

### Key Features

- **Real-time Updates**: Instant notifications for all data changes
- **Channel Subscription**: Subscribe to specific event types to reduce noise
- **User-specific Notifications**: Targeted messages based on user context
- **AI Insights**: Real-time delivery of analysis and recommendations
- **Collaborative Features**: Multi-user synchronization and conflict resolution
- **Automatic Reconnection**: Built-in connection management and retry logic

### WebSocket Endpoint

```
Production: wss://api.taskmaster.dev/ws
Development: ws://localhost:5000/ws
```

### Supported Event Types

- **Task Events**: Created, updated, completed, priority changes
- **Event/Calendar Events**: Created, updated, deleted, recurring events
- **Schedule Events**: Time pool updates, schedule regeneration
- **Notification Events**: System notifications, reminders, alerts
- **AI Events**: Analysis completion, recommendations, insights
- **Collaboration Events**: User presence, concurrent editing

## WebSocket Connection

### Basic Connection

```javascript
const ws = new WebSocket('wss://api.taskmaster.dev/ws');

ws.onopen = function(event) {
    console.log('Connected to TaskMaster WebSocket');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.onclose = function(event) {
    console.log('WebSocket connection closed:', event.code, event.reason);
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

### Connection with Authentication

```javascript
const apiKey = 'tk_live_abc123...';
const ws = new WebSocket(`wss://api.taskmaster.dev/ws?api_key=${apiKey}`);
```

### Connection States

| State | Code | Description |
|-------|------|-------------|
| CONNECTING | 0 | Connection is being established |
| OPEN | 1 | Connection is open and ready |
| CLOSING | 2 | Connection is closing |
| CLOSED | 3 | Connection is closed |

## Authentication

TaskMaster WebSocket supports multiple authentication methods:

### 1. API Key Authentication (Recommended)

```javascript
const apiKey = 'tk_live_abc123...';
const ws = new WebSocket(`wss://api.taskmaster.dev/ws?api_key=${apiKey}`);
```

### 2. Session Token Authentication

```javascript
const sessionToken = 'sess_xyz789...';
const ws = new WebSocket(`wss://api.taskmaster.dev/ws?token=${sessionToken}`);
```

### 3. Post-Connection Authentication

```javascript
const ws = new WebSocket('wss://api.taskmaster.dev/ws');

ws.onopen = function() {
    // Authenticate after connection
    ws.send(JSON.stringify({
        type: 'auth',
        api_key: 'tk_live_abc123...'
    }));
};
```

### Authentication Response

```json
{
  "type": "auth_response",
  "status": "success",
  "user_id": "user-123",
  "permissions": ["tasks.read", "tasks.write", "events.read"],
  "timestamp": "2025-09-19T10:00:00Z"
}
```

## Event Types

TaskMaster WebSocket emits various event types for different system activities.

### Task Events

#### task_created
Emitted when a new task is created.

```json
{
  "type": "task_created",
  "timestamp": "2025-09-19T10:00:00Z",
  "user_id": "user-123",
  "task": {
    "id": "task-456",
    "title": "New feature implementation",
    "description": "Implement user authentication",
    "priority": "high",
    "urgency": 8,
    "status": "active",
    "created_at": "2025-09-19T10:00:00Z",
    "project_id": "project-789"
  }
}
```

#### task_updated
Emitted when a task is modified.

```json
{
  "type": "task_updated",
  "timestamp": "2025-09-19T10:05:00Z",
  "user_id": "user-123",
  "task": {
    "id": "task-456",
    "title": "New feature implementation",
    "urgency": 9,
    "updated_at": "2025-09-19T10:05:00Z"
  },
  "changes": {
    "urgency": {"old": 8, "new": 9},
    "updated_at": {"old": "2025-09-19T10:00:00Z", "new": "2025-09-19T10:05:00Z"}
  }
}
```

#### task_completed
Emitted when a task is marked as completed.

```json
{
  "type": "task_completed",
  "timestamp": "2025-09-19T11:30:00Z",
  "user_id": "user-123",
  "task": {
    "id": "task-456",
    "title": "New feature implementation",
    "status": "completed",
    "completed_at": "2025-09-19T11:30:00Z"
  },
  "completion_time_minutes": 90
}
```

#### task_priority_changed
Emitted when task priority is specifically updated.

```json
{
  "type": "task_priority_changed",
  "timestamp": "2025-09-19T10:15:00Z",
  "user_id": "user-123",
  "task": {
    "id": "task-456",
    "title": "New feature implementation",
    "priority": "urgent"
  },
  "old_priority": "high",
  "new_priority": "urgent",
  "reason": "Deadline moved up"
}
```

### Event/Calendar Events

#### event_created
Emitted when a new calendar event is created.

```json
{
  "type": "event_created",
  "timestamp": "2025-09-19T10:00:00Z",
  "user_id": "user-123",
  "event": {
    "id": "event-789",
    "title": "Team Planning Meeting",
    "start": "2025-09-22T09:00:00Z",
    "end": "2025-09-22T10:00:00Z",
    "location": "Conference Room A",
    "event_type": "timed",
    "is_blocking": true,
    "attendees": ["user-123", "user-456"]
  }
}
```

#### event_updated
Emitted when an event is modified.

```json
{
  "type": "event_updated",
  "timestamp": "2025-09-19T10:05:00Z",
  "user_id": "user-123",
  "event": {
    "id": "event-789",
    "title": "Team Planning Meeting",
    "start": "2025-09-22T09:30:00Z",
    "updated_at": "2025-09-19T10:05:00Z"
  },
  "changes": {
    "start": {
      "old": "2025-09-22T09:00:00Z", 
      "new": "2025-09-22T09:30:00Z"
    }
  }
}
```

### Schedule Events

#### schedule_regenerated
Emitted when the task schedule is recalculated.

```json
{
  "type": "schedule_regenerated",
  "timestamp": "2025-09-19T10:00:00Z",
  "user_id": "user-123",
  "schedule_data": {
    "affected_tasks": ["task-456", "task-789"],
    "affected_time_pools": ["pool-123", "pool-456"],
    "regeneration_reason": "New high-priority task added",
    "optimization_score": 87.5
  }
}
```

#### time_pool_updated
Emitted when time pools are modified.

```json
{
  "type": "time_pool_updated",
  "timestamp": "2025-09-19T10:00:00Z",
  "time_pool": {
    "id": "pool-123",
    "pool_date": "2025-09-22",
    "start_time": "2025-09-22T09:00:00Z",
    "end_time": "2025-09-22T12:00:00Z",
    "available_minutes": 120,
    "allocated_minutes": 60
  },
  "changes": {
    "allocated_minutes": {"old": 30, "new": 60}
  }
}
```

### Notification Events

#### notification
General system notifications.

```json
{
  "type": "notification",
  "timestamp": "2025-09-19T10:00:00Z",
  "target_user_id": "user-123",
  "message": "Your task 'Feature Implementation' is due in 1 hour",
  "level": "warning",
  "category": "reminder",
  "action": {
    "type": "view_task",
    "task_id": "task-456"
  },
  "expires_at": "2025-09-19T11:00:00Z"
}
```

#### task_reminder
Task-specific reminders.

```json
{
  "type": "task_reminder",
  "timestamp": "2025-09-19T10:00:00Z",
  "target_user_id": "user-123",
  "task": {
    "id": "task-456",
    "title": "Feature Implementation",
    "due_date": "2025-09-19",
    "priority": "high"
  },
  "reminder_type": "due_soon",
  "time_until_due": "1 hour"
}
```

### AI Events

#### ai_analysis_complete
Emitted when AI analysis finishes.

```json
{
  "type": "ai_analysis_complete",
  "timestamp": "2025-09-19T10:00:00Z",
  "analysis": {
    "id": "analysis-123",
    "type": "task_prioritization",
    "target_user_id": "user-123",
    "results": {
      "recommendations": [
        "Focus on overdue tasks first",
        "Batch similar tasks together",
        "Consider task dependencies"
      ],
      "priority_changes": [
        {
          "task_id": "task-456",
          "current_priority": "medium",
          "suggested_priority": "high",
          "reason": "Blocks 3 other tasks"
        }
      ],
      "efficiency_score": 87.5
    },
    "confidence": 0.92
  }
}
```

### Collaboration Events

#### user_presence
User presence updates for collaborative features.

```json
{
  "type": "user_presence",
  "timestamp": "2025-09-19T10:00:00Z",
  "user_id": "user-456",
  "status": "online",
  "activity": {
    "type": "editing_task",
    "resource_id": "task-123",
    "resource_type": "task"
  }
}
```

## Channel Subscription

Reduce noise by subscribing only to relevant event types.

### Subscribe to Channels

```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['tasks', 'events', 'notifications']
}));
```

### Available Channels

| Channel | Events Included |
|---------|-----------------|
| `tasks` | task_created, task_updated, task_completed, task_priority_changed |
| `events` | event_created, event_updated, event_deleted |
| `schedule` | schedule_regenerated, time_pool_updated |
| `notifications` | notification, task_reminder |
| `ai` | ai_analysis_complete |
| `collaboration` | user_presence |
| `all` | All event types |

### User-Specific Subscriptions

```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['notifications'],
    user_id: 'user-123'  // Only notifications for this user
}));
```

### Project-Specific Subscriptions

```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['tasks', 'events'],
    filters: {
        project_id: 'project-789'
    }
}));
```

### Unsubscribe from Channels

```javascript
ws.send(JSON.stringify({
    type: 'unsubscribe',
    channels: ['schedule']
}));
```

## Message Format

All WebSocket messages follow a consistent JSON format.

### Outgoing Message Format (Client to Server)

```json
{
  "type": "message_type",
  "data": {},
  "request_id": "optional-request-id"
}
```

### Incoming Message Format (Server to Client)

```json
{
  "type": "event_type",
  "timestamp": "2025-09-19T10:00:00Z",
  "data": {},
  "request_id": "optional-request-id"
}
```

### Message Types

#### Client Messages

| Type | Description | Data |
|------|-------------|------|
| `auth` | Authenticate connection | `{api_key: "...", user_id: "..."}` |
| `subscribe` | Subscribe to channels | `{channels: [...], filters: {...}}` |
| `unsubscribe` | Unsubscribe from channels | `{channels: [...]}` |
| `ping` | Keep connection alive | `{}` |

#### Server Messages

| Type | Description |
|------|-------------|
| `auth_response` | Authentication result |
| `subscription_response` | Subscription confirmation |
| `ping` | Connection keep-alive |
| `error` | Error message |
| Task/Event/Schedule events | Data updates |

## Client Implementation

### JavaScript/TypeScript Client

```typescript
interface TaskMasterWebSocketOptions {
  apiKey: string;
  reconnect?: boolean;
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
}

class TaskMasterWebSocket {
  private ws: WebSocket | null = null;
  private options: TaskMasterWebSocketOptions;
  private reconnectAttempts = 0;
  private eventHandlers: Map<string, Function[]> = new Map();

  constructor(url: string, options: TaskMasterWebSocketOptions) {
    this.options = {
      reconnect: true,
      maxReconnectAttempts: 5,
      reconnectDelay: 1000,
      ...options
    };
    this.connect(url);
  }

  private connect(url: string) {
    const wsUrl = `${url}?api_key=${this.options.apiKey}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected');
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.emit('disconnected', { code: event.code, reason: event.reason });
      
      if (this.options.reconnect && this.reconnectAttempts < this.options.maxReconnectAttempts!) {
        this.scheduleReconnect(url);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
  }

  private scheduleReconnect(url: string) {
    this.reconnectAttempts++;
    const delay = this.options.reconnectDelay! * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.connect(url);
    }, delay);
  }

  private handleMessage(data: any) {
    const { type, ...payload } = data;
    this.emit(type, payload);
  }

  public on(eventType: string, handler: Function) {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType)!.push(handler);
  }

  public off(eventType: string, handler: Function) {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(eventType: string, data?: any) {
    const handlers = this.eventHandlers.get(eventType) || [];
    handlers.forEach(handler => handler(data));
  }

  public subscribe(channels: string[], filters?: any) {
    this.send({
      type: 'subscribe',
      channels,
      filters
    });
  }

  public unsubscribe(channels: string[]) {
    this.send({
      type: 'unsubscribe',
      channels
    });
  }

  private send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected');
    }
  }

  public close() {
    if (this.ws) {
      this.options.reconnect = false;
      this.ws.close();
    }
  }
}

// Usage example
const taskMasterWS = new TaskMasterWebSocket('wss://api.taskmaster.dev/ws', {
  apiKey: 'tk_live_abc123...'
});

// Subscribe to events
taskMasterWS.on('connected', () => {
  taskMasterWS.subscribe(['tasks', 'notifications']);
});

// Handle task events
taskMasterWS.on('task_created', (data) => {
  console.log('New task created:', data.task.title);
  updateTaskList(data.task);
});

taskMasterWS.on('task_completed', (data) => {
  console.log('Task completed:', data.task.title);
  markTaskComplete(data.task.id);
});

// Handle notifications
taskMasterWS.on('notification', (data) => {
  showNotification(data.message, data.level);
});
```

### Python Client

```python
import asyncio
import websockets
import json
import logging
from typing import Dict, Callable, Optional, List

class TaskMasterWebSocket:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self.websocket = None
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        
    async def connect(self):
        """Connect to WebSocket server"""
        uri = f"{self.url}?api_key={self.api_key}"
        
        try:
            self.websocket = await websockets.connect(uri)
            self.running = True
            logging.info("WebSocket connected")
            
            # Start message listening loop
            await self.listen()
            
        except Exception as e:
            logging.error(f"WebSocket connection failed: {e}")
            
    async def listen(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            logging.info("WebSocket connection closed")
        except Exception as e:
            logging.error(f"Error in message loop: {e}")
        finally:
            self.running = False
            
    async def handle_message(self, data: dict):
        """Handle incoming message"""
        event_type = data.get('type')
        if event_type and event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logging.error(f"Error in event handler: {e}")
                    
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    async def subscribe(self, channels: List[str], filters: Optional[Dict] = None):
        """Subscribe to channels"""
        message = {
            'type': 'subscribe',
            'channels': channels
        }
        if filters:
            message['filters'] = filters
            
        await self.send(message)
        
    async def send(self, data: dict):
        """Send message to server"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(json.dumps(data))
        else:
            logging.warning("WebSocket not connected")
            
    async def close(self):
        """Close WebSocket connection"""
        self.running = False
        if self.websocket:
            await self.websocket.close()

# Usage example
async def main():
    ws = TaskMasterWebSocket('wss://api.taskmaster.dev/ws', 'tk_live_abc123...')
    
    # Register event handlers
    ws.on('task_created', lambda data: print(f"New task: {data['task']['title']}"))
    ws.on('task_completed', lambda data: print(f"Completed: {data['task']['title']}"))
    
    # Connect and subscribe
    await ws.connect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

### Connection Errors

```javascript
taskMasterWS.on('error', (error) => {
    console.error('WebSocket error:', error);
    
    // Implement fallback to REST API polling
    if (error.code === 'CONNECTION_FAILED') {
        startRestAPIPolling();
    }
});

taskMasterWS.on('disconnected', (event) => {
    console.log('Disconnected:', event.code, event.reason);
    
    // Show user notification
    showNotification('Connection lost. Attempting to reconnect...', 'warning');
});
```

### Message Errors

```javascript
taskMasterWS.on('error', (data) => {
    if (data.type === 'subscription_error') {
        console.error('Subscription failed:', data.message);
        // Handle subscription errors
        handleSubscriptionError(data);
    }
});
```

### Authentication Errors

```javascript
taskMasterWS.on('auth_response', (data) => {
    if (data.status === 'error') {
        console.error('Authentication failed:', data.message);
        // Redirect to login or refresh token
        handleAuthError(data);
    }
});
```

## Best Practices

### 1. Implement Graceful Degradation

```javascript
class TaskManager {
    constructor() {
        this.useWebSocket = true;
        this.setupWebSocket();
        this.setupPollingFallback();
    }
    
    setupWebSocket() {
        this.ws = new TaskMasterWebSocket(WS_URL, { apiKey: API_KEY });
        
        this.ws.on('connected', () => {
            this.useWebSocket = true;
            this.stopPolling();
        });
        
        this.ws.on('disconnected', () => {
            this.useWebSocket = false;
            this.startPolling();
        });
    }
    
    setupPollingFallback() {
        this.pollingInterval = null;
    }
    
    startPolling() {
        if (this.pollingInterval) return;
        
        this.pollingInterval = setInterval(() => {
            this.fetchUpdates();
        }, 30000); // Poll every 30 seconds
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
}
```

### 2. Handle Concurrent Updates

```javascript
class TaskStore {
    constructor() {
        this.tasks = new Map();
        this.lastUpdated = new Map();
    }
    
    updateTask(task) {
        const existingTimestamp = this.lastUpdated.get(task.id);
        const newTimestamp = new Date(task.updated_at);
        
        // Only update if this is newer
        if (!existingTimestamp || newTimestamp > existingTimestamp) {
            this.tasks.set(task.id, task);
            this.lastUpdated.set(task.id, newTimestamp);
            this.notifyChange(task);
        }
    }
}
```

### 3. Implement Message Deduplication

```javascript
class MessageDeduplicator {
    constructor(windowSize = 1000) {
        this.seenMessages = new Set();
        this.windowSize = windowSize;
    }
    
    isDuplicate(messageId) {
        if (this.seenMessages.has(messageId)) {
            return true;
        }
        
        this.seenMessages.add(messageId);
        
        // Clean up old messages
        if (this.seenMessages.size > this.windowSize) {
            const oldMessages = Array.from(this.seenMessages).slice(0, 100);
            oldMessages.forEach(id => this.seenMessages.delete(id));
        }
        
        return false;
    }
}
```

### 4. Optimize Subscriptions

```javascript
// Subscribe only to relevant events for current view
class ViewSubscriptionManager {
    constructor(webSocket) {
        this.ws = webSocket;
        this.currentSubscriptions = new Set();
    }
    
    updateSubscriptionsForView(viewType, context) {
        const newSubscriptions = this.getSubscriptionsForView(viewType, context);
        
        // Unsubscribe from channels no longer needed
        const toUnsubscribe = Array.from(this.currentSubscriptions)
            .filter(channel => !newSubscriptions.has(channel));
        
        if (toUnsubscribe.length > 0) {
            this.ws.unsubscribe(toUnsubscribe);
        }
        
        // Subscribe to new channels
        const toSubscribe = Array.from(newSubscriptions)
            .filter(channel => !this.currentSubscriptions.has(channel));
        
        if (toSubscribe.length > 0) {
            this.ws.subscribe(toSubscribe);
        }
        
        this.currentSubscriptions = newSubscriptions;
    }
    
    getSubscriptionsForView(viewType, context) {
        const subscriptions = new Set();
        
        switch (viewType) {
            case 'dashboard':
                subscriptions.add('tasks');
                subscriptions.add('notifications');
                break;
            case 'calendar':
                subscriptions.add('events');
                subscriptions.add('schedule');
                break;
            case 'project':
                subscriptions.add('tasks');
                subscriptions.add('events');
                // Add project-specific filters
                break;
        }
        
        return subscriptions;
    }
}
```

## Code Examples

### React Integration

```jsx
import React, { useEffect, useState, useCallback } from 'react';
import { TaskMasterWebSocket } from './taskmaster-websocket';

const useTaskMasterWebSocket = (apiKey) => {
    const [ws, setWs] = useState(null);
    const [connected, setConnected] = useState(false);
    const [tasks, setTasks] = useState([]);
    
    useEffect(() => {
        const webSocket = new TaskMasterWebSocket('wss://api.taskmaster.dev/ws', {
            apiKey
        });
        
        webSocket.on('connected', () => {
            setConnected(true);
            webSocket.subscribe(['tasks', 'notifications']);
        });
        
        webSocket.on('disconnected', () => {
            setConnected(false);
        });
        
        webSocket.on('task_created', (data) => {
            setTasks(prev => [...prev, data.task]);
        });
        
        webSocket.on('task_updated', (data) => {
            setTasks(prev => prev.map(task => 
                task.id === data.task.id ? { ...task, ...data.task } : task
            ));
        });
        
        webSocket.on('task_completed', (data) => {
            setTasks(prev => prev.map(task => 
                task.id === data.task.id ? { ...task, status: 'completed' } : task
            ));
        });
        
        setWs(webSocket);
        
        return () => {
            webSocket.close();
        };
    }, [apiKey]);
    
    return { ws, connected, tasks };
};

const TaskDashboard = ({ apiKey }) => {
    const { ws, connected, tasks } = useTaskMasterWebSocket(apiKey);
    
    return (
        <div>
            <div className={`status ${connected ? 'connected' : 'disconnected'}`}>
                {connected ? 'Connected' : 'Disconnected'}
            </div>
            
            <div className="tasks">
                {tasks.map(task => (
                    <div key={task.id} className="task">
                        <h3>{task.title}</h3>
                        <span className={`status ${task.status}`}>{task.status}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
```

### Vue.js Integration

```vue
<template>
  <div>
    <div :class="['status', { connected: isConnected }]">
      {{ isConnected ? 'Connected' : 'Disconnected' }}
    </div>
    
    <div class="tasks">
      <div v-for="task in tasks" :key="task.id" class="task">
        <h3>{{ task.title }}</h3>
        <span :class="['status', task.status]">{{ task.status }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { TaskMasterWebSocket } from './taskmaster-websocket';

export default {
  name: 'TaskDashboard',
  props: ['apiKey'],
  data() {
    return {
      ws: null,
      isConnected: false,
      tasks: []
    };
  },
  mounted() {
    this.setupWebSocket();
  },
  beforeDestroy() {
    if (this.ws) {
      this.ws.close();
    }
  },
  methods: {
    setupWebSocket() {
      this.ws = new TaskMasterWebSocket('wss://api.taskmaster.dev/ws', {
        apiKey: this.apiKey
      });
      
      this.ws.on('connected', () => {
        this.isConnected = true;
        this.ws.subscribe(['tasks', 'notifications']);
      });
      
      this.ws.on('disconnected', () => {
        this.isConnected = false;
      });
      
      this.ws.on('task_created', (data) => {
        this.tasks.push(data.task);
      });
      
      this.ws.on('task_updated', (data) => {
        const index = this.tasks.findIndex(t => t.id === data.task.id);
        if (index !== -1) {
          this.$set(this.tasks, index, { ...this.tasks[index], ...data.task });
        }
      });
    }
  }
};
</script>
```

## Troubleshooting

### Common Issues

#### 1. Connection Fails Immediately

**Symptoms**: WebSocket connection closes immediately after opening

**Possible Causes**:
- Invalid API key
- Network firewall blocking WebSocket
- Incorrect URL

**Solutions**:
```javascript
// Check API key format
if (!apiKey.startsWith('tk_')) {
    console.error('Invalid API key format');
}

// Test with basic connection
const ws = new WebSocket('wss://api.taskmaster.dev/ws');
ws.onopen = () => console.log('Basic connection works');
ws.onerror = (e) => console.error('Basic connection failed:', e);
```

#### 2. Messages Not Received

**Symptoms**: WebSocket connected but no messages received

**Possible Causes**:
- Not subscribed to relevant channels
- API key lacks required scopes
- No events occurring

**Solutions**:
```javascript
// Check subscription status
ws.send(JSON.stringify({
    type: 'get_subscriptions'
}));

// Test with all channels
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['all']
}));
```

#### 3. Frequent Disconnections

**Symptoms**: Connection drops frequently

**Possible Causes**:
- Network instability
- Load balancer timeout
- Client not sending ping/pong

**Solutions**:
```javascript
// Implement heartbeat
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
    }
}, 30000);
```

#### 4. Duplicate Messages

**Symptoms**: Same event received multiple times

**Possible Causes**:
- Network retransmission
- Multiple subscriptions to same channel
- Client-side duplicate handling

**Solutions**:
```javascript
const seenMessages = new Set();

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const messageId = `${data.type}_${data.timestamp}_${data.task?.id || data.event?.id}`;
    
    if (seenMessages.has(messageId)) {
        return; // Skip duplicate
    }
    
    seenMessages.add(messageId);
    handleMessage(data);
};
```

### Debug Tools

#### Enable Debug Logging

```javascript
const ws = new TaskMasterWebSocket('wss://api.taskmaster.dev/ws', {
    apiKey: 'your-key',
    debug: true
});
```

#### Monitor Connection Stats

```javascript
// Get WebSocket statistics
fetch('https://api.taskmaster.dev/websocket/stats', {
    headers: { 'X-API-Key': apiKey }
})
.then(r => r.json())
.then(stats => console.log('WebSocket stats:', stats));
```

#### Test Event Generation

```javascript
// Trigger test events
fetch('https://api.taskmaster.dev/websocket/test-events', {
    method: 'POST',
    headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ user_id: 'your-user-id' })
});
```

This comprehensive WebSocket guide provides everything needed to implement real-time features with TaskMaster's WebSocket API, including practical examples, best practices, and troubleshooting information.