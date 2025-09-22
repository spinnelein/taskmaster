# TaskMaster Project Structure

## Overview
TaskMaster is a Flask-based task and schedule management application with integrated weather services and Telegram notifications.

## Active Project Structure

### Root Directory
```
taskmaster/
├── flask_app/              # Main Flask application
├── scripts/                # Testing and utility scripts
├── _archive/               # Archived code
├── _deprecated/            # Deprecated code and tests
├── instance/               # Flask instance folder
├── node_modules/           # Node dependencies for testing
├── __pycache__/           # Python cache files
└── (config files)         # Various configuration files
```

### Core Application Files
- **taskmaster.db** - SQLite database
- **timekeeper.py** - Standalone Telegram notification service
- **CLAUDE.md** - AI assistance documentation
- **README.md** - Project documentation
- **coding_standards.md** - Coding standards
- **requirements_timekeeper.txt** - Timekeeper dependencies
- **package.json** - Node.js dependencies for testing

### Flask Application (`flask_app/`)
```
flask_app/
├── app.py                  # Flask application factory
├── models.py               # SQLAlchemy models
├── routes/                 # Route blueprints
│   ├── __init__.py
│   ├── api.py             # RESTful API endpoints
│   ├── events.py          # Event routes
│   ├── tasks.py           # Task routes
│   └── projects.py        # Project routes
├── templates/              # Jinja2 templates
│   ├── base.html
│   ├── schedule.html
│   ├── events.html
│   ├── tasks.html
│   ├── initiatives.html
│   └── projects.html
├── static/                 # Static assets
│   ├── js/
│   │   └── fullcalendar.min.js
│   └── css/
│       └── fullcalendar.min.css
└── services/               # Business logic services
    ├── background_service.py
    ├── recurring_service.py
    ├── task_queue_service.py
    ├── assignment_service.py
    └── weather_service.py
```

### Testing Scripts (`scripts/`)
```
scripts/
├── browser-debug.js        # Browser debugging utility
├── simple-web-test.js      # Simple HTTP testing
├── simple-schedule-test.js # Schedule testing
├── comprehensive-ui-tests.js # UI testing
├── integration-tests.js    # Integration tests
└── README.md              # Scripts documentation
```

### Configuration Files
- **.env.production** - Production environment (gitignored)
- **port_config.json** - Port configuration
- **telegram_chats.txt** - Telegram chat IDs
- **.gitignore** - Git ignore rules

### Batch Scripts
- **start.bat** - Start all services
- **restart.bat** - Restart services
- **kill.bat** - Kill all processes

## Archived/Deprecated Structure

### `_archive/`
- **frontend_react/** - React frontend (migrated to server-side rendering)

### `_deprecated/`
- **fastapi_backend/** - Complete FastAPI backend (migrated to Flask)
- **migration_docs/** - Migration documentation
- **old_tests/** - Test files from migration
- **old_logs/** - Historical logs
- **old_scripts/** - Deprecated test scripts
- **data_backup/** - Database backups

## Database Schema

### Main Tables
- **events** - Calendar events with recurring support
- **tasks** - Tasks with priority, duration, and dependencies
- **initiatives** - High-level goals and objectives
- **projects** - Project management
- **project_phases** - Project phase tracking
- **time_pools_flask** - Time allocation pools
- **task_assignments** - Task to time pool assignments
- **weather_forecasts** - Weather data cache

## Key Features

1. **Task Management**
   - Priority-based task queue
   - Task dependencies and blocking
   - Recurring tasks support
   - Time pool assignments

2. **Event Scheduling**
   - Recurring events with RRULE support
   - Event notifications via Telegram
   - Calendar view with FullCalendar

3. **Weather Integration**
   - Weather-aware task scheduling
   - Outdoor/indoor task recommendations

4. **Notification System**
   - Telegram bot integration (timekeeper.py)
   - Event start notifications
   - Task reminders

## Development Commands

### Start Application
```bash
cd flask_app
python app.py
```

### Start Timekeeper (Telegram bot)
```bash
python timekeeper.py
```

### Run Tests
```bash
cd scripts
node simple-web-test.js
node browser-debug.js http://localhost:5000
```

## Environment Variables

Required in `.env.production`:
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `OPENWEATHER_API_KEY` - OpenWeatherMap API key (optional)
- Other service API keys as needed

## Port Configuration
- Flask App: 5000
- Database: SQLite (file-based)

## Migration Status
- ✅ Migrated from FastAPI to Flask
- ✅ Migrated from React to server-side rendering
- ✅ Consolidated database models
- ✅ Implemented timezone fixes
- ✅ Cleaned up deprecated code