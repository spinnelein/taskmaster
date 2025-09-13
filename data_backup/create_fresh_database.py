#!/usr/bin/env python3
"""
Create fresh database with proper schema
NO EMOJIS
"""
import sys
import os
from pathlib import Path

# Add the backend src directory to Python path
script_dir = Path(__file__).parent
backend_src = script_dir.parent / 'backend' / 'src'
sys.path.insert(0, str(backend_src))

def create_fresh_database():
    """Create a fresh database with proper schema"""
    print("Creating fresh database with proper schema...")
    
    from data.database import engine, Base
    from data.models import (
        base_model, task_model, event_model, initiative_model, 
        project_model, meal_model, dish_model, reminder_model,
        schedule_model, weather_model
    )
    
    try:
        # Create all tables
        print("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"Successfully created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")
        
        # Verify initiatives table schema
        if 'initiatives' in tables:
            print("\nInitiatives table columns:")
            columns = inspector.get_columns('initiatives')
            for col in columns:
                print(f"  - {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(required)'}")
        
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test that we can connect to and query the new database"""
    print("\nTesting database connection...")
    
    try:
        from data.database import SessionLocal
        from data.repositories.initiative_repo import InitiativeRepository
        from data.models.initiative_model import InitiativeFrequency, InitiativeStatus
        
        db = SessionLocal()
        try:
            # Test repository operations
            repo = InitiativeRepository(db)
            
            # Test get_all (should return empty list)
            initiatives = repo.get_all()
            print(f"Found {len(initiatives)} initiatives (expected 0)")
            
            # Test create operation
            test_data = {
                "title": "Test Initiative",
                "description": "Testing database functionality",
                "frequency": InitiativeFrequency.WEEKLY,
                "interval": 1,
                "status": InitiativeStatus.ACTIVE
            }
            
            new_initiative = repo.create(test_data)
            print(f"Created test initiative: {new_initiative.id}")
            
            # Test get operation
            retrieved = repo.get(new_initiative.id)
            if retrieved:
                print(f"Retrieved initiative: {retrieved.title}")
            
            # Clean up test data
            repo.delete(new_initiative.id)
            print("Cleaned up test initiative")
            
            print("Database connection test PASSED")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Database connection test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("Fresh Database Creation Script")
    print("=" * 40)
    
    # Create fresh database
    if create_fresh_database():
        print("\nDatabase created successfully!")
        
        # Test the database
        if test_database_connection():
            print("\nAll tests passed! Database is ready for use.")
        else:
            print("\nWarning: Database created but connection test failed.")
    else:
        print("\nFailed to create database.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())