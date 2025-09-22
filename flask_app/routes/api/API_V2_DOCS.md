# TaskMaster Enhanced REST API v2 Documentation

## Overview

The v2 API endpoints provide enhanced functionality including pagination, filtering, sorting, field selection, and batch operations. All v2 endpoints are backward compatible with v1 responses.

## Base URL
```
http://localhost:5000/api/v2
```

## Common Features

### Pagination
All list endpoints support pagination using `limit` and `offset` parameters:
- `limit`: Number of items to return (default: 20-50, max: 100-500 depending on endpoint)
- `offset`: Number of items to skip (default: 0)

Example: `/api/v2/tasks?limit=10&offset=20`

### Sorting
Sort results using the `sort` parameter with format `field:direction`:
- Multiple fields: `sort=priority:desc,created_at:asc`
- Default sort varies by endpoint

### Filtering
Each endpoint supports specific filters as query parameters.

### Field Selection
Reduce payload size by selecting specific fields:
- `fields=id,title,status`

### Search
Full-text search across multiple fields:
- `q=search term`

## Tasks API

### GET /api/v2/tasks
Get tasks with advanced querying.

**Query Parameters:**
- Pagination: `limit`, `offset`
- Sorting: `sort` (fields: title, created_at, updated_at, due_date, urgency, priority, duration, status)
- Search: `q` (searches title, description)
- Filters:
  - `status`: exact match (active, blocked, completed, snoozed)
  - `priority`: comma-separated list (low, medium, high, urgent)
  - `is_completed`: boolean (true/false)
  - `is_snoozed`: boolean
  - `due_date_from`, `due_date_to`: date range (ISO format)
  - `created_from`, `created_to`: datetime range
  - `duration_min`, `duration_max`: numeric range
  - `urgency_min`, `urgency_max`: numeric range (1-10)
  - `initiative_id`, `project_id`, `parent_task_id`: exact match
- Special: `root_only=true` (only tasks with no incomplete dependencies)

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "title": "Task Title",
      "description": "Description",
      "duration": 30,
      "urgency": 5,
      "priority": "medium",
      "status": "active",
      "completed": false,
      "due_date": "2025-09-20",
      "created_at": "2025-09-19T10:00:00"
    }
  ],
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

### GET /api/v2/tasks/{task_id}
Get a specific task with optional related data.

**Query Parameters:**
- `include`: comma-separated list (dependencies, subtasks)

### POST /api/v2/tasks
Create a new task.

**Request Body:**
```json
{
  "title": "Task Title (required)",
  "description": "Description",
  "duration": 30,
  "urgency": 5,
  "priority": "medium",
  "due_date": "2025-09-20",
  "start_date": "2025-09-19T10:00:00",
  "required_weather": "sunny",
  "initiative_id": "uuid",
  "project_id": "uuid",
  "parent_task_id": "uuid",
  "recurrence_days": 7
}
```

**Response:** 201 Created with Location header

### POST /api/v2/tasks/batch
Create multiple tasks in one request.

**Request Body:**
```json
{
  "tasks": [
    {"title": "Task 1", "duration": 30},
    {"title": "Task 2", "priority": "high"}
  ]
}
```

**Response:** 201 or 207 Multi-Status
```json
{
  "status": "success",
  "data": {
    "created": [...],
    "errors": [
      {"index": 2, "error": "Title is required"}
    ]
  },
  "message": "Created 2 tasks"
}
```

### PUT /api/v2/tasks/{task_id}
Update a task (partial update supported).

### DELETE /api/v2/tasks/{task_id}
Delete a task.

**Response:** 204 No Content

## Events API

### GET /api/v2/events
Get events with two modes.

**Query Parameters:**
- `mode`: "list" (default) or "calendar"
- Common: `limit`, `offset`, `sort`, `q`
- Filters:
  - `event_type`: comma-separated (timed, all_day, instant)
  - `status`: exact match
  - `is_blocking`, `is_recurring`, `notifications_enabled`: boolean
  - `start_from`, `start_to`, `end_from`, `end_to`: datetime range
  - `project_id`, `meal_id`: exact match
  - `location`: partial match
- List mode: `master_only=true` (default), `include_expansion_info=true`

### GET /api/v2/events/calendar
Get expanded events specifically for calendar display.

**Query Parameters:**
- `start`, `end`: date range (required for expansion)
- `event_type`, `is_blocking`: filters
- `limit`, `offset`: pagination on expanded results

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid",
      "title": "Event Title",
      "start": "2025-09-19T10:00:00",
      "end": "2025-09-19T11:00:00",
      "allDay": false,
      "color": "#007bff",
      "description": "",
      "location": "",
      "is_blocking": true,
      "is_recurring": true,
      "event_type": "timed"
    }
  ],
  "meta": {
    "total": 150,
    "limit": 200,
    "offset": 0,
    "has_more": false
  }
}
```

### GET /api/v2/events/{event_id}
Get a specific event.

**Query Parameters:**
- `include`: comma-separated (meal, recurring_info)

### POST /api/v2/events
Create a new event.

**Request Body:**
```json
{
  "title": "Event Title (required)",
  "start": "2025-09-19T10:00:00Z (required)",
  "end": "2025-09-19T11:00:00Z (required)",
  "description": "Description",
  "location": "Location",
  "event_type": "timed",
  "is_blocking": true,
  "notifications_enabled": true,
  "meal_id": "uuid",
  "project_id": "uuid",
  "is_recurring": false,
  "recurrence_rrule": "FREQ=WEEKLY;BYDAY=MO,WE,FR",
  "recurrence_pattern": "Weekly on Mon, Wed, Fri",
  "recurrence_end": "2025-12-31T23:59:59Z"
}
```

**Response:** 201 Created with Location header

### POST /api/v2/events/batch
Create multiple events.

**Request Body:**
```json
{
  "events": [
    {
      "title": "Event 1",
      "start": "2025-09-19T10:00:00Z",
      "end": "2025-09-19T11:00:00Z"
    }
  ]
}
```

### PUT /api/v2/events/{event_id}
Update an event.

### DELETE /api/v2/events/{event_id}
Delete an event.

**Query Parameters:**
- `delete_series=true` (for recurring events)

**Response:** 204 No Content

## Response Formats

### Success Response
```json
{
  "status": "success",
  "data": {...},
  "message": "Optional success message",
  "meta": {...}
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "errors": {
    "field_name": "Specific error"
  }
}
```

### HTTP Status Codes
- 200: OK
- 201: Created
- 204: No Content
- 207: Multi-Status (batch operations with partial success)
- 400: Bad Request
- 404: Not Found
- 415: Unsupported Media Type
- 422: Unprocessable Entity (validation errors)
- 500: Internal Server Error

## Rate Limiting

Currently no rate limiting is implemented, but the API is designed to support it in the future.

## Versioning

API version is specified in the URL path (/api/v2/). The v2 API maintains backward compatibility with v1 response structures while adding new features.

## Cache Headers

Responses include appropriate cache headers:
- `ETag`: For conditional requests
- `Cache-Control`: Caching directives
- `Last-Modified`: Resource modification time

Conditional requests supported:
- `If-None-Match`: With ETag
- `If-Modified-Since`: With Last-Modified

## Future Enhancements

Planned for future releases:
- WebSocket support for real-time updates
- GraphQL endpoint
- Webhook notifications
- API key authentication
- Rate limiting
- Response compression (gzip)