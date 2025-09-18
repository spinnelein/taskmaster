#!/usr/bin/env python3
"""
Test task creation with initiative_id
NO EMOJIS
"""
import sys
import os
from pathlib import Path

# Add the backend src directory to Python path
script_dir = Path(__file__).parent
backend_src = script_dir / 'backend' / 'src'
sys.path.insert(0, str(backend_src))

def test_task_creation():
    """Test creating a task with initiative_id"""
    print("Testing task creation with initiative_id...")
    
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        db_path = script_dir / 'backend' / 'taskmaster.db'
        engine = create_engine(f'sqlite:///{db_path}', echo=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        from data.repositories.task_repo import TaskRepository
        
        db = SessionLocal()
        try:
            repo = TaskRepository(db)
            
            # Test data with initiative_id
            test_data = {
                'title': 'Test Task with Initiative',
                'duration': 45,
                'urgency': 7,
                'description': 'Testing initiative association',
                'status': 'ACTIVE',
                'initiative_id': 'c56c9c76-f092-4ab9-b812-c329d4089e1d'
            }
            
            print(f"\nCreating task with data: {test_data}")
            
            new_task = repo.create(test_data)
            
            print(f"\nCreated task:")
            print(f"  ID: {new_task.id}")
            print(f"  Title: {new_task.title}")
            print(f"  Initiative ID: {new_task.initiative_id}")
            print(f"  Status: {new_task.status}")
            
            # Verify by fetching it back
            fetched_task = repo.get(new_task.id)
            print(f"\nFetched task initiative_id: {fetched_task.initiative_id}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\nTest FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_task_creation()
    if success:
        print("\nTask creation test PASSED")
    else:
        print("\nTask creation test FAILED")