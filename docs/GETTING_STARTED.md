# TaskMaster API - Getting Started Guide

Welcome to the TaskMaster API! This guide will help you get up and running quickly with our comprehensive task and schedule management API.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Authentication Setup](#authentication-setup)
4. [Your First API Call](#your-first-api-call)
5. [Core Concepts](#core-concepts)
6. [Common Use Cases](#common-use-cases)
7. [Interactive Tutorial](#interactive-tutorial)
8. [Next Steps](#next-steps)

## Quick Start

Get started with TaskMaster API in 5 minutes:

### 1. Get Your API Key

Contact your administrator or use the dashboard to generate an API key:

```bash
# Example API key (replace with your actual key)
export TASKMASTER_API_KEY="tk_live_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
```

### 2. Test Your Connection

```bash
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  https://api.taskmaster.dev/health
```

Expected response:
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "version": "2.4.0",
    "timestamp": "2025-09-19T10:00:00Z"
  }
}
```

### 3. Create Your First Task

```bash
curl -X POST https://api.taskmaster.dev/v2/tasks \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My first task",
    "description": "Getting started with TaskMaster API",
    "priority": "medium",
    "urgency": 5,
    "duration": 30
  }'
```

### 4. Retrieve Your Tasks

```bash
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  https://api.taskmaster.dev/v2/tasks?limit=10
```

Congratulations! You've successfully made your first API calls.

## Prerequisites

Before you begin, ensure you have:

### Development Environment
- **Command Line**: Terminal (macOS/Linux) or PowerShell (Windows)
- **HTTP Client**: cURL, Postman, or programming language HTTP library
- **Text Editor**: For viewing JSON responses and writing code

### API Access
- **API Key**: Contact your administrator or generate one from the dashboard
- **Base URL**: Use the appropriate environment URL
  - Development: `http://localhost:5000/api`
  - Production: `https://api.taskmaster.dev`

### Optional Tools
- **jq**: JSON processor for prettier command-line output
  ```bash
  # Install jq (macOS)
  brew install jq
  
  # Install jq (Ubuntu/Debian)
  sudo apt-get install jq
  
  # Usage example
  curl -H "X-API-Key: $TASKMASTER_API_KEY" \
    https://api.taskmaster.dev/v2/tasks | jq
  ```

## Authentication Setup

TaskMaster API supports multiple authentication methods. For getting started, we'll use API key authentication.

### API Key Authentication

API keys provide programmatic access with scoped permissions:

#### 1. Obtain an API Key

**Option A: Through Dashboard**
1. Log into TaskMaster dashboard
2. Navigate to Settings > API Keys
3. Click "Generate New API Key"
4. Select appropriate scopes
5. Copy and securely store your key

**Option B: Through API (if you have admin access)**
```bash
curl -X POST https://api.taskmaster.dev/auth/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-session-token>" \
  -d '{
    "name": "Getting Started Key",
    "description": "API key for learning TaskMaster API",
    "scopes": ["tasks.read", "tasks.write", "events.read", "search.read"]
  }'
```

#### 2. Store Your API Key Securely

**Environment Variable (Recommended)**
```bash
export TASKMASTER_API_KEY="your-actual-api-key-here"
```

**Configuration File**
```bash
# ~/.taskmaster/config
TASKMASTER_API_KEY=your-actual-api-key-here
TASKMASTER_BASE_URL=https://api.taskmaster.dev
```

#### 3. Test Authentication

```bash
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  https://api.taskmaster.dev/health
```

### Understanding API Key Scopes

Your API key may have specific scopes that limit access:

| Scope | Description | Endpoints |
|-------|-------------|-----------|
| `tasks.read` | Read tasks | GET /v2/tasks, GET /v2/tasks/{id} |
| `tasks.write` | Create/update tasks | POST /v2/tasks, PUT /v2/tasks/{id} |
| `events.read` | Read events | GET /v2/events, GET /v2/events/{id} |
| `events.write` | Create/update events | POST /v2/events, PUT /v2/events/{id} |
| `search.read` | Use search features | GET /search/* |
| `export.create` | Export data | POST /export/* |

## Your First API Call

Let's make your first API call and understand the response structure.

### 1. Check API Health

```bash
curl -v -H "X-API-Key: $TASKMASTER_API_KEY" \
  https://api.taskmaster.dev/health
```

**What this does:**
- `-v`: Verbose output to see headers
- `-H`: Adds the API key header
- Tests that your key works and API is available

**Expected Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999

{
  "status": "success",
  "data": {
    "status": "healthy",
    "version": "2.4.0",
    "timestamp": "2025-09-19T10:00:00Z",
    "database_status": "connected",
    "websocket_status": "active",
    "search_status": "ready"
  }
}
```

### 2. Create Your First Task

```bash
curl -X POST https://api.taskmaster.dev/v2/tasks \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn TaskMaster API",
    "description": "Complete the getting started tutorial and create my first integration",
    "priority": "high",
    "urgency": 7,
    "duration": 60,
    "due_date": "2025-09-25"
  }'
```

**What this does:**
- `POST`: Creates a new resource
- `Content-Type: application/json`: Tells server we're sending JSON
- The JSON payload contains task details

**Expected Response:**
```http
HTTP/1.1 201 Created
Location: https://api.taskmaster.dev/v2/tasks/123e4567-e89b-12d3-a456-426614174000

{
  "status": "success",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Learn TaskMaster API",
    "description": "Complete the getting started tutorial and create my first integration",
    "priority": "high",
    "urgency": 7,
    "duration": 60,
    "status": "active",
    "due_date": "2025-09-25",
    "completed": false,
    "created_at": "2025-09-19T10:00:00Z",
    "updated_at": "2025-09-19T10:00:00Z"
  },
  "message": "Task created successfully"
}
```

### 3. Retrieve Your Task

Use the ID from the creation response:

```bash
TASK_ID="123e4567-e89b-12d3-a456-426614174000"

curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  https://api.taskmaster.dev/v2/tasks/$TASK_ID
```

### 4. List All Your Tasks

```bash
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/v2/tasks?limit=10&sort=created_at:desc"
```

**Expected Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Learn TaskMaster API",
      "status": "active",
      "priority": "high",
      "created_at": "2025-09-19T10:00:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "limit": 10,
    "offset": 0,
    "has_more": false,
    "page": 1,
    "total_pages": 1
  }
}
```

## Core Concepts

Understanding these core concepts will help you use the API effectively.

### 1. Response Structure

All API responses follow a consistent format:

```json
{
  "status": "success|error",
  "data": {}, // Response data or array
  "message": "Optional message",
  "meta": {}, // Pagination and metadata
  "errors": {} // Field-specific errors (error responses only)
}
```

### 2. Resource Identifiers

All resources use UUID identifiers:
- Format: `123e4567-e89b-12d3-a456-426614174000`
- Globally unique across the system
- Used in URL paths and relationships

### 3. Timestamps

All timestamps are in ISO 8601 format with UTC timezone:
- Format: `2025-09-19T10:00:00Z`
- Always in UTC (Z suffix)
- Consistent across all endpoints

### 4. Pagination

List endpoints return paginated results:

```json
{
  "data": [...],
  "meta": {
    "total": 150,        // Total items matching query
    "limit": 20,         // Items per page
    "offset": 0,         // Items skipped
    "has_more": true,    // More pages available
    "page": 1,           // Current page (1-indexed)
    "total_pages": 8     // Total pages
  }
}
```

### 5. Filtering and Sorting

Use query parameters for filtering and sorting:

```bash
# Filter by status and priority
curl "https://api.taskmaster.dev/v2/tasks?status=active&priority=high,urgent"

# Sort by multiple fields
curl "https://api.taskmaster.dev/v2/tasks?sort=priority:desc,created_at:asc"

# Combine filtering, sorting, and pagination
curl "https://api.taskmaster.dev/v2/tasks?status=active&sort=urgency:desc&limit=50&offset=0"
```

### 6. Field Selection

Reduce response size by selecting specific fields:

```bash
# Only get essential fields
curl "https://api.taskmaster.dev/v2/tasks?fields=id,title,status,priority"
```

## Common Use Cases

Here are practical examples for common integration scenarios.

### Use Case 1: Task Management Dashboard

Create a simple task dashboard that shows active tasks:

```bash
#!/bin/bash

echo "=== TaskMaster Dashboard ==="
echo

# Get active high-priority tasks
echo "High Priority Active Tasks:"
curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/v2/tasks?status=active&priority=high,urgent&sort=urgency:desc&limit=5" \
  | jq -r '.data[] | "- \(.title) (Urgency: \(.urgency))"'

echo

# Get overdue tasks
echo "Overdue Tasks:"
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/v2/tasks?status=active&due_date_to=$YESTERDAY&sort=due_date:asc" \
  | jq -r '.data[] | "- \(.title) (Due: \(.due_date))"'

echo

# Get task completion stats
echo "Task Statistics:"
ACTIVE_COUNT=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/v2/tasks?status=active&limit=1" \
  | jq -r '.meta.total')

COMPLETED_COUNT=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/v2/tasks?status=completed&limit=1" \
  | jq -r '.meta.total')

echo "- Active Tasks: $ACTIVE_COUNT"
echo "- Completed Tasks: $COMPLETED_COUNT"
```

### Use Case 2: Bulk Task Creation

Create multiple related tasks at once:

```bash
# Create project setup tasks
curl -X POST https://api.taskmaster.dev/v2/tasks/batch \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "title": "Set up development environment",
        "description": "Install dependencies and configure IDE",
        "priority": "high",
        "urgency": 8,
        "duration": 120
      },
      {
        "title": "Create project structure",
        "description": "Set up folders and initial files",
        "priority": "high",
        "urgency": 7,
        "duration": 60
      },
      {
        "title": "Write initial documentation",
        "description": "Create README and basic docs",
        "priority": "medium",
        "urgency": 5,
        "duration": 90
      }
    ]
  }'
```

### Use Case 3: Task Search and Filter

Find specific tasks using search and filters:

```bash
# Search for documentation tasks
echo "Documentation Tasks:"
curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/search/search?q=documentation&types=tasks" \
  | jq -r '.data.results[] | "- \(.title) (\(.type))"'

# Find urgent tasks due this week
WEEK_END=$(date -d "+7 days" +%Y-%m-%d)
echo "Urgent Tasks Due This Week:"
curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/v2/tasks?urgency_min=7&due_date_to=$WEEK_END&sort=due_date:asc" \
  | jq -r '.data[] | "- \(.title) (Due: \(.due_date), Urgency: \(.urgency))"'
```

### Use Case 4: Event Management

Work with calendar events:

```bash
# Create a meeting event
curl -X POST https://api.taskmaster.dev/v2/events \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Planning Meeting",
    "description": "Weekly team planning and status update",
    "start": "2025-09-22T09:00:00Z",
    "end": "2025-09-22T10:00:00Z",
    "location": "Conference Room A",
    "event_type": "timed",
    "is_blocking": true,
    "notifications_enabled": true
  }'

# Get this week events for calendar
WEEK_START=$(date -d "monday" +%Y-%m-%d)
WEEK_END=$(date -d "sunday" +%Y-%m-%d)

curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/v2/events/calendar?start=$WEEK_START&end=$WEEK_END"
```

## Interactive Tutorial

Follow this step-by-step tutorial to explore key API features.

### Step 1: Set Up Your Environment

```bash
# Set your API key (replace with your actual key)
export TASKMASTER_API_KEY="your-api-key-here"

# Set base URL
export API_BASE="https://api.taskmaster.dev"

# Test connection
curl -H "X-API-Key: $TASKMASTER_API_KEY" "$API_BASE/health"
```

### Step 2: Create a Project Workflow

```bash
# Create a project task
PROJECT_TASK=$(curl -s -X POST "$API_BASE/v2/tasks" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Plan new feature development",
    "description": "Research, design, and plan implementation of user authentication",
    "priority": "high",
    "urgency": 8,
    "duration": 180,
    "due_date": "2025-09-24"
  }' | jq -r '.data.id')

echo "Created project task: $PROJECT_TASK"

# Create subtasks
SUBTASK1=$(curl -s -X POST "$API_BASE/v2/tasks" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Research authentication libraries\",
    \"description\": \"Compare different auth solutions\",
    \"priority\": \"medium\",
    \"urgency\": 6,
    \"duration\": 90,
    \"parent_task_id\": \"$PROJECT_TASK\"
  }" | jq -r '.data.id')

SUBTASK2=$(curl -s -X POST "$API_BASE/v2/tasks" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"Design authentication flow\",
    \"description\": \"Create user flow diagrams\",
    \"priority\": \"medium\",
    \"urgency\": 5,
    \"duration\": 120,
    \"parent_task_id\": \"$PROJECT_TASK\"
  }" | jq -r '.data.id')

echo "Created subtasks: $SUBTASK1, $SUBTASK2"
```

### Step 3: Explore Filtering and Sorting

```bash
# Get all tasks for this project
echo "All project tasks:"
curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$API_BASE/v2/tasks?sort=urgency:desc" | jq -r '.data[] | "- \(.title) (Urgency: \(.urgency))"'

# Get high-priority tasks only
echo "High priority tasks:"
curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$API_BASE/v2/tasks?priority=high&sort=created_at:desc" | jq -r '.data[] | "- \(.title)"'

# Search for authentication tasks
echo "Authentication-related tasks:"
curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$API_BASE/search/search?q=authentication&types=tasks" | jq -r '.data.results[] | "- \(.title)"'
```

### Step 4: Update Tasks

```bash
# Complete the research subtask
curl -X PUT "$API_BASE/v2/tasks/$SUBTASK1" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'

echo "Marked research task as completed"

# Update the main task priority
curl -X PUT "$API_BASE/v2/tasks/$PROJECT_TASK" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urgency": 9,
    "description": "Research complete. Moving to design phase."
  }'

echo "Updated project task priority and description"
```

### Step 5: Create Calendar Event

```bash
# Create a planning meeting
MEETING_EVENT=$(curl -s -X POST "$API_BASE/v2/events" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Authentication Feature Planning",
    "description": "Team meeting to discuss authentication implementation",
    "start": "2025-09-23T14:00:00Z",
    "end": "2025-09-23T15:30:00Z",
    "location": "Conference Room B",
    "event_type": "timed",
    "is_blocking": true
  }' | jq -r '.data.id')

echo "Created planning meeting: $MEETING_EVENT"
```

### Step 6: Export Your Data

```bash
# Export completed tasks
curl -X POST "$API_BASE/export/tasks" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "filters": {
      "status": ["completed"]
    },
    "fields": ["id", "title", "priority", "completed_at"]
  }'
```

### Step 7: Clean Up (Optional)

```bash
# Delete the test tasks
curl -X DELETE "$API_BASE/v2/tasks/$SUBTASK1" \
  -H "X-API-Key: $TASKMASTER_API_KEY"

curl -X DELETE "$API_BASE/v2/tasks/$SUBTASK2" \
  -H "X-API-Key: $TASKMASTER_API_KEY"

curl -X DELETE "$API_BASE/v2/tasks/$PROJECT_TASK" \
  -H "X-API-Key: $TASKMASTER_API_KEY"

echo "Cleaned up test tasks"
```

## Next Steps

Now that you've completed the getting started guide, here are recommended next steps:

### 1. Explore Advanced Features

**Search API**
- Learn advanced query syntax
- Implement autocomplete with suggestions
- Use faceted search for filtering UIs

**Real-time Features**
- Connect to WebSocket for live updates
- Implement real-time collaboration
- Build reactive user interfaces

**Export and Analytics**
- Set up automated data exports
- Monitor API usage with analytics
- Create custom reports

### 2. Build Your Integration

**Planning Questions:**
- What data do you need to sync?
- How often will you make API calls?
- Do you need real-time updates?
- What error handling do you need?

**Architecture Considerations:**
- Use appropriate authentication method
- Implement proper error handling
- Plan for rate limiting
- Consider caching strategies

### 3. Development Resources

**Documentation:**
- [Complete API Guide](./API_GUIDE.md) - Comprehensive reference
- [OpenAPI Specification](../openapi.yaml) - Machine-readable API spec
- [WebSocket Guide](./WEBSOCKET_GUIDE.md) - Real-time features

**Tools:**
- [Postman Collection](../postman/TaskMaster-API.json) - Ready-to-use API tests
- [Code Examples](../examples/) - Sample implementations
- [SDKs](../sdks/) - Language-specific libraries

**Community:**
- [Developer Forum](https://community.taskmaster.dev) - Ask questions and share
- [GitHub Issues](https://github.com/taskmaster/api/issues) - Report bugs
- [Status Page](https://status.taskmaster.dev) - Service status

### 4. Sample Applications

Build complete applications using TaskMaster API:

**Task Dashboard (Web)**
```bash
git clone https://github.com/taskmaster/examples/task-dashboard
cd task-dashboard
npm install
# Configure API key in .env
npm start
```

**Mobile Task App (React Native)**
```bash
git clone https://github.com/taskmaster/examples/mobile-app
cd mobile-app
# Follow README for setup
```

**CLI Tool (Python)**
```bash
pip install taskmaster-cli
taskmaster auth --api-key your-key
taskmaster tasks list --status active
```

### 5. Production Checklist

Before going to production:

- [ ] Use production API URL and credentials
- [ ] Implement proper error handling and retries
- [ ] Set up monitoring and alerting
- [ ] Configure rate limiting handling
- [ ] Implement caching where appropriate
- [ ] Test with realistic data volumes
- [ ] Set up logging for debugging
- [ ] Document your integration
- [ ] Plan for API updates and versioning

### 6. Getting Help

If you need assistance:

1. **Check Documentation**: Most questions are answered in the guides
2. **Search Community**: Others may have solved similar problems
3. **Contact Support**: api-support@taskmaster.dev for technical issues
4. **Feature Requests**: Use GitHub issues for feature suggestions

## Troubleshooting Common Issues

### Issue: "Invalid API Key" Error

**Solution:**
```bash
# Verify your API key format
echo $TASKMASTER_API_KEY | grep -E '^tk_(test|live)_[a-zA-Z0-9]{50,}$'

# Test with minimal request
curl -H "X-API-Key: $TASKMASTER_API_KEY" https://api.taskmaster.dev/health
```

### Issue: Empty Response Data

**Possible Causes:**
- No data matches your filters
- API key lacks required scopes
- Pagination offset too high

**Solution:**
```bash
# Try without filters
curl -H "X-API-Key: $TASKMASTER_API_KEY" https://api.taskmaster.dev/v2/tasks

# Check total count
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "https://api.taskmaster.dev/v2/tasks?limit=1" | jq '.meta.total'
```

### Issue: Rate Limiting

**Solution:**
```bash
# Check rate limit headers
curl -I -H "X-API-Key: $TASKMASTER_API_KEY" https://api.taskmaster.dev/v2/tasks

# Implement retry logic in your application
```

### Issue: Validation Errors

**Solution:**
```bash
# Check required fields and formats
curl -X POST https://api.taskmaster.dev/v2/tasks \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "Valid task title"}' # Minimal valid request
```

Congratulations! You've completed the TaskMaster API Getting Started Guide. You now have the foundation to build powerful integrations with our task and schedule management platform.