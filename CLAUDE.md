# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaskMaster is a full-stack task and schedule management application with:
- **Backend**: FastAPI 0.104.1 + SQLAlchemy 2.0 + SQLite/PostgreSQL (Python 3.8+)
- **Frontend**: React 19 + Vite 7 + TypeScript 5.9 + Tailwind CSS 4.1

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

# Before executing any coding tasks, read and follow CODING_STANDARDS.md
cat CODING_STANDARDS.md

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

### ✅ Recently Completed (September 2025)

**Major System Overhaul (Sept 13, 2025):**

**Recurring Events Master/Instance Architecture:**
- **Industry Standard Pattern**: Implemented Google Calendar-style master/exception architecture
- **Database Schema**: Added `recurrence_master_id`, `is_recurrence_master`, `is_recurrence_exception`, `recurrence_instance_date` fields
- **RecurringEventsService**: Complete service for managing recurring events with edit modes (This Only, This and Future, All in Series)
- **API Optimization**: Events endpoint now shows only ~15 events instead of 750+ duplicates
- **Frontend Integration**: Fixed schedule page event editing with proper timezone handling
- **Data Cleanup**: Removed 1,093 duplicate events from old recurring logic

**Core System Fixes:**
- **Task Deletion**: Corrected API method calls from `repo.get_by_id()` to `repo.get()` in delete and complete endpoints
- **Event Filtering**: Proper filtering logic to show only master events and standalone events
- **Frontend Counts**: Updated sidebar to use API's `total` field for accurate counts
- **Schema Validation**: Fixed Pydantic v2 compatibility issues across all models

**Weather Integration System:**
- **Dual API Support**: National Weather Service (free) and OpenWeatherMap (paid) integration
- **Database Caching**: Persistent weather storage with 3-hour refresh cycle
- **Smart Detection**: Automatic suitability assessment for outdoor/indoor activities
- **Real Data**: Live 7-day forecasts for Seattle, WA with comprehensive weather conditions
- **API Endpoints**: `/api/weather/current`, `/api/weather/forecast`, `/api/weather/suitable-days`, `/api/weather/update`

**Enhanced Telegram Integration:**
- **Event Notifications**: Automatic rich notifications when events start with full event details
- **Interactive Task Reminders**: Buttons for Mark Complete, Snooze, Work on Something Else
- **Notification Control**: Per-event `notifications_enabled` flag (defaults to True)
- **Background Processing**: APScheduler integration for automated messaging
- **Status Management**: Auto-updates event status to "in_progress" when notifications sent

**Frontend & Backend Stabilization:**
- **Initiatives & Projects**: Complete frontend implementation with navigation, forms, and detail views
- **Modern UI**: Sidebar navigation, real-time badges, responsive design with Tailwind CSS
- **API Stability**: Fixed SQLAlchemy relationship errors and endpoint validation issues
- **Data Models**: Enhanced models for initiatives, projects, meals, dishes with proper relationships

### ✅ Recently Completed (September 13, 2025 - Session 2)

**Critical API Issues Resolution:**
- **Repository Layer Fixes**: Added missing `get_by_id()` method and `to_dict()` serialization to BaseRepository/BaseModel
- **Task Completion Endpoint**: Fixed to use proper repository pattern, now working end-to-end
- **Missing Route Decorators**: Added `@router.get("/{task_id}")` for individual task retrieval
- **Pydantic v2 Migration**: Updated all validators from `@validator` to `@field_validator` with `@classmethod`
- **SQLAlchemy Warnings**: Fixed meal/dish relationship overlaps with proper `overlaps` parameters
- **Comprehensive Testing**: All core CRUD operations verified working with cURL testing

**API Endpoints Now Functional:**
- Tasks: GET (list), GET (individual), POST (create), POST (complete) - all working
- Events: GET (list) working with proper recurring event filtering
- Health: Server status endpoint operational
- Individual endpoints return proper JSON with correct status codes

### ✅ Recently Completed (September 13, 2025 - Session 3)

**Complete Initiatives CRUD System:**
- **Frontend Implementation**: Full-featured initiatives management with create/edit forms
- **Professional UI**: Modern React components matching existing design patterns
- **Comprehensive Routing**: Added `/initiatives/new` and `/initiatives/:id/edit` routes
- **Form Integration**: Connected InitiativeForm to API service with proper validation
- **Error Handling**: Complete error states, loading indicators, and user feedback
- **Navigation**: Updated buttons to use React Router Links instead of placeholders

**Backend Enhancements:**
- **Pydantic v2 Migration**: Updated initiative schemas with `@field_validator` and `@classmethod`
- **Enum Conversion**: Custom repository method handles string-to-enum conversion for frequency/status
- **API Compatibility**: Updated routes to use `model_dump()` instead of deprecated `dict()`
- **Database Schema**: All required tables created with proper relationships

**Code Quality:**
- **CODING_STANDARDS.md Compliance**: No emojis, proper file organization, clean architecture
- **Single Responsibility**: Each component has clear, focused purpose
- **Consistent Patterns**: Matches tasks/events UI implementation patterns

### 🔧 Current Issues to Address
- **Initiatives API Hanging**: Endpoints timeout during GET/POST operations (needs debugging)
- **Weather API**: Configuration-dependent functionality 
- **Projects API**: Similar hanging issue as initiatives (investigation needed)
- **Series-Level Editing UI**: Need frontend interface for editing recurring event series with mode selection
- **Runtime Event Expansion**: Schedule views need to dynamically expand recurring events for display

### 🚀 Planned Upgrades & Roadmap

**Phase 1: API Stabilization (✅ COMPLETED)**
- **✅ Fix Tasks Endpoint**: Schema validation errors resolved, all TaskModel fields properly handled
- **✅ Schema Validation**: Complete alignment of Pydantic schemas with SQLAlchemy models
- **✅ Error Handling**: Improved API error responses and comprehensive testing coverage

**Phase 2: Frontend-Backend Integration (✅ PARTIALLY COMPLETED)**
- **✅ Connect Initiative Forms**: Complete UI implementation with create/edit forms wired to API services
- **Connect Project Forms**: Wire up create/edit forms to `/api/projects/` endpoints  
- **Add Template Management**: UI for creating and using initiative/project templates
- **✅ Form Validation**: Client-side validation matching backend schemas implemented for initiatives

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

**Phase 7: Advanced Features (Low Priority)**
- **Meal Planning Integration**: Full meal-dish-task workflow for cooking
- **Team Collaboration**: Multi-user support, task assignment, shared projects
- **Mobile App**: React Native app for iOS/Android

**Phase 8: Performance & Scalability**
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

- **Backend**: `cd backend && uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000`
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
│       ├── event_model.py           # Event model with master/instance relationships
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
    ├── task_schemas.py              # Task Pydantic schemas (Pydantic v2 ready)
    ├── event_schemas.py             # Event Pydantic schemas
    ├── initiative_schemas.py        # Initiative Pydantic v2 schemas (updated)
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
│   ├── NewInitiative.jsx            # Initiative creation page
│   ├── EditInitiative.jsx           # Initiative editing page
│   ├── InitiativeDetail.jsx         # Initiative detail with stats
│   ├── Projects.jsx                 # Project listing page
│   └── ProjectDetail.jsx            # Project detail with phases/timeline
└── services/
    ├── api.js                       # Axios configuration
    ├── initiativeService.js         # Initiative API calls
    └── projectService.js            # Project API calls
```

## Development Process Management

### Restart Methods (USE THESE - NO DUPLICATE PROCESSES!)

**CRITICAL**: Always use these restart methods instead of manually starting uvicorn/npm to prevent duplicate processes and port conflicts.

**Backend Restart (Choose One):**
```bash
# Option 1: Python script (cross-platform, RECOMMENDED)
cd backend && python restart.py

# Option 2: API endpoint (if server is running)
curl http://localhost:8000/api/restart

# Option 3: Manual process cleanup + start
cd backend && taskkill /f /im uvicorn.exe && uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Restart:**
```bash
# Windows (recommended)
cd frontend && restart-frontend.bat

# Manual cross-platform
cd frontend && taskkill /f /im node.exe && npm run dev
```

**Process Cleanup Commands:**
- Backend: `python restart.py` (kills ALL TaskMaster processes: uvicorn, node.exe, python.exe)
- Frontend: `restart-frontend.bat` (kills all node.exe processes)  
- API Endpoint: `GET /api/restart` (built-in server restart with cleanup)

**IMPORTANT NOTES:**
- Backend restart script kills ALL TaskMaster processes: uvicorn, node.exe, AND python.exe (Telegram/workers)
- This prevents database conflicts from multiple Telegram services or background workers
- Frontend restart script kills only node.exe processes  
- Restart scripts automatically find free ports (8000-8020 for backend, 5173-5180 for frontend)
- Scripts handle process cleanup, dependency checks, and proper startup
- Never manually start servers without killing existing processes first
- Use restart methods for deployments, testing, and development workflow

### Development Commands

**Backend:**
```bash
cd backend
python restart.py              # PREFERRED - handles process cleanup
# OR manually (not recommended):
pip install -r requirements.txt
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
restart-frontend.bat           # PREFERRED - handles process cleanup  
# OR manually (not recommended):
npm install
npm run dev                    # Development server
npm run build                  # Production build
npm run lint                   # ESLint
```

**Testing:**
```bash
cd backend
python -m pytest                    # Run all tests
python -m pytest tests/unit/        # Unit tests only
python -m pytest tests/integration/ # Integration tests only
```

**Database:**
- Migration: `cd backend && alembic upgrade head`
- Create Migration: `cd backend && alembic revision --autogenerate -m "description"`

## Repository Context

This is an active project under development. When making changes:
1. Always test the full stack (backend + frontend)
2. Follow existing patterns and naming conventions
3. Update tests when adding new features
4. Use the existing repository pattern for data access
5. Follow RESTful API conventions for new endpoints
6. For Telegram integration, ensure proper error handling and logging
7. **Current State**: Core API endpoints (tasks, events) fully functional with comprehensive CRUD operations
8. **Current Priority**: Fix database enum issue (WEEKLY status) preventing initiatives API from working