# TaskMaster API Developer Guide

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Versions](#api-versions)
4. [Rate Limiting](#rate-limiting)
5. [Response Format](#response-format)
6. [Error Handling](#error-handling)
7. [Pagination](#pagination)
8. [Filtering and Sorting](#filtering-and-sorting)
9. [Search API](#search-api)
10. [Real-time Features](#real-time-features)
11. [Webhooks](#webhooks)
12. [Export API](#export-api)
13. [Analytics](#analytics)
14. [Best Practices](#best-practices)
15. [Code Examples](#code-examples)
16. [Troubleshooting](#troubleshooting)

## Overview

The TaskMaster API is a comprehensive REST API with real-time capabilities for managing tasks, events, schedules, and projects. It provides both traditional REST endpoints and modern features like WebSocket integration, advanced search, and AI-powered insights.

### Base URLs

- **Development**: `http://localhost:5000/api`
- **Production**: `https://api.taskmaster.dev`
- **Staging**: `https://staging-api.taskmaster.dev`

### API Features

- **Enhanced REST API v2**: Pagination, filtering, sorting, batch operations
- **Real-time WebSocket**: Live updates and collaborative features
- **Advanced Search**: Full-text search with faceting and suggestions
- **Data Export**: Multiple formats (CSV, JSON, PDF) with streaming
- **Webhooks**: Event-driven external integrations
- **Analytics**: Usage tracking and performance monitoring
- **AI Integration**: Task analysis and optimization recommendations

## Authentication

TaskMaster API supports multiple authentication methods to accommodate different use cases.

### API Key Authentication

API keys provide programmatic access with scoped permissions. This is the recommended method for server-to-server integrations.

#### Obtaining an API Key

```bash
# Request an API key (requires admin access)
curl -X POST https://api.taskmaster.dev/auth/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-session-token>" \
  -d '{
    "name": "My Application",
    "scopes": ["tasks.read", "tasks.write", "events.read"],
    "description": "API access for my task management app"
  }'
```

#### Using API Keys

Include your API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: tk_live_abc123..." https://api.taskmaster.dev/v2/tasks
```

#### API Key Scopes

API keys can be scoped to specific permissions:

- `tasks.read`, `tasks.write` - Task operations
- `events.read`, `events.write` - Event operations
- `initiatives.read`, `initiatives.write` - Initiative operations
- `projects.read`, `projects.write` - Project operations
- `search.read` - Search operations
- `export.create` - Data export capabilities
- `webhooks.read`, `webhooks.create`, `webhooks.manage` - Webhook management
- `analytics.read` - Usage analytics access

### Session Authentication

For web applications, use session-based authentication:

```bash
# Login to get session token
curl -X POST https://api.taskmaster.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password"
  }'
```

```bash
# Use session token
curl -H "Authorization: Bearer <session-token>" \
  https://api.taskmaster.dev/v2/tasks
```

### Bearer Token Authentication

For mobile and single-page applications, use JWT tokens:

```bash
curl -H "Authorization: Bearer <jwt-token>" \
  https://api.taskmaster.dev/v2/tasks
```

## API Versions

TaskMaster uses URL-based versioning with two supported versions:

### Version 1 (Legacy)
- Path: `/api/v1/`
- Status: Deprecated (maintained for compatibility)
- Features: Basic CRUD operations

### Version 2 (Current)
- Path: `/api/v2/`
- Status: Current recommended version
- Features: Enhanced functionality with pagination, filtering, sorting, batch operations

**Migration Recommendation**: New integrations should use v2 endpoints. v1 will be maintained for existing integrations but won't receive new features.

## Rate Limiting

API endpoints are rate limited to ensure fair usage and system stability.

### Rate Limits by Endpoint Type

| Endpoint Category | Requests per Hour | Burst Limit |
|-------------------|-------------------|-------------|
| Standard CRUD     | 1000              | 100         |
| Search            | 500               | 50          |
| Analytics         | 100               | 10          |
| Export            | 50                | 5           |
| Webhooks          | 200               | 20          |

### Rate Limit Headers

All responses include rate limiting information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1632150000
X-RateLimit-Burst-Remaining: 99
```

### Handling Rate Limits

When rate limited (429 status), respect the `Retry-After` header:

```python
import time
import requests

def make_api_call(url, headers):
    response = requests.get(url, headers=headers)
    
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return make_api_call(url, headers)
    
    return response
```

## Response Format

All API responses follow a consistent structure for predictable parsing.

### Success Response Format

```json
{
  "status": "success",
  "data": {
    // Response data here
  },
  "message": "Optional success message",
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_more": true,
    "page": 1,
    "total_pages": 5
  }
}
```

### Error Response Format

```json
{
  "status": "error",
  "message": "Human-readable error description",
  "code": "MACHINE_READABLE_ERROR_CODE",
  "errors": {
    "field_name": "Specific field validation error",
    "another_field": "Another validation error"
  },
  "details": "Additional error context"
}
```

### HTTP Status Codes

| Status Code | Meaning | Usage |
|-------------|---------|-------|
| 200 | OK | Successful GET, PUT requests |
| 201 | Created | Successful POST requests |
| 204 | No Content | Successful DELETE requests |
| 207 | Multi-Status | Batch operations with partial success |
| 400 | Bad Request | Invalid request format or parameters |
| 401 | Unauthorized | Authentication required or invalid |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict (duplicate, dependency) |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

## Error Handling

### Common Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| `VALIDATION_ERROR` | Request validation failed | Check field requirements and formats |
| `RESOURCE_NOT_FOUND` | Resource doesn't exist | Verify resource ID and permissions |
| `DUPLICATE_RESOURCE` | Resource already exists | Use PUT for updates or check uniqueness |
| `DEPENDENCY_ERROR` | Resource has dependencies | Remove dependencies first |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry with exponential backoff |
| `INSUFFICIENT_PERMISSIONS` | Missing required permissions | Check API key scopes |
| `INVALID_AUTHENTICATION` | Authentication failed | Verify credentials and token expiry |

### Error Handling Best Practices

```python
import requests
import time
from typing import Dict, Any

def handle_api_response(response: requests.Response) -> Dict[Any, Any]:
    """Handle API response with proper error handling"""
    
    if response.status_code == 200:
        return response.json()
    
    elif response.status_code == 401:
        raise Exception("Authentication failed. Check your API key or session token.")
    
    elif response.status_code == 403:
        raise Exception("Insufficient permissions. Check your API key scopes.")
    
    elif response.status_code == 404:
        raise Exception("Resource not found. Verify the resource ID.")
    
    elif response.status_code == 422:
        error_data = response.json()
        field_errors = error_data.get('errors', {})
        raise ValueError(f"Validation error: {field_errors}")
    
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        raise Exception(f"Rate limited. Retry after {retry_after} seconds.")
    
    elif response.status_code >= 500:
        raise Exception("Server error. Please try again later.")
    
    else:
        error_data = response.json()
        raise Exception(f"API error: {error_data.get('message', 'Unknown error')}")
```

## Pagination

v2 endpoints support consistent pagination with metadata.

### Pagination Parameters

- `limit`: Number of items per page (default: 20, max: 500)
- `offset`: Number of items to skip (default: 0)

### Pagination Response

```json
{
  "status": "success",
  "data": [
    // Array of items
  ],
  "meta": {
    "total": 150,
    "limit": 20,
    "offset": 40,
    "has_more": true,
    "page": 3,
    "total_pages": 8
  }
}
```

### Pagination Examples

```bash
# Get first page (20 items)
curl "https://api.taskmaster.dev/v2/tasks?limit=20&offset=0"

# Get second page
curl "https://api.taskmaster.dev/v2/tasks?limit=20&offset=20"

# Get specific page with larger page size
curl "https://api.taskmaster.dev/v2/tasks?limit=50&offset=100"
```

### Cursor-based Pagination

For real-time data or large datasets, use cursor-based pagination:

```bash
# First request
curl "https://api.taskmaster.dev/v2/tasks?limit=20"

# Subsequent requests using cursor from previous response
curl "https://api.taskmaster.dev/v2/tasks?limit=20&cursor=eyJpZCI6IjEyMyJ9"
```

## Filtering and Sorting

v2 endpoints provide comprehensive filtering and sorting capabilities.

### Common Filters

All endpoints support these common filters:
- `created_from`, `created_to`: Filter by creation date range
- `updated_from`, `updated_to`: Filter by update date range
- `q`: Full-text search query

### Task-Specific Filters

```bash
# Filter by status
curl "https://api.taskmaster.dev/v2/tasks?status=active,blocked"

# Filter by priority
curl "https://api.taskmaster.dev/v2/tasks?priority=high,urgent"

# Filter by due date range
curl "https://api.taskmaster.dev/v2/tasks?due_date_from=2025-09-20&due_date_to=2025-09-30"

# Filter by duration range
curl "https://api.taskmaster.dev/v2/tasks?duration_min=30&duration_max=120"

# Filter by urgency range
curl "https://api.taskmaster.dev/v2/tasks?urgency_min=7&urgency_max=10"

# Filter by project or initiative
curl "https://api.taskmaster.dev/v2/tasks?project_id=123e4567-e89b-12d3-a456-426614174000"

# Complex filtering
curl "https://api.taskmaster.dev/v2/tasks?status=active&priority=high,urgent&due_date_from=2025-09-20&urgency_min=5"
```

### Event-Specific Filters

```bash
# Filter by event type
curl "https://api.taskmaster.dev/v2/events?event_type=timed,all_day"

# Filter by date range
curl "https://api.taskmaster.dev/v2/events?start_from=2025-09-20T00:00:00Z&start_to=2025-09-27T23:59:59Z"

# Filter by blocking status
curl "https://api.taskmaster.dev/v2/events?is_blocking=true"

# Filter recurring events
curl "https://api.taskmaster.dev/v2/events?is_recurring=true"
```

### Sorting

Sort by one or multiple fields with direction control:

```bash
# Single field sorting
curl "https://api.taskmaster.dev/v2/tasks?sort=priority:desc"

# Multi-field sorting
curl "https://api.taskmaster.dev/v2/tasks?sort=priority:desc,created_at:asc"

# Available sort fields for tasks
curl "https://api.taskmaster.dev/v2/tasks?sort=title:asc"          # Alphabetical
curl "https://api.taskmaster.dev/v2/tasks?sort=urgency:desc"      # By urgency
curl "https://api.taskmaster.dev/v2/tasks?sort=due_date:asc"      # By due date
curl "https://api.taskmaster.dev/v2/tasks?sort=duration:desc"     # By duration
```

### Field Selection

Reduce response payload by selecting specific fields:

```bash
# Select specific fields
curl "https://api.taskmaster.dev/v2/tasks?fields=id,title,status,priority"

# Minimal response for performance
curl "https://api.taskmaster.dev/v2/tasks?fields=id,title&limit=100"
```

## Search API

The Search API provides powerful full-text search with faceting and suggestions.

### Basic Search

```bash
# Search across all entity types
curl "https://api.taskmaster.dev/search/search?q=project%20management"

# Search specific entity types
curl "https://api.taskmaster.dev/search/search?q=urgent&types=tasks,events"

# Search with pagination
curl "https://api.taskmaster.dev/search/search?q=meeting&limit=10&offset=20"
```

### Advanced Query Syntax

The search API supports advanced query syntax for precise results:

```bash
# Field-specific search
curl "https://api.taskmaster.dev/search/search?q=title:documentation"

# Status filtering in search
curl "https://api.taskmaster.dev/search/search?q=status:active%20urgent"

# Project-specific search
curl "https://api.taskmaster.dev/search/search?q=project:TaskMaster%20bug%20fix"

# Phrase search
curl "https://api.taskmaster.dev/search/search?q=\"team%20meeting\""

# Complex queries
curl "https://api.taskmaster.dev/search/search?q=priority:high%20OR%20urgency:urgent%20AND%20status:active"
```

### Search with Facets

Get faceted results to understand data distribution:

```bash
curl "https://api.taskmaster.dev/search/search?q=project&include_facets=true"
```

Response includes facets:
```json
{
  "status": "success",
  "data": {
    "results": [...],
    "facets": {
      "type": [
        {"value": "task", "count": 45, "filter_key": "type:task"},
        {"value": "event", "count": 12, "filter_key": "type:event"}
      ],
      "status": [
        {"value": "active", "count": 32, "filter_key": "status:active"},
        {"value": "completed", "count": 25, "filter_key": "status:completed"}
      ]
    }
  }
}
```

### Search Suggestions

Get auto-complete suggestions for better user experience:

```bash
# Get suggestions for partial query
curl "https://api.taskmaster.dev/search/suggestions?q=proj&limit=5"
```

Response:
```json
{
  "status": "success",
  "data": {
    "suggestions": [
      "project management",
      "project planning", 
      "project review",
      "project documentation",
      "project deployment"
    ],
    "query": "proj"
  }
}
```

### Query Analysis

Analyze search queries to understand how they're processed:

```bash
curl -X POST "https://api.taskmaster.dev/search/query/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "project:work status:active urgent task"}'
```

## Real-time Features

TaskMaster provides real-time updates through WebSocket integration.

### WebSocket Connection

Connect to the WebSocket endpoint for live updates:

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onopen = function(event) {
    console.log('Connected to TaskMaster WebSocket');
    
    // Subscribe to specific channels
    ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['tasks', 'events', 'notifications']
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received update:', data);
    
    switch(data.type) {
        case 'task_created':
            handleNewTask(data.task);
            break;
        case 'task_completed':
            handleTaskCompletion(data.task);
            break;
        case 'event_created':
            handleNewEvent(data.event);
            break;
        case 'notification':
            showNotification(data.message);
            break;
    }
};
```

### WebSocket Event Types

| Event Type | Description | Data Structure |
|------------|-------------|----------------|
| `task_created` | New task created | `{type, task, user_id, timestamp}` |
| `task_updated` | Task modified | `{type, task, changes, user_id, timestamp}` |
| `task_completed` | Task marked complete | `{type, task, user_id, timestamp}` |
| `task_priority_changed` | Task priority updated | `{type, task, old_priority, new_priority, user_id}` |
| `event_created` | New event created | `{type, event, user_id, timestamp}` |
| `event_updated` | Event modified | `{type, event, changes, user_id, timestamp}` |
| `schedule_regenerated` | Schedule recalculated | `{type, affected_tasks, affected_pools, reason}` |
| `notification` | System notification | `{type, message, level, target_user_id}` |
| `ai_analysis_complete` | AI analysis finished | `{type, analysis_id, results, confidence}` |

### WebSocket Authentication

Authenticate WebSocket connections using query parameters:

```javascript
// Using API key
const ws = new WebSocket('ws://localhost:5000/ws?api_key=tk_live_abc123...');

// Using session token
const ws = new WebSocket('ws://localhost:5000/ws?token=session_xyz...');
```

### Channel Subscription

Subscribe to specific event channels to reduce noise:

```javascript
// Subscribe to task-related events only
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['tasks']
}));

// Subscribe to user-specific notifications
ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['notifications'],
    user_id: 'user-123'
}));

// Unsubscribe from channels
ws.send(JSON.stringify({
    type: 'unsubscribe',
    channels: ['events']
}));
```

## Webhooks

Webhooks provide event-driven integration with external systems.

### Creating Webhooks

```bash
curl -X POST "https://api.taskmaster.dev/webhooks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tk_live_abc123..." \
  -d '{
    "name": "Task Notifications",
    "url": "https://your-app.com/webhooks/taskmaster",
    "events": ["task.created", "task.completed", "event.created"],
    "secret": "your-webhook-secret-key",
    "headers": {
      "Authorization": "Bearer your-app-token"
    }
  }'
```

### Webhook Events

Available webhook events:

| Event | Description | Payload |
|-------|-------------|---------|
| `task.created` | New task created | Full task object |
| `task.updated` | Task modified | Task object with changes |
| `task.completed` | Task marked complete | Task object |
| `task.deleted` | Task deleted | Task ID and metadata |
| `event.created` | New event created | Full event object |
| `event.updated` | Event modified | Event object with changes |
| `event.deleted` | Event deleted | Event ID and metadata |
| `project.created` | New project created | Full project object |
| `initiative.created` | New initiative created | Full initiative object |

### Webhook Payload Format

```json
{
  "id": "wh_evt_123456789",
  "type": "task.created",
  "timestamp": "2025-09-19T10:00:00Z",
  "data": {
    "task": {
      "id": "task-123",
      "title": "New task",
      "status": "active",
      // ... full task object
    }
  },
  "metadata": {
    "webhook_id": "wh_123",
    "attempt": 1,
    "user_id": "user-456"
  }
}
```

### Webhook Security

TaskMaster signs webhook payloads using HMAC-SHA256:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

# In your webhook handler
def handle_webhook(request):
    signature = request.headers.get('X-TaskMaster-Signature')
    payload = request.body.decode('utf-8')
    
    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return {"error": "Invalid signature"}, 401
    
    # Process webhook payload
    event_data = json.loads(payload)
    process_webhook_event(event_data)
    
    return {"status": "received"}, 200
```

### Webhook Retry Logic

TaskMaster implements exponential backoff for failed webhook deliveries:

- **Retry Schedule**: 1s, 5s, 25s, 125s, 625s (5 attempts total)
- **Timeout**: 30 seconds per attempt
- **Success Criteria**: HTTP 200-299 response
- **Failure Handling**: Webhook disabled after 5 consecutive failures

## Export API

Export data in multiple formats for analysis and backup.

### Export Formats

- **CSV**: Comma-separated values for spreadsheet analysis
- **JSON**: Structured data for programmatic processing
- **PDF**: Formatted reports for sharing and printing

### Creating Exports

```bash
# Export tasks as CSV
curl -X POST "https://api.taskmaster.dev/export/tasks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tk_live_abc123..." \
  -d '{
    "format": "csv",
    "filters": {
      "status": ["active", "blocked"],
      "priority": ["high", "urgent"],
      "due_date_from": "2025-09-20"
    },
    "fields": ["id", "title", "status", "priority", "due_date", "urgency"],
    "sort": "priority:desc,due_date:asc"
  }'
```

### Export Response

```json
{
  "status": "success",
  "data": {
    "export_id": "exp_123456789",
    "format": "csv",
    "download_url": "https://api.taskmaster.dev/exports/exp_123456789/download",
    "expires_at": "2025-09-26T10:00:00Z",
    "record_count": 150,
    "file_size_bytes": 45000
  }
}
```

### Large Dataset Exports

For large datasets, exports are queued for background processing:

```json
{
  "status": "queued",
  "data": {
    "export_id": "exp_123456789",
    "status_url": "https://api.taskmaster.dev/exports/exp_123456789/status",
    "estimated_completion": "2025-09-19T10:05:00Z"
  }
}
```

Check export status:

```bash
curl "https://api.taskmaster.dev/exports/exp_123456789/status"
```

### Scheduled Exports

Create recurring exports for automated data extraction:

```bash
curl -X POST "https://api.taskmaster.dev/export/schedules" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: tk_live_abc123..." \
  -d '{
    "name": "Weekly Task Report",
    "export_config": {
      "entity": "tasks",
      "format": "csv",
      "filters": {"status": ["completed"]},
      "fields": ["id", "title", "completed_at", "duration"]
    },
    "schedule": "0 9 * * MON",
    "webhook_url": "https://your-app.com/exports/completed"
  }'
```

## Analytics

Monitor API usage and performance with built-in analytics.

### Usage Analytics

```bash
curl "https://api.taskmaster.dev/analytics/usage?timeframe=24h&format=detailed" \
  -H "X-API-Key: tk_live_abc123..."
```

Response:
```json
{
  "status": "success",
  "data": {
    "timeframe": "24h",
    "total_requests": 2450,
    "successful_requests": 2380,
    "error_requests": 70,
    "success_rate": 97.14,
    "avg_response_time_ms": 245.5,
    "top_endpoints": [
      {
        "endpoint": "/v2/tasks",
        "requests": 850,
        "avg_response_time": 180.2
      },
      {
        "endpoint": "/v2/events",
        "requests": 620,
        "avg_response_time": 165.8
      }
    ],
    "error_breakdown": {
      "400": 25,
      "401": 10,
      "404": 20,
      "429": 15
    }
  }
}
```

### Performance Monitoring

Track API performance metrics:

```bash
curl "https://api.taskmaster.dev/analytics/performance?timeframe=7d" \
  -H "X-API-Key: tk_live_abc123..."
```

### Rate Limit Analytics

Monitor rate limiting patterns:

```bash
curl "https://api.taskmaster.dev/analytics/rate-limits?timeframe=24h" \
  -H "X-API-Key: tk_live_abc123..."
```

## Best Practices

### 1. Use Appropriate HTTP Methods

- **GET**: Retrieve data (idempotent)
- **POST**: Create new resources
- **PUT**: Update existing resources (full replacement)
- **PATCH**: Partial updates
- **DELETE**: Remove resources

### 2. Handle Pagination Properly

```python
def get_all_tasks(api_key, filters=None):
    """Get all tasks using pagination"""
    all_tasks = []
    offset = 0
    limit = 100
    
    while True:
        params = {
            'limit': limit,
            'offset': offset,
            **(filters or {})
        }
        
        response = requests.get(
            'https://api.taskmaster.dev/v2/tasks',
            headers={'X-API-Key': api_key},
            params=params
        )
        
        data = response.json()
        tasks = data['data']
        all_tasks.extend(tasks)
        
        if not data['meta']['has_more']:
            break
            
        offset += limit
    
    return all_tasks
```

### 3. Implement Proper Error Handling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_resilient_session():
    """Create session with retry logic"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session
```

### 4. Cache Responses Appropriately

```python
import time
from typing import Dict, Any

class APIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def get_with_cache(self, url: str, params: Dict = None) -> Any:
        """Get data with caching"""
        cache_key = f"{url}:{hash(str(params))}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        response = requests.get(
            url,
            headers={'X-API-Key': self.api_key},
            params=params
        )
        
        data = response.json()
        self.cache[cache_key] = (data, time.time())
        
        return data
```

### 5. Use Field Selection for Performance

```bash
# Only get required fields to reduce payload size
curl "https://api.taskmaster.dev/v2/tasks?fields=id,title,status&limit=100"
```

### 6. Implement Proper WebSocket Reconnection

```javascript
class TaskMasterWebSocket {
    constructor(url, apiKey) {
        this.url = url;
        this.apiKey = apiKey;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.connect();
    }
    
    connect() {
        this.ws = new WebSocket(`${this.url}?api_key=${this.apiKey}`);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.reconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onmessage = (event) => {
            this.handleMessage(JSON.parse(event.data));
        };
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            setTimeout(() => {
                console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
                this.connect();
            }, delay);
        }
    }
}
```

## Code Examples

### Python SDK Usage

```python
import requests
from typing import List, Dict, Optional

class TaskMasterClient:
    def __init__(self, api_key: str, base_url: str = "https://api.taskmaster.dev"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'X-API-Key': api_key})
    
    def create_task(self, title: str, **kwargs) -> Dict:
        """Create a new task"""
        data = {'title': title, **kwargs}
        response = self.session.post(f"{self.base_url}/v2/tasks", json=data)
        response.raise_for_status()
        return response.json()['data']
    
    def get_tasks(self, 
                  status: Optional[List[str]] = None,
                  priority: Optional[List[str]] = None,
                  limit: int = 20,
                  offset: int = 0) -> Dict:
        """Get tasks with filtering"""
        params = {'limit': limit, 'offset': offset}
        
        if status:
            params['status'] = ','.join(status)
        if priority:
            params['priority'] = ','.join(priority)
        
        response = self.session.get(f"{self.base_url}/v2/tasks", params=params)
        response.raise_for_status()
        return response.json()
    
    def search(self, query: str, types: Optional[List[str]] = None) -> Dict:
        """Search across entity types"""
        params = {'q': query}
        if types:
            params['types'] = ','.join(types)
        
        response = self.session.get(f"{self.base_url}/search/search", params=params)
        response.raise_for_status()
        return response.json()

# Usage example
client = TaskMasterClient('tk_live_abc123...')

# Create a task
task = client.create_task(
    title="Review API documentation",
    description="Comprehensive review of all API endpoints",
    priority="high",
    urgency=8,
    duration=120
)

# Get high priority tasks
high_priority_tasks = client.get_tasks(
    priority=['high', 'urgent'],
    status=['active'],
    limit=50
)

# Search for documentation tasks
search_results = client.search("documentation", types=['tasks'])
```

### JavaScript/Node.js Usage

```javascript
const axios = require('axios');

class TaskMasterAPI {
    constructor(apiKey, baseURL = 'https://api.taskmaster.dev') {
        this.client = axios.create({
            baseURL,
            headers: {
                'X-API-Key': apiKey,
                'Content-Type': 'application/json'
            }
        });
        
        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            response => response,
            error => {
                if (error.response?.status === 429) {
                    const retryAfter = error.response.headers['retry-after'];
                    console.warn(`Rate limited. Retry after ${retryAfter} seconds`);
                }
                throw error;
            }
        );
    }
    
    async createTask(taskData) {
        const response = await this.client.post('/v2/tasks', taskData);
        return response.data.data;
    }
    
    async getTasks(filters = {}, pagination = {}) {
        const params = {
            limit: 20,
            offset: 0,
            ...pagination,
            ...filters
        };
        
        const response = await this.client.get('/v2/tasks', { params });
        return response.data;
    }
    
    async searchAll(query, options = {}) {
        const params = {
            q: query,
            ...options
        };
        
        const response = await this.client.get('/search/search', { params });
        return response.data;
    }
    
    async exportTasks(exportConfig) {
        const response = await this.client.post('/export/tasks', exportConfig);
        return response.data.data;
    }
}

// Usage example
const api = new TaskMasterAPI('tk_live_abc123...');

async function example() {
    try {
        // Create a task
        const newTask = await api.createTask({
            title: 'Implement new feature',
            description: 'Add user authentication to the application',
            priority: 'high',
            urgency: 7,
            duration: 180,
            project_id: '123e4567-e89b-12d3-a456-426614174000'
        });
        
        console.log('Created task:', newTask);
        
        // Get active high-priority tasks
        const tasks = await api.getTasks({
            status: 'active',
            priority: 'high,urgent'
        }, {
            limit: 50
        });
        
        console.log(`Found ${tasks.meta.total} high-priority tasks`);
        
        // Search for authentication-related tasks
        const searchResults = await api.searchAll('authentication', {
            types: 'tasks,events',
            limit: 10
        });
        
        console.log('Search results:', searchResults.data.results);
        
    } catch (error) {
        console.error('API Error:', error.response?.data || error.message);
    }
}

example();
```

### cURL Examples

```bash
#!/bin/bash

API_KEY="tk_live_abc123..."
BASE_URL="https://api.taskmaster.dev"

# Create a task
curl -X POST "$BASE_URL/v2/tasks" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy to production",
    "description": "Deploy version 2.4.0 to production environment",
    "priority": "urgent",
    "urgency": 9,
    "duration": 60,
    "required_context": ["deployment", "production"]
  }'

# Get high-priority active tasks
curl "$BASE_URL/v2/tasks?status=active&priority=high,urgent&sort=urgency:desc" \
  -H "X-API-Key: $API_KEY"

# Search for deployment tasks
curl "$BASE_URL/search/search?q=deployment&types=tasks&include_facets=true" \
  -H "X-API-Key: $API_KEY"

# Export completed tasks as CSV
curl -X POST "$BASE_URL/export/tasks" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "filters": {
      "status": ["completed"],
      "completed_from": "2025-09-01"
    },
    "fields": ["id", "title", "priority", "duration", "completed_at"]
  }'

# Get API usage analytics
curl "$BASE_URL/analytics/usage?timeframe=7d&format=detailed" \
  -H "X-API-Key: $API_KEY"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Errors

**Problem**: `401 Unauthorized` responses

**Solutions**:
- Verify API key is correct and active
- Check API key scopes include required permissions
- Ensure API key is included in `X-API-Key` header
- For session auth, verify token hasn't expired

```bash
# Test API key validity
curl -H "X-API-Key: your-key" "https://api.taskmaster.dev/health"
```

#### 2. Rate Limiting

**Problem**: `429 Too Many Requests` responses

**Solutions**:
- Implement exponential backoff with jitter
- Respect `Retry-After` header values
- Consider request batching for bulk operations
- Monitor usage with analytics endpoints

#### 3. Validation Errors

**Problem**: `422 Unprocessable Entity` with field errors

**Solutions**:
- Check required fields are provided
- Verify field formats (dates, UUIDs, enums)
- Review field length limits
- Ensure foreign key references exist

#### 4. Pagination Issues

**Problem**: Inconsistent results across pages

**Solutions**:
- Use consistent sorting to avoid duplicates
- Consider cursor-based pagination for real-time data
- Account for data changes between requests
- Implement proper offset/limit validation

#### 5. Search Not Working

**Problem**: Search returns no results or errors

**Solutions**:
- Check search indexes are built (`/search/health`)
- Verify query syntax is correct
- Ensure entity types exist and have data
- Try simpler queries to isolate issues

#### 6. WebSocket Connection Issues

**Problem**: WebSocket connections failing or dropping

**Solutions**:
- Verify WebSocket URL and authentication
- Implement proper reconnection logic
- Check firewall/proxy WebSocket support
- Monitor connection statistics

### Debug Tools

#### API Health Check

```bash
curl "https://api.taskmaster.dev/health"
```

#### Search System Status

```bash
curl "https://api.taskmaster.dev/search/health"
```

#### WebSocket Statistics

```bash
curl "https://api.taskmaster.dev/websocket/stats"
```

#### Rate Limit Status

Check response headers for current limits:
```bash
curl -I "https://api.taskmaster.dev/v2/tasks" \
  -H "X-API-Key: your-key"
```

### Getting Help

1. **Documentation**: https://docs.taskmaster.dev
2. **API Reference**: Interactive OpenAPI documentation
3. **Support**: api-support@taskmaster.dev
4. **Status Page**: https://status.taskmaster.dev
5. **Community**: https://community.taskmaster.dev

### Performance Optimization

#### 1. Reduce Payload Size

```bash
# Only request needed fields
curl "https://api.taskmaster.dev/v2/tasks?fields=id,title,status"
```

#### 2. Use Appropriate Page Sizes

```bash
# Optimize page size based on use case
curl "https://api.taskmaster.dev/v2/tasks?limit=100"  # For bulk processing
curl "https://api.taskmaster.dev/v2/tasks?limit=10"   # For UI pagination
```

#### 3. Leverage Caching

- Use ETags for conditional requests
- Cache stable data (projects, initiatives)
- Implement client-side caching with TTL

#### 4. Batch Operations

```bash
# Create multiple tasks in one request
curl -X POST "https://api.taskmaster.dev/v2/tasks/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"title": "Task 1", "priority": "high"},
      {"title": "Task 2", "priority": "medium"}
    ]
  }'
```

This completes the comprehensive API Developer Guide covering authentication, all major features, best practices, and troubleshooting. The guide provides practical examples and real-world usage patterns for successful API integration.