"""
FastAPI application setup
NO EMOJIS
"""
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import tasks, events, schedule, initiatives, projects, meals, dishes, schedules, reminders, task_queue, schedule_generation, weather
from ..data.database import SessionLocal
from ..services.telegram_service import initialize_telegram_service, get_telegram_service
from ..services.weather_service import initialize_weather_service
from ..workers.reminder_worker import initialize_reminder_worker, get_reminder_worker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting TaskMaster API...")
    
    # Initialize Telegram service if token is available
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if telegram_token:
        try:
            telegram_service = initialize_telegram_service(telegram_token)
            await telegram_service.initialize()
            logger.info("Telegram service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Telegram service: {e}")
    else:
        logger.warning("TELEGRAM_BOT_TOKEN not found, Telegram service disabled")
    
    # Initialize weather service (works with or without API key)
    weather_api_key = os.getenv("OPENWEATHER_API_KEY")
    weather_location = os.getenv("WEATHER_LOCATION", "Seattle,WA,US")
    
    try:
        weather_service = initialize_weather_service(weather_api_key, weather_location)
        if weather_api_key:
            logger.info(f"Weather service initialized with OpenWeather API for {weather_location}")
        else:
            logger.info(f"Weather service initialized with National Weather Service API for {weather_location}")
    except Exception as e:
        logger.error(f"Failed to initialize weather service: {e}")
    
    # Initialize reminder worker
    try:
        reminder_worker = initialize_reminder_worker(SessionLocal)
        await reminder_worker.start()
        logger.info("Reminder worker started successfully")
    except Exception as e:
        logger.error(f"Failed to start reminder worker: {e}")
    
    logger.info("TaskMaster API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TaskMaster API...")
    
    # Stop reminder worker
    reminder_worker = get_reminder_worker()
    if reminder_worker:
        try:
            await reminder_worker.stop()
            logger.info("Reminder worker stopped")
        except Exception as e:
            logger.error(f"Error stopping reminder worker: {e}")
    
    # Stop Telegram service
    telegram_service = get_telegram_service()
    if telegram_service:
        try:
            await telegram_service.stop()
            logger.info("Telegram service stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram service: {e}")
    
    logger.info("TaskMaster API shutdown complete")

# Create FastAPI instance
app = FastAPI(
    title="TaskMaster API",
    description="Task and Schedule Management API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API prefix
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["schedule"])
app.include_router(initiatives.router, prefix="/api/initiatives", tags=["initiatives"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(meals.router, prefix="/api/meals", tags=["meals"])
app.include_router(dishes.router, prefix="/api/dishes", tags=["dishes"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["reminders"])
app.include_router(task_queue.router, prefix="/api", tags=["task-queue"])
app.include_router(schedule_generation.router, prefix="/api", tags=["schedule-generation"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])

# Health check endpoint
@app.get("/health")
def health_check():
    """Check if API is running"""
    return {"status": "healthy", "service": "TaskMaster API"}

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "TaskMaster API", "version": "1.0.0", "docs": "/docs"}

# Development restart endpoint
@app.post("/api/restart")
def restart_server():
    """Restart the server (development only)"""
    import os
    import sys
    import threading
    
    def restart():
        """Restart the current process"""
        print("=== RESTARTING SERVER ===")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # Schedule restart after response is sent
    threading.Timer(0.5, restart).start()
    
    return {"message": "Server restarting...", "status": "initiated"}