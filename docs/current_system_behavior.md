# TaskMaster Current System Behavior Documentation

**Generated**: 2025-09-18  
**Purpose**: Document current system behavior patterns for YOLO upgrade baseline

## Task Assignment Patterns

### Assignment Service Behavior

From the bulk assignment test:

1. **Assignment Strategy**: "pool-by-pool" - processes one time pool at a time
2. **Assignment Identifier**: Uses "auto_task_change" for automatic assignments
3. **Partial Assignment Support**: Can allocate partial task time to pools
4. **Pool Selection**: Appears to use chronological order (earliest pools first)

### Task Queue Prioritization

Based on task queue analysis:

1. **Priority Scoring Formula**: 
   - Overdue tasks get highest scores (255.0 for 1 day overdue)
   - Active tasks score lower (145.0 for on-time tasks)
   - Formula appears to factor in: urgency, priority level, and days overdue

2. **Task Filtering**:
   - Excludes completed tasks
   - Includes snoozed tasks in main queue
   - Tracks blocking reasons for non-schedulable tasks

## Time Pool Management

### Pool Structure
```json
{
  "pool_date": "2025-09-19",
  "start_time": "time value",
  "total_minutes": 480,
  "allocated_minutes": 382,
  "available_minutes": 98
}
```

### Pool Generation
- Creates pools for next 7 days by default
- Multiple pools per day possible
- Pool capacity tracked in minutes

## Task Lifecycle

### Task States
1. **active** - Ready for scheduling
2. **snoozed** - Temporarily hidden until snoozed_until time
3. **completed** - Finished tasks

### Recurring Task Handling
- Recurring tasks auto-snooze after completion
- Snooze duration = recurrence_days
- Never marked as truly completed (allows re-emergence)

### Task Dependencies
- Supports parent_task_id relationships
- Dependency checking via depends_on_task_ids (JSON array)
- Root tasks = no dependencies OR all dependencies completed

## API Response Patterns

### Success Response Structure
```json
{
  "success": true,
  "message": "Human-readable summary",
  "data_field": "varies by endpoint",
  "count": "number of items"
}
```

### Error Response Structure
```json
{
  "success": false,
  "message": "Error description",
  "error": "Technical error details"
}
```

### Pagination
- No pagination observed in current implementation
- All endpoints return complete datasets

## Assignment Rules

### Task Eligibility
Tasks must meet these criteria for assignment:
1. Not completed
2. Not fully assigned (remaining_minutes > 0)
3. Can be scheduled (not blocked)
4. Weather requirements met (if specified)

### Assignment Constraints
1. Cannot exceed pool available capacity
2. Respects task duration requirements
3. Maintains assignment history/audit trail
4. Supports manual and automatic assignment

## Data Consistency

### Timestamps
- All entities use UTC timestamps
- created_at and updated_at on all models
- Assignment tracking with assigned_at

### ID Generation
- Uses UUID strings for all entity IDs
- Format: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

### Relationships
- Foreign keys maintained via string UUIDs
- Soft relationships (no cascading deletes observed)

## Background Processing

### Triggers
1. Task changes trigger assignment regeneration
2. 5-second delay before regeneration (debouncing)
3. Background service handles pool and assignment updates

### Job Management
- Uses fixed job IDs to prevent duplicates
- Scheduler-based architecture (APScheduler)

## Performance Characteristics

### Current Bottlenecks
1. **Database Access**: ~2 second overhead on all queries
2. **No Caching**: Every request hits database
3. **Full Table Scans**: No evidence of index usage
4. **Large Payloads**: Complete object graphs returned

### Resource Usage
- Single-threaded Flask development server
- SQLite database (file-based)
- No connection pooling
- Synchronous request handling

## Edge Cases Handled

1. **Circular Dependencies**: JSON parsing with error handling
2. **Null Values**: Graceful handling of missing data
3. **Date Boundaries**: Timezone-aware date comparisons
4. **Concurrent Updates**: Last-write-wins strategy

## Missing Features

1. **Batch Operations**: No bulk task updates
2. **Undo/Redo**: No assignment rollback
3. **Optimization**: No smart scheduling algorithms
4. **Notifications**: No real-time updates
5. **Audit Trail**: Limited to basic timestamps

## Integration Points

### Weather Service
- Integrated for outdoor task scheduling
- Checks weather suitability for pools

### Background Service
- Handles time pool regeneration
- Manages automatic task assignments
- Processes recurring task updates

## Configuration

### Defaults
- Bulk assignment: 7 days ahead
- Task duration: 30 minutes default
- Priority: "medium" default
- Urgency: 5 (scale of 1-10)

This documentation serves as the baseline for the YOLO upgrade implementation.