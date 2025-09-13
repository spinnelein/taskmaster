# TaskMaster API Documentation

Complete API reference for the TaskMaster application. All endpoints follow RESTful conventions with `/api/` prefix.

**Base URL**: `http://localhost:8000`  
**API Prefix**: `/api/`  
**Interactive Documentation**: `/docs` (Swagger UI)

**Last Updated**: September 13, 2025  
**Version**: 1.0.0

## Authentication

Currently, no authentication is required. All endpoints are open for development.

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "data": [...],
  "total": 10,
  "message": "Success"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Core Endpoints

### Tasks API (`/api/tasks`)

Manage tasks with 3-status workflow: Active → Blocked → Completed

#### Get All Tasks ✅
```
GET /api/tasks
```

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `blocked`, `completed`)

**Response:**
```json
{
  "tasks": [
    {
      "id": "uuid",
      "title": "Task title",
      "description": "Task description",
      "status": "active",
      "priority": "high",
      "urgency": 8,
      "duration": 30,
      "due_date": "2025-09-15",
      "weather_dependent": false,
      "project_id": "uuid",
      "initiative_id": "uuid",
      "created_at": "2025-09-13T10:00:00Z",
      "updated_at": "2025-09-13T10:00:00Z"
    }
  ],
  "total": 1
}
```

#### Create Task ✅
```
POST /api/tasks
```

**Request Body:**
```json
{
  "title": "New task",
  "description": "Task description",
  "priority": "medium",
  "urgency": 5,
  "duration": 30,
  "due_date": "2025-09-15",
  "weather_dependent": false,
  "project_id": "uuid",
  "initiative_id": "uuid"
}
```

#### Get Individual Task ✅
```
GET /api/tasks/{task_id}
```

#### Update Task ⚠️
```
PUT /api/tasks/{task_id}
```

#### Delete Task ⚠️
```
DELETE /api/tasks/{task_id}
```

#### Complete Task ✅
```
POST /api/tasks/{task_id}/complete
```

#### Block/Unblock Task
```
POST /api/tasks/{task_id}/block
POST /api/tasks/{task_id}/unblock
```

### Events API (`/api/events`)

Manage events with recurring support and master/instance architecture

#### Get All Events ✅
```
GET /api/events
```

**Query Parameters:**
- `start_date` (optional): Filter events from date
- `end_date` (optional): Filter events to date
- `event_type` (optional): Filter by type (`timed`, `all_day`, `instant`)

**Response:**
```json
{
  "events": [
    {
      "id": "uuid",
      "title": "Event title",
      "description": "Event description",
      "start_time": "2025-09-13T14:00:00",
      "end_time": "2025-09-13T15:00:00",
      "event_type": "timed",
      "location": "Meeting room",
      "is_blocking": true,
      "status": "scheduled",
      "notifications_enabled": true,
      "recurrence_pattern": "weekly",
      "recurrence_interval": 1,
      "recurrence_end_date": "2025-12-31",
      "is_recurrence_master": true,
      "recurrence_master_id": null,
      "is_recurrence_exception": false,
      "created_at": "2025-09-13T10:00:00Z",
      "updated_at": "2025-09-13T10:00:00Z"
    }
  ],
  "total": 1
}
```

#### Create Event
```
POST /api/events
```

**Request Body:**
```json
{
  "title": "New event",
  "description": "Event description",
  "start_time": "2025-09-13T14:00:00",
  "end_time": "2025-09-13T15:00:00",
  "event_type": "timed",
  "location": "Meeting room",
  "is_blocking": true,
  "notifications_enabled": true,
  "recurrence_pattern": "weekly",
  "recurrence_interval": 1,
  "recurrence_end_date": "2025-12-31"
}
```

#### Update Event
```
PUT /api/events/{event_id}
```

#### Delete Event
```
DELETE /api/events/{event_id}
```

#### Recurring Events Management
```
POST /api/events/recurring/edit
POST /api/events/recurring/delete
```

**Edit Request Body:**
```json
{
  "event_id": "uuid",
  "edit_mode": "this_only|this_and_future|all_in_series",
  "updates": {
    "title": "Updated title",
    "start_time": "2025-09-13T15:00:00"
  }
}
```

### Schedule API (`/api/schedule`)

Generate and manage schedules

#### Generate Schedule
```
POST /api/schedule/generate
```

**Request Body:**
```json
{
  "date": "2025-09-13",
  "include_tasks": true,
  "include_events": true,
  "time_pools": ["09:00-12:00", "14:00-17:00"]
}
```

#### Get Schedule for Date
```
GET /api/schedule/{date}
```

### Weather API (`/api/weather`)

Weather integration with dual API support

#### Current Weather
```
GET /api/weather/current
```

**Query Parameters:**
- `location` (optional): Location override

**Response:**
```json
{
  "location": "Seattle, WA",
  "temperature": 18.5,
  "condition": "partly_cloudy",
  "humidity": 65,
  "wind_speed": 12.0,
  "wind_direction": "NW",
  "precipitation_chance": 20,
  "timestamp": "2025-09-13T10:00:00Z"
}
```

#### 7-Day Forecast
```
GET /api/weather/forecast
```

#### Weather-Suitable Days
```
GET /api/weather/suitable-days
```

**Query Parameters:**
- `activity_type`: `outdoor|indoor|both`
- `days`: Number of days to check (default: 7)

#### Update Weather Data
```
POST /api/weather/update
```

### Initiatives API (`/api/initiatives`)

Manage recurring project templates

#### Get All Initiatives
```
GET /api/initiatives
```

#### Create Initiative
```
POST /api/initiatives
```

**Request Body:**
```json
{
  "title": "Initiative title",
  "description": "Initiative description",
  "frequency": "weekly",
  "frequency_interval": 1,
  "start_date": "2025-09-13",
  "end_date": "2025-12-31",
  "is_template": false
}
```

#### Get Initiative Details
```
GET /api/initiatives/{initiative_id}
```

### Projects API (`/api/projects`)

Manage projects with phases

#### Get All Projects
```
GET /api/projects
```

#### Create Project
```
POST /api/projects
```

**Request Body:**
```json
{
  "title": "Project title",
  "description": "Project description",
  "start_date": "2025-09-13",
  "end_date": "2025-12-31",
  "status": "planning",
  "initiative_id": "uuid",
  "phases": [
    {
      "title": "Phase 1",
      "description": "Phase description",
      "start_date": "2025-09-13",
      "end_date": "2025-10-13",
      "status": "not_started",
      "order": 1
    }
  ]
}
```

#### Get Project Details
```
GET /api/projects/{project_id}
```

### Task Queue API (`/api/task-queue`)

Intelligent task prioritization

#### Get Next Task
```
GET /api/task-queue/next
```

#### Get Queue Status
```
GET /api/task-queue/status
```

#### Update Task Priority
```
POST /api/task-queue/priority
```

**Request Body:**
```json
{
  "task_id": "uuid",
  "priority_score": 85
}
```

### Reminders API (`/api/reminders`)

Telegram notification management

#### Get All Reminders
```
GET /api/reminders
```

#### Create Reminder
```
POST /api/reminders
```

#### Update Reminder
```
PUT /api/reminders/{reminder_id}
```

#### Delete Reminder
```
DELETE /api/reminders/{reminder_id}
```

### Meals API (`/api/meals`)

Meal planning integration

#### Get All Meals
```
GET /api/meals
```

#### Create Meal
```
POST /api/meals
```

### Dishes API (`/api/dishes`)

Recipe and dish management

#### Get All Dishes
```
GET /api/dishes
```

#### Create Dish
```
POST /api/dishes
```

### Initiatives API (`/api/initiatives`)

**Status**: ⚠️ API endpoints currently experiencing timeout issues (under investigation)

Recurring initiative and goal management system. Initiatives represent repeating activities that generate tasks on a scheduled basis.

#### Get All Initiatives
```
GET /api/initiatives?active_only=false&skip=0&limit=100
```

**Query Parameters:**
- `active_only` (boolean, optional): Filter to only active initiatives
- `skip` (integer, optional): Number of records to skip for pagination
- `limit` (integer, optional): Maximum number of records to return

**Response:**
```json
{
  "initiatives": [
    {
      "id": "uuid-string",
      "title": "Morning Routine",
      "description": "Daily morning activities",
      "frequency": "daily",
      "interval": 1,
      "status": "active",
      "is_template": false,
      "preferred_start_time": "08:00:00",
      "estimated_duration_minutes": 60,
      "created_at": "2025-09-13T10:00:00Z",
      "updated_at": "2025-09-13T10:00:00Z"
    }
  ],
  "total": 1
}
```

#### Get Initiative by ID
```
GET /api/initiatives/{initiative_id}
```

#### Get Initiative Statistics
```
GET /api/initiatives/{initiative_id}/stats
```

**Response:**
```json
{
  "initiative_id": "uuid-string",
  "completion_rate": 85.5,
  "average_duration_minutes": 45,
  "last_completed_at": "2025-09-13T10:00:00Z",
  "next_due_date": null,
  "overdue_count": 0
}
```

#### Create Initiative
```
POST /api/initiatives
```

**Request Body:**
```json
{
  "title": "Evening Reflection",
  "description": "Daily reflection and planning",
  "frequency": "daily",
  "interval": 1,
  "preferred_start_time": "20:00:00",
  "estimated_duration_minutes": 30
}
```

#### Update Initiative
```
PUT /api/initiatives/{initiative_id}
```

#### Delete Initiative
```
DELETE /api/initiatives/{initiative_id}
```

#### Get Initiative Templates
```
GET /api/initiatives/templates
```

#### Create from Template
```
POST /api/initiatives/templates/{template_id}/create?title=New Initiative Title
```

## Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `503` - Service Unavailable

## Data Types

### Task Status
- `active` - Task is ready to work on
- `blocked` - Task is waiting on dependencies
- `completed` - Task is finished

### Task Priority
- `low` - Priority value 1-3
- `medium` - Priority value 4-6
- `high` - Priority value 7-10

### Event Types
- `timed` - Event with specific start/end times
- `all_day` - Full day event
- `instant` - Point-in-time event

### Event Status
- `scheduled` - Event is planned
- `in_progress` - Event is currently happening
- `completed` - Event is finished
- `cancelled` - Event was cancelled

### Recurrence Patterns
- `daily` - Repeat every day(s)
- `weekly` - Repeat every week(s)
- `monthly` - Repeat every month(s)
- `yearly` - Repeat every year(s)

### Initiative Frequency
- `daily` - Execute every day
- `weekly` - Execute every week
- `monthly` - Execute every month
- `quarterly` - Execute every quarter
- `yearly` - Execute annually
- `custom` - Custom recurrence pattern

### Initiative Status
- `active` - Initiative is currently running
- `paused` - Initiative is temporarily paused
- `completed` - Initiative has been completed
- `archived` - Initiative is archived for reference

### Recurring Edit Modes
- `this_only` - Edit only this instance
- `this_and_future` - Edit this and all future instances
- `all_in_series` - Edit the entire recurring series

## Environment Variables

Configure these in `.env` file in backend directory:

```bash
# Database
DATABASE_URL=sqlite:///./taskmaster.db

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_bot_token

# Weather API (optional)
OPENWEATHER_API_KEY=your_api_key
WEATHER_LOCATION=Seattle,WA,US

# Security
SECRET_KEY=your-secret-key
```

## Error Handling

All endpoints return appropriate HTTP status codes with error details:

```json
{
  "detail": "Task not found",
  "status_code": 404
}
```

For validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

## Webhooks

### Telegram Bot Webhooks

The application automatically handles Telegram bot webhooks for interactive notifications. No manual webhook configuration is required.

## Testing the API

### Endpoint Status Summary

| Endpoint | Status | Notes |
|----------|---------|-------|
| `GET /health` | ✅ Working | Server health check |
| `GET /api/tasks` | ✅ Working | Returns task list with pagination |
| `GET /api/tasks/{id}` | ✅ Working | Individual task retrieval |
| `POST /api/tasks` | ✅ Working | Task creation |
| `POST /api/tasks/{id}/complete` | ✅ Working | Task completion |
| `GET /api/events` | ✅ Working | Event list with recurring masters |
| `GET /api/initiatives` | ⚠️ Hanging | Investigation needed |
| `GET /api/projects` | ⚠️ Hanging | Investigation needed |
| `GET /api/weather/current` | ⚠️ Config-dependent | Requires API keys |

### Using cURL - Verified Working Examples

**Health Check:**
```bash
curl -X GET "http://localhost:8000/health"
# Expected: {"status":"healthy","service":"TaskMaster API"}
```

**Task Management (Full CRUD):**
```bash
# 1. Get all tasks
curl -X GET "http://localhost:8000/api/tasks"

# 2. Create a new task
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "priority": "medium", "duration": 30}'
# Expected: JSON with new task ID

# 3. Get individual task (replace {id} with actual task ID)
curl -X GET "http://localhost:8000/api/tasks/{task_id}"

# 4. Complete the task
curl -X POST "http://localhost:8000/api/tasks/{task_id}/complete"
# Expected: {"message":"Task completed successfully","task_id":"...","status":"completed"}

# 5. Verify completion
curl -X GET "http://localhost:8000/api/tasks/{task_id}"
# Expected: status should be "completed", is_completed should be true
```

**Event Management:**
```bash
# Get all events (shows recurring masters + standalone)
curl -X GET "http://localhost:8000/api/events"
# Expected: JSON array with ~12 events including recurring masters
```

### Testing Workflow - Complete Example

```bash
# Step 1: Check server health
curl -X GET "http://localhost:8000/health"

# Step 2: Create a test task
TASK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "API Test Task", "duration": 45, "priority": "high"}')

# Step 3: Extract task ID (requires jq for JSON parsing)
TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')

# Step 4: Verify task creation
curl -X GET "http://localhost:8000/api/tasks/$TASK_ID"

# Step 5: Complete the task
curl -X POST "http://localhost:8000/api/tasks/$TASK_ID/complete"

# Step 6: Verify completion
curl -X GET "http://localhost:8000/api/tasks/$TASK_ID"
```

### Using Python requests

```python
import requests
import json

base_url = "http://localhost:8000"

# Test health endpoint
health = requests.get(f"{base_url}/health")
print(f"Health: {health.json()}")

# Test task creation and completion workflow
def test_task_workflow():
    # Create task
    task_data = {
        "title": "Python API Test",
        "duration": 30,
        "priority": "medium",
        "description": "Testing API with Python"
    }
    
    create_response = requests.post(f"{base_url}/api/tasks", json=task_data)
    print(f"Create Status: {create_response.status_code}")
    
    if create_response.status_code == 200:
        task = create_response.json()
        task_id = task['id']
        print(f"Created task: {task_id}")
        
        # Get individual task
        get_response = requests.get(f"{base_url}/api/tasks/{task_id}")
        print(f"Get Status: {get_response.status_code}")
        
        # Complete task
        complete_response = requests.post(f"{base_url}/api/tasks/{task_id}/complete")
        print(f"Complete Status: {complete_response.status_code}")
        print(f"Complete Response: {complete_response.json()}")
        
        # Verify completion
        verify_response = requests.get(f"{base_url}/api/tasks/{task_id}")
        if verify_response.status_code == 200:
            final_task = verify_response.json()
            print(f"Final Status: {final_task['status']}")
            print(f"Is Completed: {final_task['is_completed']}")

test_task_workflow()
```

### Troubleshooting

**Common Issues:**

1. **Server Not Running**
   ```bash
   curl: (7) Failed to connect to localhost port 8000
   ```
   Solution: Start the server with `uvicorn src.api.app:app --reload --port 8000`

2. **500 Internal Server Error**
   ```bash
   Internal Server Error
   ```
   Solution: Check server logs, restart server with `/api/restart` endpoint

3. **Endpoints Hanging**
   - Initiatives and Projects endpoints currently hang
   - This is a known issue requiring separate investigation

**Server Restart:**
```bash
curl -X POST "http://localhost:8000/api/restart"
# Server will restart automatically
```

## Interactive API Documentation

Visit `http://localhost:8000/docs` when the server is running for interactive Swagger UI documentation with the ability to test endpoints directly from your browser.

## API Versioning

Currently using v1 (implicit). Future versions will use explicit versioning in the URL path (`/api/v2/`).