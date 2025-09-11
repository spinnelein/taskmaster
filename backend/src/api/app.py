"""
FastAPI application setup
NO EMOJIS in comments
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Health check endpoint
@app.get("/health")
def health_check():
    """Check if API is running"""
    return {"status": "healthy", "service": "TaskMaster API"}

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "TaskMaster API", "version": "1.0.0"}