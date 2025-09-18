#!/usr/bin/env python3
"""
Create a fresh database with corrected initiative schema
NO EMOJIS
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / 'src'))

def create_corrected_database():
    """Create fresh database with corrected schema"""
    print("Creating corrected database...")
    
    try:
        from sqlalchemy import create_engine
        from data.database import Base
        
        # Import all models to ensure they're registered
        from data.models.base_model import BaseModel
        from data.models.task_model import TaskModel
        from data.models.event_model import EventModel
        from data.models.reminder_model import ReminderModel
        from data.models.weather_model import WeatherForecastModel
        from data.models.initiative_model import InitiativeModel
        from data.models.project_model import ProjectModel, ProjectPhaseModel
        from data.models.meal_model import MealModel, MealDishModel
        from data.models.dish_model import DishModel
        # from data.models.note_model import NoteModel  # May not exist yet
        
        # Create new database
        db_path = script_dir / 'taskmaster_corrected.db'
        if db_path.exists():
            db_path.unlink()
            
        engine = create_engine(f'sqlite:///{db_path}', echo=True)
        
        # Create all tables
        print("\nCreating tables...")
        Base.metadata.create_all(bind=engine)
        
        print(f"\n✓ Database created successfully at: {db_path}")
        print(f"  Created at: {datetime.now()}")
        
        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n  Tables created ({len(tables)}):")
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            print(f"    - {table} ({len(columns)} columns)")
        
        # Check initiatives table specifically
        print("\n  Initiatives table columns:")
        for col in inspector.get_columns('initiatives'):
            print(f"    - {col['name']}: {col['type']}")
            
        return True
        
    except Exception as e:
        print(f"\nError creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_corrected_database()
    sys.exit(0 if success else 1)