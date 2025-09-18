# TaskMaster Advanced Priority Services

This directory contains the advanced priority scoring services for the TaskMaster YOLO upgrade.

## Services

### ProjectAwarePriorityService

**File**: `project_aware_priority_service.py`

The main priority scoring engine that implements advanced task prioritization based on:

- **Time Criticality** (0-300 points): Overdue tasks, due dates, urgency levels
- **Project Context** (0-200 points): Project priority, phase deadlines, active status  
- **Dependency Impact** (0-200 points): Tasks that block other tasks get higher priority
- **Progress Momentum** (0-150 points): Continue work on partially completed tasks/projects
- **Recurring Task Timing** (0-100 points): Recurring task schedule adherence
- **Meal Preparation Timing** (0-150 points): Meal tasks prioritized near serve times
- **Quick Wins** (0-50 points): Short, easy tasks for momentum

#### Key Methods

```python
# Calculate total priority score for a task
score = service.calculate_priority_score(task_dict, all_tasks_list)

# Get comprehensive task context with relationships
context = service.get_task_context(task_id)
```

### EnhancedTaskQueueService

**File**: `enhanced_task_queue_service.py`

Wrapper service that integrates the ProjectAwarePriorityService with the existing Flask task queue system.

#### Key Methods

```python
# Get enhanced task queue with advanced priority scoring
queue = service.get_enhanced_task_queue(limit=50)

# Get only available (unassigned) tasks
available = service.get_available_enhanced_queue(limit=20)

# Deep analysis of a specific task's priority factors
analysis = service.get_task_context_analysis(task_id)

# Compare multiple tasks' priority scores and factors
comparison = service.compare_task_priorities([task_id1, task_id2, task_id3])
```

## Integration Examples

### Basic Priority Queue

```python
from flask_app.services.enhanced_task_queue_service import get_enhanced_task_queue_service

service = get_enhanced_task_queue_service()
enhanced_queue = service.get_enhanced_task_queue(limit=20)

for task in enhanced_queue:
    print(f"{task['title']}: {task['enhanced_priority_score']:.1f} points")
```

### Task Context Analysis

```python
from flask_app.services.project_aware_priority_service import get_project_aware_priority_service

service = get_project_aware_priority_service()
context = service.get_task_context('task-id-123')

print(f"Task: {context['task']['title']}")
print(f"Project: {context['project']['title'] if context['project'] else 'None'}")
print(f"Blocking {len(context['blocking_tasks'])} other tasks")
```

### API Route Integration

```python
from flask import Blueprint, jsonify
from flask_app.services.enhanced_task_queue_service import get_enhanced_task_queue_service

@app.route('/api/tasks/enhanced-queue')
def get_enhanced_queue():
    service = get_enhanced_task_queue_service()
    queue = service.get_enhanced_task_queue(limit=50)
    return jsonify({
        'tasks': queue,
        'count': len(queue)
    })

@app.route('/api/tasks/<task_id>/analysis')
def get_task_analysis(task_id):
    service = get_enhanced_task_queue_service()
    analysis = service.get_task_context_analysis(task_id)
    return jsonify(analysis)
```

## Priority Score Breakdown

The enhanced priority scoring provides much more nuanced prioritization than simple urgency levels:

### Example Scores

- **Overdue High-Priority Task**: ~400-600 points
- **Due Today with Dependencies**: ~300-450 points  
- **Meal Prep Near Serve Time**: ~200-350 points
- **Recurring Task Overdue**: ~150-250 points
- **Standard Task**: ~50-150 points
- **Blocked Task**: ~0-100 points (negative dependency impact)

### Component Analysis

Each task's priority is broken down into components for transparency:

```python
analysis = service.get_task_context_analysis(task_id)
components = analysis['priority_analysis']['components']

print(f"Time Criticality: {components['time_criticality']:.1f}")
print(f"Project Context: {components['project_urgency']:.1f}")  
print(f"Dependency Impact: {components['dependency_impact']:.1f}")
print(f"Progress Momentum: {components['progress_momentum']:.1f}")
```

## Edge Cases Handled

- **Missing Data**: Service handles null/missing fields gracefully
- **Circular Dependencies**: Dependency analysis prevents infinite loops
- **Invalid Dates**: Date parsing is robust with fallbacks
- **Database Errors**: All database queries include error handling
- **JSON Parsing**: Handles both string and object forms of JSON fields

## Performance Considerations

- **Caching**: Service instances are singletons to avoid recreation overhead
- **Query Optimization**: Minimizes database queries through batching
- **Memory Efficient**: Only loads necessary data for calculations
- **Logging**: Comprehensive logging for debugging without performance impact

## Future Enhancements

The service architecture supports easy extension for:

- **Machine Learning**: Historical completion patterns
- **Context Awareness**: Location, time of day, energy levels
- **Team Collaboration**: Multi-user priority coordination
- **Smart Scheduling**: Automatic optimal time slot selection