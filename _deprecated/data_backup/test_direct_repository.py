#!/usr/bin/env python3
"""
Test repository directly with new database
NO EMOJIS
"""
import sys
import os
from pathlib import Path

# Add the backend src directory to Python path
script_dir = Path(__file__).parent
backend_src = script_dir.parent / 'backend' / 'src'
sys.path.insert(0, str(backend_src))

def test_repository_directly():
    """Test the repository directly"""
    print("Testing InitiativeRepository directly...")
    
    try:
        # Configure database connection to new database
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        new_db_path = script_dir.parent / 'backend' / 'taskmaster_new.db'
        engine = create_engine(f'sqlite:///{new_db_path}', echo=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        from data.repositories.initiative_repo import InitiativeRepository
        from data.models.initiative_model import InitiativeFrequency, InitiativeStatus
        
        db = SessionLocal()
        try:
            repo = InitiativeRepository(db)
            
            print("1. Testing get_all (should be empty)")
            initiatives = repo.get_all()
            print(f"Found {len(initiatives)} initiatives")
            
            print("\n2. Testing create with proper enum values")
            test_data = {
                "title": "Direct Test Initiative",
                "description": "Testing repository directly",
                "frequency": "daily",  # lowercase string
                "interval": 1
            }
            
            new_initiative = repo.create(test_data)
            print(f"Created initiative: {new_initiative.id}")
            print(f"Stored frequency: {new_initiative.frequency}")
            print(f"Frequency type: {type(new_initiative.frequency)}")
            
            print("\n3. Testing get_all again")
            initiatives = repo.get_all()
            print(f"Found {len(initiatives)} initiatives")
            for init in initiatives:
                print(f"  - {init.title}: frequency={init.frequency} (type: {type(init.frequency)})")
                
            print("\n4. Testing serialization")
            initiative_dict = new_initiative.to_dict()
            print(f"Serialized: {initiative_dict}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Repository test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_repository_directly()
    if success:
        print("\nRepository test PASSED")
    else:
        print("\nRepository test FAILED")