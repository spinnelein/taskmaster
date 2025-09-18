#!/usr/bin/env python3
"""
Isolated test to identify where the recursion is happening
NO EMOJIS
"""
import sys
import os

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test importing modules one by one to find recursion source"""
    print("Testing imports...")
    
    try:
        print("1. Testing basic imports...")
        from data.database import SessionLocal
        print("   - database import OK")
        
        from data.models.base_model import BaseModel
        print("   - base_model import OK")
        
        from data.models.initiative_model import InitiativeModel
        print("   - initiative_model import OK")
        
        from data.models.task_model import TaskModel
        print("   - task_model import OK")
        
        from data.models.project_model import ProjectModel  
        print("   - project_model import OK")
        
        print("2. Testing database session...")
        db = SessionLocal()
        print("   - database session created OK")
        
        print("3. Testing simple query...")
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).scalar()
        print(f"   - simple query OK: {result}")
        
        print("4. Testing initiatives table...")
        result = db.execute(text("SELECT COUNT(*) FROM initiatives")).scalar()
        print(f"   - initiatives count: {result}")
        
        print("5. Testing model creation...")
        initiative = InitiativeModel()
        print("   - InitiativeModel creation OK")
        
        task = TaskModel()
        print("   - TaskModel creation OK")
        
        project = ProjectModel()
        print("   - ProjectModel creation OK")
        
        db.close()
        print("ALL TESTS PASSED")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)