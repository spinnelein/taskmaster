"""
FastAPI application setup
NO EMOJIS
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import tasks, events, schedule

# Create FastAPI instance
app = FastAPI(
    title="TaskMaster API",
    description="Task and Schedule Management API",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with API prefix
app.include_router(tasks.router, prefix="/api/tasks")
app.include_router(events.router, prefix="/api/events")
app.include_router(schedule.router, prefix="/api/schedule")

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