# TaskMaster JavaScript/TypeScript SDK and Examples

Modern JavaScript SDK for the TaskMaster API with TypeScript support, Promise-based operations, and comprehensive real-time features.

## Installation

```bash
# NPM
npm install @taskmaster/api

# Yarn
yarn add @taskmaster/api

# PNPM
pnpm add @taskmaster/api
```

## Quick Start

### JavaScript (Node.js)

```javascript
const { TaskMasterClient } = require('@taskmaster/api');

// Initialize client
const client = new TaskMasterClient({
    apiKey: 'tk_live_abc123...'
});

// Create a task
const task = await client.tasks.create({
    title: 'Complete project documentation',
    description: 'Write comprehensive API documentation',
    priority: 'high',
    urgency: 8,
    duration: 120,
    dueDate: '2025-09-25'
});

console.log(`Created task: ${task.id}`);

// List active high-priority tasks
const tasks = await client.tasks.list({
    status: 'active',
    priority: ['high', 'urgent'],
    sort: 'urgency:desc',
    limit: 20
});

tasks.data.forEach(task => {
    console.log(`- ${task.title} (Urgency: ${task.urgency})`);
});
```

### TypeScript

```typescript
import { TaskMasterClient, Task, CreateTaskData } from '@taskmaster/api';

// Initialize client with type safety
const client = new TaskMasterClient({
    apiKey: 'tk_live_abc123...'
});

// Create a task with full type support
const taskData: CreateTaskData = {
    title: 'Complete project documentation',
    description: 'Write comprehensive API documentation',
    priority: 'high',
    urgency: 8,
    duration: 120,
    dueDate: '2025-09-25'
};

const task: Task = await client.tasks.create(taskData);

// List tasks with typed responses
const response = await client.tasks.list({
    status: 'active',
    priority: ['high', 'urgent'],
    sort: 'urgency:desc',
    limit: 20
});

response.data.forEach((task: Task) => {
    console.log(`- ${task.title} (Urgency: ${task.urgency})`);
});
```

## SDK Features

### ✅ Modern JavaScript
- Promise-based API with async/await support
- ES6+ modules with tree-shaking support
- TypeScript definitions included
- Browser and Node.js compatible

### ✅ Comprehensive API Coverage
- Tasks API v2 with advanced filtering
- Events API v2 with calendar optimization
- Search API with faceting
- Export API with streaming support
- WebSocket API for real-time updates
- Analytics and Webhooks

### ✅ Developer Experience
- Intuitive Promise-based API
- Comprehensive TypeScript support
- Rich error handling with custom error types
- Automatic retry with exponential backoff
- Built-in request/response interceptors

### ✅ Production Ready
- Rate limiting with automatic retry
- Connection pooling and keep-alive
- Request timeout configuration
- Comprehensive logging
- Error recovery mechanisms

## Basic Usage

### Client Configuration

```javascript
import { TaskMasterClient } from '@taskmaster/api';

// Basic configuration
const client = new TaskMasterClient({
    apiKey: 'tk_live_abc123...'
});

// Advanced configuration
const client = new TaskMasterClient({
    apiKey: 'tk_live_abc123...',
    baseURL: 'https://api.taskmaster.dev',
    timeout: 30000,
    retries: 3,
    retryDelay: 1000,
    debug: true
});

// Environment-based configuration
const client = new TaskMasterClient({
    apiKey: process.env.TASKMASTER_API_KEY,
    baseURL: process.env.TASKMASTER_BASE_URL || 'https://api.taskmaster.dev'
});
```

### Authentication

```javascript
// API Key authentication (recommended)
const client = new TaskMasterClient({
    apiKey: 'tk_live_abc123...'
});

// Session token authentication
const client = new TaskMasterClient({
    sessionToken: 'sess_xyz789...'
});

// Bearer token authentication
const client = new TaskMasterClient({
    bearerToken: 'jwt_token_here...'
});
```

### Tasks Management

```javascript
// Create a task
const task = await client.tasks.create({
    title: 'Implement user authentication',
    description: 'Add login, registration, and password reset',
    priority: 'urgent',
    urgency: 9,
    duration: 240,
    dueDate: '2025-09-22',
    projectId: 'proj-123',
    requiredContext: ['computer', 'internet'],
    equipmentNeeded: ['laptop']
});

// Get task by ID
const task = await client.tasks.get(taskId);

// Update task
const updatedTask = await client.tasks.update(taskId, {
    status: 'in_progress',
    urgency: 10,
    description: 'Added OAuth integration requirements'
});

// List tasks with advanced filtering
const response = await client.tasks.list({
    status: 'active',
    priority: ['high', 'urgent'],
    dueDateFrom: '2025-09-20',
    dueDateTo: '2025-09-30',
    urgencyMin: 7,
    sort: 'urgency:desc,created_at:asc',
    limit: 50,
    offset: 0
});

// Search tasks
const searchResults = await client.search.search({
    query: 'authentication security',
    types: ['tasks'],
    limit: 10
});

// Complete task
const completedTask = await client.tasks.complete(taskId);

// Delete task
await client.tasks.delete(taskId);
```

### Batch Operations

```javascript
// Create multiple tasks
const tasksData = [
    {
        title: 'Setup CI/CD pipeline',
        priority: 'high',
        duration: 180
    },
    {
        title: 'Write unit tests',
        priority: 'medium',
        duration: 240
    },
    {
        title: 'Update documentation',
        priority: 'low',
        duration: 60
    }
];

const batchResult = await client.tasks.createBatch(tasksData);
console.log(`Created ${batchResult.created.length} tasks`);
if (batchResult.errors.length > 0) {
    console.log('Errors:', batchResult.errors);
}
```

### Events Management

```javascript
// Create an event
const startTime = new Date();
startTime.setDate(startTime.getDate() + 1); // Tomorrow
const endTime = new Date(startTime.getTime() + (2 * 60 * 60 * 1000)); // +2 hours

const event = await client.events.create({
    title: 'Team Planning Meeting',
    description: 'Weekly team planning and status update',
    start: startTime.toISOString(),
    end: endTime.toISOString(),
    location: 'Conference Room A',
    eventType: 'timed',
    isBlocking: true,
    notificationsEnabled: true
});

// Get calendar events for a date range
const events = await client.events.getCalendar({
    start: '2025-09-20',
    end: '2025-09-27'
});

// List events with filtering
const eventsList = await client.events.list({
    eventType: ['timed', 'all_day'],
    isBlocking: true,
    startFrom: '2025-09-20T00:00:00Z',
    startTo: '2025-09-27T23:59:59Z'
});
```

### Search Integration

```javascript
// Comprehensive search
const results = await client.search.search({
    query: 'project management urgent',
    types: ['tasks', 'events', 'projects'],
    includeFacets: true,
    limit: 20
});

console.log(`Found ${results.totalCount} results`);
results.results.forEach(result => {
    console.log(`- ${result.title} (${result.type})`);
});

// Search suggestions
const suggestions = await client.search.getSuggestions('proj', { limit: 5 });
console.log('Suggestions:', suggestions);

// Analyze query
const analysis = await client.search.analyzeQuery('status:active priority:high urgent');
console.log('Query analysis:', analysis);
```

## WebSocket Integration

### Basic WebSocket Usage

```javascript
import { TaskMasterWebSocket } from '@taskmaster/api';

// Initialize WebSocket client
const ws = new TaskMasterWebSocket({
    url: 'wss://api.taskmaster.dev/ws',
    apiKey: 'tk_live_abc123...'
});

// Event handlers
ws.on('connected', () => {
    console.log('Connected to TaskMaster WebSocket');
    ws.subscribe(['tasks', 'notifications']);
});

ws.on('disconnected', () => {
    console.log('WebSocket disconnected');
});

ws.on('task_created', (data) => {
    console.log('New task created:', data.task.title);
});

ws.on('task_completed', (data) => {
    console.log('Task completed:', data.task.title);
});

ws.on('notification', (data) => {
    console.log('Notification:', data.message);
});

// Connect
ws.connect();
```

### Advanced WebSocket Features

```javascript
import { TaskMasterWebSocket } from '@taskmaster/api';

class TaskMasterRealtimeSync {
    constructor(apiKey) {
        this.ws = new TaskMasterWebSocket({
            url: 'wss://api.taskmaster.dev/ws',
            apiKey,
            reconnect: true,
            maxReconnectAttempts: 5,
            reconnectDelay: 1000
        });
        
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Connection events
        this.ws.on('connected', () => {
            console.log('✅ Connected to TaskMaster');
            this.onConnected();
        });
        
        this.ws.on('disconnected', (event) => {
            console.log('❌ Disconnected from TaskMaster');
            this.onDisconnected(event);
        });
        
        this.ws.on('error', (error) => {
            console.error('WebSocket error:', error);
            this.onError(error);
        });
        
        // Task events
        this.ws.on('task_created', (data) => this.onTaskCreated(data));
        this.ws.on('task_updated', (data) => this.onTaskUpdated(data));
        this.ws.on('task_completed', (data) => this.onTaskCompleted(data));
        
        // Event events
        this.ws.on('event_created', (data) => this.onEventCreated(data));
        this.ws.on('event_updated', (data) => this.onEventUpdated(data));
        
        // System events
        this.ws.on('notification', (data) => this.onNotification(data));
        this.ws.on('ai_analysis_complete', (data) => this.onAIAnalysis(data));
    }
    
    onConnected() {
        // Subscribe to relevant channels
        this.ws.subscribe(['tasks', 'events', 'notifications']);
        
        // Notify application of connection
        this.emit('realtime_connected');
    }
    
    onTaskCreated(data) {
        // Handle new task creation
        this.emit('task_created', data.task);
    }
    
    onTaskUpdated(data) {
        // Handle task updates
        this.emit('task_updated', data.task, data.changes);
    }
    
    onTaskCompleted(data) {
        // Handle task completion
        this.emit('task_completed', data.task);
    }
    
    // Event emitter functionality
    on(event, handler) {
        if (!this.handlers) this.handlers = {};
        if (!this.handlers[event]) this.handlers[event] = [];
        this.handlers[event].push(handler);
    }
    
    emit(event, ...args) {
        if (this.handlers && this.handlers[event]) {
            this.handlers[event].forEach(handler => handler(...args));
        }
    }
    
    connect() {
        return this.ws.connect();
    }
    
    disconnect() {
        return this.ws.disconnect();
    }
}

// Usage
const sync = new TaskMasterRealtimeSync('tk_live_abc123...');

sync.on('task_created', (task) => {
    // Update UI with new task
    addTaskToUI(task);
});

sync.on('task_completed', (task) => {
    // Update UI to show completion
    markTaskCompleteInUI(task.id);
});

sync.connect();
```

## Error Handling

```javascript
import {
    TaskMasterClient,
    TaskMasterError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError
} from '@taskmaster/api';

const client = new TaskMasterClient({ apiKey: 'tk_live_abc123...' });

try {
    const task = await client.tasks.create({
        title: 'Test task',
        priority: 'invalid_priority'  // This will cause validation error
    });
} catch (error) {
    if (error instanceof ValidationError) {
        console.log('Validation error:', error.message);
        console.log('Field errors:', error.errors);
    } else if (error instanceof AuthenticationError) {
        console.log('Authentication failed:', error.message);
    } else if (error instanceof RateLimitError) {
        console.log(`Rate limited. Retry after ${error.retryAfter} seconds`);
    } else if (error instanceof NotFoundError) {
        console.log('Resource not found:', error.message);
    } else if (error instanceof TaskMasterError) {
        console.log('API error:', error.message);
    } else {
        console.log('Unexpected error:', error);
    }
}
```

### Retry Configuration

```javascript
const client = new TaskMasterClient({
    apiKey: 'tk_live_abc123...',
    retries: 3,
    retryDelay: 1000,
    retryCondition: (error) => {
        // Retry on network errors and 5xx responses
        return !error.response || error.response.status >= 500;
    },
    retryDelayFunction: (retryCount) => {
        // Exponential backoff with jitter
        return Math.min(1000 * Math.pow(2, retryCount) + Math.random() * 1000, 30000);
    }
});
```

## Framework Integrations

### React Integration

```jsx
// hooks/useTaskMaster.js
import { useState, useEffect, useCallback } from 'react';
import { TaskMasterClient, TaskMasterWebSocket } from '@taskmaster/api';

export function useTaskMaster(apiKey) {
    const [client] = useState(() => new TaskMasterClient({ apiKey }));
    const [ws, setWs] = useState(null);
    const [connected, setConnected] = useState(false);
    const [tasks, setTasks] = useState([]);
    
    useEffect(() => {
        // Initialize WebSocket
        const websocket = new TaskMasterWebSocket({
            url: 'wss://api.taskmaster.dev/ws',
            apiKey
        });
        
        websocket.on('connected', () => {
            setConnected(true);
            websocket.subscribe(['tasks', 'notifications']);
        });
        
        websocket.on('disconnected', () => {
            setConnected(false);
        });
        
        websocket.on('task_created', (data) => {
            setTasks(prev => [...prev, data.task]);
        });
        
        websocket.on('task_updated', (data) => {
            setTasks(prev => prev.map(task => 
                task.id === data.task.id ? { ...task, ...data.task } : task
            ));
        });
        
        websocket.on('task_completed', (data) => {
            setTasks(prev => prev.map(task => 
                task.id === data.task.id ? { ...task, status: 'completed' } : task
            ));
        });
        
        websocket.connect();
        setWs(websocket);
        
        return () => {
            websocket.disconnect();
        };
    }, [apiKey]);
    
    const createTask = useCallback(async (taskData) => {
        try {
            const task = await client.tasks.create(taskData);
            return task;
        } catch (error) {
            console.error('Failed to create task:', error);
            throw error;
        }
    }, [client]);
    
    const loadTasks = useCallback(async (filters = {}) => {
        try {
            const response = await client.tasks.list(filters);
            setTasks(response.data);
            return response;
        } catch (error) {
            console.error('Failed to load tasks:', error);
            throw error;
        }
    }, [client]);
    
    return {
        client,
        ws,
        connected,
        tasks,
        createTask,
        loadTasks
    };
}

// components/TaskDashboard.jsx
import React, { useEffect, useState } from 'react';
import { useTaskMaster } from '../hooks/useTaskMaster';

export function TaskDashboard({ apiKey }) {
    const { client, connected, tasks, createTask, loadTasks } = useTaskMaster(apiKey);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        loadTasks({ status: 'active', limit: 50 })
            .finally(() => setLoading(false));
    }, [loadTasks]);
    
    const handleCreateTask = async (title) => {
        try {
            await createTask({
                title,
                priority: 'medium',
                urgency: 5
            });
        } catch (error) {
            alert('Failed to create task: ' + error.message);
        }
    };
    
    if (loading) {
        return <div>Loading tasks...</div>;
    }
    
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
                        <span className={`priority ${task.priority}`}>{task.priority}</span>
                    </div>
                ))}
            </div>
            
            <button onClick={() => handleCreateTask('New Task')}>
                Create Task
            </button>
        </div>
    );
}
```

### Vue.js Integration

```vue
<!-- TaskDashboard.vue -->
<template>
  <div>
    <div :class="['status', { connected: isConnected }]">
      {{ isConnected ? 'Connected' : 'Disconnected' }}
    </div>
    
    <div class="tasks">
      <div v-for="task in tasks" :key="task.id" class="task">
        <h3>{{ task.title }}</h3>
        <span :class="['status', task.status]">{{ task.status }}</span>
        <span :class="['priority', task.priority]">{{ task.priority }}</span>
      </div>
    </div>
    
    <button @click="createNewTask">Create Task</button>
  </div>
</template>

<script>
import { TaskMasterClient, TaskMasterWebSocket } from '@taskmaster/api';

export default {
  name: 'TaskDashboard',
  props: ['apiKey'],
  data() {
    return {
      client: null,
      ws: null,
      isConnected: false,
      tasks: []
    };
  },
  async mounted() {
    this.setupTaskMaster();
    await this.loadTasks();
  },
  beforeDestroy() {
    if (this.ws) {
      this.ws.disconnect();
    }
  },
  methods: {
    setupTaskMaster() {
      // Initialize client
      this.client = new TaskMasterClient({ apiKey: this.apiKey });
      
      // Initialize WebSocket
      this.ws = new TaskMasterWebSocket({
        url: 'wss://api.taskmaster.dev/ws',
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
      
      this.ws.connect();
    },
    
    async loadTasks() {
      try {
        const response = await this.client.tasks.list({
          status: 'active',
          limit: 50
        });
        this.tasks = response.data;
      } catch (error) {
        console.error('Failed to load tasks:', error);
      }
    },
    
    async createNewTask() {
      try {
        await this.client.tasks.create({
          title: 'New Task from Vue',
          priority: 'medium',
          urgency: 5
        });
      } catch (error) {
        alert('Failed to create task: ' + error.message);
      }
    }
  }
};
</script>
```

### Express.js Integration

```javascript
// app.js
const express = require('express');
const { TaskMasterClient } = require('@taskmaster/api');

const app = express();
app.use(express.json());

// Initialize TaskMaster client
const client = new TaskMasterClient({
    apiKey: process.env.TASKMASTER_API_KEY
});

// Middleware for error handling
const handleTaskMasterError = (error, req, res, next) => {
    if (error.name === 'ValidationError') {
        return res.status(422).json({
            error: error.message,
            errors: error.errors
        });
    } else if (error.name === 'NotFoundError') {
        return res.status(404).json({
            error: error.message
        });
    } else if (error.name === 'AuthenticationError') {
        return res.status(401).json({
            error: error.message
        });
    }
    
    console.error('TaskMaster API error:', error);
    res.status(500).json({
        error: 'Internal server error'
    });
};

// Routes
app.get('/api/tasks', async (req, res, next) => {
    try {
        const { status, priority, limit = 20, offset = 0 } = req.query;
        
        const response = await client.tasks.list({
            status,
            priority: priority ? priority.split(',') : undefined,
            limit: parseInt(limit),
            offset: parseInt(offset)
        });
        
        res.json({
            tasks: response.data,
            meta: response.meta
        });
    } catch (error) {
        next(error);
    }
});

app.post('/api/tasks', async (req, res, next) => {
    try {
        const task = await client.tasks.create(req.body);
        res.status(201).json(task);
    } catch (error) {
        next(error);
    }
});

app.get('/api/tasks/:id', async (req, res, next) => {
    try {
        const task = await client.tasks.get(req.params.id);
        res.json(task);
    } catch (error) {
        next(error);
    }
});

app.put('/api/tasks/:id', async (req, res, next) => {
    try {
        const task = await client.tasks.update(req.params.id, req.body);
        res.json(task);
    } catch (error) {
        next(error);
    }
});

app.delete('/api/tasks/:id', async (req, res, next) => {
    try {
        await client.tasks.delete(req.params.id);
        res.status(204).send();
    } catch (error) {
        next(error);
    }
});

// Error handling middleware
app.use(handleTaskMasterError);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

## Advanced Features

### Pagination Helpers

```javascript
// Auto-pagination utility
async function getAllTasks(client, filters = {}) {
    const allTasks = [];
    let offset = 0;
    const limit = 100;
    
    while (true) {
        const response = await client.tasks.list({
            ...filters,
            limit,
            offset
        });
        
        allTasks.push(...response.data);
        
        if (!response.meta.hasMore) {
            break;
        }
        
        offset += limit;
    }
    
    return allTasks;
}

// Generator for memory-efficient iteration
async function* iterateAllTasks(client, filters = {}) {
    let offset = 0;
    const limit = 50;
    
    while (true) {
        const response = await client.tasks.list({
            ...filters,
            limit,
            offset
        });
        
        for (const task of response.data) {
            yield task;
        }
        
        if (!response.meta.hasMore) {
            break;
        }
        
        offset += limit;
    }
}

// Usage
const allTasks = await getAllTasks(client, { status: 'active' });

// Or for memory efficiency
for await (const task of iterateAllTasks(client, { status: 'active' })) {
    console.log(`Processing task: ${task.title}`);
}
```

### Request Interceptors

```javascript
import { TaskMasterClient } from '@taskmaster/api';

const client = new TaskMasterClient({
    apiKey: 'tk_live_abc123...'
});

// Request interceptor
client.interceptors.request.use(
    (config) => {
        // Add custom headers
        config.headers['X-Client-Version'] = '1.0.0';
        config.headers['X-Request-ID'] = generateRequestId();
        
        // Log requests in debug mode
        if (process.env.NODE_ENV === 'development') {
            console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
        }
        
        return config;
    },
    (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor
client.interceptors.response.use(
    (response) => {
        // Log responses in debug mode
        if (process.env.NODE_ENV === 'development') {
            console.log(`API Response: ${response.status} ${response.config.url}`);
        }
        
        return response;
    },
    (error) => {
        // Global error handling
        if (error.response?.status === 401) {
            // Handle authentication errors
            console.error('Authentication failed. Redirecting to login...');
            // Redirect to login or refresh token
        } else if (error.response?.status === 429) {
            // Handle rate limiting
            console.warn('Rate limited. Consider implementing backoff.');
        }
        
        return Promise.reject(error);
    }
);
```

### Testing

```javascript
// __tests__/taskmaster.test.js
import { TaskMasterClient } from '@taskmaster/api';
import nock from 'nock';

describe('TaskMaster Client', () => {
    let client;
    
    beforeEach(() => {
        client = new TaskMasterClient({
            apiKey: 'tk_test_123',
            baseURL: 'https://test-api.taskmaster.dev'
        });
    });
    
    afterEach(() => {
        nock.cleanAll();
    });
    
    describe('Tasks', () => {
        test('should create a task', async () => {
            const taskData = {
                title: 'Test Task',
                priority: 'high'
            };
            
            const expectedResponse = {
                status: 'success',
                data: {
                    id: 'task-123',
                    ...taskData,
                    createdAt: '2025-09-19T10:00:00Z'
                }
            };
            
            nock('https://test-api.taskmaster.dev')
                .post('/v2/tasks')
                .reply(201, expectedResponse);
            
            const task = await client.tasks.create(taskData);
            
            expect(task.id).toBe('task-123');
            expect(task.title).toBe('Test Task');
            expect(task.priority).toBe('high');
        });
        
        test('should handle validation errors', async () => {
            const invalidTaskData = {
                // Missing required title
                priority: 'invalid_priority'
            };
            
            nock('https://test-api.taskmaster.dev')
                .post('/v2/tasks')
                .reply(422, {
                    status: 'error',
                    message: 'Validation failed',
                    errors: {
                        title: 'Title is required',
                        priority: 'Invalid priority value'
                    }
                });
            
            await expect(client.tasks.create(invalidTaskData))
                .rejects
                .toThrow('Validation failed');
        });
        
        test('should list tasks with filtering', async () => {
            const expectedResponse = {
                status: 'success',
                data: [
                    { id: 'task-1', title: 'Task 1', status: 'active' },
                    { id: 'task-2', title: 'Task 2', status: 'active' }
                ],
                meta: {
                    total: 2,
                    limit: 20,
                    offset: 0,
                    hasMore: false
                }
            };
            
            nock('https://test-api.taskmaster.dev')
                .get('/v2/tasks')
                .query({ status: 'active', priority: 'high' })
                .reply(200, expectedResponse);
            
            const response = await client.tasks.list({
                status: 'active',
                priority: 'high'
            });
            
            expect(response.data).toHaveLength(2);
            expect(response.meta.total).toBe(2);
        });
    });
    
    describe('WebSocket', () => {
        test('should connect and receive events', (done) => {
            const { TaskMasterWebSocket } = require('@taskmaster/api');
            
            // Mock WebSocket for testing
            global.WebSocket = jest.fn().mockImplementation(() => ({
                addEventListener: jest.fn(),
                send: jest.fn(),
                close: jest.fn(),
                readyState: 1
            }));
            
            const ws = new TaskMasterWebSocket({
                url: 'wss://test-api.taskmaster.dev/ws',
                apiKey: 'tk_test_123'
            });
            
            ws.on('connected', () => {
                expect(true).toBe(true);
                done();
            });
            
            ws.connect();
            
            // Simulate connection
            ws.emit('connected');
        });
    });
});
```

## TypeScript Support

### Type Definitions

```typescript
// types.ts
export interface Task {
    id: string;
    title: string;
    description?: string;
    priority: 'low' | 'medium' | 'high' | 'urgent';
    urgency: number;
    status: 'active' | 'blocked' | 'completed' | 'snoozed';
    duration?: number;
    dueDate?: string;
    completed: boolean;
    createdAt: string;
    updatedAt: string;
    projectId?: string;
    initiativeId?: string;
    parentTaskId?: string;
}

export interface CreateTaskData {
    title: string;
    description?: string;
    priority?: Task['priority'];
    urgency?: number;
    duration?: number;
    dueDate?: string;
    projectId?: string;
    initiativeId?: string;
    parentTaskId?: string;
    requiredContext?: string[];
    equipmentNeeded?: string[];
}

export interface TaskListResponse {
    data: Task[];
    meta: {
        total: number;
        limit: number;
        offset: number;
        hasMore: boolean;
        page: number;
        totalPages: number;
    };
}

export interface TaskFilters {
    status?: Task['status'] | Task['status'][];
    priority?: Task['priority'] | Task['priority'][];
    isCompleted?: boolean;
    isSnoozed?: boolean;
    dueDateFrom?: string;
    dueDateTo?: string;
    createdFrom?: string;
    createdTo?: string;
    urgencyMin?: number;
    urgencyMax?: number;
    projectId?: string;
    initiativeId?: string;
    parentTaskId?: string;
    limit?: number;
    offset?: number;
    sort?: string;
    fields?: string[];
    q?: string;
}
```

### Typed Client Usage

```typescript
import { 
    TaskMasterClient, 
    Task, 
    CreateTaskData, 
    TaskFilters,
    TaskListResponse 
} from '@taskmaster/api';

class TaskService {
    private client: TaskMasterClient;
    
    constructor(apiKey: string) {
        this.client = new TaskMasterClient({ apiKey });
    }
    
    async createTask(data: CreateTaskData): Promise<Task> {
        return await this.client.tasks.create(data);
    }
    
    async getTasks(filters: TaskFilters = {}): Promise<TaskListResponse> {
        return await this.client.tasks.list(filters);
    }
    
    async getHighPriorityTasks(): Promise<Task[]> {
        const response = await this.client.tasks.list({
            priority: ['high', 'urgent'],
            status: 'active',
            sort: 'urgency:desc'
        });
        
        return response.data;
    }
    
    async markTaskComplete(taskId: string): Promise<Task> {
        return await this.client.tasks.update(taskId, {
            status: 'completed'
        });
    }
}

// Usage with full type safety
const taskService = new TaskService('tk_live_abc123...');

const newTask = await taskService.createTask({
    title: 'TypeScript integration',
    priority: 'high',
    urgency: 8
});

console.log(`Created task: ${newTask.title} with ID: ${newTask.id}`);
```

This comprehensive JavaScript/TypeScript SDK provides everything needed for modern web application integration with the TaskMaster API, including real-time features, type safety, and production-ready error handling.