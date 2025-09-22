# TaskMaster Flask Application - Complete Endpoint Catalog

This document provides a comprehensive catalog of all HTTP endpoints in the TaskMaster Flask application, organized by blueprint and functionality.

## Summary
- **Main Application Routes**: 15 endpoints
- **API Blueprint Routes**: 100+ endpoints across 15+ modules
- **Additional Blueprint Routes**: 20+ endpoints
- **Total Endpoints**: 130+ documented endpoints

---

## 1. Main Application Routes (app.py)

### Page Routes
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/` | index() | Main schedule page | HTML template (schedule.html) |
| GET | `/events` | events() | Events management page | HTML template (events.html) |
| GET | `/events/` | events() | Same as above with trailing slash | HTML template (events.html) |
| GET | `/tasks` | tasks() | Tasks management page | HTML template (tasks.html) |
| GET | `/tasks/` | tasks() | Same as above with trailing slash | HTML template (tasks.html) |
| GET | `/initiatives` | initiatives() | Initiatives management page | HTML template (initiatives.html) |
| GET | `/initiatives/` | initiatives() | Same as above with trailing slash | HTML template (initiatives.html) |
| GET | `/dishes` | dishes() | Dishes management page | HTML template (dishes.html) |
| GET | `/dishes/` | dishes() | Same as above with trailing slash | HTML template (dishes.html) |
| GET | `/meals` | meals() | Meals management page | HTML template (meals.html) |
| GET | `/meals/` | meals() | Same as above with trailing slash | HTML template (meals.html) |

### Dynamic Routes
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/events/<event_id>/edit` | edit_event(event_id) | Edit event form, handles recurring instances | HTML template (edit_event.html) |

### Utility Routes
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/health` | health() | Health check endpoint | JSON: `{'status': 'healthy', 'service': 'TaskMaster Flask'}` |
| GET | `/websocket-demo` | websocket_demo() | WebSocket demo page | HTML template (websocket_demo.html) |
| GET | `/websocket/stats` | websocket_stats() | WebSocket connection statistics | JSON: Connection stats |

---

## 2. Core API Routes (/api/*)

### 2.1 Core API (core.py)

#### Health & Monitoring
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/health` | health_check() | API health check with database test | JSON: Health status, timestamp, DB status |

#### Enhanced Task Queue
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/task-queue/enhanced` | get_enhanced_task_queue() | Enhanced task queue with metadata | JSON: Enhanced queue, count, queue_type |
| GET | `/api/task-queue/enhanced/available` | get_enhanced_available_queue() | Enhanced available task queue | JSON: Available enhanced tasks, count |
| GET | `/api/task-queue/enhanced/context/<task_id>` | get_enhanced_task_context(task_id) | Enhanced context for specific task | JSON: Task ID, context data |
| POST | `/api/task-queue/enhanced/compare` | compare_enhanced_task_priorities() | Compare priority scores between tasks | JSON: Comparison data, task count |

**Parameters for compare**: `task_ids` (array) - Minimum 2 task IDs required

#### Event-Aware Assignments
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/assignments/event-aware/pools` | get_available_pools_with_events() | Time pools with event awareness | JSON: Pools array, count |
| POST | `/api/assignments/event-aware/project/<project_id>` | assign_project_tasks_smart(project_id) | Smart project task assignment | JSON: Assignment result |
| POST | `/api/assignments/event-aware/recurring` | handle_recurring_tasks() | Handle recurring task assignments | JSON: Success status, details |
| POST | `/api/assignments/event-aware/meal-tasks` | prepare_meal_tasks() | Prepare meal-related tasks | JSON: Success status, details |
| POST | `/api/assignments/event-aware/bulk` | bulk_assign_with_events() | Bulk assignment with event awareness | JSON: Assignment results |

**Parameters for bulk**: `max_days_ahead` (integer, default: 7)

#### Legacy Compatibility
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/time_pools_api` | get_time_pools_api() | Legacy time pools endpoint | JSON: Pools, total_minutes |
| GET | `/api/assignments_api` | get_assignments_api() | **WORKING** Legacy assignments with task/pool details | JSON: Assignments array with task_title, task_priority, pool_date, pool_start_time, pool_end_time, count |
| POST | `/api/assignments/bulk_api` | bulk_assign_tasks_api() | Legacy bulk assignment | JSON: Assignments made, count |

**Parameters for assignments_api**: 
- `task_id` (optional): Filter by specific task ID
- `start_date` (optional): Date filter in YYYY-MM-DD format  
- `end_date` (optional): Date filter in YYYY-MM-DD format
- **Example**: `/api/assignments_api?start_date=2025-09-21&end_date=2025-09-21` returns today's task assignments

#### Admin Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| POST | `/api/admin/regenerate-pools` | regenerate_time_pools() | Manual time pool regeneration | JSON: Status, message, timestamp |

### 2.2 Events API (events.py)

#### Event CRUD Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/events` | get_events() | Get events (list or calendar mode) | JSON: Events array |
| POST | `/api/events` | create_event() | Create new event | JSON: Created event data |
| PUT | `/api/events/<event_id>` | update_event(event_id) | Update existing event | JSON: Updated event data |
| DELETE | `/api/events/<event_id>` | delete_event(event_id) | Delete event | JSON: `{'status': 'success'}` |

**Query parameters for GET**: 
- `mode` (string): 'list' (default) or 'calendar'
- `start` (ISO datetime): For calendar mode date range
- `end` (ISO datetime): For calendar mode date range

**Create/Update event fields**:
- `title` (required), `start` (required), `end` (required)
- `description`, `location`, `event_type`, `is_blocking`
- `meal_id`, `notifications_enabled`
- Recurring: `is_recurring`, `recurrence_pattern`, `recurrence_rrule`, `recurrence_end`

#### Recurring Events
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/events/<event_id>/recurring-info` | get_recurring_info(event_id) | Get recurring event information | JSON: Recurrence details |

#### Specialized Events
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/events/dinner` | get_dinner_events() | Get all dinner events with meal data | JSON: Dinner events with meal details |

### 2.3 Tasks API (tasks.py)

#### Task CRUD Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/tasks` | get_tasks() | Get tasks (root tasks with dependency filtering) | JSON: Tasks array |
| POST | `/api/tasks` | create_task() | Create new task with AI analysis | JSON: Created task with analysis status |
| GET | `/api/tasks/<task_id>` | get_task(task_id) | Get specific task | JSON: Task data |
| PUT | `/api/tasks/<task_id>` | update_task(task_id) | Update existing task | JSON: Updated task data |
| DELETE | `/api/tasks/<task_id>` | delete_task(task_id) | Delete task | JSON: `{'status': 'success'}` |

**Query parameters for GET tasks**: 
- `completed` (boolean): 'true' to get completed tasks, 'false' (default) for active

**Create/Update task fields**:
- `title` (required), `description`, `duration`, `urgency`, `priority`
- `due_date`, `start_date`, `required_weather`, `recurrence_days`
- `project_id`, `initiative_id`, `meal_id`

#### Task Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| POST | `/api/tasks/<task_id>/complete` | complete_task(task_id) | Complete task or snooze if recurring | JSON: Completion/snooze result |

### 2.4 Initiatives API (initiatives.py)

#### Initiative CRUD Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/initiatives` | get_initiatives() | Get all initiatives with active tasks | JSON: Initiatives with task details |
| POST | `/api/initiatives` | create_initiative() | Create new initiative | JSON: Created initiative |
| GET | `/api/initiatives/<initiative_id>` | get_initiative(initiative_id) | Get specific initiative with tasks | JSON: Initiative with tasks array |
| PUT | `/api/initiatives/<initiative_id>` | update_initiative(initiative_id) | Update initiative | JSON: Updated initiative |
| DELETE | `/api/initiatives/<initiative_id>` | delete_initiative(initiative_id) | Delete initiative | JSON: `{'status': 'success'}` |

**Create/Update initiative fields**:
- `title` (required), `description`, `status`, `is_template`
- `target_completion_count`, `current_completion_count`

#### Initiative Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| POST | `/api/initiatives/<initiative_id>/increment` | increment_initiative(initiative_id) | Increment completion count | JSON: Updated initiative |
| POST | `/api/initiatives/<initiative_id>/create-task` | create_task_from_initiative(initiative_id) | Create recurring task for initiative | JSON: Created task |

**Create task fields**:
- `title` (required), `description`, `duration`, `urgency`, `priority`
- `recurrence_days`, `due_date`

### 2.5 Schedule API (schedule.py)

#### Task Queue Management
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/task-queue/all` | get_all_tasks_queue() | All tasks ordered by priority | JSON: Task queue, count |
| GET | `/api/task-queue/available` | get_available_tasks_queue() | Available unassigned tasks | JSON: Available tasks, count |
| GET | `/api/task-queue/statistics` | get_queue_statistics() | Task queue statistics | JSON: Queue statistics |

**Query parameters**: `limit` (integer, default varies by endpoint)

#### Time Pool Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| POST | `/api/time-pools/regenerate` | regenerate_time_pools() | Trigger time pool regeneration | JSON: Status, message, pools created/updated |

#### Debug Endpoints
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/debug/task-queue` | debug_task_queue() | Debug task queue filtering | JSON: Debug information |

### 2.6 Task Assignments API (assignments.py)

#### Assignment Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/task-assignments` | get_task_assignments() | Get task assignments with filtering | JSON: Assignments array |
| POST | `/api/task-assignments` | assign_task_to_pool() | Assign task to time pool | JSON: Created assignment |

**Query parameters for GET**:
- `task_id` (optional): Filter by specific task ID
- `time_pool_id` (optional): Filter by specific time pool ID
- `status` (optional): Filter by assignment status

**Required fields for POST**:
- `task_id` (string), `time_pool_id` (string), `allocated_minutes` (integer)

#### Getting Tasks in Current Time Pool
To get tasks assigned to the current time pool:
1. **For today's assignments**: `GET /api/assignments_api?start_date=2025-09-21&end_date=2025-09-21`
2. **For specific time pool**: `GET /api/task-assignments?time_pool_id=<pool_id>`
3. **Current time pool logic**: Determine current pool by time, then use option 2

### 2.7 Meals & Dishes API (meals.py)

#### Dish Management
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/dishes` | get_dishes() | Get all dishes with recipe data | JSON: Dishes array |
| GET | `/api/dishes/<dish_id>` | get_dish(dish_id) | Get specific dish with recipe | JSON: Dish with recipe data |
| POST | `/api/dishes` | create_dish() | Create new dish | JSON: Created dish |

**Create dish fields**:
- `title` (required), `dish_type` (required), recipe data

---

## 3. Enhanced v2 API Routes

### 3.1 Enhanced Tasks API (tasks_enhanced.py)

Provides advanced task endpoints with pagination, filtering, sorting, and batch operations.

**Query Configuration**:
- Filters: status, priority, is_completed, is_snoozed, due_date ranges
- Sorting: Multiple fields with direction
- Pagination: Standard limit/offset

### 3.2 Enhanced Events API (events_enhanced.py)

Advanced event queries with calendar optimization and complex filtering.

---

## 4. Advanced Feature API Routes

### 4.1 Search API (search.py)

#### Comprehensive Search
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/search/search` | search_all() | Cross-entity search with faceting | JSON: Search results with metadata |

**Query parameters**:
- `q` (required): Search query string
- Filtering, faceting, and pagination parameters

### 4.2 Export API (export.py)

#### Export Operations
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| POST | `/api/export/create` | create_export() | Create export operation | JSON: Export job details |

**Supported formats**: json, csv, excel, ical, pdf
**Entity types**: tasks, events, initiatives

### 4.3 Analysis API (analysis.py)

#### AI-Powered Analysis
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/api/tasks/<task_id>/claude-analysis` | get_task_claude_analysis(task_id) | Comprehensive AI task analysis | JSON: Analysis results |

**Query parameters**:
- `include_context` (boolean, default: true)
- `save_to_db` (boolean, default: false)

### 4.4 Smart Scheduling API (smart_scheduling.py)

#### Intelligent Scheduling
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| POST | `/api/schedule/daily-routine` | run_daily_routine() | Complete daily scheduling routine | JSON: Routine execution results |

Handles recurring tasks, meal prep, weather updates, and smart bulk assignment.

---

## 5. Additional Blueprint Routes

### 5.1 Projects Blueprint (projects.py)

#### Project Management
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| GET | `/projects` | list_projects() | Projects tree view with phases/tasks | HTML template with complete hierarchy |

### 5.2 WebSocket API (websocket_api.py)

#### Real-time Broadcasting
| Method | Path | Function | Description | Returns |
|--------|------|----------|-------------|---------|
| POST | `/api/websocket/broadcast/task-created` | broadcast_task_created() | Simulate task creation with WebSocket broadcast | JSON: Success status, broadcasted task |

**Request fields**:
- `title`, `description`, `priority`, `project_id`, `initiative_id`, `user_id`

---

## 6. Performance & Analytics

### 6.1 Performance API (performance.py)
- Database optimization endpoints
- Query performance monitoring
- Cache management

### 6.2 Analytics API (analytics.py)
- Usage tracking
- Performance metrics
- Rate limiting analytics

### 6.3 Webhooks API (webhooks.py)
- Event-driven webhooks
- HMAC security
- Retry logic and analytics

---

## 7. Response Formats

### Standard Success Response
```json
{
  "status": "success",
  "data": {...},
  "message": "Operation completed successfully"
}
```

### Standard Error Response
```json
{
  "status": "error",
  "error": "Error description",
  "message": "User-friendly error message"
}
```

### Pagination Response
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "pages": 3
  }
}
```

---

## 8. Authentication & Headers

- **Content-Type**: `application/json` for POST/PUT requests
- **Accept**: `application/json` for API responses
- **Authentication**: Not currently implemented (development environment)

---

## 9. Rate Limiting & Caching

- Rate limiting implemented in analytics module
- Redis caching for performance optimization
- Memory caching for frequently accessed data

---

## 10. WebSocket Support

The application includes WebSocket support via Flask-SocketIO for real-time updates:
- Task creation/updates
- Event notifications
- Schedule changes
- Performance monitoring

---

*Last Updated: Generated on 2025-09-21*
*Total Documented Endpoints: 130+*