# TaskMaster Python SDK and Examples

Complete Python integration for the TaskMaster API with async support, type hints, and comprehensive error handling.

## Installation

```bash
pip install taskmaster-api
```

Or install from source:

```bash
git clone https://github.com/taskmaster/python-sdk
cd python-sdk
pip install -e .
```

## Quick Start

```python
from taskmaster import TaskMasterClient

# Initialize client
client = TaskMasterClient(api_key="tk_live_abc123...")

# Create a task
task = client.tasks.create(
    title="Complete project documentation",
    description="Write comprehensive API documentation",
    priority="high",
    urgency=8,
    duration=120,
    due_date="2025-09-25"
)

print(f"Created task: {task.id}")

# List active high-priority tasks
tasks = client.tasks.list(
    status="active",
    priority=["high", "urgent"],
    sort="urgency:desc",
    limit=20
)

for task in tasks:
    print(f"- {task.title} (Urgency: {task.urgency})")
```

## SDK Features

### ✅ Complete API Coverage
- Tasks API v2 with filtering, sorting, pagination
- Events API v2 with calendar optimization
- Search API with faceting and suggestions
- Export API with multiple formats
- WebSocket API for real-time updates
- Analytics and Webhooks

### ✅ Modern Python Features
- Type hints for better IDE support
- Async/await support for non-blocking operations
- Dataclasses for response objects
- Context managers for resource cleanup

### ✅ Production Ready
- Comprehensive error handling
- Automatic retry with exponential backoff
- Rate limiting with respect for API limits
- Logging integration
- Connection pooling

### ✅ Developer Experience
- Intuitive API design
- Comprehensive documentation
- Rich error messages
- Debug mode for development

## Basic Usage

### Authentication

```python
from taskmaster import TaskMasterClient

# API Key authentication (recommended)
client = TaskMasterClient(api_key="tk_live_abc123...")

# Session token authentication
client = TaskMasterClient(session_token="sess_xyz789...")

# Custom base URL (for development)
client = TaskMasterClient(
    api_key="tk_test_dev123...",
    base_url="http://localhost:5000/api"
)
```

### Tasks Management

```python
# Create a task
task = client.tasks.create(
    title="Implement user authentication",
    description="Add login, registration, and password reset",
    priority="urgent",
    urgency=9,
    duration=240,
    due_date="2025-09-22",
    project_id="proj-123",
    required_context=["computer", "internet"],
    equipment_needed=["laptop"]
)

# Get task by ID
task = client.tasks.get(task.id)

# Update task
updated_task = client.tasks.update(
    task.id,
    status="in_progress",
    urgency=10,
    description="Added OAuth integration requirements"
)

# List tasks with advanced filtering
tasks = client.tasks.list(
    status="active",
    priority=["high", "urgent"],
    due_date_from="2025-09-20",
    due_date_to="2025-09-30",
    urgency_min=7,
    sort="urgency:desc,created_at:asc",
    limit=50,
    offset=0
)

# Search tasks
search_results = client.tasks.search(
    query="authentication security",
    limit=10
)

# Complete task
completed_task = client.tasks.complete(task.id)

# Delete task
client.tasks.delete(task.id)
```

### Batch Operations

```python
# Create multiple tasks
tasks_data = [
    {
        "title": "Setup CI/CD pipeline",
        "priority": "high",
        "duration": 180
    },
    {
        "title": "Write unit tests",
        "priority": "medium", 
        "duration": 240
    },
    {
        "title": "Update documentation",
        "priority": "low",
        "duration": 60
    }
]

batch_result = client.tasks.create_batch(tasks_data)
print(f"Created {len(batch_result.created)} tasks")
if batch_result.errors:
    print(f"Errors: {batch_result.errors}")
```

### Events Management

```python
from datetime import datetime, timedelta

# Create an event
start_time = datetime.now() + timedelta(days=1)
end_time = start_time + timedelta(hours=2)

event = client.events.create(
    title="Team Planning Meeting",
    description="Weekly team planning and status update",
    start=start_time,
    end=end_time,
    location="Conference Room A",
    event_type="timed",
    is_blocking=True,
    notifications_enabled=True
)

# Get calendar events for a date range
events = client.events.get_calendar(
    start="2025-09-20",
    end="2025-09-27"
)

# List events with filtering
events = client.events.list(
    event_type=["timed", "all_day"],
    is_blocking=True,
    start_from="2025-09-20T00:00:00Z",
    start_to="2025-09-27T23:59:59Z"
)
```

### Search Integration

```python
# Comprehensive search
results = client.search.search(
    query="project management urgent",
    types=["tasks", "events", "projects"],
    include_facets=True,
    limit=20
)

print(f"Found {results.total_count} results")
for result in results.results:
    print(f"- {result.title} ({result.type})")

# Search suggestions
suggestions = client.search.get_suggestions("proj", limit=5)
print("Suggestions:", suggestions)

# Analyze query
analysis = client.search.analyze_query("status:active priority:high urgent")
print("Query analysis:", analysis)
```

## Async Support

```python
import asyncio
from taskmaster import AsyncTaskMasterClient

async def main():
    # Initialize async client
    client = AsyncTaskMasterClient(api_key="tk_live_abc123...")
    
    # Async operations
    task = await client.tasks.create(
        title="Async task creation",
        priority="high"
    )
    
    tasks = await client.tasks.list(
        status="active",
        limit=10
    )
    
    # Close client when done
    await client.close()

# Run async code
asyncio.run(main())
```

### Async Context Manager

```python
async def main():
    async with AsyncTaskMasterClient(api_key="tk_live_abc123...") as client:
        # Client automatically closed when exiting context
        task = await client.tasks.create(
            title="Context managed task",
            priority="medium"
        )
        
        return task

task = asyncio.run(main())
```

## WebSocket Integration

```python
import asyncio
from taskmaster import TaskMasterWebSocket

async def handle_task_created(data):
    print(f"New task created: {data['task']['title']}")

async def handle_task_completed(data):
    print(f"Task completed: {data['task']['title']}")

async def main():
    # Initialize WebSocket client
    ws = TaskMasterWebSocket(
        url="wss://api.taskmaster.dev/ws",
        api_key="tk_live_abc123..."
    )
    
    # Register event handlers
    ws.on('task_created', handle_task_created)
    ws.on('task_completed', handle_task_completed)
    
    # Connect and subscribe
    await ws.connect()
    await ws.subscribe(['tasks', 'notifications'])
    
    # Keep connection alive
    try:
        await ws.listen()  # Blocks until connection closes
    except KeyboardInterrupt:
        await ws.close()

asyncio.run(main())
```

## Error Handling

```python
from taskmaster import (
    TaskMasterClient,
    TaskMasterError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError
)

client = TaskMasterClient(api_key="tk_live_abc123...")

try:
    task = client.tasks.create(
        title="Test task",
        priority="invalid_priority"  # This will cause validation error
    )
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Field errors: {e.errors}")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except NotFoundError as e:
    print(f"Resource not found: {e.message}")
except TaskMasterError as e:
    print(f"API error: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

```python
from taskmaster import TaskMasterClient
from taskmaster.retry import RetryConfig

# Configure retry behavior
retry_config = RetryConfig(
    max_attempts=3,
    backoff_factor=2.0,
    max_backoff=60.0,
    retry_on_status=[429, 500, 502, 503, 504]
)

client = TaskMasterClient(
    api_key="tk_live_abc123...",
    retry_config=retry_config
)

# Client will automatically retry failed requests
task = client.tasks.create(title="Resilient task creation")
```

## Advanced Features

### Pagination Helpers

```python
# Automatic pagination
all_tasks = []
for page in client.tasks.list_paginated(status="active", limit=50):
    all_tasks.extend(page.data)
    print(f"Loaded page {page.meta.page} of {page.meta.total_pages}")

print(f"Total tasks loaded: {len(all_tasks)}")

# Generator for memory efficiency
def get_all_active_tasks():
    for task in client.tasks.iterate_all(status="active"):
        yield task

# Process tasks one by one without loading all into memory
for task in get_all_active_tasks():
    print(f"Processing task: {task.title}")
```

### Custom Session Configuration

```python
import requests
from taskmaster import TaskMasterClient

# Custom session with connection pooling
session = requests.Session()
session.mount('https://', requests.adapters.HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=3
))

client = TaskMasterClient(
    api_key="tk_live_abc123...",
    session=session
)
```

### Logging Integration

```python
import logging
from taskmaster import TaskMasterClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Client with logging
client = TaskMasterClient(
    api_key="tk_live_abc123...",
    debug=True  # Enables request/response logging
)

# Custom logger
client.set_logger(logger)
```

## Data Models

The SDK uses typed data models for better IDE support and validation:

```python
from taskmaster.models import Task, Event, SearchResult
from typing import List

# Type hints for better development experience
def process_tasks(tasks: List[Task]) -> None:
    for task in tasks:
        # IDE provides autocomplete for all task properties
        print(f"Task: {task.title}")
        print(f"Priority: {task.priority}")
        print(f"Due: {task.due_date}")
        print(f"Completed: {task.completed}")

# Search results are also typed
def process_search_results(results: List[SearchResult]) -> None:
    for result in results:
        print(f"Found: {result.title} ({result.type})")
        print(f"Relevance: {result.relevance_score}")
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from taskmaster import TaskMasterClient

@pytest.fixture
def client():
    return TaskMasterClient(api_key="tk_test_123")

@pytest.fixture
def mock_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "status": "success",
        "data": {
            "id": "task-123",
            "title": "Test Task",
            "priority": "high"
        }
    }
    return response

def test_create_task(client, mock_response):
    with patch('requests.Session.post', return_value=mock_response):
        task = client.tasks.create(title="Test Task", priority="high")
        
        assert task.id == "task-123"
        assert task.title == "Test Task"
        assert task.priority == "high"

def test_list_tasks_with_filtering(client):
    with patch('requests.Session.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "success",
            "data": [],
            "meta": {"total": 0, "limit": 20, "offset": 0}
        }
        
        tasks = client.tasks.list(status="active", priority=["high"])
        
        # Verify correct API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "status=active" in kwargs['params']
        assert "priority=high" in kwargs['params']
```

### Integration Tests

```python
import pytest
from taskmaster import TaskMasterClient

@pytest.fixture
def client():
    # Use test API key and test environment
    return TaskMasterClient(
        api_key="tk_test_integration_key",
        base_url="https://test-api.taskmaster.dev"
    )

@pytest.mark.integration
def test_full_task_lifecycle(client):
    # Create task
    task = client.tasks.create(
        title="Integration Test Task",
        priority="medium"
    )
    assert task.id is not None
    
    # Retrieve task
    retrieved_task = client.tasks.get(task.id)
    assert retrieved_task.title == "Integration Test Task"
    
    # Update task
    updated_task = client.tasks.update(
        task.id,
        priority="high",
        urgency=8
    )
    assert updated_task.priority == "high"
    assert updated_task.urgency == 8
    
    # Delete task
    client.tasks.delete(task.id)
    
    # Verify deletion
    with pytest.raises(NotFoundError):
        client.tasks.get(task.id)
```

## Framework Integrations

### Django Integration

```python
# django_integration.py
from django.conf import settings
from taskmaster import TaskMasterClient

# Initialize client as singleton
client = TaskMasterClient(api_key=settings.TASKMASTER_API_KEY)

# Django model integration
from django.db import models

class DjangoTask(models.Model):
    taskmaster_id = models.CharField(max_length=36, unique=True)
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20)
    
    def sync_to_taskmaster(self):
        """Sync Django model to TaskMaster"""
        if self.taskmaster_id:
            # Update existing task
            client.tasks.update(
                self.taskmaster_id,
                title=self.title,
                status=self.status
            )
        else:
            # Create new task
            task = client.tasks.create(
                title=self.title,
                status=self.status
            )
            self.taskmaster_id = task.id
            self.save()
    
    def sync_from_taskmaster(self):
        """Sync from TaskMaster to Django model"""
        if self.taskmaster_id:
            task = client.tasks.get(self.taskmaster_id)
            self.title = task.title
            self.status = task.status
            self.save()
```

### Flask Integration

```python
# flask_integration.py
from flask import Flask, jsonify, request
from taskmaster import TaskMasterClient

app = Flask(__name__)
client = TaskMasterClient(api_key=app.config['TASKMASTER_API_KEY'])

@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    # Get query parameters
    status = request.args.get('status')
    priority = request.args.getlist('priority')
    limit = int(request.args.get('limit', 20))
    
    # Query TaskMaster API
    tasks = client.tasks.list(
        status=status,
        priority=priority,
        limit=limit
    )
    
    return jsonify({
        'tasks': [task.to_dict() for task in tasks.data],
        'meta': tasks.meta.to_dict()
    })

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    
    try:
        task = client.tasks.create(**data)
        return jsonify(task.to_dict()), 201
    except ValidationError as e:
        return jsonify({'error': e.message, 'errors': e.errors}), 422

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI Integration

```python
# fastapi_integration.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from taskmaster import TaskMasterClient, ValidationError

app = FastAPI()

def get_taskmaster_client():
    return TaskMasterClient(api_key="tk_live_abc123...")

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    urgency: int = 5
    duration: Optional[int] = None

@app.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[List[str]] = None,
    limit: int = 20,
    client: TaskMasterClient = Depends(get_taskmaster_client)
):
    tasks = client.tasks.list(
        status=status,
        priority=priority,
        limit=limit
    )
    return {
        "tasks": [task.to_dict() for task in tasks.data],
        "meta": tasks.meta.to_dict()
    }

@app.post("/tasks")
async def create_task(
    task_data: TaskCreate,
    client: TaskMasterClient = Depends(get_taskmaster_client)
):
    try:
        task = client.tasks.create(**task_data.dict())
        return task.to_dict()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors)
```

## Environment Configuration

```python
# config.py
import os
from taskmaster import TaskMasterClient

# Environment-based configuration
def get_client():
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        return TaskMasterClient(
            api_key=os.getenv('TASKMASTER_PROD_API_KEY'),
            base_url="https://api.taskmaster.dev"
        )
    elif env == 'staging':
        return TaskMasterClient(
            api_key=os.getenv('TASKMASTER_STAGING_API_KEY'),
            base_url="https://staging-api.taskmaster.dev"
        )
    else:  # development
        return TaskMasterClient(
            api_key=os.getenv('TASKMASTER_DEV_API_KEY'),
            base_url="http://localhost:5000/api",
            debug=True
        )

# Usage
client = get_client()
```

## Performance Tips

### 1. Use Batch Operations

```python
# Instead of creating tasks one by one
tasks_data = [{"title": f"Task {i}"} for i in range(100)]
batch_result = client.tasks.create_batch(tasks_data)

# Instead of multiple API calls
task_ids = ["task-1", "task-2", "task-3"]
tasks = client.tasks.get_batch(task_ids)
```

### 2. Optimize Pagination

```python
# Use appropriate page sizes
tasks = client.tasks.list(limit=100)  # Larger pages for bulk processing

# Use field selection to reduce payload
tasks = client.tasks.list(
    fields=["id", "title", "status"],  # Only needed fields
    limit=50
)
```

### 3. Connection Reuse

```python
# Reuse client instance across requests
client = TaskMasterClient(api_key="tk_live_abc123...")

# Don't create new clients repeatedly
for i in range(100):
    # Good: reuse client
    task = client.tasks.create(title=f"Task {i}")
    
    # Bad: new client each time
    # new_client = TaskMasterClient(api_key="...")
    # task = new_client.tasks.create(title=f"Task {i}")
```

This comprehensive Python SDK provides everything needed for robust TaskMaster API integration with modern Python features and best practices.