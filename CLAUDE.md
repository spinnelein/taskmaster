# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaskMaster is a full-stack task and schedule management application with:
- **Backend**: FastAPI + SQLAlchemy + SQLite/PostgreSQL (Python)
- **Frontend**: React + Vite + TypeScript + Tailwind CSS

## Architecture

### Backend Structure (`backend/src/`)
- **API Layer**: FastAPI app in `api/app.py` with routers in `api/routes/`
- **Domain Layer**: Business logic in `domain/` (task.py, event.py, schedule.py)
- **Data Layer**: SQLAlchemy models in `data/models/`, repositories in `data/repositories/`
- **Schemas**: Pydantic models for API serialization in `schemas/`
- **Services**: Business services in `services/` (telegram_service.py, reminder_service.py)
- **Workers**: Background processing in `workers/` (reminder_worker.py with APScheduler)
- **Base Model**: All models inherit from `BaseModel` with UUID primary keys and timestamps

### Frontend Structure (`frontend/src/`)
- **React Router**: Multi-page application with modern UI components
- **State Management**: Local state with React hooks
- **API Layer**: Axios-based services in `services/`
- **Components**: Organized by feature (tasks/, events/, schedule/, common/)
- **Modern Design**: Custom CSS with Tailwind, drag-and-drop scheduling

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Development server (port 5173)
npm run build    # Production build
npm run lint     # ESLint
```

### Testing
```bash
cd backend
python -m pytest                    # Run all tests
python -m pytest tests/unit/        # Unit tests only
python -m pytest tests/integration/ # Integration tests only
```

## Key Patterns

### Database Models
- All models extend `BaseModel` with UUID `id`, `created_at`, `updated_at`
- Models are in `backend/src/data/models/` (task_model.py, event_model.py, etc.)
- Use Alembic for migrations: `alembic revision --autogenerate -m "description"`

### API Routes
- Prefix: `/api/{resource}` (e.g., `/api/tasks`, `/api/events`)
- CORS configured for localhost:5173 and localhost:3000
- Health check at `/health`

### Domain Logic
- Business rules in `domain/` classes (Task, Event, Schedule)
- Repository pattern for data access
- Domain objects are separate from SQLAlchemy models

### Frontend Components
- TypeScript preferred for new components
- Use existing patterns in `components/` directories
- API calls through service classes in `services/`

## Important Notes

- **NO EMOJIS**: The codebase explicitly avoids emojis in all code and comments
- **UUID IDs**: All entities use string UUIDs as primary keys
- **Modern UI**: Current focus on modern, clean interface design
- **Testing**: Comprehensive test suite with pytest for backend

## Branch Strategy

- **main**: Stable production branch
- **develop**: Integration branch for features
- **enhanced-data-structures**: Current working branch with new models (dishes, meals, initiatives, projects)
- **gui-overhaul**: UI/UX improvements branch

## Current Development State (enhanced-data-structures branch)

### ✅ Recently Completed (Sept 2025)

**Frontend - Initiatives & Projects Integration:**
- **Complete Frontend Implementation**: Full initiatives and projects pages with navigation, forms, and detail views
- **Advanced Data Models**: Initiative and project models with phases, templates, and relationships
- **Rich UI Components**: Listing pages with filtering, detail pages with stats/timeline, comprehensive forms
- **Navigation Integration**: Added to sidebar with proper routing and page transitions

**Backend - Database & API Fixes:**
- **SQLAlchemy Mapper Fixes**: Resolved critical relationship errors (TaskModel self-reference, EventModel/MealModel circular dependencies)
- **API Endpoint Stabilization**: Fixed initiatives (`/api/initiatives/`), projects (`/api/projects/`), and events (`/api/events/`) endpoints
- **Schema Alignment**: Updated EventResponse and TaskResponse schemas to match model fields
- **Pydantic v2 Compatibility**: Migrated from `.dict()` to `.model_validate()` for proper schema validation
- **Database Migration**: Added `notifications_enabled` field to events table

**Telegram Event Notifications (NEW):**
- **Event Start Notifications**: Automatic Telegram messages when events begin
- **Rich Message Format**: Event details, duration, location, end time, and type information
- **Notification Control**: Per-event `notifications_enabled` flag (defaults to True)
- **Scheduler Integration**: Integrated with existing reminder worker (checks every minute)
- **Status Management**: Auto-updates event status to "in_progress" when notification sent

**Previous Major Updates:**
- **Modern UI Overhaul**: Complete redesign with sidebar navigation, real-time badges, responsive design
- **Task System Simplification**: Reduced from 4 statuses to 3 (Active, Blocked, Completed)  
- **Recurring Events**: Full support for daily/weekly/monthly/yearly patterns with custom intervals
- **Timezone Handling**: Pacific timezone support with proper local time display
- **Enhanced Data Models**: Complete implementation of initiatives, projects, meals, dishes with relationships
- **Telegram Bot Integration**: Interactive task reminders with buttons (Mark Complete, Snooze, Work on Something Else)

**Weather Integration (NEW):**
- **Comprehensive Weather Service**: Dual-API support with National Weather Service (free) and OpenWeatherMap (paid)
- **Database Caching**: Persistent weather storage with 3-hour refresh cycle
- **Smart Weather Detection**: Automatic suitability assessment for outdoor/indoor activities
- **Real Weather Data**: Live 7-day forecasts for Seattle, WA with temperature, precipitation, wind conditions
- **API Endpoints**: `/api/weather/current`, `/api/weather/forecast`, `/api/weather/suitable-days`, `/api/weather/update`

### 🔧 Current Issues to Address
- **Tasks API Endpoint**: Still returning 500 errors due to schema validation issues
- **Form Integration**: Initiative/Project forms need API connection for create/edit operations

### 🚀 Planned Upgrades & Roadmap

**Phase 1: API Stabilization (High Priority)**
- **Fix Tasks Endpoint**: Resolve schema validation errors, ensure all TaskModel fields are properly handled
- **Schema Validation**: Complete alignment of all Pydantic schemas with SQLAlchemy models
- **Error Handling**: Improve API error responses and logging for debugging

**Phase 2: Frontend-Backend Integration (High Priority)**
- **Connect Initiative Forms**: Wire up create/edit forms to `/api/initiatives/` endpoints
- **Connect Project Forms**: Wire up create/edit forms to `/api/projects/` endpoints  
- **Add Template Management**: UI for creating and using initiative/project templates
- **Form Validation**: Client-side validation matching backend schemas

**Phase 3: Advanced Task Management (Medium Priority)**
- **Task Dependencies**: Implement task dependency visualization and management
- **Recurring Tasks**: Task recurrence patterns and automatic generation
- **Task Queue Optimization**: Priority scoring algorithm refinement
- **Bulk Operations**: Multi-select task operations (bulk complete, move, etc.)

**Phase 4: Enhanced Scheduling (Medium Priority)**
- **Schedule Generation**: Automatic task scheduling into time pools
- **Conflict Resolution**: Smart scheduling with conflict detection
- **Calendar Integration**: Google Calendar sync for events
- **Time Tracking**: Actual vs estimated time tracking for tasks/events

**Phase 5: Advanced Notifications (Medium Priority)**  
- **Event Reminders**: Notifications X minutes before event start (configurable per event)
- **Task Deadlines**: Smart deadline reminders based on priority and time remaining
- **Daily Schedule Summary**: Morning digest of day's events and top tasks
- **Notification Channels**: Email notifications in addition to Telegram

**Phase 6: Reporting & Analytics (Low Priority)**
- **Completion Analytics**: Task/project completion rates and trends
- **Time Analytics**: Time spent vs estimated, productivity insights
- **Project Progress**: Gantt charts, milestone tracking, phase completion
- **Export Capabilities**: PDF reports, CSV data export

**Phase 3: Weather Integration (✅ COMPLETED)**
- **✅ Weather Service**: Dual API support (National Weather Service + OpenWeatherMap) with database caching
- **✅ Weather Database Storage**: Persistent weather forecasts with 3-hour cache duration
- **✅ Weather-Based Task Suggestions**: Smart recommendations based on weather conditions
- **✅ API Endpoints**: Current weather, 7-day forecast, suitable days finder, manual updates
- **✅ Task Weather Requirements**: Support for weather-dependent task filtering (already in TaskModel)

**Phase 4: Advanced Task Management (Medium Priority)**
- **Task Dependencies**: Implement task dependency visualization and management
- **Recurring Tasks**: Task recurrence patterns and automatic generation
- **Task Queue Optimization**: Priority scoring algorithm refinement
- **Bulk Operations**: Multi-select task operations (bulk complete, move, etc.)

**Phase 5: Enhanced Scheduling (Medium Priority)**
- **Schedule Generation**: Automatic task scheduling into time pools
- **Conflict Resolution**: Smart scheduling with conflict detection
- **Calendar Integration**: Google Calendar sync for events
- **Time Tracking**: Actual vs estimated time tracking for tasks/events

**Phase 6: Advanced Notifications (Medium Priority)**  
- **Event Reminders**: Notifications X minutes before event start (configurable per event)
- **Task Deadlines**: Smart deadline reminders based on priority and time remaining
- **Daily Schedule Summary**: Morning digest of day's events and top tasks
- **Notification Channels**: Email notifications in addition to Telegram

**Phase 7: Reporting & Analytics (Low Priority)**
- **Completion Analytics**: Task/project completion rates and trends
- **Time Analytics**: Time spent vs estimated, productivity insights
- **Project Progress**: Gantt charts, milestone tracking, phase completion
- **Export Capabilities**: PDF reports, CSV data export

**Phase 8: Advanced Features (Low Priority)**
- **Meal Planning Integration**: Full meal-dish-task workflow for cooking
- **Team Collaboration**: Multi-user support, task assignment, shared projects
- **Mobile App**: React Native app for iOS/Android

**Phase 9: Performance & Scalability**
- **Database Optimization**: Query optimization, proper indexing
- **Caching Layer**: Redis caching for frequently accessed data
- **Background Jobs**: Celery/Redis for heavy operations
- **API Rate Limiting**: Protection against abuse
- **PostgreSQL Migration**: Move from SQLite to PostgreSQL for production

## Key Features

### Task Management
- Simplified 3-status workflow: Active → Blocked → Completed
- Block/unblock functionality for dependency management
- Real-time completion toggles in dashboard
- Project and initiative relationships

### Event System
- Recurring event patterns with flexible end conditions
- Event types: Timed, All Day, Instant
- Pacific timezone with proper local display
- Auto-updating end times based on duration

### Schedule Interface
- Drag-and-drop time pool scheduling
- Time axis visualization with event blocks
- Task queue management
- Mobile-responsive design

## Telegram Bot Integration

### Overview
Comprehensive Telegram notifications for both tasks and events:

**Task Reminders** (Interactive):
- **Mark Complete**: Marks task as finished
- **Snooze Task**: Snoozes reminder (15min, 30min, 1hr, 2hr options)
- **Work on Something Else**: Shows next priority task from queue

**Event Notifications** (Informational):
- **Event Start**: Rich notifications when events begin (unless disabled)
- **Event Details**: Title, description, location, duration, end time, and type
- **Status Updates**: Automatically marks events as "in_progress"

### Components
- **TelegramService** (`services/telegram_service.py`): Bot communication, message sending, button handling
- **EventNotificationService** (`services/event_notification_service.py`): Event-specific notification logic
- **ReminderService** (`services/reminder_service.py`): Task reminder creation and scheduling
- **ReminderWorker** (`workers/reminder_worker.py`): Background processing with APScheduler (tasks + events)
- **ReminderRepository** (`repositories/reminder_repo.py`): Database operations for reminders
- **API Routes** (`api/routes/reminders.py`): REST endpoints for reminder management

### Key Features
- **Interactive Task Messages**: Task details with action buttons
- **Rich Event Messages**: Comprehensive event information with professional formatting
- **Notification Control**: Per-event `notifications_enabled` toggle
- **Smart Scheduling**: Time-based reminders and event notifications
- **Background Processing**: APScheduler handles all notification types
- **Error Handling**: Retry logic and comprehensive logging
- **Status Management**: Automatic status updates for events

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- **IMPORTANT**: Use `.env.production` for sensitive tokens (gitignored)
- **No Chat ID Required**: Bot automatically tracks users who interact with it

### Bot Commands
- `/start`: Register for notifications (automatic)
- `/register`: Alternative registration command
- `/current_task`: Show current task (when implemented)

## Commands to Remember

- **Backend**: `cd backend && uvicorn src.main:app --reload --port 8000`
- **Frontend**: `cd frontend && npm run dev` (usually runs on port 5173)
- **Database Migration**: `cd backend && alembic upgrade head`
- **Create Migration**: `cd backend && alembic revision --autogenerate -m "description"`
- **Run Tests**: `cd backend && python -m pytest tests/`
- **Install Dependencies**: `cd backend && pip install -r requirements.txt`
- **Restart Server**: Available at `/api/restart` endpoint (development only)

## Current File Structure (Key Files)

### Backend (`backend/src/`)
```
├── main.py                          # FastAPI app entry point
├── api/
│   ├── app.py                       # FastAPI application setup
│   └── routes/
│       ├── tasks.py                 # Task CRUD endpoints
│       ├── events.py                # Event CRUD endpoints  
│       ├── initiatives.py           # Initiative CRUD endpoints
│       ├── projects.py              # Project CRUD endpoints
│       └── reminders.py             # Reminder management endpoints
├── data/
│   ├── database.py                  # SQLAlchemy configuration
│   └── models/
│       ├── base_model.py            # Base model with UUID/timestamps
│       ├── task_model.py            # Enhanced task model with relationships
│       ├── event_model.py           # Event model with notifications_enabled
│       ├── initiative_model.py      # Initiative model with recurrence
│       ├── project_model.py         # Project + ProjectPhase models
│       ├── meal_model.py            # Meal planning models
│       └── dish_model.py            # Recipe/dish models
├── services/
│   ├── telegram_service.py          # Telegram bot + event notifications
│   ├── event_notification_service.py # Event-specific notification logic
│   ├── reminder_service.py          # Task reminder management
│   └── task_queue_service.py        # Task priority and queue management
├── workers/
│   └── reminder_worker.py           # APScheduler background jobs (tasks + events)
└── schemas/
    ├── task_schemas.py              # Task Pydantic schemas (needs fixing)
    ├── event_schemas.py             # Event Pydantic schemas
    ├── initiative_schemas.py        # Initiative Pydantic schemas
    └── project_schemas.py           # Project Pydantic schemas
```

### Frontend (`frontend/src/`)
```
├── main.jsx                         # React entry point
├── App.jsx                          # Router configuration with all routes
├── components/
│   ├── layout/
│   │   ├── SidebarNav.jsx           # Navigation with initiatives/projects
│   │   └── ModernLayout.jsx         # Layout wrapper
│   └── forms/
│       ├── InitiativeForm.jsx       # Initiative create/edit form
│       └── ProjectForm.jsx          # Project create/edit form  
├── pages/
│   ├── Initiatives.jsx              # Initiative listing page
│   ├── InitiativeDetail.jsx         # Initiative detail with stats
│   ├── Projects.jsx                 # Project listing page
│   └── ProjectDetail.jsx            # Project detail with phases/timeline
└── services/
    ├── api.js                       # Axios configuration
    ├── initiativeService.js         # Initiative API calls
    └── projectService.js            # Project API calls
```

## Repository Context

This is an active project under development. When making changes:
1. Always test the full stack (backend + frontend)
2. Follow existing patterns and naming conventions
3. Update tests when adding new features
4. Use the existing repository pattern for data access
5. Follow RESTful API conventions for new endpoints
6. For Telegram integration, ensure proper error handling and logging
7. **Known Issues**: Tasks and Events API endpoints return 500 errors due to schema validation mismatches
8. **Current Priority**: Fix API endpoints, then connect frontend forms to working backends