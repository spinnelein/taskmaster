# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TaskMaster is a full-stack task and schedule management application with:
- **Backend**: Flask + SQLAlchemy + SQLite (Python 3.8+)
- **Frontend**: Server-side rendered HTML templates with vanilla JavaScript
- **Migration Status**: Recently migrated from FastAPI/React to Flask for simplified deployment

## Architecture

### Flask Application Structure (`flask_app/`)
- **Main App**: Flask application factory in `app.py` with route definitions
- **Models**: SQLAlchemy models in `models.py` (Event, Task, Initiative, Project, ProjectPhase)
- **Routes**: Blueprint-based routing in `routes/` directory
  - `api.py`: RESTful API endpoints for AJAX calls
  - `events.py`: Event-specific routes
  - `tasks.py`: Task-specific routes  
  - `projects.py`: Project-specific routes
- **Templates**: Jinja2 HTML templates in `templates/`
- **Static Files**: CSS/JS assets in `static/`
- **Services**: Background services in separate files (background_service.py, recurring_service.py)

### Legacy Backend Structure (`backend/src/`) - DEPRECATED
- Previous FastAPI implementation - kept for reference during migration
- Contains comprehensive business logic and services that may be ported to Flask

## Development Commands

# Before executing any coding tasks, read and follow CODING_STANDARDS.md
cat CODING_STANDARDS.md

### Quick Start (Recommended)
```bash
# Start Flask application
cd flask_app
python app.py        # Starts on port 5000

# Or use the legacy development script (may need updates)
python dev.py flask  # If dev.py has been updated for Flask
```

### Flask Development Commands
```bash
# Flask application
cd flask_app
pip install flask flask-sqlalchemy  # Install dependencies
python app.py                       # Development server on port 5000
flask run                          # Alternative startup method

# Database operations (if Flask-Migrate is added)
flask db init       # Initialize migration repository
flask db migrate    # Create migration
flask db upgrade    # Apply migrations
```

### Testing
```bash
# Flask application testing
cd flask_app
python -m pytest tests/             # Run Flask tests (if test directory exists)

# Test Flask endpoints directly
curl http://localhost:5000/health   # Health check
curl http://localhost:5000/api/events  # API endpoints

# Playwright browser testing (works great with Flask!)
npm run test:web                    # Playwright tests against Flask server
npm run test:ui                     # UI component tests on server-rendered pages
npm run debug:browser -- --head    # Interactive browser debugging

# Legacy backend testing (from previous FastAPI setup)
cd backend
python -m pytest                    # Legacy backend tests for reference
```

## Key Patterns

### Database Models
- All models in `flask_app/models.py` with UUID `id`, `created_at`, `updated_at`
- Models: Event, Task, Initiative, Project, ProjectPhase
- Uses Flask-SQLAlchemy with SQLite database
- Models have `to_dict()` methods for JSON serialization
- Database path: `taskmaster.db` in project root

### API Routes
- Flask blueprints in `flask_app/routes/` directory
- RESTful API endpoints: `/api/{resource}` (e.g., `/api/tasks`, `/api/events`)
- Page routes: `/`, `/events`, `/tasks`, `/initiatives`, `/projects`
- Health check at `/health`

### Templates & Frontend
- Jinja2 templates in `flask_app/templates/`
- Server-side rendering with vanilla JavaScript for interactivity
- FullCalendar integration for schedule views
- Base template structure for consistent layout

### Data Access
- Direct SQLAlchemy model usage (simplified from repository pattern)
- Models handle their own serialization via `to_dict()` methods
- Database session management through Flask-SQLAlchemy

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

## Current Development State (flask-migration branch)

### ✅ Recently Completed (September 2025)

**Major Architecture Migration (Sept 16, 2025):**
- **FastAPI to Flask Migration**: Migrated from FastAPI/React to Flask with server-side rendering
- **Simplified Deployment**: Single Flask application instead of separate backend/frontend
- **Template-Based Frontend**: Jinja2 templates replace React components
- **Consolidated Models**: All models moved to `flask_app/models.py`
- **Blueprint Architecture**: Organized routes using Flask blueprints
- **Database Preservation**: Maintained existing SQLite database and schema

### ✅ Previously Completed (September 2025)

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

### ✅ Recently Completed (September 13, 2025 - Session 4)

**Projects API Complete Stabilization:**
- **Fixed Enum Conversion**: ProjectRepository now handles string-to-enum conversion for priority/status fields (like InitiativeRepository)
- **Pydantic v2 Migration**: Updated all project schemas from `@validator` to `@field_validator` with `@classmethod`
- **Deprecated Method Replacement**: Replaced all `.dict()` calls with `.model_dump()` in project routes
- **Repository Pattern Compliance**: Moved direct database queries to proper repository methods (added `update_phase()` method)

**Process Management Improvements:**
- **Enhanced Node.js Detection**: Improved restart script to target only TaskMaster/Vite processes instead of all node.exe
- **Graceful Shutdown Coordination**: Added proper SIGTERM handling with fallback to SIGKILL for uvicorn and Python services
- **Process Verification**: Added comprehensive verification to ensure all TaskMaster processes are terminated
- **Better Coordination**: Increased shutdown timeouts and added database cleanup coordination

**API Status Update:**
- **Projects API**: Now fully functional with proper enum handling and Pydantic v2 compatibility
- **Initiatives API**: Already working (previous "hanging" documentation was outdated)
- **Core APIs**: Tasks, events, initiatives, and projects all operational with comprehensive CRUD

**Development Environment Improvements:**
- **Enhanced dev.py Script**: Single command to start/stop/status all services with port auto-detection
- **Smart Port Management**: Backend on 8000, frontend auto-detects 5173-5180 with Vite
- **Process Cleanup**: `python dev.py clean` removes orphaned processes and frees ports
- **Cross-Platform**: Works on Windows, macOS, and Linux with proper process handling

### ✅ UI/UX Overhaul Complete (September 14, 2025)

**Phase 1: Modal System & Forms (COMPLETED)**
- **Modal System**: 90vh height limit solving form scrolling issues
- **Enhanced Forms**: Progressive disclosure with collapsible sections
- **Form Components**: Reusable FormGrid, FormField, FormSection, PriorityMatrix
- **Accessibility**: Focus trap, keyboard navigation, WCAG 2.1 AA compliance

**Phase 2: Enhanced Scheduling Interface (COMPLETED)**
- **Multi-Layer Calendar**: 5 distinct layers (events, tasks, meals, personal, work)
- **Drag-and-Drop**: Full support for moving and resizing calendar items
- **Quick Event Creation**: Natural language input ("Meeting at 3pm for 1 hour")
- **Conflict Detection**: Real-time detection with visual indicators

**Phase 3: Dashboard & Navigation (COMPLETED)**
- **Widget Dashboard**: Customizable grid with drag-and-drop using @dnd-kit
- **Command Palette**: Cmd+K/Ctrl+K global access with fuzzy search
- **Smart Notifications**: Toast system with actions, auto-dismiss, and progress bars
- **Real Widgets**: TodaysFocusWidget and CalendarSnapshotWidget with live API data

**Testing Infrastructure Added:**
- **Playwright Integration**: Browser automation for UI testing
- **Test Scripts**: browser-debug.js, test-ui-demo.js for component validation
- **npm Scripts**: test:web, test:ui, debug:browser commands

### 🔧 Current Issues to Address
- **Weather API**: Configuration-dependent functionality (requires API keys)
- **Series-Level Editing UI**: Need frontend interface for editing recurring event series with mode selection
- **Runtime Event Expansion**: Schedule views need to dynamically expand recurring events for display

### 🚀 Planned Upgrades & Roadmap

**Phase 1: API Stabilization (✅ COMPLETED)**
- **✅ Fix Tasks Endpoint**: Schema validation errors resolved, all TaskModel fields properly handled
- **✅ Schema Validation**: Complete alignment of Pydantic schemas with SQLAlchemy models
- **✅ Error Handling**: Improved API error responses and comprehensive testing coverage

**Phase 2: Frontend-Backend Integration (✅ MOSTLY COMPLETED)**
- **✅ Connect Initiative Forms**: Complete UI implementation with create/edit forms wired to API services
- **✅ Fix Projects API**: ProjectRepository enum handling, Pydantic v2 migration, and repository pattern compliance
- **Connect Project Forms**: Wire up create/edit forms to `/api/projects/` endpoints (backend ready, frontend needs connection)
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

## Additional Development Commands

### **Database Operations**:
```bash
# Database migrations
cd backend && alembic upgrade head                     # Apply migrations
cd backend && alembic revision --autogenerate -m "msg" # Create migration

# Run tests
cd backend && python -m pytest tests/               # All tests
cd backend && python -m pytest tests/unit/          # Unit tests only
cd backend && python -m pytest tests/integration/   # Integration tests only
```

### **Dependency Management**:
```bash
# Backend dependencies
cd backend && pip install -r requirements.txt

# Frontend dependencies  
cd frontend && npm install
```

### **Frontend Commands**:
```bash
cd frontend
npm run build        # Production build
npm run lint         # ESLint
npm run test:web     # Playwright browser tests
npm run test:ui      # UI component tests
```

## Current File Structure (Key Files)

### Flask Application (`flask_app/`)
```
├── app.py                           # Flask application factory and main routes
├── models.py                        # SQLAlchemy models (Event, Task, Initiative, Project, ProjectPhase)
├── background_service.py            # Background processing services
├── recurring_service.py             # Recurring event management
├── routes/
│   ├── __init__.py                  # Blueprint initialization
│   ├── api.py                       # RESTful API endpoints for AJAX
│   ├── events.py                    # Event-specific routes
│   ├── tasks.py                     # Task-specific routes
│   └── projects.py                  # Project-specific routes
├── templates/
│   ├── base.html                    # Base Jinja2 template
│   ├── schedule.html                # Main calendar/schedule page
│   ├── events.html                  # Events management page
│   ├── tasks.html                   # Tasks management page
│   ├── initiatives.html             # Initiatives management page
│   └── projects.html                # Projects management page
└── static/
    ├── css/
    │   └── fullcalendar.min.css     # FullCalendar styles
    └── js/
        └── fullcalendar.min.js      # FullCalendar library
```

### Legacy Structure (DEPRECATED - kept for reference)
```
backend/src/                         # Previous FastAPI implementation
frontend/src/                        # Previous React implementation
```

### Root Directory
```
├── taskmaster.db                    # SQLite database (shared with Flask app)
├── flask_app/                      # Current Flask application
├── backend/                         # Legacy FastAPI backend (deprecated)
├── frontend/                        # Legacy React frontend (deprecated)
├── scripts/                         # Testing and utility scripts
│   ├── browser-debug.js             # Playwright browser debugging (still useful!)
│   └── test-ui-demo.js              # UI testing scripts
└── logs/                           # Application and test logs
```

## Development Process Management

### Restart Methods (Flask Application)

**Flask Application Restart:**
```bash
# Simple restart (Ctrl+C then restart)
cd flask_app
python app.py                        # Starts on port 5000

# Process cleanup if needed
taskkill /f /im python.exe           # Windows - kills all Python processes
pkill -f "python app.py"             # Linux/macOS - kills Flask specifically

# Alternative startup methods
cd flask_app
flask run                            # Using Flask CLI
python -m flask run                  # Alternative Flask CLI
```

**Legacy Methods (DEPRECATED - for FastAPI/React):**
```bash
# These were for the previous architecture
cd backend && python restart.py     # Legacy FastAPI restart
cd frontend && restart-frontend.bat # Legacy React restart
```

**Process Cleanup Commands:**
- Backend: `python restart.py` (kills ALL TaskMaster processes: uvicorn, node.exe, python.exe)
- Frontend: `restart-frontend.bat` (kills all node.exe processes)  
- API Endpoint: `GET /api/restart` (built-in server restart with cleanup)

**IMPORTANT NOTES:**
- **Graceful Shutdown**: Backend restart script now uses SIGTERM for graceful shutdown with fallback to SIGKILL
- **Targeted Process Detection**: Enhanced to target only TaskMaster-related processes (uvicorn, node.js with Vite, Python services)
- **Process Verification**: Comprehensive verification ensures all TaskMaster processes are terminated before restart
- **Database Coordination**: Longer wait times allow for proper database connection cleanup
- **Port Management**: Automatically finds free ports (8000-8020 for backend, 5173-5180 for frontend)
- **Cross-Platform**: Scripts work on Windows, Linux, and macOS with proper process handling
- **Development Workflow**: Use restart methods for deployments, testing, and development to prevent conflicts

### Development Commands

**Flask Application:**
```bash
cd flask_app
pip install flask flask-sqlalchemy    # Install dependencies
python app.py                         # Start development server (port 5000)
flask run                            # Alternative startup method

# Database operations (manual for now)
python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
```

**Legacy Commands (DEPRECATED):**
```bash
# Previous FastAPI/React setup
cd backend && python restart.py      # Legacy backend restart
cd frontend && restart-frontend.bat  # Legacy frontend restart
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

**Testing & Debugging:**
- Quick Web Test: `cd frontend && npm run test:web` (tests all endpoints without browser)
- UI Component Test: `cd frontend && npm run test:ui` (automated browser testing with screenshots)
- Interactive Debug: `cd frontend && npm run debug:browser -- --head` (visible browser debugging)
- Direct Script: `node scripts/simple-web-test.js` or `node scripts/browser-debug.js [url] [--head]`

## Repository Context

## Web Testing and Debugging Tools

### Available Testing Scripts (in `/scripts/` directory):

1. **simple-web-test.js** - Lightweight HTTP testing
   - Tests all routes (/, /ui-demo, /tasks, /events, /schedule)
   - Tests API endpoints (/health, /api/tasks, /api/events)
   - No browser installation required
   - Use for: Quick health checks, endpoint validation

2. **browser-debug.js** - Full browser automation with Playwright
   - Console log capture with timestamps
   - JavaScript error detection and stack traces
   - Network request/response monitoring
   - Screenshot capability
   - Custom actions (click, fill, wait, evaluate)
   - Use for: Deep debugging, interaction testing

3. **test-ui-demo.js** - Automated UI testing
   - Tests Phase 1 UI improvements (modals, forms)
   - Automated form interactions and modal testing
   - Screenshots at key interaction points
   - Use for: UI regression testing, modal system validation

### Usage Examples:
- **Quick Check**: `npm run test:web` - Always works, no setup needed
- **UI Testing**: `npm run test:ui` - Full UI automation with screenshots
- **Debug Session**: `npm run debug:browser -- --head` - Interactive browser debugging
- **Custom URL**: `node scripts/browser-debug.js http://localhost:5175/tasks --head`

### Output Files:
- Logs: `/logs/browser-console-{timestamp}.log`
- Screenshots: `/logs/*.png`
- See `/scripts/README.md` for complete documentation

## Repository Context

This is an active project under development. When making changes:
1. Always test the full stack (backend + frontend)
2. **Use testing tools**: Run `npm run test:web` before committing changes
3. Follow existing patterns and naming conventions
4. Update tests when adding new features
5. Use the existing repository pattern for data access
6. Follow RESTful API conventions for new endpoints
7. For Telegram integration, ensure proper error handling and logging
8. **Current State**: Core API endpoints (tasks, events) fully functional with comprehensive CRUD operations
9. **Current Priority**: Phase 1 UI improvements completed with modal system and enhanced forms