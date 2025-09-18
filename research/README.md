# TaskMaster Research Directory

This directory contains essential files copied from the TaskMaster project to understand the task queue and assignment system.

## Directory Structure

```
research/
├── README.md                      # This file
├── models.py                      # Flask SQLAlchemy models (current)
├── app.py                         # Flask main application
├── task_queue_service.py          # Flask task queue service (current)
├── assignment_service.py          # Flask assignment service (current)
├── weather_service.py             # Flask weather service (current)
├── test_performance.py            # Performance testing
├── routes/                        # Flask API routes (current)
│   ├── api.py                     # Main API endpoints
│   ├── tasks.py                   # Task-specific routes
│   └── projects.py                # Project-specific routes
├── schemas/                       # Legacy FastAPI schemas (for reference)
│   ├── task_schemas.py            # Task data validation schemas
│   ├── schedule_schemas.py        # Schedule data schemas
│   └── weather_schemas.py         # Weather data schemas
├── legacy_fastapi/               # Legacy FastAPI implementation (for reference)
│   ├── task_queue_service.py     # Original task queue implementation
│   ├── weather_service.py        # Original weather implementation
│   ├── task_queue.py              # Task queue API routes
│   ├── tasks.py                   # Task API routes
│   └── schedule_generation.py    # Schedule generation logic
├── legacy_models/                # Legacy FastAPI models (for reference)
│   ├── base_model.py             # Base model with common fields
│   ├── task_model.py             # Comprehensive task model
│   └── schedule_model.py         # Schedule and time pool models
└── tests/                        # Test files for insights
    ├── test_task_queue_system.py # Task queue system tests
    └── test_assignment_triggers.py # Assignment trigger tests
```

## Key Files for Task Queue Analysis

### Current Flask Implementation
1. **models.py** - Current SQLAlchemy models including:
   - Task model with all fields and relationships
   - TimePool model for time availability
   - Assignment-related models
   - Project, Initiative models

2. **task_queue_service.py** - Current task queueing logic:
   - How tasks are prioritized and filtered
   - Queue organization methods
   - Current algorithms

3. **assignment_service.py** - Current assignment logic:
   - How tasks are assigned to time slots
   - Assignment criteria and rules

4. **weather_service.py** - Weather integration:
   - How weather affects task scheduling
   - Context detection for outdoor tasks

### Legacy FastAPI Implementation (Reference)
5. **legacy_fastapi/task_queue_service.py** - Original comprehensive implementation
6. **legacy_models/task_model.py** - Detailed task model with all possible fields
7. **legacy_models/schedule_model.py** - TimePool and scheduling models

### API Routes
8. **routes/api.py** - Current REST endpoints
9. **routes/tasks.py** - Task-specific endpoints
10. **legacy_fastapi/task_queue.py** - Original task queue API

### Schemas & Validation
11. **schemas/task_schemas.py** - Data validation patterns
12. **schemas/schedule_schemas.py** - Schedule data structures

## Next Steps for Research

1. **Analyze Current Models** (`models.py`)
   - Understand Task model fields and relationships
   - Identify TimePool structure and constraints
   - Map assignment-related models

2. **Study Task Queue Logic** (`task_queue_service.py`)
   - Current prioritization algorithms
   - Filtering and sorting mechanisms
   - Queue management strategies

3. **Examine Assignment Service** (`assignment_service.py`)
   - Assignment criteria and rules
   - Time slot allocation logic
   - Conflict resolution

4. **Compare with Legacy Implementation**
   - Review `legacy_fastapi/task_queue_service.py` for comprehensive patterns
   - Analyze `legacy_models/task_model.py` for all possible fields
   - Understand evolution from FastAPI to Flask

5. **Weather Integration Analysis** (`weather_service.py`)
   - How weather data influences scheduling
   - Context detection for indoor/outdoor tasks
   - Pattern recognition capabilities

6. **API Patterns** (`routes/`)
   - Current endpoint structure
   - User interaction patterns
   - Parameter handling

## Key Areas to Focus On

- **Prioritization Algorithms**: How tasks are ranked and ordered
- **Time Allocation**: How time pools are managed and assigned
- **Context Awareness**: Weather, user preferences, historical data
- **Dependency Management**: Task relationships and blocking
- **Performance Optimization**: Queue efficiency and response times
- **User Customization**: Configurable parameters and preferences

This research foundation provides comprehensive insight into both current and legacy implementations for developing an enhanced task queue and assignment system.