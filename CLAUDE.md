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

Recent major updates completed:
- **Modern UI Overhaul**: Complete redesign with sidebar navigation, real-time badges, responsive design
- **Task System Simplification**: Reduced from 4 statuses to 3 (Active, Blocked, Completed)
- **Recurring Events**: Full support for daily/weekly/monthly/yearly patterns with custom intervals
- **Timezone Handling**: Pacific timezone support with proper local time display
- **Real Data Integration**: Replaced all mock data with live API calls
- **Enhanced Data Models**: Complete implementation of initiatives, projects, meals, dishes with relationships
- **Telegram Bot Integration**: Interactive task reminders with buttons (Mark Complete, Snooze, Work on Something Else)

Current branch enhancements in progress:
- Enhanced data structures for dishes, meals, initiatives, and projects
- New models: `dish_model.py`, `meal_model.py`, `initiative_model.py`, `project_model.py`, `project_template_model.py`
- Extended task management with project relationships

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
Interactive task reminders sent via Telegram with inline keyboard buttons:
- **Mark Complete**: Marks task as finished
- **Snooze Task**: Snoozes reminder (15min, 30min, 1hr, 2hr options)
- **Work on Something Else**: Shows next priority task from queue

### Components
- **TelegramService** (`services/telegram_service.py`): Bot communication, message sending, button handling
- **ReminderService** (`services/reminder_service.py`): Reminder creation, scheduling, template processing
- **ReminderWorker** (`workers/reminder_worker.py`): Background processing with APScheduler
- **ReminderRepository** (`repositories/reminder_repo.py`): Database operations for reminders
- **API Routes** (`api/routes/reminders.py`): REST endpoints for reminder management

### Key Features
- **Interactive Messages**: Task details with action buttons
- **Smart Scheduling**: Time-based reminders with snooze functionality  
- **Template System**: Reusable reminder configurations
- **Background Processing**: APScheduler handles reminder sending
- **Error Handling**: Retry logic for failed messages
- **Status Tracking**: Complete reminder lifecycle management

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- `TELEGRAM_DEFAULT_CHAT_ID`: Default chat for reminders
- **IMPORTANT**: Use `.env.production` for sensitive tokens (gitignored)

### Bot Commands
- `/start`: Welcome message
- `/register`: Get chat ID for reminder setup
- `/current_task`: Show current task (when implemented)

## Commands to Remember

- **Backend**: `cd backend && uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000`
- **Frontend**: `cd frontend && npm run dev`
- **Database Migration**: `cd backend && alembic upgrade head`
- **Run Tests**: `cd backend && python -m pytest tests/`
- **Install Dependencies**: `cd backend && pip install -r requirements.txt`

## Repository Context

This is an active project under development. When making changes:
1. Always test the full stack (backend + frontend)
2. Follow existing patterns and naming conventions
3. Update tests when adding new features
4. Use the existing repository pattern for data access
5. Follow RESTful API conventions for new endpoints
6. For Telegram integration, ensure proper error handling and logging