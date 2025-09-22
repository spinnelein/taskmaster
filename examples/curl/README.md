# TaskMaster cURL Examples

Comprehensive command-line examples for the TaskMaster API using cURL. Perfect for testing, automation, CI/CD integration, and shell scripting.

## Setup

### Environment Variables

```bash
# Set your API credentials
export TASKMASTER_API_KEY="tk_live_abc123..."
export TASKMASTER_BASE_URL="https://api.taskmaster.dev"

# Optional: Set user context
export TASKMASTER_USER_ID="your-user-id"
```

### Helper Functions

Add these to your `.bashrc` or `.zshrc` for easier usage:

```bash
# Helper function for TaskMaster API calls
tmapi() {
    local method="${1:-GET}"
    local endpoint="$2"
    local data="$3"
    
    local curl_opts=(-X "$method" -H "X-API-Key: $TASKMASTER_API_KEY" -H "Content-Type: application/json")
    
    if [[ -n "$data" ]]; then
        curl_opts+=(-d "$data")
    fi
    
    curl "${curl_opts[@]}" "$TASKMASTER_BASE_URL$endpoint" | jq '.'
}

# Pretty print JSON responses
tmapi_get() { tmapi GET "$1"; }
tmapi_post() { tmapi POST "$1" "$2"; }
tmapi_put() { tmapi PUT "$1" "$2"; }
tmapi_delete() { tmapi DELETE "$1"; }
```

## Quick Start

### Health Check

```bash
# Test API connectivity
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/health" | jq '.'
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

### Authentication Test

```bash
# Verify API key works
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks?limit=1" | jq '.status'
```

## Basic Operations

### Tasks API

#### Create a Task

```bash
curl -X POST "$TASKMASTER_BASE_URL/v2/tasks" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation with examples",
    "priority": "high",
    "urgency": 8,
    "duration": 120,
    "due_date": "2025-09-25",
    "required_context": ["computer", "internet"],
    "equipment_needed": ["laptop"]
  }' | jq '.'
```

#### List Tasks

```bash
# Basic list
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks" | jq '.data[] | {id, title, status, priority}'

# With filtering and sorting
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks?status=active&priority=high,urgent&sort=urgency:desc&limit=10" \
  | jq '.data[] | {title, urgency, priority}'
```

#### Get Specific Task

```bash
# Get task by ID (replace with actual task ID)
TASK_ID="123e4567-e89b-12d3-a456-426614174000"

curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks/$TASK_ID" | jq '.'
```

#### Update Task

```bash
# Update task properties
curl -X PUT "$TASKMASTER_BASE_URL/v2/tasks/$TASK_ID" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urgency": 9,
    "priority": "urgent",
    "status": "in_progress"
  }' | jq '.'
```

#### Complete Task

```bash
# Mark task as completed
curl -X PUT "$TASKMASTER_BASE_URL/v2/tasks/$TASK_ID" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}' | jq '.'
```

#### Delete Task

```bash
# Delete task
curl -X DELETE "$TASKMASTER_BASE_URL/v2/tasks/$TASK_ID" \
  -H "X-API-Key: $TASKMASTER_API_KEY"
```

### Events API

#### Create Event

```bash
# Create a calendar event
curl -X POST "$TASKMASTER_BASE_URL/v2/events" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team Planning Meeting",
    "description": "Weekly team planning and status update",
    "start": "2025-09-22T09:00:00Z",
    "end": "2025-09-22T10:30:00Z",
    "location": "Conference Room A",
    "event_type": "timed",
    "is_blocking": true,
    "notifications_enabled": true
  }' | jq '.'
```

#### List Events

```bash
# List all events
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/events" | jq '.data[] | {title, start, end, location}'

# Get calendar events for a specific date range
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/events/calendar?start=2025-09-20&end=2025-09-27" \
  | jq '.data[] | {title, start, end, allDay}'
```

#### Update Event

```bash
# Update event (replace with actual event ID)
EVENT_ID="event-123"

curl -X PUT "$TASKMASTER_BASE_URL/v2/events/$EVENT_ID" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Conference Room B - Updated",
    "description": "Updated meeting location"
  }' | jq '.'
```

## Advanced Features

### Batch Operations

#### Create Multiple Tasks

```bash
curl -X POST "$TASKMASTER_BASE_URL/v2/tasks/batch" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "title": "Setup development environment",
        "priority": "high",
        "duration": 120
      },
      {
        "title": "Write unit tests",
        "priority": "medium",
        "duration": 180
      },
      {
        "title": "Update documentation",
        "priority": "low",
        "duration": 60
      }
    ]
  }' | jq '.'
```

### Search API

#### Basic Search

```bash
# Search across all entity types
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/search/search?q=project%20management" \
  | jq '.data.results[] | {title, type, relevance_score}'
```

#### Advanced Search with Facets

```bash
# Search with faceting enabled
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/search/search?q=urgent&include_facets=true&types=tasks,events" \
  | jq '{
    results: .data.results[] | {title, type},
    facets: .data.facets
  }'
```

#### Search Suggestions

```bash
# Get auto-complete suggestions
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/search/suggestions?q=proj&limit=5" \
  | jq '.data.suggestions[]'
```

#### Query Analysis

```bash
# Analyze search query
curl -X POST "$TASKMASTER_BASE_URL/search/query/analyze" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "status:active priority:high urgent task"}' \
  | jq '.'
```

### Export API

#### Export Tasks as CSV

```bash
curl -X POST "$TASKMASTER_BASE_URL/export/tasks" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "filters": {
      "status": ["active", "completed"],
      "priority": ["high", "urgent"]
    },
    "fields": ["id", "title", "status", "priority", "urgency", "created_at"],
    "sort": "created_at:desc"
  }' | jq '.'
```

#### Export Events as JSON

```bash
curl -X POST "$TASKMASTER_BASE_URL/export/events" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "filters": {
      "start_from": "2025-09-01T00:00:00Z",
      "start_to": "2025-09-30T23:59:59Z"
    },
    "fields": ["id", "title", "start", "end", "location", "event_type"]
  }' | jq '.'
```

### Analytics API

#### Usage Analytics

```bash
# Get 24-hour usage summary
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/analytics/usage?timeframe=24h&format=summary" \
  | jq '.data | {total_requests, success_rate, avg_response_time_ms}'

# Get detailed 7-day analytics
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/analytics/usage?timeframe=7d&format=detailed" \
  | jq '.data | {total_requests, top_endpoints, error_breakdown}'
```

### WebSocket API

#### WebSocket Statistics

```bash
# Get current WebSocket statistics
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/websocket/stats" \
  | jq '.data | {active_connections, total_connections_today, messages_sent_today}'
```

#### Test WebSocket Broadcasting

```bash
# Trigger a test WebSocket event
curl -X POST "$TASKMASTER_BASE_URL/websocket/broadcast/task-created" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "WebSocket Test Task",
    "description": "This task creation will be broadcast via WebSocket",
    "priority": "medium",
    "user_id": "'$TASKMASTER_USER_ID'"
  }' | jq '.'
```

### Webhooks API

#### List Webhooks

```bash
# Get all configured webhooks
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/webhooks" \
  | jq '.data[] | {id, name, url, events, is_active}'
```

#### Create Webhook

```bash
# Create a new webhook (update URL to your endpoint)
curl -X POST "$TASKMASTER_BASE_URL/webhooks" \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Task Notifications",
    "url": "https://your-app.com/webhooks/taskmaster",
    "events": ["task.created", "task.completed", "event.created"],
    "is_active": true,
    "secret": "your-webhook-secret-key",
    "headers": {
      "Authorization": "Bearer your-app-token"
    }
  }' | jq '.'
```

## Filtering and Pagination

### Advanced Task Filtering

```bash
# Complex filtering example
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks?\
status=active&\
priority=high,urgent&\
due_date_from=2025-09-20&\
due_date_to=2025-09-30&\
urgency_min=7&\
duration_min=60&\
sort=urgency:desc,due_date:asc&\
limit=25&\
fields=id,title,status,priority,urgency,due_date" \
  | jq '.data[] | {title, urgency, priority, due_date}'
```

### Pagination Example

```bash
# Function to get all tasks with pagination
get_all_tasks() {
    local status="$1"
    local limit=50
    local offset=0
    local all_tasks=()
    
    while true; do
        echo "Fetching page $((offset/limit + 1))..." >&2
        
        local response=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
            "$TASKMASTER_BASE_URL/v2/tasks?status=$status&limit=$limit&offset=$offset")
        
        local tasks=$(echo "$response" | jq -r '.data[]')
        local has_more=$(echo "$response" | jq -r '.meta.has_more')
        
        if [[ "$tasks" == "" ]]; then
            break
        fi
        
        all_tasks+=("$tasks")
        
        if [[ "$has_more" != "true" ]]; then
            break
        fi
        
        offset=$((offset + limit))
    done
    
    printf '%s\n' "${all_tasks[@]}"
}

# Usage
get_all_tasks "active" | jq -s '.' > all_active_tasks.json
```

### Date Range Filtering

```bash
# Tasks due this week
WEEK_START=$(date -d "monday" +%Y-%m-%d)
WEEK_END=$(date -d "sunday" +%Y-%m-%d)

curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks?due_date_from=$WEEK_START&due_date_to=$WEEK_END&sort=due_date:asc" \
  | jq '.data[] | {title, due_date, priority}'

# Events for current month
MONTH_START=$(date +%Y-%m-01)
MONTH_END=$(date -d "$(date +%Y-%m-01) +1 month -1 day" +%Y-%m-%d)

curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/events?start_from=${MONTH_START}T00:00:00Z&start_to=${MONTH_END}T23:59:59Z" \
  | jq '.data[] | {title, start, end}'
```

## Error Handling

### Comprehensive Error Handling Script

```bash
#!/bin/bash

# Function to make API calls with error handling
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local description="$4"
    
    echo "Making $method request to $endpoint..."
    if [[ -n "$description" ]]; then
        echo "Description: $description"
    fi
    
    local curl_opts=(-s -w "%{http_code}" -o response.json)
    curl_opts+=(-X "$method")
    curl_opts+=(-H "X-API-Key: $TASKMASTER_API_KEY")
    curl_opts+=(-H "Content-Type: application/json")
    
    if [[ -n "$data" ]]; then
        curl_opts+=(-d "$data")
    fi
    
    local http_code=$(curl "${curl_opts[@]}" "$TASKMASTER_BASE_URL$endpoint")
    
    case "$http_code" in
        200|201)
            echo "✅ Success ($http_code)"
            jq '.' response.json
            ;;
        204)
            echo "✅ Success ($http_code) - No Content"
            ;;
        400)
            echo "❌ Bad Request (400)"
            jq '.message // .error' response.json
            ;;
        401)
            echo "❌ Unauthorized (401) - Check your API key"
            jq '.message // .error' response.json
            ;;
        404)
            echo "❌ Not Found (404)"
            jq '.message // .error' response.json
            ;;
        422)
            echo "❌ Validation Error (422)"
            echo "Errors:"
            jq '.errors // .message' response.json
            ;;
        429)
            echo "❌ Rate Limited (429)"
            local retry_after=$(curl -s -I -H "X-API-Key: $TASKMASTER_API_KEY" "$TASKMASTER_BASE_URL$endpoint" | grep -i "retry-after" | cut -d' ' -f2 | tr -d '\r')
            echo "Retry after: ${retry_after:-60} seconds"
            ;;
        5*)
            echo "❌ Server Error ($http_code)"
            jq '.message // .error // "Internal server error"' response.json
            ;;
        *)
            echo "❌ Unexpected response code: $http_code"
            cat response.json
            ;;
    esac
    
    rm -f response.json
    echo
}

# Test various scenarios
echo "=== Testing API Error Handling ==="

# Valid request
api_call GET "/health" "" "Health check"

# Invalid API key
ORIGINAL_KEY="$TASKMASTER_API_KEY"
TASKMASTER_API_KEY="invalid-key"
api_call GET "/v2/tasks" "" "Invalid API key test"
TASKMASTER_API_KEY="$ORIGINAL_KEY"

# Not found
api_call GET "/v2/tasks/00000000-0000-0000-0000-000000000000" "" "Non-existent task"

# Validation error
api_call POST "/v2/tasks" '{"description": "Task without title"}' "Missing required field"

# Invalid endpoint
api_call GET "/v2/nonexistent" "" "Invalid endpoint"
```

## Automation Scripts

### Daily Task Report

```bash
#!/bin/bash

# Daily task summary report
generate_daily_report() {
    local date="${1:-$(date +%Y-%m-%d)}"
    local report_file="task_report_$date.json"
    
    echo "Generating task report for $date..."
    
    # Get task counts by status
    local active_count=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
        "$TASKMASTER_BASE_URL/v2/tasks?status=active&limit=1" | jq '.meta.total')
    
    local completed_count=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
        "$TASKMASTER_BASE_URL/v2/tasks?status=completed&limit=1" | jq '.meta.total')
    
    local blocked_count=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
        "$TASKMASTER_BASE_URL/v2/tasks?status=blocked&limit=1" | jq '.meta.total')
    
    # Get overdue tasks
    local yesterday=$(date -d "yesterday" +%Y-%m-%d)
    local overdue_tasks=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
        "$TASKMASTER_BASE_URL/v2/tasks?status=active&due_date_to=$yesterday" | jq '.data')
    
    # Get high priority tasks
    local high_priority_tasks=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
        "$TASKMASTER_BASE_URL/v2/tasks?status=active&priority=high,urgent&sort=urgency:desc" | jq '.data')
    
    # Generate report
    cat > "$report_file" <<EOF
{
  "report_date": "$date",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "summary": {
    "active_tasks": $active_count,
    "completed_tasks": $completed_count,
    "blocked_tasks": $blocked_count,
    "overdue_tasks": $(echo "$overdue_tasks" | jq length)
  },
  "overdue_tasks": $overdue_tasks,
  "high_priority_tasks": $high_priority_tasks
}
EOF
    
    echo "Report saved to $report_file"
    
    # Display summary
    echo
    echo "=== Daily Task Summary for $date ==="
    echo "Active Tasks: $active_count"
    echo "Completed Tasks: $completed_count"
    echo "Blocked Tasks: $blocked_count"
    echo "Overdue Tasks: $(echo "$overdue_tasks" | jq length)"
    echo "High Priority Active: $(echo "$high_priority_tasks" | jq length)"
}

# Run report
generate_daily_report
```

### Task Migration Script

```bash
#!/bin/bash

# Migrate tasks from one project to another
migrate_tasks() {
    local from_project="$1"
    local to_project="$2"
    
    if [[ -z "$from_project" || -z "$to_project" ]]; then
        echo "Usage: migrate_tasks <from_project_id> <to_project_id>"
        return 1
    fi
    
    echo "Migrating tasks from project $from_project to $to_project..."
    
    # Get all tasks from source project
    local tasks=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
        "$TASKMASTER_BASE_URL/v2/tasks?project_id=$from_project&limit=1000" | jq '.data')
    
    local task_count=$(echo "$tasks" | jq length)
    echo "Found $task_count tasks to migrate"
    
    # Migrate each task
    local migrated=0
    local failed=0
    
    echo "$tasks" | jq -c '.[]' | while read -r task; do
        local task_id=$(echo "$task" | jq -r '.id')
        local task_title=$(echo "$task" | jq -r '.title')
        
        echo "Migrating task: $task_title"
        
        local result=$(curl -s -w "%{http_code}" -o /dev/null \
            -X PUT "$TASKMASTER_BASE_URL/v2/tasks/$task_id" \
            -H "X-API-Key: $TASKMASTER_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{\"project_id\": \"$to_project\"}")
        
        if [[ "$result" == "200" ]]; then
            echo "  ✅ Migrated successfully"
            ((migrated++))
        else
            echo "  ❌ Migration failed (HTTP $result)"
            ((failed++))
        fi
    done
    
    echo
    echo "Migration complete:"
    echo "  Migrated: $migrated"
    echo "  Failed: $failed"
}

# Usage example
# migrate_tasks "old-project-id" "new-project-id"
```

### Bulk Task Operations

```bash
#!/bin/bash

# Bulk complete tasks matching criteria
bulk_complete_tasks() {
    local project_id="$1"
    local status="${2:-active}"
    
    echo "Bulk completing $status tasks in project $project_id..."
    
    # Get tasks matching criteria
    local tasks=$(curl -s -H "X-API-Key: $TASKMASTER_API_KEY" \
        "$TASKMASTER_BASE_URL/v2/tasks?project_id=$project_id&status=$status&limit=1000" \
        | jq -r '.data[] | .id')
    
    local task_count=$(echo "$tasks" | wc -l)
    echo "Found $task_count tasks to complete"
    
    if [[ $task_count -eq 0 ]]; then
        echo "No tasks found matching criteria"
        return 0
    fi
    
    # Confirm operation
    read -p "Are you sure you want to complete $task_count tasks? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Operation cancelled"
        return 0
    fi
    
    # Complete each task
    local completed=0
    local failed=0
    
    echo "$tasks" | while read -r task_id; do
        if [[ -z "$task_id" ]]; then
            continue
        fi
        
        echo "Completing task: $task_id"
        
        local result=$(curl -s -w "%{http_code}" -o /dev/null \
            -X PUT "$TASKMASTER_BASE_URL/v2/tasks/$task_id" \
            -H "X-API-Key: $TASKMASTER_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{"status": "completed"}')
        
        if [[ "$result" == "200" ]]; then
            echo "  ✅ Completed"
            ((completed++))
        else
            echo "  ❌ Failed (HTTP $result)"
            ((failed++))
        fi
        
        # Rate limiting: pause between requests
        sleep 0.1
    done
    
    echo
    echo "Bulk operation complete:"
    echo "  Completed: $completed"
    echo "  Failed: $failed"
}

# Usage example
# bulk_complete_tasks "project-123" "active"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/taskmaster-integration.yml
name: TaskMaster Integration Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-api:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Test TaskMaster API
      env:
        TASKMASTER_API_KEY: ${{ secrets.TASKMASTER_API_KEY }}
        TASKMASTER_BASE_URL: https://api.taskmaster.dev
      run: |
        # Test API health
        response=$(curl -s -w "%{http_code}" -o response.json \
          -H "X-API-Key: $TASKMASTER_API_KEY" \
          "$TASKMASTER_BASE_URL/health")
        
        if [[ "$response" != "200" ]]; then
          echo "API health check failed"
          cat response.json
          exit 1
        fi
        
        echo "✅ API health check passed"
        
        # Test task creation
        task_response=$(curl -s -X POST "$TASKMASTER_BASE_URL/v2/tasks" \
          -H "X-API-Key: $TASKMASTER_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "title": "CI/CD Test Task",
            "description": "Created by GitHub Actions",
            "priority": "low"
          }')
        
        task_id=$(echo "$task_response" | jq -r '.data.id')
        
        if [[ "$task_id" == "null" || -z "$task_id" ]]; then
          echo "Task creation failed"
          echo "$task_response"
          exit 1
        fi
        
        echo "✅ Task created: $task_id"
        
        # Clean up test task
        curl -s -X DELETE "$TASKMASTER_BASE_URL/v2/tasks/$task_id" \
          -H "X-API-Key: $TASKMASTER_API_KEY"
        
        echo "✅ Test task cleaned up"
        
        rm -f response.json
```

### Jenkins Pipeline Example

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        TASKMASTER_API_KEY = credentials('taskmaster-api-key')
        TASKMASTER_BASE_URL = 'https://api.taskmaster.dev'
    }
    
    stages {
        stage('Test TaskMaster Integration') {
            steps {
                script {
                    // Test API connectivity
                    def healthResponse = sh(
                        script: """
                            curl -s -w "%{http_code}" -o health.json \
                              -H "X-API-Key: $TASKMASTER_API_KEY" \
                              "$TASKMASTER_BASE_URL/health"
                        """,
                        returnStdout: true
                    ).trim()
                    
                    if (healthResponse != "200") {
                        error("API health check failed with code: ${healthResponse}")
                    }
                    
                    echo "✅ API health check passed"
                    
                    // Create deployment tracking task
                    def taskResponse = sh(
                        script: """
                            curl -s -X POST "$TASKMASTER_BASE_URL/v2/tasks" \
                              -H "X-API-Key: $TASKMASTER_API_KEY" \
                              -H "Content-Type: application/json" \
                              -d '{
                                "title": "Deploy ${env.BUILD_TAG}",
                                "description": "Deployment tracking for build ${env.BUILD_NUMBER}",
                                "priority": "high",
                                "project_id": "deployment-project-id"
                              }'
                        """,
                        returnStdout: true
                    )
                    
                    def taskId = sh(
                        script: "echo '${taskResponse}' | jq -r '.data.id'",
                        returnStdout: true
                    ).trim()
                    
                    echo "✅ Deployment task created: ${taskId}"
                    env.DEPLOYMENT_TASK_ID = taskId
                }
            }
        }
        
        stage('Deploy') {
            steps {
                // Your deployment steps here
                echo "Deploying application..."
                
                // Update task progress
                sh """
                    curl -s -X PUT "$TASKMASTER_BASE_URL/v2/tasks/$DEPLOYMENT_TASK_ID" \
                      -H "X-API-Key: $TASKMASTER_API_KEY" \
                      -H "Content-Type: application/json" \
                      -d '{"status": "in_progress", "description": "Deployment in progress..."}'
                """
            }
        }
    }
    
    post {
        success {
            // Mark deployment task as completed
            sh """
                curl -s -X PUT "$TASKMASTER_BASE_URL/v2/tasks/$DEPLOYMENT_TASK_ID" \
                  -H "X-API-Key: $TASKMASTER_API_KEY" \
                  -H "Content-Type: application/json" \
                  -d '{"status": "completed", "description": "Deployment completed successfully"}'
            """
            echo "✅ Deployment task marked as completed"
        }
        
        failure {
            // Mark deployment task as failed
            sh """
                curl -s -X PUT "$TASKMASTER_BASE_URL/v2/tasks/$DEPLOYMENT_TASK_ID" \
                  -H "X-API-Key: $TASKMASTER_API_KEY" \
                  -H "Content-Type: application/json" \
                  -d '{"status": "blocked", "description": "Deployment failed - requires investigation"}'
            """
            echo "❌ Deployment task marked as blocked due to failure"
        }
        
        cleanup {
            sh "rm -f health.json"
        }
    }
}
```

## Performance Tips

### Optimize API Calls

```bash
# Use field selection to reduce payload size
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks?fields=id,title,status&limit=100"

# Use larger page sizes for bulk operations
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks?limit=500"

# Use specific filters to reduce dataset
curl -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks?status=active&due_date_from=2025-09-20"
```

### Connection Reuse

```bash
# Use curl's connection reuse with --keepalive
curl --keepalive-time 60 \
  -H "X-API-Key: $TASKMASTER_API_KEY" \
  "$TASKMASTER_BASE_URL/v2/tasks"

# Use curl's config file for repeated options
echo 'header = "X-API-Key: '$TASKMASTER_API_KEY'"' > .curlrc
echo 'header = "Content-Type: application/json"' >> .curlrc
echo 'url = "'$TASKMASTER_BASE_URL'"' >> .curlrc

# Now you can use simplified commands
curl /v2/tasks
curl -X POST /v2/tasks -d '{"title": "New task"}'
```

This comprehensive cURL guide provides everything needed for command-line interaction with the TaskMaster API, from basic operations to advanced automation and CI/CD integration.