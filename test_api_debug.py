#!/usr/bin/env python3
"""
Debug the API issue
NO EMOJIS
"""
import sys
import os
from pathlib import Path

# Add the backend src directory to Python path
script_dir = Path(__file__).parent
backend_src = script_dir / 'backend' / 'src'
sys.path.insert(0, str(backend_src))

def test_create_via_api_layer():
    """Test the create process through the API layer"""
    print("Testing create through API layer components...")
    
    try:
        # Set up database connection like the API does
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        db_path = script_dir / 'backend' / 'taskmaster.db'
        engine = create_engine(f'sqlite:///{db_path}', echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        from data.repositories.initiative_repo import InitiativeRepository
        from schemas.initiative_schemas import InitiativeCreate
        
        # Test the schema validation first
        print("1. Testing Pydantic schema validation...")
        test_data = {
            "title": "API Test Initiative",
            "description": "Testing API layer",
            "frequency": "weekly",  # lowercase
            "interval": 2
        }
        
        # Create InitiativeCreate object (this is what FastAPI does)
        initiative_create = InitiativeCreate(**test_data)
        print(f"Schema validated: {initiative_create}")
        print(f"Frequency after validation: {initiative_create.frequency}")
        
        # Convert to dict (this is what model_dump() does)
        create_dict = initiative_create.model_dump()
        print(f"model_dump() result: {create_dict}")
        
        # Test repository create
        print("\n2. Testing repository create...")
        db = SessionLocal()
        try:
            repo = InitiativeRepository(db)
            
            print(f"Before repo.create, data: {create_dict}")
            new_initiative = repo.create(create_dict)
            print(f"Created successfully: {new_initiative.id}")
            print(f"Stored frequency: {new_initiative.frequency}")
            print(f"Frequency type: {type(new_initiative.frequency)}")
            
            # Test serialization
            print(f"Serialized: {new_initiative.to_dict()}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_create_via_api_layer()
    if success:
        print("\nAPI layer test PASSED")
    else:
        print("\nAPI layer test FAILED")