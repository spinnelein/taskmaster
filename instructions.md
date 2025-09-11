Complete Instructions for Claude Code - Initial Setup
Initial Project Setup for TaskMaster
CRITICAL RULES

NO EMOJIS anywhere in code or comments
Use only ASCII characters
Keep files under 150 lines
This is Windows - use appropriate commands

Step 1: Create Project Structure
Commands to run in Windows:

mkdir backend
mkdir backend\src
mkdir backend\src\api
mkdir backend\src\api\routes
mkdir backend\src\domain
mkdir backend\src\data
mkdir backend\src\data\models
mkdir backend\src\data\repositories
mkdir backend\src\services
mkdir backend\src\schemas
mkdir backend\tests
mkdir backend\tests\unit
mkdir backend\tests\integration
mkdir backend\tests\fixtures
mkdir frontend

Step 2: Create .gitignore file in root directory
Create file: .gitignore with content:
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
.env
*.db
.pytest_cache/
.coverage
htmlcov/
*.log

# Node
node_modules/
dist/
.env.local
npm-debug.log*
yarn-debug.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Project
tmp/
*.sqlite
*.db
Step 3: Create README.md in root directory
Create file: README.md with content:
TaskMaster
A web-based task and schedule management application.
Tech Stack

Backend: FastAPI, SQLAlchemy, PostgreSQL/SQLite
Frontend: React, Vite, Tailwind CSS

Setup
See documentation for setup instructions.
Step 4: Commit Initial Structure
Commands to run:

git add .
git commit -m "Initial project structure"
git push origin develop


Now, Milestone 1 for Claude Code:
Milestone 1: Backend Foundation
Git Setup - RUN THESE FIRST

git checkout develop
git pull origin develop
git checkout -b feature/backend-foundation

Create these files in order:
1. backend\requirements.txt
Content:
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
2. backend.env.example
Content:
DATABASE_URL=sqlite:///./taskmaster.db
TEST_DATABASE_URL=sqlite:///./test.db
SECRET_KEY=change-this-secret-key
3. backend\src_init_.py
Create empty file (just for Python package)
4. backend\src\api_init_.py
Create empty file
5. backend\src\api\app.py
Content:
python"""
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
6. backend\src\data_init_.py
Create empty file
7. backend\src\data\database.py
Content:
python"""
Database configuration
NO EMOJIS
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./taskmaster.db")

# Create engine with SQLite compatibility
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
8. backend\src\data\models_init_.py
Content:
python"""
Import all models for Alembic
"""
from .base_model import BaseModel
from .task_model import TaskModel
from .event_model import EventModel

__all__ = ["BaseModel", "TaskModel", "EventModel"]
9. backend\src\data\models\base_model.py
Content:
python"""
Base model with common fields
NO EMOJIS
"""
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..database import Base

class BaseModel(Base):
    """Base model with id and timestamps"""
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        nullable=False
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
10. backend\src\data\models\task_model.py
Content:
python"""
Task database model
NO EMOJIS
"""
from sqlalchemy import Column, String, Integer, Date, Time, Boolean
from .base_model import BaseModel

class TaskModel(BaseModel):
    """Task table model"""
    __tablename__ = "tasks"
    
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    duration = Column(Integer, nullable=False)  # in minutes
    urgency = Column(Integer, default=5)  # 1-10
    status = Column(String(50), default="pending")
    due_date = Column(Date, nullable=True)
    due_time = Column(Time, nullable=True)
    is_completed = Column(Boolean, default=False)
11. backend\src\data\models\event_model.py
Content:
python"""
Event database model
NO EMOJIS
"""
from sqlalchemy import Column, String, DateTime, Boolean
from .base_model import BaseModel

class EventModel(BaseModel):
    """Event table model"""
    __tablename__ = "events"
    
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_blocking = Column(Boolean, default=True)
    location = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
12. backend\tests_init_.py
Create empty file
13. backend\tests\conftest.py
Content:
python"""
Test configuration
NO EMOJIS
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.database import Base
from src.api.app import app

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)
14. backend\tests\unit\test_models.py
Content:
python"""
Test database models
NO EMOJIS
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from datetime import datetime, date, time
from src.data.models.task_model import TaskModel
from src.data.models.event_model import EventModel

def test_task_model_creation(db_session):
    """Test creating a task model"""
    task = TaskModel(
        title="Test Task",
        description="Test Description",
        duration=30,
        urgency=7,
        status="pending"
    )
    
    db_session.add(task)
    db_session.commit()
    
    assert task.id is not None
    assert task.title == "Test Task"
    assert task.duration == 30
    assert task.urgency == 7
    assert task.created_at is not None

def test_event_model_creation(db_session):
    """Test creating an event model"""
    event = EventModel(
        title="Test Event",
        start_time=datetime.now(),
        end_time=datetime.now(),
        is_blocking=True
    )
    
    db_session.add(event)
    db_session.commit()
    
    assert event.id is not None
    assert event.title == "Test Event"
    assert event.is_blocking == True
    assert event.created_at is not None

def test_api_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
Windows Commands to Execute:
Navigate to backend:

cd backend

Create virtual environment:

python -m venv venv

Activate virtual environment:

venv\Scripts\activate

Install requirements:

pip install -r requirements.txt

Create .env file:

copy .env.example .env

Run tests:

pytest tests\unit\test_models.py -v

If tests pass, start the server:

uvicorn src.api.app:app --reload

Server should run on http://localhost:8000
Check http://localhost:8000/health
Git Commands to Complete Milestone:
After tests pass and server runs:

git add .
git commit -m "feat: backend foundation - FastAPI setup with SQLAlchemy models"
git push origin feature/backend-foundation

Create pull request on GitHub or merge locally:

git checkout develop
git merge feature/backend-foundation
git push origin develop
git branch -d feature/backend-foundation

Success Criteria:

All tests pass
Server runs on http://localhost:8000
/health endpoint returns {"status": "healthy"}
No errors in console
Git commits pushed