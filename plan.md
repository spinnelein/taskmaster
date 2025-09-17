Instructions for Claude to Fix Initiatives System
markdown# Fix Initiatives System - Recurring Task Generator

## Current Problem
The initiatives system has a circular import/recursion error caused by bidirectional relationships between InitiativeModel and TaskModel. The website crashes when trying to access initiatives.

## Your Task
Redesign and fix the initiatives system to work as a simple recurring task generator. When a task from an initiative is completed, it should automatically create the next occurrence.

## Design Requirements

### Core Concept
An initiative is simply a container that holds recurring task templates. Each template defines:
- Task title and description
- Duration in minutes
- Recurrence frequency in days

Example: "Vacuum the floor" with 2-day frequency. If completed after 4 days, the next task appears 2 days from completion.

### Implementation Rules
1. NO bidirectional relationships between models (remove all back_populates)
2. Initiatives store task templates as JSON, not complex ORM relationships
3. Task completion logic handles creating the next occurrence
4. Use raw SQL in routes to avoid ORM recursion issues
5. Keep it simple - initiatives are just recurring task generators

## Files to Modify

### 1. backend/src/data/models/initiative_model.py
- Remove the back_populates from relationships
- Add task_templates column as JSON to store templates
- Simplify to just: id, title, description, is_active, task_templates
- Keep relationship one-way only (tasks reference initiatives)

### 2. backend/src/data/models/task_model.py
- Remove back_populates="tasks" from initiative relationship
- Add recurrence_days field (Integer)
- Keep initiative_id foreign key
- Ensure parent_task_id field exists for tracking recurring instances

### 3. backend/src/api/routes/initiatives.py
- Replace entire file with working version using raw SQL
- Must include proper imports: Session, Depends, get_db, text, uuid, datetime
- Implement these endpoints:
  - GET / - List all initiatives with task counts
  - GET /{id} - Get specific initiative with its tasks
  - POST / - Create initiative with task templates
  - DELETE /{id} - Delete initiative and its tasks

### 4. backend/src/api/routes/tasks.py
- Add or update the complete task endpoint
- When task is completed:
  1. Mark current task as completed
  2. Check if task has initiative_id and recurrence_days
  3. If yes, create new task with due_date = now + recurrence_days
  4. Link new task to same initiative_id

### 5. backend/src/api/app.py
- Change router registration from test_router to proper initiatives router:
```python
  from .routes import initiatives
  app.include_router(initiatives.router, prefix="/api/initiatives", tags=["initiatives"])
Database Migration
Create a migration to:

Add task_templates JSON column to initiatives table
Add recurrence_days column to tasks table
Remove any unnecessary columns from initiatives (status, completion counts, etc.)

Example Data Structure
Initiative with templates:
json{
  "title": "House Cleaning",
  "description": "Regular cleaning tasks",
  "task_templates": [
    {
      "title": "Vacuum the floor",
      "duration": 45,
      "recurrence_days": 2
    },
    {
      "title": "Clean bathroom",
      "duration": 30,
      "recurrence_days": 7
    }
  ]
}
Task completion flow:

User completes "Vacuum the floor" task
System marks it completed
System creates new "Vacuum the floor" task due in 2 days
New task has same initiative_id, allowing tracking

Testing Steps
After implementation:

Create an initiative with 2-3 task templates
Verify tasks are created from templates
Complete a task
Verify new task is created with correct due date
Check that GET /initiatives shows correct task counts
Ensure no recursion errors occur

Success Criteria

No recursion/circular import errors
Can create initiatives with recurring task templates
Completing a task auto-generates the next occurrence
Simple, maintainable code without complex ORM relationships
All endpoints work without crashes

DO NOT

Create bidirectional relationships (no back_populates)
Make the system complex
Use heavy ORM queries that might cause recursion
Add unnecessary features beyond recurring task generation

Start by fixing the model relationships, then update the routes, and finally add the task completion logic.

## Additional Context for Claude

You can also provide this context:
```markdown
## Current Error Context
The system is crashing with a recursion error when accessing /initiatives. This is caused by:
- InitiativeModel.tasks has back_populates="initiative"
- TaskModel.initiative has back_populates="tasks"
- These create a circular dependency

## Key Files Locations
- Models: backend/src/data/models/
- Routes: backend/src/api/routes/
- Database: backend/src/data/database.py
- App: backend/src/api/app.py

## Database Information
- Using SQLAlchemy with PostgreSQL/SQLite
- All IDs are UUIDs (36-character strings)
- Timestamps use datetime.utcnow()

## Priority Order
1. Fix model relationships (highest priority - stops crashes)
2. Update initiatives.py routes with proper imports
3. Fix app.py router registration
4. Add task completion logic
5. Test everything works