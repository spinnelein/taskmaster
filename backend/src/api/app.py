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
            
            # Start polling in background for message handling
            import asyncio
            asyncio.create_task(telegram_service.start_background_polling())
            
            logger.info("Telegram service initialized and polling started")
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
    """Restart the server (development only) with proper process cleanup"""
    import os
    import sys
    import threading
    import subprocess
    import psutil
    import time
    
    def cleanup_and_restart():
        """Clean up processes and restart"""
        try:
            print("=== RESTARTING SERVER ===")
            
            # Get current process info
            current_pid = os.getpid()
            current_port = None
            
            # Find current server port
            for conn in psutil.net_connections():
                if conn.pid == current_pid and conn.laddr and conn.laddr.port >= 8000:
                    current_port = conn.laddr.port
                    break
            
            print(f"Current PID: {current_pid}, Port: {current_port}")
            
            # Find and kill other uvicorn processes on similar ports
            killed_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'uvicorn.exe' and proc.info['pid'] != current_pid:
                        # Check if it's a TaskMaster server by looking at command line
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'src.api.app:app' in cmdline:
                            print(f"Killing conflicting uvicorn process: PID {proc.info['pid']}")
                            proc.kill()
                            killed_processes.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_processes:
                print(f"Killed {len(killed_processes)} conflicting processes")
                time.sleep(1)  # Wait for processes to die
            
            # Find an available port
            import socket
            def find_free_port(start_port=8000):
                for port in range(start_port, start_port + 10):
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        try:
                            s.bind(('', port))
                            return port
                        except OSError:
                            continue
                return start_port + 10  # Fallback
            
            new_port = current_port if current_port else find_free_port()
            
            # Build new command
            new_cmd = [
                sys.executable, 
                '-m', 'uvicorn', 
                'src.api.app:app',
                '--reload',
                '--host', '0.0.0.0',
                '--port', str(new_port)
            ]
            
            print(f"Starting new server on port {new_port}")
            print(f"Command: {' '.join(new_cmd)}")
            
            # Change to backend directory
            backend_dir = os.path.join(os.path.dirname(__file__), '..', '..')
            backend_dir = os.path.abspath(backend_dir)
            
            # Start new process
            subprocess.Popen(
                new_cmd,
                cwd=backend_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            print(f"New server started on port {new_port}")
            time.sleep(2)  # Give new server time to start
            
            # Kill current process
            print("Terminating current process...")
            os._exit(0)
            
        except Exception as e:
            print(f"Error during restart: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simple restart
            os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # Schedule restart after response is sent
    threading.Timer(1.0, cleanup_and_restart).start()
    
    return {"message": "Server restarting with process cleanup...", "status": "initiated"}