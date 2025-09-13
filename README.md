# TaskMaster

A sophisticated full-stack task and schedule management application with advanced features including recurring events, Telegram notifications, weather integration, and intelligent task scheduling.

## Features

### Task Management
- **Smart Task Queue**: Priority-based task organization with intelligent scoring
- **3-Status Workflow**: Active → Blocked → Completed with dependency management
- **Interactive Reminders**: Telegram notifications with action buttons (Mark Complete, Snooze, Work on Something Else)
- **Project Integration**: Link tasks to initiatives and projects with phase tracking

### Event System
- **Recurring Events**: Industry-standard master/instance architecture for daily/weekly/monthly/yearly patterns
- **Smart Scheduling**: Drag-and-drop time pool scheduling with conflict detection
- **Event Notifications**: Automatic Telegram alerts when events start
- **Pacific Timezone**: Proper local time display and handling

### Advanced Features
- **Weather Integration**: 7-day forecasts with activity suitability recommendations
- **Initiatives & Projects**: Recurring project templates with multi-phase management
- **Meal Planning**: Integrated dish-meal-task workflow for cooking automation
- **Real-time Dashboard**: Live task/event counts with responsive sidebar navigation

## Technology Stack

### Backend
- **FastAPI** 0.104.1 - Modern Python web framework
- **SQLAlchemy** 2.0.23 - Database ORM with async support
- **Pydantic** v2.5.0 - Data validation and serialization
- **APScheduler** 3.10.4 - Background task scheduling
- **Python Telegram Bot** 21.0.1 - Interactive notifications
- **Alembic** 1.12.1 - Database migrations

### Frontend
- **React** 19.1.1 - Modern UI framework
- **Vite** 7.1.2 - Fast build tool
- **TypeScript** 5.9.2 - Type safety
- **React Router** v7.8.2 - Client-side routing
- **Tailwind CSS** 4.1.13 - Utility-first styling
- **React DnD** 16.0.1 - Drag-and-drop functionality

### Database
- **SQLite** (development) with **PostgreSQL** migration path
- UUID primary keys with automatic timestamps
- Comprehensive relationships and foreign key constraints

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git

### 1. Clone Repository
```bash
git clone <repository-url>
cd TaskMaster
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install

# Start development server (runs on port 5173)
npm run dev
```

### 4. Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Environment Configuration

### Required Environment Variables
Create a `.env` file in the `backend/` directory:

```bash
# Database (optional - defaults to SQLite)
DATABASE_URL=sqlite:///./taskmaster.db
# For PostgreSQL: postgresql://user:password@localhost/taskmaster

# Telegram Bot (optional - enables notifications)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Weather API (optional - enables weather features)
OPENWEATHER_API_KEY=your_openweather_api_key
WEATHER_LOCATION=Seattle,WA,US

# Security
SECRET_KEY=your-secret-key-here
```

### Telegram Bot Setup (Optional)
1. Create a bot with [@BotFather](https://t.me/botfather) on Telegram
2. Get your bot token and add it to `.env`
3. Start a conversation with your bot
4. The bot will automatically register users who interact with it

### Weather Service Setup (Optional)
- **Free Option**: Uses National Weather Service API (US locations only)
- **Paid Option**: Get API key from [OpenWeatherMap](https://openweathermap.org/api)
- Add your API key to `.env` for global weather support

## Development

### Database Migrations
```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migrations
alembic downgrade -1
```

### Testing
```bash
cd backend

# Run all tests
python -m pytest

# Run specific test types
python -m pytest tests/unit/         # Unit tests
python -m pytest tests/integration/  # Integration tests

# Run with coverage
python -m pytest --cov=src tests/
```

### Code Quality
```bash
cd frontend

# Lint frontend code
npm run lint

# Build for production
npm run build
```

## API Endpoints

The API follows RESTful conventions with the following main endpoints:

- **Tasks**: `/api/tasks` - Task CRUD operations
- **Events**: `/api/events` - Event management with recurring support
- **Schedule**: `/api/schedule` - Schedule generation and viewing
- **Initiatives**: `/api/initiatives` - Initiative management
- **Projects**: `/api/projects` - Project and phase management
- **Weather**: `/api/weather` - Weather data and forecasts
- **Reminders**: `/api/reminders` - Reminder management
- **Task Queue**: `/api/task-queue` - Task queue operations

Full API documentation is available at `/docs` when the server is running.

## Project Structure

```
TaskMaster/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── api/            # API routes and app setup
│   │   ├── data/           # Models and repositories
│   │   ├── domain/         # Business logic
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business services
│   │   ├── workers/        # Background workers
│   │   └── utils/          # Utility functions
│   ├── tests/              # Test suite
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API service layer
│   │   ├── types/          # TypeScript definitions
│   │   └── utils/          # Utility functions
│   └── package.json        # Node.js dependencies
└── docs/                   # Documentation
```

## Recent Updates (September 2025)

### Major Features Completed
- **Recurring Events**: Master/instance architecture with series editing capabilities
- **Telegram Integration**: Interactive task reminders and event notifications
- **Weather Integration**: Dual API support with database caching
- **Task System Fixes**: Resolved deletion and completion issues
- **Data Cleanup**: Removed 1,093+ duplicate events from old system

### Current Status
- ✅ Backend API fully functional with comprehensive endpoints
- ✅ Frontend React application with modern UI and responsive design
- ✅ Database schema optimized with proper relationships
- ✅ Background workers for automated notifications and scheduling
- ✅ Integration tests and comprehensive test coverage

## Contributing

1. Follow the coding standards in `CODING_STANDARDS.md`
2. No emojis in code (ASCII only for compatibility)
3. Write tests for new features
4. Follow the established architecture patterns
5. Update documentation for new features

## Support

For issues and feature requests, please check the existing documentation in:
- `CLAUDE.md` - Development guidelines and project context
- `FIXES_SUMMARY_2025_09_13.md` - Recent fixes and improvements
- API documentation at `/docs` endpoint

## License

[Add your license information here]